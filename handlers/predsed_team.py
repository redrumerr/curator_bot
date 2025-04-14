import datetime
import os

import sqlalchemy
import vkbottle
from vkbottle.bot import Message, BotLabeler

import time

from global_variables.variables import *
from global_variables.states import *
from global_variables.token import api

from orm.database import select, update, async_session, delete, asc, desc
from orm.models import AlmostCurator, CompetitionActivity, CompetitionRules, CompetitionInteractions, \
    CompetitionAdditional, CompetitionResponsibility, Deadline

from keyboards.main_keyboards import admin_kb, strikes_kb, back_kb, competition_kb, homework_kb, accept_spam_kb,\
    choose_deadline_kb, top_kb, top_asc_desc_kb
from vkbottle.dispatch.handlers import MessageReplyHandler

from handlers.deadlines import add_deadline_to_schedule

import re

import random

import aiohttp
import aiofiles
import aioshutil

import asyncio

admin_labeler = BotLabeler()
admin_labeler.vbml_ignore_case = True


@admin_labeler.private_message(text=['Админ-панель'])
async def admin_welcome(message: Message):
    await message.answer('Привет, волчара🤙', keyboard=admin_kb())


@admin_labeler.private_message(text=['Страйки'])
async def strikes_center(message: Message):
    await message.answer('Таак, что будем делать?', keyboard=strikes_kb())


@admin_labeler.private_message(text=['Выдать страйк'])
async def set_strike(message: Message):
    await message.answer('Введи Фамилию человека, которого страйкаем', keyboard=back_kb())
    await state_dispenser.set(message.from_id, BotStates.SET_STRIKE)


@admin_labeler.private_message(state=BotStates.SET_STRIKE)
async def set_strike_name(message: Message):
    fullname = message.text
    async with async_session as session:
        result = await session.execute(select(AlmostCurator.strikes_number, AlmostCurator.vk_id)
                                       .where(AlmostCurator.name == fullname))
        try:
            strikes_num, vk_id = result.fetchall()[0]
        except IndexError:
            await message.answer('Данный человек не найден. Возможно ты где-то ошибся. Попробуй еще раз')
            await state_dispenser.delete(message.from_id)
            await state_dispenser.set(message.from_id, BotStates.SET_STRIKE)
            return
        await session.execute(update(AlmostCurator)
                              .where(AlmostCurator.name == fullname)
                              .values(strikes_number=strikes_num + 1))
        await session.commit()

    await message.answer(f'Человек был страйкнут, теперь у него всего {strikes_num + 1} страйков',
                         keyboard=admin_kb())
    await state_dispenser.delete(message.from_id)
    await api.messages.send(user_id=vk_id, random_id=random.randint(0, 1000),
                            message=f'Тебе прилетел страйк, теперь у тебя их всего {strikes_num + 1}')


@admin_labeler.private_message(text=['Убрать страйк'])
async def set_strike(message: Message):
    await message.answer('Введи Фамилию человека, у которого убираем страйк',
                         keyboard=back_kb())
    await state_dispenser.set(message.from_id, BotStates.CANCEL_STRIKE)


@admin_labeler.private_message(state=BotStates.CANCEL_STRIKE)
async def set_strike_name(message: Message):
    fullname = message.text
    async with async_session as session:
        result = await session.execute(select(AlmostCurator.strikes_number, AlmostCurator.vk_id)
                                       .where(AlmostCurator.name == fullname))
        try:
            strikes_num, vk_id = result.fetchall()[0]
        except IndexError:
            await message.answer('Данный человек не найден. Возможно ты где-то ошибся. Попробуй еще раз')
            await state_dispenser.delete(message.from_id)
            await state_dispenser.set(message.from_id, BotStates.CANCEL_STRIKE)
            return
        await session.execute(update(AlmostCurator)
                              .where(AlmostCurator.name == fullname)
                              .values(strikes_number=strikes_num - 1))
        await session.commit()
    await message.answer(f'Страйк был убран, теперь у человека всего {strikes_num - 1} страйков',
                         keyboard=admin_kb())
    await api.messages.send(user_id=vk_id, random_id=random.randint(0, 1000),
                            message=f'У тебя был убран страйк, теперь у тебя их всего {strikes_num - 1}')
    await state_dispenser.delete(message.from_id)


@admin_labeler.private_message(text=['Матрица компетенций'])
async def start_competition_matrix(message: Message):
    await message.answer('Введи Фамилию человека, компетенцию которого ты хочешь оценить',
                         keyboard=back_kb())
    await state_dispenser.set(message.from_id, BotStates.RATE_COMP)


@admin_labeler.private_message(state=BotStates.RATE_COMP)
async def get_name_competition_matrix(message: Message):
    fullname = message.text
    async with async_session as session:
        result = await session.execute(select(AlmostCurator).where(AlmostCurator.name.contains(fullname)))
        try:
            ac = result.fetchall()[0][0]
        except IndexError:
            await message.answer('Данный человек не найден. Возможно ты где-то ошибся. Попробуй еще раз')
            await state_dispenser.delete(message.from_id)
            return
        ctx.set(str(message.from_id) + '_rated_person', ac.id)
        await message.answer(repr(ac), keyboard=competition_kb())
        result = await session.execute(select(CompetitionAdditional)
                                       .where(CompetitionAdditional.almost_curator_id == ac.id))
        comp = result.scalars().first()
        await message.answer(f'Комментарии:\n{str(comp)}')
        await state_dispenser.delete(message.from_id)


@admin_labeler.private_message(text=['Активность'])
async def rate_activity_comp(message: Message):
    ac_id = ctx.get(str(message.from_id) + '_rated_person')
    async with async_session as session:
        result = await session.execute(select(CompetitionActivity)
                                       .where(CompetitionActivity.almost_curator_id == ac_id))
        comp = result.scalars().first()
    if comp:
        await message.answer(str(comp))
        await message.answer('Напиши свою оценку от 1 до 10 (только целые числа)', keyboard=back_kb())
        ctx.set(str(message.from_id) + '_comp', 'activity')
        await state_dispenser.set(message.from_id, BotStates.RATE_COMP_NEXT)
    else:
        await message.answer('Этот человек не найден, попробуй еще раз', keyboard=admin_kb())


@admin_labeler.private_message(text=['Ответственность'])
async def rate_activity_comp(message: Message):
    ac_id = ctx.get(str(message.from_id) + '_rated_person')
    async with async_session as session:
        result = await session.execute(select(CompetitionResponsibility)
                                       .where(CompetitionResponsibility.almost_curator_id == ac_id))
        comp = result.scalars().first()
    if comp:
        await message.answer(str(comp))
        await message.answer('Напиши свою оценку от 1 до 10 (только целые числа)', keyboard=back_kb())
        ctx.set(str(message.from_id) + '_comp', 'responsibility')
        await state_dispenser.set(message.from_id, BotStates.RATE_COMP_NEXT)
    else:
        await message.answer('Этот человек не найден, попробуй еще раз', keyboard=admin_kb())


@admin_labeler.private_message(text=['Соблюдение правил'])
async def rate_activity_comp(message: Message):
    ac_id = ctx.get(str(message.from_id) + '_rated_person')
    async with async_session as session:
        result = await session.execute(select(CompetitionRules)
                                       .where(CompetitionRules.almost_curator_id == ac_id))
        comp = result.scalars().first()
    if comp:
        await message.answer(str(comp))
        await message.answer('Напиши свою оценку от 1 до 10 (только целые числа)', keyboard=back_kb())
        ctx.set(str(message.from_id) + '_comp', 'rules')
        await state_dispenser.set(message.from_id, BotStates.RATE_COMP_NEXT)
    else:
        await message.answer('Этот человек не найден, попробуй еще раз', keyboard=admin_kb())


@admin_labeler.private_message(text=['Взаимодействия'])
async def rate_activity_comp(message: Message):
    ac_id = ctx.get(str(message.from_id) + '_rated_person')
    async with async_session as session:
        result = await session.execute(select(CompetitionInteractions)
                                       .where(CompetitionInteractions.almost_curator_id == ac_id))
        comp = result.scalars().first()
    if comp:
        await message.answer(str(comp))
        await message.answer('Напиши свою оценку от 1 до 10 (только целые числа)', keyboard=back_kb())
        ctx.set(str(message.from_id) + '_comp', 'interactions')
        await state_dispenser.set(message.from_id, BotStates.RATE_COMP_NEXT)
    else:
        await message.answer('Этот человек не найден, попробуй еще раз', keyboard=admin_kb())


@admin_labeler.private_message(text=['Доп комментарий'])
async def rate_activity_comp(message: Message):
    ac_id = ctx.get(str(message.from_id) + '_rated_person')
    async with async_session as session:
        result = await session.execute(select(CompetitionAdditional)
                                       .where(CompetitionAdditional.almost_curator_id == ac_id))
        comp = result.scalars().first()
    if comp:
        await message.answer(str(comp))
        await message.answer('Напиши свои мысли насчет человека', keyboard=back_kb())
        ctx.set(str(message.from_id) + '_comp', 'additional')
        await state_dispenser.set(message.from_id, BotStates.RATE_COMP_NEXT)
    else:
        await message.answer('Этот человек не найден, попробуй еще раз', keyboard=admin_kb())


@admin_labeler.private_message(state=BotStates.RATE_COMP_NEXT)
async def get_rate(message: Message):
    rate = message.text
    comp = ctx.get(str(message.from_id) + '_comp')
    if comp != 'additional':
        comp = comp_dict[comp][0]
        if not (1 <= int(rate) <= 10):
            await message.answer('Только целые числа от 1 до 10...', keyboard=competition_kb())
            await state_dispenser.delete(message.from_id)
        else:
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
    else:
        comp = comp_dict[comp][0]
        pt = predsed_team_dict[str(message.from_id)]
        ac_id = ctx.get(str(message.from_id) + '_rated_person')
        async with async_session as session:
            await session.execute(update(comp).where(comp.almost_curator_id == ac_id).values(**{pt: rate}))
            await session.commit()
        await message.answer(f'Твоя оценка была изменена на {rate}', keyboard=admin_kb())
    await state_dispenser.delete(message.from_id)


@admin_labeler.private_message(text=['Отметить отсутствующих'])
async def mark_absent(message: Message):
    await message.answer('Напиши через новую строку Фамилии отсутствующих '
                         '\n\nНапример:\nМакейкин\nДорофеев', keyboard=back_kb())
    await state_dispenser.set(message.from_id, BotStates.MARK_ABSENT)


@admin_labeler.private_message(state=BotStates.MARK_ABSENT)
async def get_mark_absent(message: Message):
    people = message.text.split('\n')
    async with async_session as session:
        for ac in people:
            ac = ac.strip()
            result = await session.execute(select(AlmostCurator.meeting_attendance, AlmostCurator.vk_id)
                                           .where(AlmostCurator.name == ac))
            try:
                meeting_attendance, ac_id = result.fetchall()[0]
                await session.execute(update(AlmostCurator)
                                      .where(AlmostCurator.vk_id == ac_id)
                                      .values(meeting_attendance=meeting_attendance + 1))
            except IndexError:
                await message.answer(f'Почтикуратор с фамилией {ac} не найден.')
        await session.commit()
    await message.answer('Все готово!', keyboard=admin_kb())
    await state_dispenser.delete(message.from_id)


@admin_labeler.private_message(text=['Кикнуть'])
async def kick_ac(message: Message):
    await message.answer('Напиши через новую строку Фамилии'
                         '\n\nНапример:\nМакейкин\nДорофеев', keyboard=back_kb())
    await state_dispenser.set(message.from_id, BotStates.KICK_AC)


@admin_labeler.private_message(state=BotStates.KICK_AC)
async def get_kick_ac(message: Message):
    people = message.text.split('\n')
    async with async_session as session:
        for ac in people:
            result = await session.execute(select(AlmostCurator).where(AlmostCurator.name == ac))
            ac_to_delete = result.scalars().first()
            if ac_to_delete:
                await session.execute(delete(CompetitionActivity)
                                      .where(CompetitionActivity.almost_curator_id == ac_to_delete.id))
                await session.execute(delete(CompetitionInteractions)
                                      .where(CompetitionInteractions.almost_curator_id == ac_to_delete.id))
                await session.execute(delete(CompetitionRules)
                                      .where(CompetitionRules.almost_curator_id == ac_to_delete.id))
                await session.execute(delete(CompetitionAdditional)
                                      .where(CompetitionAdditional.almost_curator_id == ac_to_delete.id))
                await session.execute(delete(CompetitionResponsibility)
                                      .where(CompetitionResponsibility.almost_curator_id == ac_to_delete.id))
                await session.delete(ac_to_delete)
            else:
                await message.answer(f'Почтикуратор с фамилией {ac} не найден')
        await session.commit()
    await message.answer('Все готово!\n\n ❗ВАЖНО❗ \n\nНе забудь заблокировать этих людей в самой группе и удалить '
                         'историю сообщений с ними', keyboard=admin_kb())
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
                async with aiofiles.open("photo.png", "wb") as file:
                    await file.write(await response.read())
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
    await state_dispenser.set(message.peer_id, BotStates.DEADLINE_GET_NAME)


@admin_labeler.private_message(state=BotStates.DEADLINE_GET_NAME)
async def preview_spam(message: Message):
    message = await message.get_full_message()
    ctx.set(str(message.from_id) + '_text', message.text.replace("\n", "\\n"))
    await message.answer('Теперь установи время дедлайна в формате ДД.ММ ЧЧ:ММ', keyboard=back_kb())
    await state_dispenser.set(message.peer_id, BotStates.DEADLINE_GET_TIME)


@admin_labeler.private_message(state=BotStates.DEADLINE_GET_TIME)
async def get_deadline_text(message: Message):
    now = datetime.datetime.now()
    deadline = message.text

    try:
        deadline_time = datetime.datetime.strptime(f'{now.year} {deadline}', '%Y %d.%m %H:%M')
    except ValueError:
        await message.answer('Неправильный формат дедлайна. Используй ДД.ММ ЧЧ:ММ')
        await state_dispenser.delete(message.from_id)
        await state_dispenser.set(message.from_id, BotStates.DEADLINE_GET_TIME)
        return

    if deadline_time < now:
        await message.answer("Дедлайн должен быть позже текущего времени")
        await state_dispenser.delete(message.from_id)
        await state_dispenser.set(message.from_id, BotStates.DEADLINE_GET_TIME)
        return

    deadline_time_msg = '\n'.join((str(deadline_time)).split(' '))

    ctx.set(str(message.from_id) + '_deadline_time', deadline_time)

    await message.answer(f"\nВремя:\n{deadline_time_msg}\n"
                         f"\nНазвание:\n{ctx.get(str(message.from_id) + '_text')}\n\nОтправляю?",
                         keyboard=accept_spam_kb())
    await state_dispenser.set(message.from_id, BotStates.DEADLINE_ACCEPT)


@admin_labeler.private_message(state=BotStates.DEADLINE_ACCEPT)
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

        add_deadline_to_schedule(deadline.id,
                                 ctx.get(str(message.from_id) + "_deadline_time"),
                                 False,
                                 ctx.get(str(message.from_id) + "_text"), text)
        await message.answer(f'Рассылаем сообщения...', keyboard=admin_kb())
        ctx.delete(str(message.from_id) + "_deadline_time")
        ctx.delete(str(message.from_id) + "_text")
        await state_dispenser.delete(message.from_id)


@admin_labeler.private_message(text=['Выгрузить домашку'])
async def get_hw(message: Message):
    file_names = await asyncio.to_thread(os.listdir, 'homework')
    if file_names:
        await message.answer('Выбери дедлайн из доступных:', keyboard=choose_deadline_kb(*file_names))
        await state_dispenser.set(message.from_id, BotStates.HW_CHOOSE_ADM)
    else:
        await message.answer('Текущих заданий нет!')


@admin_labeler.private_message(state=BotStates.HW_CHOOSE_ADM)
async def choose_hw_adm(message: Message):
    folder_path = 'homework\\' + message.text
    output_zip_path = await aioshutil.make_archive(f'homework_zips\\{message.text}', 'zip', folder_path)

    if not os.path.exists(output_zip_path):
        await message.answer("Не удалось создать архив")
        return

    for i in range(1, 4):
        await message.answer(f'Пытаюсь отправить файл... Попытка №{i}')
        try:
            doc = await doc_uploader.upload(
                file_source=output_zip_path,
                peer_id=message.peer_id,
            )
            if doc:
                await message.answer(f'Вот тебе архив с заданием {message.text}:', attachment=doc, keyboard=admin_kb())
                await state_dispenser.delete(message.from_id)
                return
        except Exception as exception:
            await message.answer(f'Ошибка!\n\n{exception}')

    await message.answer('Чето херня какая-то с архивом, попроси саню ручками выгрузить', keyboard=admin_kb())


@admin_labeler.private_message(text=['Топы'])
async def top_hub(message: Message):
    await message.answer('Ты в меню топов', keyboard=top_kb())
    await state_dispenser.set(message.from_id, BotStates.TOP_GET_TAG)


@admin_labeler.private_message(state=BotStates.TOP_GET_TAG)
async def get_tag_top(message: Message):
    ctx.set(str(message.from_id) + '_tag', message.text)
    await message.answer('Теперь выбери порядок сортировки', keyboard=top_asc_desc_kb())
    await state_dispenser.set(message.from_id, BotStates.TOP_GET_ORDER_BY)


@admin_labeler.private_message(state=BotStates.TOP_GET_ORDER_BY)
async def get_order_by_top(message: Message):
    if message.text == 'По возрастанию':
        async with async_session as session:
            result = await session.execute(select(AlmostCurator)
                                           .order_by(asc(getattr(AlmostCurator, top_tags_dict[ctx.get(str(message.from_id) + '_tag')]))))
            acs = result.scalars().all()
    elif message.text == 'По убыванию':
        async with async_session as session:
            result = await session.execute(select(AlmostCurator)
                                           .order_by(
                desc(getattr(AlmostCurator, top_tags_dict[ctx.get(str(message.from_id) + '_tag')]))))
            acs = result.scalars().all()
    else:
        await message.answer('Такого варианта нет, попробуй еще раз', keyboard=top_asc_desc_kb())
        await state_dispenser.delete(message.from_id)
        await state_dispenser.set(message.from_id, BotStates.TOP_GET_TAG)
        return
    msg = f'Топ {ctx.get(str(message.from_id) + "_tag").lower()}, {message.text.lower()}:\n'
    for ac in acs:
        msg += f'{ac.name}: {getattr(ac, top_tags_dict[ctx.get(str(message.from_id) + "_tag")])}\n'
    await message.answer(msg, keyboard=admin_kb())
    await state_dispenser.delete(message.from_id)
