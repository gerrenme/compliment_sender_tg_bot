import telebot
import psycopg2

from telebot import types
from config import host, user, password, db_name, entity_name


class ComplementSender:
    def __init__(self):
        self.bot = telebot.TeleBot('6353944311:AAF3BwfqcHAdFX3IqWe6H6HVXC55OXyxEyY')
        self.user_id = ""
        self.connection = psycopg2.connect(host=host, user=user, password=password, database=db_name)
        self.connection.autocommit = True

        @self.bot.message_handler(commands=['start'])
        def start(message):
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

            new_user_btn = types.KeyboardButton("Add user to mailing list")
            check_users_btn = types.KeyboardButton("Check mailing list")

            markup.add(new_user_btn)
            markup.add(check_users_btn)

            self.bot.send_message(message.from_user.id, "test_message for start", reply_markup=markup)

        @self.bot.message_handler(content_types=['text'])
        def get_text_messages(message):

            if message.text == "/add":
                self.bot.send_message(message.from_user.id, "Please indicate user id")
                self.bot.register_next_step_handler(message, add_user)

            if message.text == "/show":
                self.bot.send_message(message.from_user.id, "Preparing data, please wait a few seconds")
                show_users(message)
                print("FINISHED")

        def add_user(user_id):
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
                        print(data)
                        users = [t[0] for t in data]
                        print(users)
                        self.bot.send_message(message.from_user.id, "\n".join(users))

                    else:
                        self.bot.send_message(message.from_user.id, "There are no users in the database")

            except Exception as _ex:
                print(f"[LOG_show_users] Error!! {_ex}")

    def run(self):
        with self.connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {entity_name};")
            cursor.execute(f"""CREATE TABLE IF NOT EXISTS {entity_name} (
            user_id VARCHAR(50) PRIMARY KEY
                           );""")

        self.bot.polling(none_stop=True, interval=0)


if __name__ == "__main__":
    complement_sender = ComplementSender()
    complement_sender.run()
