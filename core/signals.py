import requests
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import CalendarSportInfo, User
from utils import send_telegram_message
from concurrent.futures import ThreadPoolExecutor

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

def send_http_request(title, content):
    url = 'http://90.156.208.88:8080/bryansk/api/farebase/messages/push-global'
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json'
    }
    data = {
        'title': title,
        'content': content
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print(f"Failed to send HTTP request: {response.status_code} - {response.text}")

@receiver(post_save, sender=CalendarSportInfo)
def calendar_sport_info_post_save(sender, instance, created, **kwargs):
    try:
        details = get_calendar_sport_info_details(instance)
        title = 'Добавлено событие' if created else 'Изменено событие'
        content = details
        send_http_request(title, content)
        message = f'{title}, вот информация:\n{details}'
        users_with_tg_chat = User.objects.filter(tg_chat__isnull=False).exclude(tg_chat='')
        send_message_to_users(message, users_with_tg_chat)
    except Exception as e:
        print(e)

@receiver(post_delete, sender=CalendarSportInfo)
def calendar_sport_info_post_delete(sender, instance, **kwargs):
    try:
        details = get_calendar_sport_info_details(instance)
        title = 'Прошло событие'
        content = details
        send_http_request(title, content)
        message = f'{title}, вот информация:\n{details}'
        users_with_tg_chat = User.objects.filter(tg_chat__isnull=False).exclude(tg_chat='')
        send_message_to_users(message, users_with_tg_chat)
    except Exception as e:
        print(e)