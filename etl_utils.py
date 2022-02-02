import json
from dateutil.parser import parse
import global_vars as gv
import os
from datetime import date


def response_to_json(r_text):
    try:
        res = json.loads(r_text)
    except TypeError:
        res = None
    return res


def get_month(my_date):
    p_date = parse(my_date)
    res = "%s_%02d" % (p_date.year, p_date.month)
    return res


def get_parsed_date(my_date):
    p_date = parse(my_date)
    res = "%s-%02d-%02d" % (p_date.year, p_date.month, p_date.day)
    return res


def get_week(my_date):
    p_date = parse(my_date)
    res = "W_%s_%s" % (p_date.strftime('%Y'), p_date.strftime('%V'))
    return res


def get_role(cen_id):
    # returns role based on entry in my_squads csv file
    res = gv.my_squads.loc[gv.my_squads['id'] == cen_id].get('role')
    if len(res.index) == 0:
        return 'NOT_FOUND'
    return res.values[0]


def get_squad(cen_id):
    # returns squad based on entry in my_squads csv file
    res = gv.my_squads.loc[gv.my_squads['id'] == cen_id].get('squad')
    if len(res.index) == 0:
        return 'NOT_FOUND'
    return res.values[0]


def get_name(cen_id):
    # returns name based on entry in my_squads csv file
    res = gv.my_squads.loc[gv.my_squads['id'] == cen_id].get('name')
    if len(res.index) == 0:
        # print(cen_id + ' NOT_FOUND')
        return 'NOT_FOUND'
    return res.values[0]


def has_rtb_label(my_labels):
    if 'rtb' in my_labels or 'RTB' in my_labels:
        return True
    else:
        return False


def has_ctb_label(my_labels):
    if 'ctb' in my_labels or 'CTB' in my_labels:
        return True
    else:
        return False


def agg_labels(jira_issue, parent_issue):
    issue_labels = jira_issue.get('fields').get('labels')
    if parent_issue is not None:
        parent_labels = parent_issue.get('fields').get('labels')
    else:
        parent_labels = []
    return issue_labels + parent_labels


def get_rtb_ctb(wt):
    # returns value based on worklog type
    if wt == 'Unknown':
        return 'Unknown'
    elif wt in ['Label_CTB', 'TechDebt']:
        return 'CTB'
    elif wt == 'Řízení dodávky':
        return 'Overhead'
    elif wt == 'Rozvoj':
        return 'Rozvoj'
    else:
        return 'RTB'


def get_csv_fname():
    return '%s%s.csv' % (gv.config[gv.ENV]['base_csv'], get_parsed_date(date.today().strftime('%Y-%m-%d')))


def save_csv(my_df):
    fname = get_csv_fname()
    if gv.simplify_switch:      # for case when we do not need some columns
        my_df = my_df.drop(columns=['WORK_TYPE', 'WORK_RTB_CTB', 'ROLE'])
    if not os.path.isfile(fname):
        my_df.to_csv(fname, sep=';', index=False, encoding='utf8', decimal=',')
    else:
        my_df.to_csv(fname, sep=';', index=False, encoding='utf8', mode='a', header=False, decimal=',')


def delete_csv():
    fname = get_csv_fname()
    if os.path.exists(fname):
        os.remove(fname)


def print_progressbar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', print_end="\r"):
    if total == 0:
        percent = 100.0
        filled_length = length
    else:
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=print_end)
    # Print New Line on Complete
    if iteration == total:
        print()
