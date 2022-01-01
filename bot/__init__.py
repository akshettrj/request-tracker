import os
import re
from pyrogram import filters
from dotenv import load_dotenv

import logging

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
if BOT_TOKEN == '':
    _missing_env_var('BOT_TOKEN')

# '''''''''''''''''''''''''''''''''''''''''''''''''''''''

GROUP_ID = int(os.environ.get('GROUP_ID', '-1'))
if GROUP_ID == -1:
    _missing_env_var('GROUP_ID')

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

ENG_REQ_TIME = os.environ.get('ENG_REQ_TIME', '7d').strip()
NON_ENG_REQ_TIME = os.environ.get('NON_ENG_REQ_TIME', '14d').strip()

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

# '''''''''''''''''''''''''''''''''''''''''''''''''''''''

_COMMAND_CHATS_FILTER = filters.chat(GROUP_ID)
for user_id in SUDO_USERS:
    _COMMAND_CHATS_FILTER = _COMMAND_CHATS_FILTER | filters.chat(user_id)

FULFILL_FILTER = (
            ~filters.edited &
            filters.chat(GROUP_ID) &
            (filters.audio | filters.document | filters.voice)
        )

REQUEST_FILTER = (
            ~filters.edited &
            filters.chat(GROUP_ID) &
            filters.text
        )

REQUESTS_COMMAND_FILTER = (
            (_COMMAND_CHATS_FILTER) &
            filters.text &
            filters.command('requests')
        )

CLEAR_LAST_REQUEST_COMMAND_FILTER = (
            (_COMMAND_CHATS_FILTER) &
            filters.text &
            filters.command('dellastreq')
        )

START_COMMAND_FILTER = (
            (_COMMAND_CHATS_FILTER) &
            filters.text &
            filters.command('start')
        )

LIMITS_COMMAND_FILTER = (
            (_COMMAND_CHATS_FILTER) &
            filters.text &
            filters.command('limits')
        )

DROP_DB_COMMAND_FILTER = (
            (_COMMAND_CHATS_FILTER) &
            filters.text &
            filters.command('dropdb')
        )

# '''''''''''''''''''''''''''''''''''''''''''''''''''''''

DATABASE_URL = os.environ.get('DATABASE_URL', '')
if DATABASE_URL == '':
    _missing_env_var('DATABASE_URL')
