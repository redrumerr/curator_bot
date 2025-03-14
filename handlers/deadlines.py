from global_variables.variables import deadline_scheduler, predsed_team_ids
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from global_variables.token import api
from orm.models import *
from orm.database import delete, select
import random


async def send_spam(text, pt=False):
    if pt:
        users_mailing = []

        for vk_id in predsed_team_ids:
            users_mailing.append(asyncio.create_task(send_message(user_id=vk_id, text=text)))

        await asyncio.gather(*users_mailing)
    else:
        conversations = await api.messages.get_conversations(count=200)

        users_mailing = []

        for i in range(conversations.count):
            peer_type = conversations.items[i].conversation.peer.type.value
            if peer_type == 'user':
                user_id = conversations.items[i].conversation.peer.id
                users_mailing.append(asyncio.create_task(send_message(user_id=user_id, text=text)))

        await asyncio.gather(*users_mailing)


async def send_message(user_id, text):
    allow_message = await api.messages.is_messages_from_group_allowed(group_id=229122565, user_id=user_id)
    if allow_message.is_allowed:
        await api.messages.send(random_id=random.randint(1, 1000), peer_id=user_id, message=text)
        async with async_session as session:
            await session.execute(
                update(AlmostCurator).where(AlmostCurator.vk_id == user_id).values(hw_completion=False))
            session.commit()


async def deadline_reminder(deadline_id, name, is_birthday, remain_time_sec, text=''):
    if is_birthday:
        minutes, remain_time_sec = divmod(remain_time_sec, 60)  # перевод секунд в минуты
        hours, minutes = divmod(minutes, 60)  # перевод минут в часы

        msg = f'{name} через {hours} часов, {minutes} минут'

        await send_spam(msg, is_birthday)
        return

    if remain_time_sec == 0:
        msg = f"Дедлайн на {name} прошел!"
        async with async_session as session:
            await session.execute(delete(Deadline).where(Deadline.id == deadline_id))
            await session.commit()
        await send_spam(msg)
    else:
        msg = text
        await send_spam(msg)


def add_deadline_to_schedule(id_deadline: int, deadline_end: datetime, is_birthday: bool, name: str, text=''):
    now = datetime.now()
    if is_birthday:
        for remaining_seconds in [180, 43200]:
            reminder = deadline_end - timedelta(seconds=remaining_seconds)

            # Если напоминалка уже была, то пропускаем
            if now > reminder:
                continue

            deadline_scheduler.add_job(func=deadline_reminder,
                                       trigger=CronTrigger(year=reminder.year,
                                                           month=reminder.month,
                                                           day=reminder.day,
                                                           hour=reminder.hour,
                                                           minute=reminder.minute,
                                                           timezone="Europe/Moscow"),
                                       args=[id_deadline, name, is_birthday, remaining_seconds])
    else:
        remaining_time = (deadline_end - datetime.now()).total_seconds()

        for i in [1, 0]:
            remaining_seconds = round(remaining_time * i)

            # Если остаётся меньше минуты до дедлайна, то уже не напоминаем
            if remaining_seconds < 60 and remaining_seconds != 0:
                continue

            # Создаём задачу для напоминания о дедлайне
            reminder = deadline_end - timedelta(seconds=remaining_seconds)

            # Если напоминалка уже была, то пропускаем
            if now > reminder:
                continue

            deadline_scheduler.add_job(func=deadline_reminder,
                                       trigger=CronTrigger(year=reminder.year,
                                                           month=reminder.month,
                                                           day=reminder.day,
                                                           hour=reminder.hour,
                                                           minute=reminder.minute,
                                                           timezone="Europe/Moscow"),
                                       args=[id_deadline, name, is_birthday, remaining_seconds, text])
