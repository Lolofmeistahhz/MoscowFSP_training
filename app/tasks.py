# app/tasks.py

import logging

from celery import shared_task

from app.celery import app as celery_app
from core.models import CalendarSportInfo, User
from utils import send_telegram_message
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

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
def task_example():
    result = 2 + 3
    logger.info(f"Task 'add' executed = {result}")
    print(result)
