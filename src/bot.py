import telebot
import threading
import psycopg2
# import schedule
# import time
import asyncio

from telebot import types
from re import match
from config import db_host, db_user, db_password, db_name, db_entity_name, admin_password


class ComplementSender:
    def __init__(self):
        self.bot = telebot.TeleBot('6353944311:AAF3BwfqcHAdFX3IqWe6H6HVXC55OXyxEyY')
        self.username = ""
        self.connection = psycopg2.connect(host=db_host, user=db_user, password=db_password, database=db_name)
        self.connection.autocommit = True
        self.chat_id = '0000000000'

        @self.bot.message_handler(commands=['start'])
        def start(message):
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

            # new_user_btn = types.KeyboardButton("Add user to mailing list")
            # check_users_btn = types.KeyboardButton("Check mailing list")
            # send_complement_btn = types.KeyboardButton("Send complement")
            #
            # markup.add(new_user_btn)
            # markup.add(check_users_btn)
            # markup.add(send_complement_btn)

            add_user(message)

            # self.bot.send_message(message.from_user.id, f"test_message for start. you're username is "
            #                                             f"{message.from_user.username}", reply_markup=markup)

        @self.bot.message_handler(commands=['chat'])
        def get_user_data(message):
            self.chat_id = message.from_user.id
            self.username = message.from_user.username
            # print(f'[LOG_get_user_data] Chat ID is {self.chat_id} and username is {self.username}')

        @self.bot.message_handler(content_types=['text'])
        def get_text_messages(message):

            if message.text == "/send" or message.text.lower() == "send a compliment to the user":
                get_user_data(message)
                self.bot.send_message(message.from_user.id, "Please indicate user id")
                self.bot.register_next_step_handler(message, send_complement)

            # elif message.text == "/show" or message.text.lower() == "check mailing list":
            #     get_user_data(message)
            #     self.bot.send_message(message.from_user.id, "Preparing data, please wait a few seconds")
            #     show_local_users(message)

            elif message.text == "/admin_show_db":
                get_user_data(message)
                self.bot.send_message(message.from_user.id, "Enter admin password")
                self.bot.register_next_step_handler(message, show_all_users)

            elif message.text == "/admin_show_chat_id":
                get_user_data(message)
                self.bot.send_message(message.from_user.id, f"Current chat id is {self.chat_id}")

            else:
                get_user_data(message)
                self.bot.send_message(message.from_user.id, "I do not understand what you want. Please use one of "
                                                            "the standard commands")

        def add_user(message):
            get_user_data(message)
            try:
                with self.connection.cursor() as cursor:
                    cursor.execute(f"SELECT * FROM {db_entity_name} WHERE user_id = '{self.username}';")
                    result = cursor.fetchone()

                if result is None:
                    with self.connection.cursor() as cursor:
                        cursor.execute(f"INSERT INTO {db_entity_name} VALUES('{self.username}', '{self.chat_id}', 0);")
                        self.bot.send_message(self.chat_id, "You have successfully registered, "
                                                            "But you can invite your friends to register in the bot "
                                                            "to send them compliments!!")

                else:
                    self.bot.send_message(self.chat_id, "You are already registered in my database")

            except Exception as _ex:
                print(f"[LOG_add_user] Error!! {_ex}")

        # def show_local_users(message):
        #     try:
        #         pass
        #
        #     except Exception as _ex:
        #         print(f"[LOG_show_users] Error!! {_ex}")

        def show_all_users(message):
            print(f'[LOG_show_all_users] User {self.username} requests admin rights')
            if check_admin_password(message):
                try:
                    with self.connection.cursor() as cursor:
                        cursor.execute(f"SELECT * FROM {db_entity_name};")
                        data = cursor.fetchall()

                        if data is not None:
                            users = [f"User {t[0]} received {t[2]} compliments" for t in data]
                            self.bot.send_message(message.from_user.id, "\n".join(users))

                        else:
                            self.bot.send_message(message.from_user.id, "There are no users in the database")
                except Exception as _ex:
                    print(f"[LOG_show_all_users] Error!! {_ex}")
            else:
                print(f'[LOG_show_all_users] Incorrect password from user {self.username}')
                self.bot.send_message(message.from_user_id, "Incorrect password")

        def send_complement(message):
            get_user_data(message)
            try:
                with self.connection.cursor() as cursor:
                    cursor.execute(f"SELECT * FROM {db_entity_name} WHERE user_id = '{message.text.split()[0]}';")
                    data = cursor.fetchall()

                    if data is not None and data != []:
                        cursor.execute(f"UPDATE {db_entity_name} SET complements_received = complements_received + 1 WHERE user_id = '{data[0][0]}';")
                        self.bot.send_message(data[0][1], f"You received a compliment!! {' '.join(message.text.split()[1:])}")
                        print(f'[LOG_send_complement] User {self.username} send complement to {data[0][0]}')

                    else:
                        self.bot.send_message(message.from_user.id, "There are no users in the database")
            except Exception as _ex:
                print(f"[LOG_send_complement] Error!! {_ex}")

        def check_admin_password(message):
            return message.text == admin_password

    def run(self):
        with self.connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {db_entity_name};")
            cursor.execute(f"""CREATE TABLE IF NOT EXISTS {db_entity_name} (
            user_id VARCHAR(50) PRIMARY KEY, 
            user_chat_id VARCHAR(10),
            complements_received INT
                           );""")

        main_thread = threading.Thread(target=self.bot.polling, kwargs={"none_stop": True, "interval": 0})
        # message_thread = threading.Thread(target=self.send_minute_message)

        # message_thread.daemon = True

        main_thread.start()
        # message_thread.start()


if __name__ == "__main__":
    complement_sender = ComplementSender()
    complement_sender.run()
