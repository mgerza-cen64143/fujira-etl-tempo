import requests
from requests.auth import HTTPBasicAuth
import json
import pandas as pd
import time
import configparser
import sys
import getopt
import global_vars as gv
from jira_utils import *
import os

requests.packages.urllib3.disable_warnings()

'''
Init application
'''
try:
    opts, args = getopt.getopt(sys.argv[1:], "e:")
except getopt.GetoptError:
    print('etl.py -e <jira_environment>')
    sys.exit(2)

if len(opts) == 0:
    print('etl.py -e <jira_environment>')
    sys.exit(2)

gv.ENV = opts[0][1]
gv.config = configparser.ConfigParser()
gv.config.read('etl.conf', encoding="utf8")
gv.auth = HTTPBasicAuth(gv.config[gv.ENV]['jira_username'], gv.config[gv.ENV]['jira_password'])
gv.oldest_date = parse(gv.config[gv.ENV]['start_date'])
gv.my_squads = pd.read_csv(gv.config[gv.ENV]['my_squads'], delimiter=';', encoding='CP1250')
gv.overloaded_issues = json.loads(gv.config[gv.ENV]['issues_top_overload'])
gv.simplify_switch = gv.config[gv.ENV].getboolean('simplify')
gv.base_url = gv.config[gv.ENV]['base_url']
gv.auth_cookies = gv.config[gv.ENV].getboolean('auth_cookies')
if gv.config[gv.ENV]['auth_cookies'] is None:
    gv.cj = ''
    gv.auth_cookies=False
elif not gv.config[gv.ENV]['auth_cookies']:
    gv.cj = ''
    gv.auth_cookies = False
else:
    from os.path import expanduser
    import browser_cookie3
    my_home = expanduser("~")
    gv.cj = browser_cookie3.chrome(
       cookie_file="%s\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 2\\Network\\Cookies" % my_home)
    gv.auth_cookies=True

'''
Functions definitions
'''


def main():
    jql_query = assemble_query()
    print('Querying for JIRA issues.')
    jira_issues = get_issues_jql(jql_query)
    iss = jira_issues.get('issues')
    iss_count = len(iss)
    print('Got issues, count:', iss_count)
    delete_csv()

    for i_count, i in enumerate(iss):
        df = pd.DataFrame()
        gv.current_labels = None
        ti = get_top_parent(i)
        wl = get_worklogs(i['key'])
        wl_count = len(wl['worklogs'])
        print(i['key'], '- Worklog count: ', wl_count)
        print_progressbar(0, wl_count, prefix='[%05d / %05d] %10s progress' % (i_count, iss_count, i['key']),
                          suffix='Complete', length=50, print_end='')
        for c, wlog in enumerate(wl['worklogs']):
            print_progressbar(c + 1, wl_count, prefix='[%05d / %05d] %10s progress' % (i_count, iss_count, i['key']),
                              suffix='Complete', length=50, print_end='')
            my_dict = parse_worklog(wlog, ti, i)
            if my_dict is not None:
                df = pd.DataFrame(my_dict,index=[0])
                save_csv(df)

    print('Processed %d issues' % iss_count)
    print('Profile used: %s'% gv.ENV)
    print('CSV saved as %s' % get_csv_fname())
    print('REST api JQL calls:', gv.total_calls)
    print('REST api Worklog calls:', gv.total_worklog_calls)
    print('Total REST api calls:', gv.total_calls + gv.total_worklog_calls)


'''
main part of code
'''
if __name__ == "__main__":
    start_time = time.time()
    main()
    print("--- %0d seconds ---" % (time.time() - start_time))
