import psycopg2
import os

def _missing_env_var(var: str):
    print(f'Environment variable {var} missing!')
    exit(1)

DATABASE_URL = os.environ.get('DATABASE_URL', '')
if DATABASE_URL == '':
    _missing_env_var('DATABASE_URL')

connection = psycopg2.connect(DATABASE_URL)

cur = connection.cursor()
try:
    cur.execute(
        "CREATE TABLE IF NOT EXISTS users (" +
            "user_id                   BIGINT       PRIMARY KEY," +
            "last_eng_req              TIMESTAMP    DEFAULT NULL," +
            "last_eng_req_id           BIGINT       DEFAULT NULL," +
            "last_eng_fulfill          TIMESTAMP    DEFAULT NULL," +
            "last_eng_fulfill_id       BIGINT       DEFAULT NULL," +
            "last_non_eng_req          TIMESTAMP    DEFAULT NULL," +
            "last_non_eng_req_id       BIGINT       DEFAULT NULL," +
            "last_non_eng_fulfill      TIMESTAMP    DEFAULT NULL," +
            "last_non_eng_fulfill_id   BIGINT       DEFAULT NULL" +
        ");"
    )
    connection.commit()
    cur.close()
except Exception as e:
    print('Error occured:', e)
    exit(1)
else:
    pass

connection.close()
