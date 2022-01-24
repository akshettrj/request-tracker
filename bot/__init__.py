import os
import re
from dotenv import load_dotenv

import logging

from bot.helpers.database import Database

logging.basicConfig(
    format='[%(levelname)s] (%(asctime)s) %(message)s'
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

if os.path.exists('./config.env'):
    print("Loading config variables from config.env file")
    load_dotenv('./config.env')

def _missing_env_var(var: str):
    logger.error(f'Environment variable {var} missing or has some errors! Check sample_config.py for more')
    exit(1)

# '''''''''''''''''''''''''''''''''''''''''''''''''''''''

API_ID = int(os.environ.get('API_ID', '-1'))
if API_ID == -1:
    _missing_env_var('API_ID')

API_HASH = os.environ.get('API_HASH', '')
if API_HASH == '':
    _missing_env_var('API_HASH')

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
SESSION_STRING = os.environ.get('SESSION_STRING', '')

if BOT_TOKEN == '' and SESSION_STRING == '':
    logger.error('Set either BOT_TOKEN or SESSION_STRING to continue!')
    exit(1)

# '''''''''''''''''''''''''''''''''''''''''''''''''''''''

GROUP_ID = int(os.environ.get('GROUP_ID', '-1'))
if GROUP_ID == -1:
    _missing_env_var('GROUP_ID')

GROUP_NAME = os.environ.get('GROUP_NAME', '')
if GROUP_NAME == '':
    _missing_env_var('GROUP_NAME')

EZBOOKBOT_ID = int(os.environ.get('EZBOOKBOT_ID', '1699727751'))

_SUDO_USERS = os.environ.get('SUDO_USERS', '').split()
if len(_SUDO_USERS) == 0:
    _missing_env_var('SUDO_USERS')

SUDO_USERS = []
for usr_id in _SUDO_USERS:
    if usr_id.isnumeric():
        SUDO_USERS.append(int(usr_id))
    else:
        logger.warning(f'The value {usr_id} is not a valid user id.')

if len(SUDO_USERS) == 0:
    _missing_env_var('SUDO_USERS')

_req_time_regex = re.compile(r'^(\d+)(min|d|s)$')

ENG_REQ_TIME = os.environ.get('ENG_REQ_TIME', '8d').strip()
NON_ENG_REQ_TIME = os.environ.get('NON_ENG_REQ_TIME', '15d').strip()

_eng_req_time = _req_time_regex.fullmatch(ENG_REQ_TIME)
if (_eng_req_time is None) or (len(_eng_req_time.groups()) != 2):
    _missing_env_var('ENG_REQ_TIME')
_non_eng_req_time = _req_time_regex.fullmatch(NON_ENG_REQ_TIME)
if (_non_eng_req_time is None) or (len(_non_eng_req_time.groups()) != 2):
    _missing_env_var('NON_ENG_REQ_TIME')

REQ_TIMES = {
            'eng': {
                'value': int(_eng_req_time.groups()[0]),
                'type': _eng_req_time.groups()[1]
            },
            'non_eng': {
                'value': int(_non_eng_req_time.groups()[0]),
                'type': _non_eng_req_time.groups()[1]
            }
        }

if REQ_TIMES['eng']['type'] == 'd':
    REQ_TIMES['eng']['full'] = f'{REQ_TIMES["eng"]["value"]} days'
elif REQ_TIMES['eng']['type'] == 'min':
    REQ_TIMES['eng']['full'] = f'{REQ_TIMES["eng"]["value"]} minutes'
elif REQ_TIMES['eng']['type'] == 's':
    REQ_TIMES['eng']['full'] = f'{REQ_TIMES["eng"]["value"]} seconds'

if REQ_TIMES['non_eng']['type'] == 'd':
    REQ_TIMES['non_eng']['full'] = f'{REQ_TIMES["non_eng"]["value"]} days'
elif REQ_TIMES['non_eng']['type'] == 'min':
    REQ_TIMES['non_eng']['full'] = f'{REQ_TIMES["non_eng"]["value"]} minutes'
elif REQ_TIMES['non_eng']['type'] == 's':
    REQ_TIMES['non_eng']['full'] = f'{REQ_TIMES["non_eng"]["value"]} seconds'

EXCLUDED_HASHTAGS = os.environ.get('EXCLUDED_HASHTAGS', '#scribd #storytel').strip().split()
EXCLUDED_HASHTAGS = set([hashtag.lower() for hashtag in EXCLUDED_HASHTAGS])


DATABASE_URL = os.environ.get('DATABASE_URL', '')
if DATABASE_URL == '':
    _missing_env_var('DATABASE_URL')

COMMAND_PREFIXES = ["/", "!"]

DB = Database(DATABASE_URL)

NAME_CACHE = DB.get_users()

HELP_DATA = [
    ["help", "Get this help message", ["SUDO", "ADMINS"]],
    ["start", "Get confirmation that the bot is up", ["SUDO", "ADMINS"]],
]


GRAPH_REQUESTS_COLOR = os.environ.get("REQUESTS_COLOR", "#ff3333")
GRAPH_FULFILLED_COLOR = os.environ.get("FULFILLED_COLOR", "#80ff80")


DB_BACKUP_CHAT_ID = int(os.environ.get("DB_BACKUP_CHAT_ID", "-1"))
if DB_BACKUP_CHAT_ID == -1:
    logger.info("No db backup chat id provided, the database will not be backed up")
