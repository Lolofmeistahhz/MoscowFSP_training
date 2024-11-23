# app/tasks.py
import datetime
import logging

from celery.utils.log import get_task_logger
from django.utils import timezone

from app.celery import app as celery_app
from core.models import CalendarSportInfo, User, Notifications
from utils import send_telegram_message
from concurrent.futures import ThreadPoolExecutor

logger = get_task_logger(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_calendar_sport_info_details(instance):
    details = (
        f"EKP: {instance.ekp}\n"
        f"Description: {instance.description}\n"
        f"Image: {instance.image}\n"
        f"Calendar Sport Type: {instance.calendar_sport_type}\n"
        f"Calendar Sport: {instance.calendar_sport}\n"
        f"Team: {instance.team}\n"
        f"Date From: {instance.date_from}\n"
        f"Date To: {instance.date_to}\n"
        f"Location: {instance.location}\n"
        f"Count: {instance.count}\n"
        f"Perfomer: {instance.perfomer}\n"
    )
    return details


def send_message_to_users(message, users):
    with ThreadPoolExecutor() as executor:
        for user in users:
            executor.submit(send_telegram_message, message=message, chat_id=user.tg_chat)


@celery_app.task
def test_task():
    try:
        calendar_sport_info = CalendarSportInfo.objects.get(id=16)
        details = get_calendar_sport_info_details(calendar_sport_info)
        message = f'Последнее событие, вот информация:\n{details}'
        users_with_tg_chat = User.objects.filter(tg_chat__isnull=False).exclude(tg_chat='')
        send_message_to_users(message, users_with_tg_chat)
    except CalendarSportInfo.DoesNotExist:
        logger.error(f"CalendarSportInfo with id {16} does not exist.")

@celery_app.task
def send_notifications():
    now = datetime.datetime.now()
    logging.info(now)
    print(now)
    notifications = Notifications.objects.filter(alert_datetime__lte=now)
    try:
        for notification in notifications:
            user = notification.user
            if user.tg_chat:
                calendar_sport_info = notification.calendar_sport_info
                details = get_calendar_sport_info_details(calendar_sport_info)
                message = f'Уведомление: {notification.name}\nИнформация о событии:\n{details}'
                send_message_to_users(message, [user])

            notification.delete()
    except Exception as e:
        print(e)
        logging.info(e)
