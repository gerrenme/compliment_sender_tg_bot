from typing import Dict

db_host: str = '127.0.0.1'
db_user: str = 'gerrenme'
db_password: str = '1'
db_name: str = 'compliment_sender'
db_entity_name: str = "users"

admin_password: str = "1"
open_ai_key: str = "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"
telebot_key: str = "6353944311:AAF3BwfqcHAdFX3IqWe6H6HVXC55OXyxEyY"

info_message: Dict[str, str] = {"send_standard_compliment": "First indicate the id of the person to whom "
                                                            "you want to send a compliment, then (separated by "
                                                            "a space) - the compliment itself",

                                "send_random_compliment": "You sent a random compliment to a random user. "
                                                          "Thank you for making other people's days brighter😊",

                                "bot_help": "This bot is designed to send anonymous comments to other users who "
                                            "are also using the bot. You can send the following commands:\n"
                                            " /start - to start interacting with the bot\n"
                                            " /send - to send an anonymous compliment to another user\n"
                                            " /random - to send random compliment to random user\n"
                                            " /stat - to get statistics on your account\n"
                                            " /top - to get top 5 users based on received and sent compliments",

                                "miss_command": "Unfortunately, I don't know such commands. Please use the /help "
                                                "command to see the bot capabilities😔",

                                "need_register": "You need to register in the bot using the /start command to get "
                                                 "statistics",

                                "success_register": "You have successfully registered, "
                                                            "But you can invite your friends to register in the bot "
                                                            "to send them compliments😜",

                                "success_compliment": "You have successfully sent a compliment!! "
                                                            "Someone's day just became a little kinder😊",

                                "already_register": "You are already registered in my database",

                                "generate_compliment": "Come up with a nice unique compliment and send just that",

                                "receive_random_compliment": "Congratulations!! You received a "
                                                             "compliment from a random user🎉🎉\n\n",

                                "add_to_queue": "We are currently receiving a lot of compliments for the generation, "
                                                "so your request has been added to the generation queue. As soon as "
                                                "the compliment is generated and sent, you will receive a notification",

                                "no_user_db": "There is no such user in the database😞 "
                                              "Perhaps you would like to invite him?",

                                "bot_blocked": "Something went wrong😞 "
                                               "The user you want to send a compliment to has probably blocked the bot"}
