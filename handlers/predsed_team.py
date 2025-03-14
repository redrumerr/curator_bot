import datetime

from vkbottle.bot import Message, BotLabeler

import time

from global_variables.variables import *
from global_variables.states import *
from global_variables.token import api

from orm.database import engine, select, update, async_session, delete
from orm.models import Student, AlmostCurator, CompetitionActivity, CompetitionRules, CompetitionInteractions, \
    CompetitionAdditional, CompetitionResponsibility, Deadline

from keyboards.main_keyboards import admin_kb, strikes_kb, back_kb, competition_kb, homework_kb, accept_spam_kb
from vkbottle.dispatch.handlers import MessageReplyHandler

from sqlalchemy import event

from handlers.deadlines import add_deadline_to_schedule

import re

import random

import aiohttp

import asyncio

admin_labeler = BotLabeler()
admin_labeler.vbml_ignore_case = True


@admin_labeler.private_message(text=['Админ-панель'])
async def admin_welcome(message: Message):
    await message.answer('Привет, волчара🤙', keyboard=admin_kb())


@admin_labeler.private_message(text=['Страйки'])
async def strikes_center(message: Message):
    await message.answer('Таак, что будем делать?', keyboard=strikes_kb())

    async with async_session as session:
        x = await session.execute(select(AlmostCurator))
        z = x.scalars().all()[-1]
        print(z.id)


@admin_labeler.private_message(text=['Выдать страйк'])
async def set_strike(message: Message):
    await message.answer('Введи Фамилию Имя человека, которого страйкаем \n\nНапример: Иванов Иван', keyboard=back_kb())
    await state_dispenser.set(message.from_id, BotStates.SET_STRIKE)


@admin_labeler.private_message(state=BotStates.SET_STRIKE)
async def set_strike_name(message: Message):
    fullname = message.text
    if not (len(fullname.split()) == 2 and all(
            list(filter(lambda x: str(x[0]).isupper(), fullname.split())))):
        await message.answer('Похоже, что ты написал Фамилию Имя не в том формате. Попробуй еще раз')
        await state_dispenser.delete(message.from_id)
        await state_dispenser.set(message.from_id, BotStates.SET_STRIKE)
    else:
        async with async_session as session:
            result = await session.execute(
                select(AlmostCurator.strikes_number, AlmostCurator.vk_id).filter(AlmostCurator.name.contains(fullname)))
            try:
                strikes_num, vk_id = result.fetchall()[0]
            except IndexError:
                await message.answer('Данный человек не найден. Возможно ты где-то ошибся. Попробуй еще раз')
                await state_dispenser.delete(message.from_id)
                await state_dispenser.set(message.from_id, BotStates.SET_STRIKE)
            await session.execute(update(AlmostCurator).filter(AlmostCurator.name.contains(fullname)).values(
                strikes_number=strikes_num + 1))
            await session.commit()
        await message.answer(f'Человек был страйкнут, теперь у него всего {strikes_num + 1} страйков',
                             keyboard=admin_kb())
        await state_dispenser.delete(message.from_id)
        await api.messages.send(user_id=vk_id, random_id=random.randint(0, 1000),
                                message=f'Тебе прилетел страйк, теперь у тебя их всего {strikes_num + 1}')


@admin_labeler.private_message(text=['Убрать страйк'])
async def set_strike(message: Message):
    await message.answer('Введи Фамилию Имя человека, у которого убираем страйк \n\nНапример: Иванов Иван',
                         keyboard=back_kb())
    await state_dispenser.set(message.from_id, BotStates.CANCEL_STRIKE)


@admin_labeler.private_message(state=BotStates.CANCEL_STRIKE)
async def set_strike_name(message: Message):
    fullname = message.text
    if not (len(fullname.split()) == 2 and all(
            list(filter(lambda x: str(x[0]).isupper(), fullname.split())))):
        await message.answer('Похоже, что ты написал Фамилию Имя не в том формате. Попробуй еще раз')
        await state_dispenser.delete(message.from_id)
        await state_dispenser.set(message.from_id, BotStates.CANCEL_STRIKE)
    else:
        async with async_session as session:
            result = await session.execute(
                select(AlmostCurator.strikes_number, AlmostCurator.vk_id).filter(AlmostCurator.name.contains(fullname)))
            try:
                strikes_num, vk_id = result.fetchall()[0]
            except IndexError:
                await message.answer('Данный человек не найден. Возможно ты где-то ошибся. Попробуй еще раз')
                await state_dispenser.delete(message.from_id)
                return
            await session.execute(update(AlmostCurator).filter(AlmostCurator.name.contains(fullname)).values(
                strikes_number=strikes_num - 1))
            await session.commit()
        await message.answer(f'Страйк был убран, теперь у человека всего {strikes_num - 1} страйков',
                             keyboard=admin_kb())
        await api.messages.send(user_id=vk_id, random_id=random.randint(0, 1000),
                                message=f'У тебя был убран страйк, теперь у тебя их всего {strikes_num - 1}')
        await state_dispenser.delete(message.from_id)


@admin_labeler.private_message(text=['Матрица компетенций'])
async def start_competition_matrix(message: Message):
    await message.answer('Введи Фамилию Имя человека, компетенцию которого ты хочешь оценить \n\nНапример: Иванов Иван',
                         keyboard=back_kb())
    await state_dispenser.set(message.from_id, BotStates.RATE_COMP)


@admin_labeler.private_message(state=BotStates.RATE_COMP)
async def get_name_competition_matrix(message: Message):
    fullname = message.text
    if not (len(fullname.split()) == 2 and all(
            list(filter(lambda x: str(x[0]).isupper(), fullname.split())))):
        await message.answer('Похоже, что ты написал Фамилию Имя не в том формате. Попробуй еще раз')
        await state_dispenser.delete(message.from_id)
        await state_dispenser.set(message.from_id, BotStates.RATE_COMP)
    else:
        async with async_session as session:
            result = await session.execute(select(AlmostCurator).filter(AlmostCurator.name.contains(fullname)))
            try:
                ac = result.fetchall()[0][0]
            except IndexError:
                await message.answer('Данный человек не найден. Возможно ты где-то ошибся. Попробуй еще раз ')
                await state_dispenser.delete(message.from_id)
                return
            ctx.set(str(message.from_id) + '_rated_person', ac.id)
            await message.answer(repr(ac), keyboard=competition_kb())
            await state_dispenser.delete(message.from_id)


@admin_labeler.private_message(text=['Активность'])
async def rate_activity_comp(message: Message):
    await message.answer('Напиши свою оценку от 1 до 5 (только целые числа)', keyboard=back_kb())
    ctx.set(str(message.from_id) + '_comp', 'activity')
    await state_dispenser.set(message.from_id, BotStates.RATE_COMP_NEXT)


@admin_labeler.private_message(text=['Ответственность'])
async def rate_activity_comp(message: Message):
    await message.answer('Напиши свою оценку от 1 до 5 (только целые числа)', keyboard=back_kb())
    ctx.set(str(message.from_id) + '_comp', 'responsibility')
    await state_dispenser.set(message.from_id, BotStates.RATE_COMP_NEXT)


@admin_labeler.private_message(text=['Соблюдение правил'])
async def rate_activity_comp(message: Message):
    await message.answer('Напиши свою оценку от 1 до 5 (только целые числа)', keyboard=back_kb())
    ctx.set(str(message.from_id) + '_comp', 'rules')
    await state_dispenser.set(message.from_id, BotStates.RATE_COMP_NEXT)


@admin_labeler.private_message(text=['Взаимодействия'])
async def rate_activity_comp(message: Message):
    await message.answer('Напиши свою оценку от 1 до 5 (только целые числа)', keyboard=back_kb())
    ctx.set(str(message.from_id) + '_comp', 'interactions')
    await state_dispenser.set(message.from_id, BotStates.RATE_COMP_NEXT)


@admin_labeler.private_message(text=['Доп комментарии'])
async def rate_activity_comp(message: Message):
    await message.answer('Напиши свою оценку от 1 до 10 (только целые числа)', keyboard=back_kb())
    ctx.set(str(message.from_id) + '_comp', 'additional')
    await state_dispenser.set(message.from_id, BotStates.RATE_COMP_NEXT)


@admin_labeler.private_message(state=BotStates.RATE_COMP_NEXT)
async def get_rate(message: Message):
    rate = message.text
    if not (1 <= int(rate) <= 10):
        await message.answer('Только целые числа от 1 до 10...', keyboard=competition_kb())
        await state_dispenser.delete(message.from_id)
    else:
        comp = comp_dict[ctx.get(str(message.from_id) + '_comp')][0]
        ac_comp_rate = comp_dict[ctx.get(str(message.from_id) + '_comp')][1]
        pt = predsed_team_dict[str(message.from_id)]
        ac_id = ctx.get(str(message.from_id) + '_rated_person')
        async with async_session as session:
            await session.execute(update(comp).where(comp.almost_curator_id == ac_id).values(**{pt: rate}))
            await session.commit()
            result = await session.execute(select(comp).where(comp.almost_curator_id == ac_id))
            comp_obj = result.scalars().first()
            comp_rates = [int(e) for e in str(comp_obj).split() if e.isdigit()]
            comp_avg = sum(comp_rates) / len(comp_rates)
            await session.execute(update(AlmostCurator).where(AlmostCurator.id == ac_id)
                                  .values(**{ac_comp_rate: round(comp_avg, 2)}))
            await session.commit()
            result = await session.execute(select(AlmostCurator.competition_rules_rate,
                                                  AlmostCurator.competition_interactions_rate,
                                                  AlmostCurator.competition_responsibility_rate,
                                                  AlmostCurator.competition_activity_rate, )
                                           .where(AlmostCurator.id == ac_id))
            x = sum(result.fetchall()[0]) / 4
            await session.execute(update(AlmostCurator).where(AlmostCurator.id == ac_id).values(rating=round(x, 2)))
            await session.commit()
            await message.answer(f'Твоя оценка была изменена на {rate}', keyboard=admin_kb())
        await state_dispenser.delete(message.from_id)


@admin_labeler.private_message(text=['Отметить отсутствующих'])
async def mark_absent(message: Message):
    await message.answer('Напиши через новую строку Фамилии или Фамилии Имена отсутствующих '
                         '\n\nНапример:\nМакейкин\nДорофеев Федор', keyboard=back_kb())
    await state_dispenser.set(message.from_id, BotStates.MARK_ABSENT)


@admin_labeler.private_message(state=BotStates.MARK_ABSENT)
async def get_mark_absent(message: Message):
    people = message.text.split('\n')
    for ac in people:
        async with async_session as session:
            result = await session.execute(
                select(AlmostCurator.meeting_attendance).where(AlmostCurator.name.contains(ac)))
            meeting_attendance = result.scalars().first()
            await session.execute(update(AlmostCurator)
                                  .where(AlmostCurator.name.contains(ac))
                                  .values(meeting_attendance=meeting_attendance + 1))
            await session.commit()
    await message.answer('Все готово!', keyboard=admin_kb())


@admin_labeler.private_message(text=['Кикнуть'])
async def kick_ac(message: Message):
    await message.answer('Напиши через новую строку Фамилии или Фамилии Имена отсутствующих '
                         '\n\nНапример:\nМакейкин\nДорофеев Федор', keyboard=back_kb())
    await state_dispenser.set(message.from_id, BotStates.KICK_AC)


@admin_labeler.private_message(state=BotStates.KICK_AC)
async def get_kick_ac(message: Message):
    people = message.text.split('\n')
    for ac in people:
        async with async_session as session:
            await session.execute(delete(AlmostCurator).where(AlmostCurator.name.contains(ac)))
            await session.commit()
    await message.answer('Все готово!', keyboard=admin_kb())
    await state_dispenser.delete(message.from_id)


@admin_labeler.private_message(text=['Загрузить календарь'])
async def upload_calendar(message: Message):
    await message.answer('Пришли новое фото для календаря', keyboard=back_kb())
    await state_dispenser.set(message.from_id, BotStates.GET_CALENDAR)


@admin_labeler.private_message(state=BotStates.GET_CALENDAR)
async def get_photo_calendar(message: Message):
    photo_url = message.attachments[0].doc.url
    async with aiohttp.ClientSession() as session:
        async with session.get(photo_url) as response:
            if response.status == 200:
                with open("photo.png", "wb") as file:
                    file.write(await response.read())
                await message.answer("Фото успешно загружено и сохранено!", keyboard=admin_kb())
            else:
                await message.answer("Не удалось загрузить фото. Попробуй заново", keyboard=admin_kb())
    await state_dispenser.delete(message.from_id)


@admin_labeler.private_message(text=['Домашка'])
async def hw_hub(message: Message):
    await message.answer('Выбери, что хочешь сделать', keyboard=homework_kb())


@admin_labeler.private_message(text=['Поставить дедлайн'])
async def get_deadline_time(message: Message):
    await message.answer('Введи название дедлайна', keyboard=back_kb())
    await state_dispenser.set(message.peer_id, BotStates.GET_DEADLINE_NAME)


@admin_labeler.private_message(state=BotStates.GET_DEADLINE_NAME)
async def preview_spam(message: Message):
    message = await message.get_full_message()
    ctx.set(str(message.from_id) + '_text', message.text.replace("\n", "\\n"))
    await message.answer('Теперь установи время дедлайна в формате ДД.ММ ЧЧ:ММ', keyboard=back_kb())
    await state_dispenser.set(message.peer_id, BotStates.GET_DEADLINE_TIME)


@admin_labeler.private_message(state=BotStates.GET_DEADLINE_TIME)
async def get_deadline_text(message: Message):
    now = datetime.datetime.now()
    deadline = message.text

    try:
        deadline_time = datetime.datetime.strptime(f'{now.year} {deadline}', '%Y %d.%m %H:%M')
    except ValueError:
        await message.answer('Неправильный формат дедлайна. Используй ДД.ММ ЧЧ:ММ')
        await state_dispenser.delete(message.from_id)
        await state_dispenser.set(message.from_id, BotStates.GET_DEADLINE_TIME)
        return

    if deadline_time < now:
        await message.answer("Дедлайн должен быть позже текущего времени")
        await state_dispenser.delete(message.from_id)
        await state_dispenser.set(message.from_id, BotStates.GET_DEADLINE_TIME)
        return

    deadline_time_msg = '\n'.join((str(deadline_time)).split(' '))

    ctx.set(str(message.from_id) + '_deadline_time', deadline_time)

    await message.answer(f"\nВремя:\n{deadline_time_msg}\n"
                         f"\nНазвание:\n{ctx.get(str(message.from_id) + '_text')}\n\nОтправляю?",
                         keyboard=accept_spam_kb())
    await state_dispenser.set(message.from_id, BotStates.ACCEPT_DEADLINE)


@admin_labeler.private_message(state=BotStates.ACCEPT_DEADLINE)
async def accept_deadline(message: Message):
    result = message.text
    if result == 'Отмена':
        await message.answer('Привет, волчара🤙', keyboard=admin_kb())
        return
    else:
        deadline_time_msg = '\n'.join((str(ctx.get(str(message.from_id) + "_deadline_time"))).split(' '))
        text = f'Юху! Новый дедлайн!\nДата и время:\n{deadline_time_msg}\n\n' \
               f'Название:\n{ctx.get(str(message.from_id) + "_text")}'

        deadline = Deadline(time=ctx.get(str(message.from_id) + "_deadline_time"),
                            name=ctx.get(str(message.from_id) + "_text"))
        async with async_session as session:
            session.add(deadline)
            await session.commit()
        start_time = time.time()
        add_deadline_to_schedule(deadline.id,
                                 ctx.get(str(message.from_id) + "_deadline_time"),
                                 False,
                                 ctx.get(str(message.from_id) + "_text"), text)
        end_time = time.time()
        await message.answer(f'Рассылка завершена за {round(end_time - start_time, 1)} сек.', keyboard=admin_kb())
        await state_dispenser.delete(message.from_id)
