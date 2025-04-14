from global_variables.variables import deadline_scheduler, predsed_team_ids
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from global_variables.token import api
from orm.models import *
from orm.database import delete, select, update, and_
import random
import asyncio


async def send_spam(text, pt=False, finish=False, more_deadlines=False):
    if pt:
        for vk_id in predsed_team_ids:
            await send_message(user_id=vk_id, text=text)
    else:
        conversations = await api.messages.get_conversations(count=200)

        for i in range(conversations.count):
            peer_type = conversations.items[i].conversation.peer.type.value
            if peer_type == 'user':
                user_id = conversations.items[i].conversation.peer.id
                await send_message(user_id=user_id, text=text, finish=finish, more_deadlines=more_deadlines)


async def send_message(user_id, text, finish=False, more_deadlines=False):
    allow_message = await api.messages.is_messages_from_group_allowed(group_id=229122565, user_id=user_id)
    if allow_message.is_allowed:
        await api.messages.send(random_id=random.randint(1, 1000), peer_id=user_id, message=text)
        if not finish:
            async with async_session as session:
                await session.execute(update(AlmostCurator)
                                      .where(AlmostCurator.vk_id == user_id)
                                      .values(hw_completion=False))
                await session.commit()
        else:
            if user_id not in predsed_team_ids:
                async with async_session as session:
                    result = await session.execute(select(AlmostCurator.strikes_number)
                                                   .where(and_(AlmostCurator.hw_completion == False,
                                                               AlmostCurator.vk_id == user_id)))  # noqa
                    strikes_num = result.scalars().first()
                    if strikes_num is not None:
                        await session.execute(update(AlmostCurator)
                                              .where(AlmostCurator.vk_id == user_id)
                                              .values(strikes_number=strikes_num + 1))
                        await api.messages.send(random_id=random.randint(1, 1000), peer_id=user_id,
                                                message='Тебе выдан страйк!')
                        await session.commit()
                        if not more_deadlines:
                            await session.execute(update(AlmostCurator)
                                                  .where(AlmostCurator.vk_id == user_id)
                                                  .values(hw_completion=True))
                            await session.commit()


async def deadline_reminder(deadline_id, name, is_birthday, remain_time_sec, text=''):
    if is_birthday:
        minutes, remain_time_sec = divmod(remain_time_sec, 60)  # перевод секунд в минуты
        hours, minutes = divmod(minutes, 60)  # перевод минут в часы

        msg = f'{name} через {hours} часов, {minutes} минут'
    else:
        msg = text

    if remain_time_sec == 0 and not is_birthday:
        msg = f"Дедлайн на {name} прошел!"
        async with async_session as session:
            await session.execute(delete(Deadline).where(Deadline.id == deadline_id))
            await session.commit()
            deadlines = await session.execute(select(Deadline))
            deadlines = deadlines.scalars().first()
        await send_spam(msg, finish=True, more_deadlines=bool(deadlines))
        return

    await send_spam(msg, is_birthday)


def add_deadline_to_schedule(id_deadline: int, deadline_end: datetime, is_birthday: bool, name: str, text=''):
    now = datetime.now()
    if is_birthday:
        for remaining_seconds in [180, 43200]:
            remaining_seconds = round(remaining_seconds)
            reminder = deadline_end - timedelta(seconds=remaining_seconds)

            deadline_scheduler.add_job(func=deadline_reminder,
                                       trigger=CronTrigger(month=reminder.month,
                                                           day=reminder.day,
                                                           hour=reminder.hour,
                                                           minute=reminder.minute,
                                                           second=reminder.second,
                                                           timezone="Europe/Moscow"),
                                       args=[id_deadline, name, is_birthday, remaining_seconds, text])
    else:
        remaining_time = (deadline_end - datetime.now()).total_seconds()

        for i in [1, 0]:
            remaining_seconds = round(remaining_time * i)

            if i == 1:
                reminder = now + timedelta(seconds=10)
            else:
                reminder = deadline_end - timedelta(seconds=remaining_seconds)

            deadline_scheduler.add_job(func=deadline_reminder,
                                       trigger=CronTrigger(year=reminder.year,
                                                           month=reminder.month,
                                                           day=reminder.day,
                                                           hour=reminder.hour,
                                                           minute=reminder.minute,
                                                           second=reminder.second,
                                                           timezone="Europe/Moscow"),
                                       args=[id_deadline, name, is_birthday, remaining_seconds, text])


async def load_deadline():
    now = (datetime.now().month, datetime.now().day,
           datetime.now().hour, datetime.now().minute, datetime.now().second)
    async with async_session as session:
        deadlines = await session.execute(select(Deadline))
        deadlines = deadlines.scalars().all()
    for deadline in deadlines:
        deadline_time = (deadline.time.month, deadline.time.day,
                         deadline.time.hour, deadline.time.minute, deadline.time.second)
        if deadline_time >= now:
            add_deadline_to_schedule(deadline.id, deadline.time, deadline.birthday, deadline.name)
        else:
            async with async_session as session:
                await session.execute(delete(Deadline).where(Deadline.id == deadline.id))
                await session.commit()
