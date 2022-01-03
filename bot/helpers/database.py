import psycopg2
from datetime import datetime

class Database:

    def __init__(self, database_url: str):
        self.connection = psycopg2.connect(database_url)
        self.create_schema()

    def __del__(self):
        self.connection.close()


    def create_schema(self):

        cur = self.connection.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS users (" +
                "user_id                   BIGINT       PRIMARY KEY" +
            ");"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS requests (" +
                "user_id                BIGINT NOT NULL," +
                "is_english             BOOLEAN NOT NULL," +
                "message_id             BIGINT PRIMARY KEY DEFAULT NULL," +
                "req_time               TIMESTAMP DEFAULT NULL,"
                "fulfill_message_id     BIGINT DEFAULT NULL," +
                "fulfill_time           TIMESTAMP DEFAULT NULL," +
                "CONSTRAINT fk_user_id\n" +
                "   FOREIGN KEY(user_id)\n" +
                "       REFERENCES users(user_id)\n" +
                "       ON DELETE CASCADE" +
            ");"
        )
        self.connection.commit()
        cur.close()


    def drop_database(self):

        cur = self.connection.cursor()
        cur.execute(
            "DROP TABLE IF EXISTS users CASCADE;" +
            "DROP TABLE IF EXISTS requests;"
        )
        self.connection.commit()
        cur.close()


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
            "SELECT user_id FROM users WHERE user_id = %s",
            [user_id]
        )
        (usr_id) = next(cur, (None))
        cur.close()
        return usr_id


    def get_user_requests(self, user_id: int):
        cur = self.connection.cursor()
        cur.execute(
            "SELECT " +
                "user_id, is_english, message_id, req_time," +
                "fulfill_message_id, fulfill_time " +
            "FROM requests WHERE user_id = %s;",
            [user_id]
        )
        user_requests = []
        while True:
            ( usr_id, is_english, msg_id,
            req_time, fulfill_message_id, fulfill_time ) = next(cur, (None, None, None, None, None, None))
            if usr_id is None:
                break

            user_requests.append(( usr_id, is_english, msg_id,
            req_time, fulfill_message_id, fulfill_time ))

        cur.close()
        user_requests = [
                            {
                                'user_id': req[0],
                                'is_english': req[1],
                                'message_id': req[2],
                                'req_time': req[3],
                                'fulfill_message_id': req[4],
                                'fulfill_time': req[5]
                            }
                            for req in user_requests
                        ]
        return user_requests


    def get_request(self, user_id: int, message_id: int):
        cur = self.connection.cursor()
        cur.execute(
            "SELECT " +
                "user_id, is_english, message_id, req_time," +
                "fulfill_message_id, fulfill_time " +
            "FROM requests WHERE user_id = %s AND message_id = %s;",
            [user_id, message_id]
        )
        ( usr_id, is_english, msg_id,
        req_time, fulfill_message_id, fulfill_time ) = next(cur, (None, None, None, None, None, None));
        cur.close()

        return ( usr_id, is_english, msg_id,
        req_time, fulfill_message_id, fulfill_time )


    def get_requests(self):
        cur = self.connection.cursor()
        cur.execute(
            "SELECT " +
                "user_id, is_english, message_id, req_time," +
                "fulfill_message_id, fulfill_time " +
            "FROM requests;",
        )
        requests = []
        while True:
            ( usr_id, is_english, msg_id,
            req_time, fulfill_message_id, fulfill_time ) = next(cur, (None, None, None, None, None, None))
            if usr_id is None:
                break

            requests.append(( usr_id, is_english, msg_id,
            req_time, fulfill_message_id, fulfill_time ))

        cur.close()
        requests = [
                    {
                        'user_id': req[0],
                        'is_english': req[1],
                        'message_id': req[2],
                        'req_time': req[3],
                        'fulfill_message_id': req[4],
                        'fulfill_time': req[5]
                    }
                    for req in requests
                ]
        return requests


    def get_pending_requests(self):

        cur = self.connection.cursor()
        cur.execute(
            "SELECT " +
                "user_id, is_english, message_id, req_time " +
            "FROM requests WHERE fulfill_time is NULL;",
        )
        pending_requests = []
        while True:
            ( usr_id, is_english, msg_id,
            req_time ) = next(cur, (None, None, None, None))
            if usr_id is None:
                break

            pending_requests.append(( usr_id, is_english, msg_id,
            req_time ))

        cur.close()
        pending_requests = [
                    {
                        'user_id': req[0],
                        'is_english': req[1],
                        'message_id': req[2],
                        'req_time': req[3]
                    }
                    for req in pending_requests
                ]
        return pending_requests


    def delete_request(self, message_id: int):
        cur = self.connection.cursor()
        cur.execute(
            "DELETE FROM requests WHERE message_id = %s;",
            [message_id]
        )
        self.connection.commit()
        cur.close()


    def register_request(self, user_id: int, is_english: bool, message_id: int):
        cur = self.connection.cursor()
        cur.execute(
            "INSERT INTO requests (user_id, is_english, message_id, req_time) " +
            "VALUES (%s, %s, %s, %s)",
            [user_id, is_english, message_id, datetime.now()]
        )
        self.connection.commit()
        cur.close()


    def register_request_fulfillment(self, user_id: int, message_id: int, fulfill_id: int):
        cur = self.connection.cursor()
        cur.execute(
            "UPDATE requests " +
            "SET fulfill_message_id = %s, fulfill_time = %s " +
            "WHERE (user_id = %s AND message_id = %s);",
            [fulfill_id, datetime.now(), user_id, message_id]
        )
        self.connection.commit()
        cur.close()
