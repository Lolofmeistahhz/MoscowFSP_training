import os

from telebot import TeleBot


def get_telegram_bot():
    if hasattr(get_telegram_bot, 'bot'): return get_telegram_bot.bot

    # token = os.getenv('ALERT_BOT_TOKEN')
    get_telegram_bot.bot = TeleBot("7940948222:AAFd0rD-U9pt1uGTq9lkf1dIM5ENDsRL-DI")
    return get_telegram_bot.bot


notification_bot = get_telegram_bot()
chat_id = '2108938640'

def send_telegram_message(chat_id: int, message: str):
    try:
        notification_bot.send_message(chat_id, message)
        print("Telegram test message sent to {}".format(chat_id))
    except Exception as e:
        print(f"{send_telegram_message.__name__} {e}")
