from requests.auth import HTTPBasicAuth
from dateutil.parser import parse
import json
import pandas as pd

ENV = None
config = None
auth = None
cpath = None
cj = None
current_issue = None
current_labels = None
parent_cache = {}
oldest_date = None
my_squads = None
overloaded_issues = None
simplify_switch = None
base_url = None
auth_cookies = None
total_worklog_calls = 0
total_calls = 0
