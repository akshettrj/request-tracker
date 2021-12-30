import os
from pyrogram import filters
from dotenv import load_dotenv

if os.path.exists('./config.env'):
    print("Loading config variables from config.env file")
    load_dotenv('./config.env')

def _missing_env_var(var: str):
    print(f'Environment variable {var} missing!')
    exit(1)

API_ID = int(os.environ.get('API_ID', '-1'))
if API_ID == -1:
    _missing_env_var('API_ID')

API_HASH = os.environ.get('API_HASH', '')
if API_HASH == '':
    _missing_env_var('API_HASH')

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
if BOT_TOKEN == '':
    _missing_env_var('BOT_TOKEN')

GROUP_ID = int(os.environ.get('GROUP_ID', '-1'))
if GROUP_ID == -1:
    _missing_env_var('GROUP_ID')

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

STATS_COMMAND_FILTER = (
            filters.chat(GROUP_ID) &
            filters.text &
            filters.command('stats')
        )

START_COMMAND_FILTER = (
            filters.chat(GROUP_ID) &
            filters.text &
            filters.command('start')
        )

DATABASE_URL = os.environ.get('DATABASE_URL', '')
if DATABASE_URL == '':
    _missing_env_var('DATABASE_URL')
