import telebot
import threading
import psycopg2

from telebot import types
from config import db_host, db_user, db_password, db_name, db_entity_name, admin_password


class ComplementSender:
    def __init__(self):
        self.bot = telebot.TeleBot('6353944311:AAF3BwfqcHAdFX3IqWe6H6HVXC55OXyxEyY')

        self.connection = psycopg2.connect(host=db_host, user=db_user, password=db_password, database=db_name)
        self.connection.autocommit = True

        self.username = ""
        self.chat_id = '0000000000'

        @self.bot.message_handler(commands=['start'])
        def start(message):
            add_user(message)

        @self.bot.message_handler(commands=['chat'])
        def get_user_data(message):
            self.chat_id = message.from_user.id
            self.username = message.from_user.username

        @self.bot.message_handler(content_types=['text'])
        def get_text_messages(message):
            get_user_data(message)

            with self.connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT * FROM {db_entity_name} WHERE username = '{message.from_user.username}';")
                data = cursor.fetchall()

                if data is not None and data != []:
                    if message.text == "/send":
                        self.bot.send_message(message.from_user.id, "First indicate the id of the person to whom "
                                                                    "you want to send a compliment, then (separated by "
                                                                    "a space) - the compliment itself")
                        self.bot.register_next_step_handler(message, send_complement)

                    elif message.text == "/stat":
                        get_stat(message)

                    elif message.text == "/top":
                        get_top_users(message)

                    elif message.text == "/admin_show_db":
                        self.bot.send_message(message.from_user.id, "Enter admin password")
                        self.bot.register_next_step_handler(message, show_all_users)

                    elif message.text == "/admin_show_user_data":
                        self.bot.send_message(message.from_user.id,
                                              f"Current chat id is {self.chat_id} and username is {self.username}")

                    elif message.text == "/help":
                        self.bot.send_message(message.from_user.id,
                                              "This bot is designed to send anonymous comments to other users who "
                                              "are also using the bot. You can send the following commands:\n"
                                              " /start - to start interacting with the bot\n"
                                              " /send - to send an anonymous compliment to another user\n"
                                              " /stat - to get statistics on your account\n"
                                              " /top - to get top 5 users based on received and sent compliments")

                    else:
                        self.bot.send_message(message.from_user.id,
                                              "Unfortunately, I don't know such commands. Please use the /help "
                                              "command to see the bot capabilities")

                else:
                    self.bot.send_message(message.from_user.id, f"You need to register in the bot using the "
                                                                f"/start command to get statistics")

        def add_user(message):
            get_user_data(message)
            try:
                with self.connection.cursor() as cursor:
                    cursor.execute(
                        f"SELECT * FROM {db_entity_name} WHERE username = '{self.username}';")
                    result = cursor.fetchone()

                if result is None:
                    with self.connection.cursor() as cursor:
                        cursor.execute(
                            f"INSERT INTO {db_entity_name} VALUES('{self.username}', '{self.chat_id}', 0, 0);")
                        self.bot.send_message(self.chat_id, "You have successfully registered, "
                                                            "But you can invite your friends to register in the bot "
                                                            "to send them compliments!!")

                else:
                    self.bot.send_message(self.chat_id, "You are already registered in my database")

            except Exception as _ex:
                print(f"[LOG_add_user] Error!! {_ex}")

        def show_all_users(message):
            print(f'[LOG_show_all_users] User {self.username} requests admin rights')
            if check_admin_password(message):
                try:
                    with self.connection.cursor() as cursor:
                        cursor.execute(
                            f"SELECT * FROM {db_entity_name};")
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
                    cursor.execute(f"SELECT * FROM {db_entity_name} WHERE username = '{message.text.split()[0]}';")
                    data = cursor.fetchall()

                    if data is not None and data != []:
                        cursor.execute(
                            f"UPDATE {db_entity_name} SET complements_received = complements_received + 1 WHERE username = '{data[0][0]}';")
                        cursor.execute(
                            f"UPDATE {db_entity_name} SET complements_sended = complements_sended + 1 WHERE username = '{self.username}';")

                        self.bot.send_message(data[0][1], f"You received a compliment!! {' '.join(message.text.split()[1:])}")
                        self.bot.send_message(self.chat_id, "You have successfully sent a compliment!! "
                                                            "Someone's day just became a little kinder😊")
                        print(f'[LOG_send_complement] User {self.username} send complement to {data[0][0]}')

                    else:
                        self.bot.send_message(message.from_user.id, "There are no users in the database")
            except Exception as _ex:
                print(f"[LOG_send_complement] Error!! {_ex}")

        def get_stat(message):
            try:
                with self.connection.cursor() as cursor:
                    cursor.execute(
                        f"SELECT * FROM {db_entity_name} WHERE username = '{message.from_user.username}';")
                    data = cursor.fetchall()
                    self.bot.send_message(message.from_user.id, f"User {data[0][0]} sent {data[0][3]} "
                                                                f"compliments and received {data[0][2]} compliments")

            except Exception as _ex:
                print(f"[LOG_get_stat] Error!! {_ex}")

        def get_top_users(message):
            try:
                with self.connection.cursor() as cursor:
                    cursor.execute(
                        f"SELECT us.username, us.complements_received FROM {db_entity_name} AS us ORDER BY us.complements_received DESC LIMIT 5;")
                    top_received = cursor.fetchall()

                    cursor.execute(
                        f"SELECT us.username, us.complements_sended FROM {db_entity_name} AS us ORDER BY us.complements_sended DESC LIMIT 5;")
                    top_sended = cursor.fetchall()

                    message_received = "\n".join([f'User {t[0]} received {t[1]} complements' for t in top_received])
                    message_sended = "\n".join([f'User {t[0]} sent {t[1]} complements' for t in top_sended])

                    self.bot.send_message(self.chat_id, f"top_receivers are:\n{message_received}\n\n"
                                                        f"and top_senders are:\n{message_sended}")

            except Exception as _ex:
                print(f"[LOG_get_top_users] Error!! {_ex}")

        def check_admin_password(message):
            return message.text == admin_password

    def run(self):
        with self.connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {db_entity_name};")
            cursor.execute(f"""CREATE TABLE IF NOT EXISTS {db_entity_name} (
            username VARCHAR(50) PRIMARY KEY, 
            user_chat_id VARCHAR(10),
            complements_received INT,
            complements_sended INT
                           );""")

        main_thread = threading.Thread(target=self.bot.polling, kwargs={"none_stop": True, "interval": 0})
        main_thread.start()


if __name__ == "__main__":
    complement_sender = ComplementSender()
    complement_sender.run()
