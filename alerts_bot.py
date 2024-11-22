import os

import django
import telebot
from telebot import types
from django.http import HttpResponse
from django.views import View
from django.core.mail import send_mail
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

TOKEN = '7940948222:AAFd0rD-U9pt1uGTq9lkf1dIM5ENDsRL-DI'

from core.models import User

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    args = message.text.split()[1:]

    if args:
        user_id = args[0]
        try:
            user = User.objects.get(id=user_id)
            user.tg_chat = chat_id
            user.save()
            bot.reply_to(message, f"Привет! Я привязал твой chat_id))")
        except User.DoesNotExist:
            bot.reply_to(message, "Пользователь не найден.")
    else:
        bot.reply_to(message, "Привет! Ты перешел по ссылке без параметра start.")

bot.polling()