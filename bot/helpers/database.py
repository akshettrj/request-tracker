import psycopg2
from datetime import datetime

class Database:

    def __init__(self, database_url: str):

        self.connection = psycopg2.connect(database_url)
        cur = self.connection.cursor()
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
        self.connection.commit()
        cur.close()

    def __del__(self):
        self.connection.close()

    def add_user(self, user_id: int):
        cur = self.connection.cursor()
        cur.execute(
            "INSERT INTO users (user_id) " +
            "VALUES (%s);",
            [user_id]
        )
        self.connection.commit()
        cur.close()

    def get_user(self, user_id: int):
        cur = self.connection.cursor()
        cur.execute(
            "SELECT user_id, " +
                    "last_eng_req, last_eng_req_id, " +
                    "last_eng_fulfill, last_eng_fulfill_id, " +
                    "last_non_eng_req, last_non_eng_req_id, " +
                    "last_non_eng_fulfill, last_non_eng_fulfill_id FROM users " +
            "WHERE user_id = %s;",
            [user_id]
        )
        ( usr_id, last_eng_req, last_eng_req_id, last_eng_fulfill,
                last_eng_fulfill_id, last_non_eng_req,
                last_non_eng_req_id, last_non_eng_fulfill,
                last_non_eng_fulfill_id ) = next(cur, tuple([None] * 9))
        cur.close()
        return  ( usr_id, last_eng_req, last_eng_req_id, last_eng_fulfill,
                last_eng_fulfill_id, last_non_eng_req,
                last_non_eng_req_id, last_non_eng_fulfill,
                last_non_eng_fulfill_id )

    def register_request(self, user_id: int, is_english: bool, message_id: int):
        cur = self.connection.cursor()
        if is_english:
            cur.execute(
                "UPDATE users SET last_eng_req = %s, last_eng_req_id = %s WHERE user_id = %s;",
                [datetime.now(), message_id, user_id]
            )
        else:
            cur.execute(
                "UPDATE users SET last_non_eng_req = %s, last_eng_req_id = %s WHERE user_id = %s;",
                [datetime.now(), message_id, user_id]
            )
        self.connection.commit()
        cur.close()

    def register_request_fulfillment(self, user_id: int, is_english: bool, message_id: int):
        cur = self.connection.cursor()
        if is_english:
            cur.execute(
                "UPDATE users SET last_eng_fulfill = %s, last_eng_fulfill_id = %s WHERE user_id = %s;",
                [datetime.now(), message_id, user_id]
            )
        else:
            cur.execute(
                "UPDATE users SET last_non_eng_fulfill = %s, last_non_eng_fulfill_id = %s WHERE user_id = %s;",
                [datetime.now(), message_id, user_id]
            )
        self.connection.commit()
        cur.close()
