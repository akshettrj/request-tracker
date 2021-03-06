import os
from typing import Tuple
import psycopg2
from datetime import datetime, timedelta
from zipfile import ZipFile

import pytz


class Database:

    def __init__(self, database_url: str):
        self.connection = psycopg2.connect(database_url)
        self.create_schema()

    def __del__(self):
        self.connection.close()


    def create_schema(self):

        cur = self.connection.cursor()
        try:
            cur.execute(
                "CREATE TABLE IF NOT EXISTS users (" +
                    "user_id        BIGINT       PRIMARY KEY," +
                    "name           TEXT         DEFAULT NULL," +
                    "user_name      TEXT         DEFAULT NULL" +
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
                    "fulfilled_by           BIGINT DEFAULT NULL," +
                    "CONSTRAINT fk_user_id\n" +
                    "   FOREIGN KEY(user_id)\n" +
                    "       REFERENCES users(user_id)\n" +
                    "       ON DELETE CASCADE" +
                ");"
            )

        except Exception as ex:
            self.connection.rollback()
            raise ex

        finally:
            self.connection.commit()
            cur.close()


    def drop_database(self):

        cur = self.connection.cursor()
        try:
            cur.execute(
                "DROP TABLE IF EXISTS users CASCADE;" +
                "DROP TABLE IF EXISTS requests;"
            )

        except Exception as ex:
            self.connection.rollback()
            raise ex

        finally:
            self.connection.commit()
            cur.close()


    def add_user(self, user_id: int, name: str, user_name: str):
        cur = self.connection.cursor()
        try:
            cur.execute(
                "INSERT INTO users (user_id, name, user_name) " +
                "VALUES (%s, %s, %s);",
                [user_id, name, user_name]
            )

        except Exception as ex:
            self.connection.rollback()
            raise ex

        finally:
            self.connection.commit()
            cur.close()


    def get_user_details(self, user_id: int):
        cur = self.connection.cursor()
        try:
            cur.execute(
                "SELECT user_id, name, user_name FROM users WHERE user_id = %s",
                [user_id]
            )
            (usr_id, name, user_name) = next(cur, (None, None, None))

        except Exception as ex:
            self.connection.rollback()
            raise ex

        finally:
            cur.close()

        return {
            "user_id": usr_id,
            "name": name,
            "user_name": user_name
        } if usr_id is not None else None


    def get_user(self, user_id: int):
        cur = self.connection.cursor()
        try:
            cur.execute(
                "SELECT user_id FROM users WHERE user_id = %s",
                [user_id]
            )
            (usr_id) = next(cur, (None))

        except Exception as ex:
            self.connection.rollback()
            raise ex

        finally:
            cur.close()

        return usr_id


    def update_user(self, user_id: int, name: str, username: str):
        cur = self.connection.cursor()
        try:
            cur.execute(
                "UPDATE users " +
                "SET name = %s, user_name = %s " +
                "WHERE (user_id = %s);",
                [name, username, user_id]
            )

        except Exception as ex:
            self.connection.rollback()
            raise ex

        finally:
            cur.close()


    def get_users(self):
        cur = self.connection.cursor()
        try:
            cur.execute(
                "SELECT user_id, name, user_name FROM users;"
            )
            results = cur.fetchall()

        except Exception as ex:
            self.connection.rollback()
            raise ex

        finally:
            cur.close()

        return {
            result[0]: {"name": result[1], "user_name": result[2]}
            for result in results
        }


    def get_user_last_request(self, user_id: int):

        cur = self.connection.cursor()
        try:
            cur.execute(
                "SELECT " +
                    "user_id, is_english, message_id, req_time," +
                    "fulfill_message_id, fulfill_time " +
                "FROM requests WHERE user_id = %s " +
                "ORDER BY " +
                "   message_id DESC " +
                "LIMIT 1;",
                [user_id]
            )

            ( usr_id, is_english, msg_id,
            req_time, fulfill_message_id, fulfill_time ) = next(cur, (None, None, None, None, None, None))

            last_request = {
                'user_id': usr_id,
                'is_english': is_english,
                'message_id': msg_id,
                'req_time': req_time,
                'fulfill_message_id': fulfill_message_id,
                'fulfill_time': fulfill_time
            }

        except Exception as ex:
            self.connection.rollback()
            raise ex

        finally:
            cur.close()

        return last_request


    def get_user_stats(self, user_id: int) -> Tuple[int, int, int, int]:

        cur = self.connection.cursor()
        try:
            cur.execute(
                "WITH new_table AS (" +
                "   SELECT " +
                "       is_english," +
                "       (fulfill_time IS NOT NULL) AS is_fulfilled " +
                "   FROM requests WHERE user_id = %s" +
                ") "
                "SELECT " +
                    "is_fulfilled, is_english, COUNT(is_english) AS cnt " +
                "FROM new_table " +
                "GROUP BY is_english, is_fulfilled;",
                [user_id]
            )

            ( english_fulfilled, non_english_fulfilled,
            english_not_fulfilled, non_english_not_fulfilled ) = 0, 0, 0, 0

            while True:

                (is_fulfilled, is_english, req_count) = next(cur, (None, None, None))
                if is_fulfilled is None or is_english is None or req_count is None:
                    break

                if is_fulfilled:
                    if is_english:
                        english_fulfilled = req_count
                    else:
                        non_english_fulfilled = req_count
                else:
                    if is_english:
                        english_not_fulfilled = req_count
                    else:
                        non_english_not_fulfilled = req_count

        except Exception as ex:
            self.connection.rollback()
            raise ex

        finally:
            cur.close()

        return ( english_fulfilled, non_english_fulfilled,
        english_not_fulfilled, non_english_not_fulfilled )


    def get_global_stats(self) -> Tuple[int, int, int, int]:

        cur = self.connection.cursor()
        try:
            cur.execute(
                "WITH new_table AS (" +
                "   SELECT " +
                "       is_english," +
                "       (fulfill_time IS NOT NULL) AS is_fulfilled " +
                "   FROM requests" +
                ") "
                "SELECT " +
                    "is_fulfilled, is_english, COUNT(is_english) AS cnt " +
                "FROM new_table " +
                "GROUP BY is_english, is_fulfilled;"
            )

            ( english_fulfilled, non_english_fulfilled,
            english_not_fulfilled, non_english_not_fulfilled ) = 0, 0, 0, 0

            while True:

                (is_fulfilled, is_english, req_count) = next(cur, (None, None, None))
                if is_fulfilled is None or is_english is None or req_count is None:
                    break

                if is_fulfilled:
                    if is_english:
                        english_fulfilled = req_count
                    else:
                        non_english_fulfilled = req_count
                else:
                    if is_english:
                        english_not_fulfilled = req_count
                    else:
                        non_english_not_fulfilled = req_count

        except Exception as ex:
            self.connection.rollback()
            raise ex

        finally:
            cur.close()

        return ( english_fulfilled, non_english_fulfilled,
        english_not_fulfilled, non_english_not_fulfilled )


    def get_user_requests(self, user_id: int):

        cur = self.connection.cursor()
        try:
            cur.execute(
                "SELECT " +
                    "user_id, is_english, message_id, req_time," +
                    "fulfill_message_id, fulfill_time " +
                "FROM requests WHERE user_id = %s " +
                "ORDER BY" +
                "   message_id ASC;",
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

        except Exception as ex:
            self.connection.rollback()
            raise ex

        finally:
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


    def get_oldest_request_time(self):

        cur = self.connection.cursor()
        try:
            cur.execute(
                "SELECT " +
                    "req_time " +
                "FROM requests " +
                "ORDER BY" +
                "   req_time ASC LIMIT 1;"
            )

            (req_time) = next(cur, (None))

        except Exception as ex:
            self.connection.rollback()
            raise ex

        finally:
            cur.close()

        return req_time


    def get_latest_fulfilled(self):

        cur = self.connection.cursor()
        try:
            cur.execute(
                "SELECT " +
                    "user_id, is_english, message_id, req_time," +
                    "fulfill_message_id, fulfill_time, fulfilled_by " +
                "FROM requests " +
                "WHERE fulfill_time is NOT NULL " +
                "ORDER BY" +
                "   fulfill_time DESC LIMIT 1;"
            )

            ( usr_id, is_english, msg_id,
            req_time, fulfill_message_id, fulfill_time,
            fulfilled_by ) = next(cur, (None, None, None, None, None, None, None))

        except Exception as ex:
            self.connection.rollback()
            raise ex

        finally:
            cur.close()

        return {
            'user_id': usr_id,
            'is_english': is_english,
            'message_id': msg_id,
            'req_time': req_time,
            'fulfill_message_id': fulfill_message_id,
            'fulfill_time': fulfill_time,
            'fulfilled_by': fulfilled_by
        }


    def get_request(self, user_id: int, message_id: int):
        cur = self.connection.cursor()
        try:
            cur.execute(
                "SELECT " +
                    "user_id, is_english, message_id, req_time," +
                    "fulfill_message_id, fulfill_time " +
                "FROM requests WHERE user_id = %s AND message_id = %s;",
                [user_id, message_id]
            )
            ( usr_id, is_english, msg_id,
            req_time, fulfill_message_id, fulfill_time ) = next(cur, (None, None, None, None, None, None));

        except Exception as ex:
            self.connection.rollback()
            raise ex

        finally:
            cur.close()

        return ( usr_id, is_english, msg_id,
        req_time, fulfill_message_id, fulfill_time )


    def get_requests(self):
        cur = self.connection.cursor()
        try:
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


        except Exception as ex:
            self.connection.rollback()
            raise ex

        finally:
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
        try:
            cur.execute(
                "SELECT " +
                    "user_id, is_english, message_id, req_time " +
                "FROM requests " +
                "WHERE fulfill_time is NULL " +
                "ORDER BY req_time;"
            )
            pending_requests = []
            while True:
                ( usr_id, is_english, msg_id,
                req_time ) = next(cur, (None, None, None, None))
                if usr_id is None:
                    break

                pending_requests.append(( usr_id, is_english, msg_id,
                req_time ))


        except Exception as ex:
            self.connection.rollback()
            raise ex

        finally:
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
        try:
            cur.execute(
                "DELETE FROM requests WHERE message_id = %s;",
                [message_id]
            )

        except Exception as ex:
            self.connection.rollback()
            raise ex

        finally:
            self.connection.commit()
            cur.close()


    def register_request(self, user_id: int, is_english: bool, message_id: int):
        cur = self.connection.cursor()
        try:
            cur.execute(
                "INSERT INTO requests (user_id, is_english, message_id, req_time) " +
                "VALUES (%s, %s, %s, %s)",
                [user_id, is_english, message_id, datetime.now()]
            )

        except Exception as ex:
            self.connection.rollback()
            raise ex

        finally:
            self.connection.commit()
            cur.close()


    def mark_request_not_done(self, user_id: int, message_id: int):

        cur = self.connection.cursor()
        try:
            cur.execute(
                "UPDATE requests " +
                "SET fulfill_message_id = NULL, fulfill_time = NULL, fulfilled_by = NULL " +
                "WHERE (user_id = %s AND message_id = %s);",
                [user_id, message_id]
            )

        except Exception as ex:
            self.connection.rollback()
            raise ex

        finally:
            self.connection.commit()
            cur.close()


    def register_request_fulfillment(self, user_id: int, message_id: int, fulfill_id: int, fulfilled_by: int):

        cur = self.connection.cursor()
        try:
            cur.execute(
                "UPDATE requests " +
                "SET fulfill_message_id = %s, fulfill_time = %s, fulfilled_by = %s " +
                "WHERE (user_id = %s AND message_id = %s);",
                [fulfill_id, datetime.now(), fulfilled_by, user_id, message_id]
            )

        except Exception as ex:
            self.connection.rollback()
            raise ex

        finally:
            self.connection.commit()
            cur.close()


    def run_qeury(self, query: str, op=False):

        cur = self.connection.cursor()
        try:
            cur.execute( query )
            if op:
                output = cur.fetchall()
            else:
                output = None

        except Exception as ex:
            self.connection.rollback()
            raise ex

        finally:
            self.connection.commit()
            cur.close()

        return output


    def get_schemas(self):

        query = (
            "SELECT column_name, data_type, is_nullable "
            "FROM information_schema.columns "
            "WHERE table_name = %s;"
        )

        cur = self.connection.cursor()
        try:
            cur.execute( query, ["users"])
            output1 = cur.fetchall()
            cur.execute( query, ["requests"])
            output2 = cur.fetchall()

        except Exception as ex:
            self.connection.rollback()
            raise ex

        finally:
            self.connection.commit()
            cur.close()

        return output1, output2


    def update_fulfilled_by(self, fulfill_message_id, fulfilled_by):

        cur = self.connection.cursor()
        try:
            cur.execute(
                "UPDATE requests " +
                "SET fulfilled_by = %s " +
                "WHERE fulfill_message_id = %s;",
                [fulfilled_by, fulfill_message_id]
            )

        except Exception as ex:
            self.connection.rollback()
            raise ex

        finally:
            self.connection.commit()
            cur.close()


    def get_leaderboard(self):

        cur = self.connection.cursor()
        try:
            cur.execute(
                "SELECT COUNT(message_id) AS count, fulfilled_by " +
                "FROM requests " +
                "WHERE fulfilled_by IS NOT NULL " +
                "GROUP BY fulfilled_by " +
                "ORDER BY count DESC;"
            )
            result = cur.fetchall()

        except Exception as ex:
            self.connection.rollback()
            raise ex

        finally:
            self.connection.commit()
            cur.close()

        return result


    def get_weekly_stats(self, weeks):

        cur = self.connection.cursor()
        results = {}
        try:
            for week in weeks:
                week_start, week_end, week_number = week
                week_end = week_end + timedelta(days=1)

                cur.execute(
                    "SELECT count(message_id) FROM requests " +
                    "WHERE req_time >= %s AND req_time <= %s;",
                    [week_start, week_end]
                )
                requests_count = cur.fetchone()[0]

                cur.execute(
                    "SELECT count(message_id) FROM requests " +
                    "WHERE fulfill_time >= %s AND fulfill_time <= %s;",
                    [week_start, week_end]
                )
                fulfill_count = cur.fetchone()[0]

                results[week_number] = (requests_count, fulfill_count)

        except Exception as ex:
            self.connection.rollback()
            raise ex

        finally:
            self.connection.commit()
            cur.close()

        return results


    def get_backup_data(self):

        cur = self.connection.cursor()

        table_names = [
            "users",
            "requests"
        ]
        cur_time = datetime.now(tz=pytz.timezone('Asia/Kolkata'))
        zip_file_name = f"database_backup_{cur_time:%d-%m-%Y-%H:%M:%S}.zip"

        def format_data(val):
            if val is None:
                return 'NULL'
            elif isinstance(val, datetime):
                return f"{val:'%Y-%m-%d %H:%M:%S'}"
            else:
                return repr(val)

        try:
            zipObj = ZipFile(zip_file_name, "w")
            for table_name in table_names:
                cur.execute(
                    f"SELECT * FROM {table_name};"
                )
                columns = [_.name for _ in cur.description]
                insert_prefix = f'INSERT INTO {table_name} ({", ".join(columns)}) VALUES'
                table_data = cur.fetchall()
                with open(f"{table_name}.sql", "w") as f:
                    for row in table_data:
                        row_data = [format_data(val) for val in row]
                        f.write(f"{insert_prefix} ({', '.join(row_data)});\n")

                zipObj.write(f"{table_name}.sql")
            zipObj.close()

            os.remove("users.sql")
            os.remove("requests.sql")

        except Exception as ex:
            self.connection.rollback()
            raise ex

        finally:
            self.connection.commit()
            cur.close()

        return zip_file_name
