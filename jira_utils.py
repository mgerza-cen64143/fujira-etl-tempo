from etl_utils import *
import requests
import global_vars as gv


def get_issues_jql(my_query):
    # input JQL query
    # returns JSON acquired from REST API
    url = gv.base_url + 'search'
    query = {
        'jql': my_query,
        'maxResults': 10000
    }
    if gv.auth_cookies:
        response = requests.request(
            "GET",
            url,
            headers={"Accept": "application/json"},
            params=query,
            cookies=gv.cj,
            verify=False
        )
    else:
        response = requests.request(
            "GET",
            url,
            headers={"Accept": "application/json"},
            params=query,
            auth=gv.auth,
            verify=False
        )

    if not response.ok:
        print('JIRA query failed', response.text)
        return None
    gv.total_calls = gv.total_calls + 1
    return response_to_json(response.text)


def get_worklogs(issue_key):
    # returns worklog from JIRA ticket
    url = gv.base_url + "issue/%s/worklog" % issue_key
    if gv.auth_cookies:
        response = requests.request(
            "GET",
            url,
            headers={"Accept": "application/json"},
            cookies=gv.cj,
            verify=False
        )
    else:
        response = requests.request(
            "GET",
            url,
            headers={"Accept": "application/json"},
            auth=gv.auth,
            verify=False
        )

    if not response.ok:
        print('JIRA query failed', response.text)
        return None
    gv.total_worklog_calls = gv.total_worklog_calls + 1
    return response_to_json(response.text)


def get_issue(jira_key):
    # returns single jira ticket specified by JIRA key
    i = get_issues_jql('issue=%s' % jira_key)
    return i['issues'][0]


def get_parent_ini_folder(jira_issue):
    # returns parent Initiative or Folder when found, or None
    if jira_issue['fields'].get('issuelinks') is not None:
        for il in jira_issue['fields'].get('issuelinks'):
            if il.get('type') is None:
                break
            if il.get('inwardIssue') is None:
                break
            if il['type']['name'] == "Initiative" or il['type']['name'] == "Folder":
                return get_issue(il['inwardIssue']['key'])
    return None


def get_parent(jira_issue):
    # function to acquire parent in JIRA hierarchy
    # uses caching
    # logic is - first match wins in following order
    # 1. key in list of overloaded top parents
    # 2. parent of subtask
    # 3. Epic of issue
    # 4. Initiative or Folder
    # 5. Parent of Defect, which can be in relationship
    # 5.1 Created by Story, Task, Epic, Execution
    # 5.2 Belongs to Epic
    # 5.3 Relates to Story/Task

    if jira_issue is None:
        return None
    if gv.parent_cache.get(jira_issue.get('key')) is not None:
        return gv.parent_cache.get(jira_issue['key'])

    defect_parent = get_defect_parent(jira_issue)

    parent_ini_folder = get_parent_ini_folder(jira_issue)
    if jira_issue['key'] in list(gv.overloaded_issues.keys()):
        parent_issue = get_issue(jira_issue['key'])
    elif jira_issue['fields'].get('parent') is not None:
        parent_issue = get_issue(jira_issue['fields'].get('parent').get('key'))
    elif jira_issue['fields'].get('customfield_10101') is not None:
        parent_issue = get_issue(jira_issue['fields'].get('customfield_10101'))
    elif parent_ini_folder is not None:
        parent_issue = parent_ini_folder
    elif defect_parent is not None:
        parent_issue = defect_parent
    else:
        parent_issue = None
    if parent_issue is not None:
        gv.parent_cache[jira_issue['key']] = parent_issue
    return parent_issue


def is_overloaded_parent(jira_issue):
    if jira_issue is None:
        return False
    if jira_issue['key'] in list(gv.overloaded_issues.keys()):
        return True
    return False


def update_current_label(my_work_label):
    if my_work_label is None:
        return
    if gv.current_labels is None:
        gv.current_labels = my_work_label


def get_top_parent(jira_issue):
    # Recursively travers JIRA ticket hierarchy for TOP parent
    last_parent = jira_issue
    new_parent = get_parent(last_parent)
    if is_overloaded_parent(jira_issue):
        return jira_issue
    while new_parent is not None:
        update_current_label(get_work_label(new_parent['fields']['labels']))
        last_parent = new_parent
        new_parent = get_parent(last_parent)
        if new_parent == last_parent:
            break
    return last_parent


def is_measured_worklog(my_date):
    # parse worklogs only after start_date
    p_date = parse(my_date)
    if p_date >= gv.oldest_date.astimezone():
        return True
    return False


def get_test_execution_parent(j_issue):
    i_links = j_issue['fields'].get('issuelinks')
    if i_links is None:
        return j_issue

    res = j_issue
    for i_link in i_links:
        if get_issuelink_type(i_link) in ['created by', 'relates to'] and \
                get_issuelink_name(i_link) in ['T-Task', 'Story', 'Task']:
            my_issue = get_linked_issue(i_link)
            res = get_top_parent(my_issue)

    return res


def get_issuelink_type(issue_link):
    if issue_link is not None:
        return issue_link['type']['inward']


def get_extract_link(issue_link):
    res = issue_link.get('inwardIssue')
    if res is None:
        res = issue_link.get('outwardIssue')
    if res is None:
        return None
    return res


def get_issuelink_name(issue_link):
    res = get_extract_link(issue_link)
    if res is None:
        return None
    return res['fields']['issuetype']['name']


def get_linked_issue(issue_link):
    res = get_extract_link(issue_link)
    if res is None:
        return None
    return get_issue(res['key'])


def get_work_label(issue_labels):
    if issue_labels is None:
        return None
    if 'RTB' in issue_labels:
        return 'Label_RTB'
    if 'CTB' in issue_labels:
        return 'Label_CTB'


def get_defect_parent(jira_issue):
    if jira_issue['fields']['issuetype']['name'] != 'Defect':
        return None
    i_links = jira_issue['fields'].get('issuelinks')
    if i_links is None:
        return jira_issue
    res = jira_issue
    for i_link in i_links:
        if get_issuelink_type(i_link) in ['created by', 'relates to'] \
                and get_issuelink_name(i_link) in ['Story', 'Task', 'Epic']:
            my_issue = get_linked_issue(i_link)
            res = get_top_parent(my_issue)
        elif get_issuelink_type(i_link) == 'created by' and get_issuelink_name(i_link) == 'T-Task':
            res = get_top_parent(get_linked_issue(i_link))
        elif get_issuelink_type(i_link) == 'created by' and get_issuelink_name(i_link) == 'Test Execution':
            res = get_test_execution_parent(get_linked_issue(i_link))
    return res


def is_fat_defect(jira_issue):
    # FAT defects are CTB if not specified otherwise
    if jira_issue['fields']['issuetype']['name'] != 'Defect':
        return False
    if jira_issue['fields']['reporter']['name'] == 'CEN67440' and \
            jira_issue['fields']['customfield_13404'][0]['value'] == 'INT':
        return True
    return False


def is_dev_defect(jira_issue):
    if jira_issue['fields']['issuetype']['name'] != 'Defect':
        return False
    if jira_issue['fields']['customfield_13404'][0]['value'] == 'DEV':
        return True
    return False


def is_prod_defect(jira_issue):
    if jira_issue['fields']['issuetype']['name'] != 'Defect':
        return False
    if jira_issue['fields']['customfield_13404'][0]['value'] in ['PROD', 'PRS']:
        return True
    return False


def get_folder_type(jira_issue):
    # When ther is no label
    if jira_issue['fields']['customfield_13108']['value'] == 'Drobný rozvoj':
        return 'Label_CTB'
    elif jira_issue['fields']['customfield_13108']['value'] == 'BAU':
        return 'Label_RTB'
    return 'Unknown'


def get_epic(jira_issue):
    # Epics are specified by customfield 10101
    if jira_issue['fields'].get('customfield_10101') is not None:
        my_key = jira_issue['fields'].get('customfield_10101')
        return my_key, my_key + ' ' + get_issue(my_key)['fields']['summary']
    elif jira_issue['fields']['issuetype']['name'] == 'Epic':
        return jira_issue['key'], jira_issue['key'] + ' ' + jira_issue['fields']['summary']
    return 'Unknown', 'Unknown'


# returns {'Label_CTB', 'Label_RTB', 'Overhead', 'ProdBugs', 'Regression', ..., 'Unknown'}
def get_work_type(jira_issue, my_parent, my_top_parent):
    if gv.simplify_switch:
        return 'Unknown'
    my_labels = agg_labels(jira_issue, my_parent)
    if my_top_parent['key'] in list(gv.overloaded_issues.keys()):
        return gv.overloaded_issues[my_top_parent['key']]
    elif has_rtb_label(my_labels):
        return 'Label_RTB'
    elif has_ctb_label(my_labels):
        return 'Label_CTB'
    elif my_top_parent['fields']['issuetype']['name'] == 'Initiative' and \
            my_top_parent['fields']['project']['key'] == 'UF':
        return 'Label_CTB'
    elif my_top_parent['fields']['issuetype']['name'] in ['Initiative', 'Folder'] and \
            my_top_parent['fields']['project']['key'] != 'UF':
        return 'Label_RTB'
    elif is_fat_defect(jira_issue):
        return 'Label_CTB'
    elif is_dev_defect(jira_issue) and jira_issue == my_top_parent:
        return 'Label_CTB'
    elif is_prod_defect(jira_issue):
        return 'Label_RTB'
    elif gv.current_labels is not None:
        return gv.current_labels
    elif my_top_parent['fields']['issuetype']['name'] == 'Folder':
        return get_folder_type(my_top_parent)

    return 'Unknown'


def parse_worklog(my_wlog, top_parent, jira_issue):
    # parses worklog and adds metadata
    my_user_cen = my_wlog['author']['name']
    my_user_name = get_name(my_user_cen)
    if my_user_name == 'NOT_FOUND':
        # print('Not found: ', my_user_cen, jira_issue['key'])
        return None

    if not is_measured_worklog(my_wlog['started']):
        return None

    my_time_spent = float(my_wlog['timeSpentSeconds']) / 3600
    my_role = get_role(my_user_cen)
    my_squad = get_squad(my_user_cen)

    if my_role == 'NOT_FOUND' and my_squad == 'NOT_FOUND':
        return None

    my_date_logged = get_parsed_date(my_wlog['started'])
    my_week_logged = get_week(my_wlog['started'])
    my_top_parent = top_parent['key']
    my_top_parent_type = top_parent['fields']['issuetype']['name']
    my_parent = get_parent(jira_issue)

    if my_parent is None:
        my_parent = top_parent
    my_work_type = get_work_type(jira_issue, my_parent, top_parent)
    my_work_rtbctb = get_rtb_ctb(my_work_type)
    my_month = get_month(my_date_logged)

    my_epic, my_epic_name = get_epic(jira_issue)
    ticket_name = jira_issue['key'] + ' ' + jira_issue['fields']['summary']
    parent_name = top_parent['key'] + ' ' + top_parent['fields']['summary']
    my_key = jira_issue['key']

    my_dict = {'KEY': my_key, 'TIME_SPENT': my_time_spent, 'USER_ID': my_user_cen, 'DATE': my_date_logged,
               'MONTH': my_month, 'WEEK': my_week_logged,
               'PARENT': my_top_parent, 'PARENT_TYPE': my_top_parent_type, 'WORK_TYPE': my_work_type,
               'WORK_RTB_CTB': my_work_rtbctb, 'USER_NAME': my_user_name,
               'SQUAD': my_squad, 'ROLE': my_role, 'EPIC': my_epic, 'EPIC_NAME': my_epic_name,
               'PARENT_NAME': parent_name, 'TICKET_NAME': ticket_name}
    return my_dict


def assemble_query():
    # prepares query for JIRA tickets based on squad members
    if gv.config[gv.ENV]['jira_query'] != '__SQUADS__':
        return gv.config[gv.ENV]['jira_query']

    my_cens = gv.my_squads.get('id')
    my_jql_query = ''
    my_date = get_parsed_date(gv.config[gv.ENV]['start_date'])
    for my_id in my_cens:
        str1 = '''issueFunction in worklogged("after '%s' by %s") OR ''' % (my_date, my_id)
        my_jql_query = my_jql_query + str1
    return my_jql_query[:len(my_jql_query) - 3]
