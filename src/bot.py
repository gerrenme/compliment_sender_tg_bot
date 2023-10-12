import openai
import telebot
import psycopg2
import threading

from datetime import datetime
from collections import deque
from random import choice
from config import (db_host, db_user, db_password, db_name, db_entity_name,
                    admin_password, info_message, telebot_key, open_ai_key)
from typing import List, Tuple, Dict

openai.api_key = open_ai_key


class ComplementSender:
    def __init__(self) -> None:
        self.__bot = telebot.TeleBot(telebot_key)

        self.__connection: psycopg2.connect = psycopg2.connect(host=db_host, user=db_user,
                                                               password=db_password, database=db_name)
        self.__connection.autocommit = True

        self._username: str = ""
        self.chat_id: str = "0000000000"
        self.__last_random_compliment_send_time: datetime = datetime.now()
        self.__random_compliment_queue: deque[Dict[str, str]] = deque()

        @self.__bot.message_handler(commands=['start'])
        def start(message: telebot.types.Message) -> None:
            add_user(message)

        @self.__bot.message_handler(commands=['chat'])
        def get_user_data(message: telebot.types.Message) -> None:
            self.chat_id = message.from_user.id
            self._username = message.from_user.username

        @self.__bot.message_handler(content_types=['text'])
        def get_text_messages(message: telebot.types.Message) -> None:
            get_user_data(message)

            with self.__connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT * "
                    f"FROM {db_entity_name} "
                    f"WHERE username = '{message.from_user.username}';")

                data: List[Tuple[str, str, int, int]] = cursor.fetchall()

                if data is not None and data != []:
                    if message.text == "/send":
                        self.__bot.send_message(message.from_user.id, info_message["send_standard_compliment"])
                        self.__bot.register_next_step_handler(message, send_complement)

                    elif message.text == "/random":
                        send_random_compliment(message)

                    elif message.text == "/stat":
                        get_stat(message)

                    elif message.text == "/top":
                        get_top_users()

                    elif message.text == "/admin_show_db":
                        print(f'[LOG_show_all_users] User {self._username} requests admin rights')
                        self.__bot.send_message(message.from_user.id, "Enter admin password")
                        self.__bot.register_next_step_handler(message, show_all_users)

                    elif message.text == "/admin_show_user_data":
                        print(f'[LOG_show_all_users] User {self._username} requests admin rights')
                        self.__bot.send_message(message.from_user.id,
                                                f"Current chat id is {self.chat_id} and username is {self._username}")

                    elif message.text == "/help":
                        self.__bot.send_message(message.from_user.id,
                                                info_message["bot_help"])

                    else:
                        self.__bot.send_message(message.from_user.id, info_message["miss_command"])

                else:
                    self.__bot.send_message(message.from_user.id, info_message["need_register"])

        def add_user(message: telebot.types.Message) -> None:
            get_user_data(message)
            try:
                with self.__connection.cursor() as cursor:
                    cursor.execute(
                        f"SELECT * "
                        f"FROM {db_entity_name} "
                        f"WHERE username = '{self._username}';")

                    result: List[Tuple[str, str, int, int]] = cursor.fetchone()

                if result is None:
                    with self.__connection.cursor() as cursor:
                        cursor.execute(
                            f"INSERT INTO {db_entity_name} "
                            f"VALUES('{self._username}', '{self.chat_id}', 0, 0);")

                        self.__bot.send_message(self.chat_id, info_message["success_register"])
                        print(f"[LOG_add_user] User {message.from_user.username} was added successfully")

                else:
                    self.__bot.send_message(self.chat_id, info_message["already_register"])

            except Exception as _ex:
                print(f"[LOG_add_user] Error!! {_ex}")

        def show_all_users(message: telebot.types.Message) -> None:
            if check_admin_password(message):
                try:
                    with self.__connection.cursor() as cursor:
                        cursor.execute(
                            f"SELECT * "
                            f"FROM {db_entity_name};")

                        data: List[Tuple[str, str, int, int]] = cursor.fetchall()

                        if data is not None:
                            users = [f"User {t[0]} received {t[2]} compliments" for t in data]
                            self.__bot.send_message(message.from_user.id, "\n".join(users))

                        else:
                            self.__bot.send_message(message.from_user.id, "There are no users in the database")
                except Exception as _ex:
                    print(f"[LOG_show_all_users] Error!! {_ex}")
            else:
                print(f'[LOG_show_all_users] Incorrect password from user {self._username}')
                self.__bot.send_message(message.from_user.id, "Incorrect password")

        def send_complement(message: telebot.types.Message) -> None:
            try:
                with self.__connection.cursor() as cursor:
                    cursor.execute(f"SELECT * "
                                   f"FROM {db_entity_name} "
                                   f"WHERE username = '{message.text.split()[0]}';")

                    data: List[Tuple[str, str, int, int]] = cursor.fetchall()

                    if data is not None and data != []:
                        cursor.execute(
                            f"UPDATE {db_entity_name} "
                            f"SET complements_received = complements_received + 1 "
                            f"WHERE username = '{data[0][0]}';")

                        cursor.execute(
                            f"UPDATE {db_entity_name} "
                            f"SET complements_sended = complements_sended + 1 "
                            f"WHERE username = '{self._username}';")

                        self.__bot.send_message(data[0][1],
                                                f"You received a compliment!! {' '.join(message.text.split()[1:])}")

                        self.__bot.send_message(self.chat_id, info_message["success_compliment"])
                        print(f'[LOG_send_complement] User {self._username} send complement to {data[0][0]}')

                    else:
                        self.__bot.send_message(message.from_user.id, info_message["no_such_user"])

            except Exception as _ex:
                print(f"[LOG_send_complement] Error!! {_ex}")
                self.__bot.send_message(message.from_user.id, info_message["bot_blocked"])

        def send_random_compliment(message: telebot.types.Message) -> None:
            try:
                with self.__connection.cursor() as cursor:
                    cursor.execute(f"SELECT username, user_chat_id FROM {db_entity_name} "
                                   f"WHERE username != '{message.from_user.username}';")

                    data: List[str] = cursor.fetchall()
                    if data is not None:
                        random_user: str = choice(data)

                        cursor.execute(
                            f"UPDATE {db_entity_name} "
                            f"SET complements_received = complements_received + 1 "
                            f"WHERE username = '{random_user[0]}';")

                        cursor.execute(
                            f"UPDATE {db_entity_name} "
                            f"SET complements_sended = complements_sended + 1 "
                            f"WHERE username = '{self._username}';")

                        self.__random_compliment_queue.append({"snd_username": self._username,
                                                               "snd_id": message.from_user.id,
                                                               "rec_username": random_user[0],
                                                               "rec_id": random_user[1]
                                                               })

                        self.__bot.send_message(message.from_user.id, info_message["add_to_queue"])

                        # random_compliment: str = self.generate_random_compliment()
                        # self.__bot.send_message(random_user[-1],
                        #                         info_message["receive_random_compliment"] + random_compliment)
                        # self.__bot.send_message(message.from_user.id, info_message["send_random_compliment"])

                        # print(f"[LOG_send_random_compliment] User {message.from_user.username} send "
                        #       f"random compliment to {random_user[0]}")

                    else:
                        self.__bot.send_message(message.from_user.id, info_message["no_user_sad"])

            except Exception as _ex:
                print(f"[LOG_send_random_compliment] Error!! {_ex}")
                self.__bot.send_message(message.from_user.id, info_message["bot_blocked"])

        def get_stat(message: telebot.types.Message) -> None:
            try:
                with self.__connection.cursor() as cursor:
                    cursor.execute(
                        f"SELECT * "
                        f"FROM {db_entity_name} "
                        f"WHERE username = '{message.from_user.username}';")

                    data: List[Tuple[str, str, int, int]] = cursor.fetchall()
                    self.__bot.send_message(message.from_user.id, f"User {data[0][0]} sent {data[0][3]} "
                                                                  f"compliments and received {data[0][2]} compliments")

            except Exception as _ex:
                print(f"[LOG_get_stat] Error!! {_ex}")

        def get_top_users() -> None:
            try:
                with self.__connection.cursor() as cursor:
                    cursor.execute(
                        f"SELECT us.username, us.complements_received "
                        f"FROM {db_entity_name} AS us "
                        f"ORDER BY us.complements_received DESC "
                        f"LIMIT 5;")

                    top_received: List[Tuple[str, str, int, int]] = cursor.fetchall()

                    cursor.execute(
                        f"SELECT us.username, us.complements_sended "
                        f"FROM {db_entity_name} AS us "
                        f"ORDER BY us.complements_sended DESC "
                        f"LIMIT 5;")
                    top_send: List[Tuple[str, str, int, int]] = cursor.fetchall()

                    message_received: str = "\n".join([f'💌 User {t[0]} received {t[1]} complements'
                                                       for t in top_received])
                    message_send: str = "\n".join([f'💘 User {t[0]} sent {t[1]} complements' for t in top_send])

                    self.__bot.send_message(self.chat_id, f"• The following users "
                                                          f"received the most compliments:\n{message_received}\n\n"
                                                          f"• The following users sent the most compliments:\n"
                                                          f"{message_send}")

            except Exception as _ex:
                print(f"[LOG_get_top_users] Error!! {_ex}")

        def check_admin_password(message) -> bool:
            return message.text == admin_password

    @staticmethod
    def generate_random_compliment() -> str:
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{
            "role": "user", "content": info_message["generate_compliment"]}])

        return completion.choices[0].message.content

    def check_sending_random_compliments(self):
        while True:
            current_time: datetime = datetime.now()
            time_elapsed = current_time - self.__last_random_compliment_send_time
            try:
                if time_elapsed.total_seconds() > 21 and len(self.__random_compliment_queue) > 0:
                    current_users: Dict[str, str] = self.__random_compliment_queue.popleft()

                    sender_username: str = current_users["snd_username"]
                    sender_id: str = current_users["snd_id"]
                    receiver_username: str = current_users["rec_username"]
                    receiver_id: str = current_users["rec_id"]

                    random_compliment: str = self.generate_random_compliment()

                    self.__bot.send_message(receiver_id,
                                            info_message["receive_random_compliment"] + random_compliment)
                    self.__bot.send_message(sender_id, info_message["send_random_compliment"])

                    print(f"[LOG_send_random_compliment] User {sender_username} send "
                          f"random compliment to {receiver_username}")

                    self.update_time()

            except Exception as _ex:
                print(f"[LOG_check_sending_random_compliments] Error!! {_ex}")

    def update_time(self):
        self.__last_random_compliment_send_time = datetime.now()

    def run(self) -> None:
        with self.__connection.cursor() as cursor:
            # # do not touch # # cursor.execute(f"DROP TABLE IF EXISTS {db_entity_name};")
            cursor.execute(f"""CREATE TABLE IF NOT EXISTS {db_entity_name} (
            username VARCHAR(50) PRIMARY KEY, 
            user_chat_id VARCHAR(10),
            complements_received INT,
            complements_sended INT
                           );""")

        bot_polling_thread: threading.Thread = threading.Thread(target=self.__bot.polling)
        time_check_thread: threading.Thread = threading.Thread(target=self.check_sending_random_compliments)
        time_check_thread.daemon = True

        time_check_thread.start()
        bot_polling_thread.start()


if __name__ == "__main__":
    complement_sender: ComplementSender = ComplementSender()
    complement_sender.run()
