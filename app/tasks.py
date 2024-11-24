import datetime
import logging
import requests
from celery import Celery
from core.models import Notifications, User
from utils import send_telegram_message
from concurrent.futures import ThreadPoolExecutor

celery_app = Celery('your_app')

def get_calendar_sport_info_details(instance):
    details = (
        f"EКП: {instance.ekp}\n"
        f"Тип соревнований: {instance.calendar_sport_type}\n"
        f"Вид спорта: {instance.calendar_sport}\n"
        f"Команда: {instance.team}\n"
        f"Дата начала: {instance.date_from}\n"
        f"Дата окончния: {instance.date_to}\n"
        f"Место проведения: {instance.location}\n"
        f"Количество участников: {instance.count}\n"
    )
    return details

def send_message_to_users(message, users):
    with ThreadPoolExecutor() as executor:
        for user in users:
            executor.submit(send_telegram_message, message=message, chat_id=user.tg_chat)

def send_http_request(title, content,fcm_token):
    url = 'http://90.156.208.88:8080/bryansk/api/farebase/messages/push'
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json'
    }
    data = {
        'title': title,
        'content': content,
        'target': fcm_token
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        logging.info(f"Failed to send HTTP request: {response.status_code} - {response.text}")

@celery_app.task
def send_notifications():
    now = datetime.datetime.now()
    logging.info(now)
    notifications = Notifications.objects.filter(alert_datetime__lte=now)
    try:
        for notification in notifications:
            user = notification.user
            calendar_sport_info = notification.calendar_sport_info
            details = get_calendar_sport_info_details(calendar_sport_info)
            message = f'Уведомление: {notification.name}\nИнформация о событии:\n{details}'
            if user.tg_chat:
                send_message_to_users(message, [user])
            if user.fcm_token:
                send_http_request(notification.name, message,user.fcm_token)

            notification.delete()
    except Exception as e:
        print(e)
        logging.info(e)