import telebot
from telebot import types

bot = telebot.TeleBot('6353944311:AAF3BwfqcHAdFX3IqWe6H6HVXC55OXyxEyY')
user_id = ""


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    new_user_btn = types.KeyboardButton("Add user to mailing list")
    check_users_btn = types.KeyboardButton("Check mailing list")

    markup.add(new_user_btn)
    markup.add(check_users_btn)

    bot.send_message(message.from_user.id, "test_message for start", reply_markup=markup)


@bot.message_handler(content_types=['text'])
def get_text_messages(message):

    if message.text == "/add":
        bot.send_message(message.from_user.id, "Please indicate user id")
        bot.register_next_step_handler(message, get_id)


def get_id(message):
    global user_id
    user_id = message.text
    bot.send_message(message.from_user.id, text='user add successfully')
    bot.send_message(message.from_user.id, text=f'user |{user_id}| in system')


if __name__ == "__main__":
    bot.polling(none_stop=True, interval=0)
