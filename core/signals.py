from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import CalendarSportInfo, User
from utils import send_telegram_message
from concurrent.futures import ThreadPoolExecutor

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
#
# @receiver(post_save, sender=CalendarSportInfo)
# def calendar_sport_info_post_save(sender, instance, created, **kwargs):
#     details = get_calendar_sport_info_details(instance)
#     message = f'Добавлено событие, вот информация:\n{details}' if created else f'Изменено событие, вот информация:\n{details}'
#     users_with_tg_chat = User.objects.filter(tg_chat__isnull=False).exclude(tg_chat='')
#     send_message_to_users(message, users_with_tg_chat)
#
# @receiver(post_delete, sender=CalendarSportInfo)
# def calendar_sport_info_post_delete(sender, instance, **kwargs):
#     details = get_calendar_sport_info_details(instance)
#     message = f'Прошло событие, вот информация:\n{details}'
#     users_with_tg_chat = User.objects.filter(tg_chat__isnull=False).exclude(tg_chat='')
#     send_message_to_users(message, users_with_tg_chat)