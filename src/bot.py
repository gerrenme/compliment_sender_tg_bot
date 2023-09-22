import telebot
import threading
import psycopg2
import schedule
import time

from telebot import types
from re import match
from config import host, user, password, db_name, entity_name


class ComplementSender:
    def __init__(self):
        self.bot = telebot.TeleBot('6353944311:AAF3BwfqcHAdFX3IqWe6H6HVXC55OXyxEyY')
        self.user_id = ""
        self.connection = psycopg2.connect(host=host, user=user, password=password, database=db_name)
        self.connection.autocommit = True
        self.chat_id = '1254904638'

        @self.bot.message_handler(commands=['start'])
        def start(message):
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

            new_user_btn = types.KeyboardButton("Add user to mailing list")
            check_users_btn = types.KeyboardButton("Check mailing list")
            send_complement_btn = types.KeyboardButton("Send complement")

            markup.add(new_user_btn)
            markup.add(check_users_btn)
            markup.add(send_complement_btn)

            get_chat_id(message)

            self.bot.send_message(message.from_user.id, "test_message for start", reply_markup=markup)

        @self.bot.message_handler(commands=['chat'])
        def get_chat_id(message):
            self.chat_id = message.from_user.id
            print(f'[LOG_get_chat_id] Chat ID is {self.chat_id}')

        @self.bot.message_handler(content_types=['text'])
        def get_text_messages(message):

            if message.text == "/add" or message.text == "Add user to mailing list":
                self.bot.send_message(message.from_user.id, "Please indicate user id")
                self.bot.register_next_step_handler(message, add_user)

            elif message.text == "/show" or message.text == "Check mailing list":
                self.bot.send_message(message.from_user.id, "Preparing data, please wait a few seconds")
                show_users(message)

            else:
                self.bot.send_message(message.from_user.id, "I do not understand what you want. Please use one of "
                                                            "the standard commands")

        def add_user(user_id):
            user_id.text = user_id.text.lower()
            if (user_id.text[0].isdigit() or len(user_id.text) < 5 or user_id.text[0] == '_' or
                    not bool(match(r"^[a-zA-Z][a-zA-Z0-9_]*$", user_id.text))):
                self.bot.send_message(user_id.from_user.id, "User_id must be at least 5 characters long, and the "
                                                            "first character cannot be a number or an underscore. "
                                                            "The following characters are allowed: a-z, 0-9, _")

            else:
                try:
                    with self.connection.cursor() as cursor:
                        cursor.execute(f"SELECT * FROM {entity_name} WHERE user_id = '{user_id.text}';")
                        result = cursor.fetchone()

                    if result is None:
                        with self.connection.cursor() as cursor:
                            cursor.execute(f"INSERT INTO {entity_name} VALUES('{ user_id.text}');")
                            self.bot.send_message(user_id.from_user.id, "Entry added successfully")

                    else:
                        self.bot.send_message(user_id.from_user.id, "A user with this user_id is already present in the database")

                except Exception as _ex:
                    print(f"[LOG_add_user] Error!! {_ex}")

        def show_users(message):
            try:
                with self.connection.cursor() as cursor:
                    cursor.execute(f"SELECT * FROM {entity_name};")
                    data = cursor.fetchall()

                    if data is not None:
                        users = [t[0] for t in data]
                        self.bot.send_message(message.from_user.id, "\n".join(users))

                    else:
                        self.bot.send_message(message.from_user.id, "There are no users in the database")

            except Exception as _ex:
                print(f"[LOG_show_users] Error!! {_ex}")

    def send_minute_message(self):
        self.bot.send_message(self.chat_id, "minute message")

    def run(self):
        with self.connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {entity_name};")
            cursor.execute(f"""CREATE TABLE IF NOT EXISTS {entity_name} (
            user_id VARCHAR(50) PRIMARY KEY
                           );""")

        main_thread = threading.Thread(target=self.bot.polling, kwargs={"none_stop": True, "interval": 0})
        message_thread = threading.Thread(target=self.send_minute_message)

        message_thread.daemon = True

        main_thread.start()
        message_thread.start()


if __name__ == "__main__":
    complement_sender = ComplementSender()
    complement_sender.run()
