import datetime
import os

from vkbottle.bot import Message, BotLabeler

from global_variables.variables import *
from global_variables.states import *

from orm.database import select, async_session, update, engine
from orm.models import AlmostCurator, CompetitionActivity, CompetitionResponsibility, CompetitionInteractions, \
    CompetitionRules, CompetitionAdditional, Deadline

from keyboards.main_keyboards import main_kb, back_kb, choose_deadline_kb

from handlers.deadlines import add_deadline_to_schedule

from sqlalchemy import event

import aiofiles
import aiohttp

import re

main_labeler = BotLabeler()
main_labeler.vbml_ignore_case = True


@main_labeler.private_message(text=['Выход'])
async def return_back(message: Message):
    try:
        await state_dispenser.delete(message.from_id)
    except KeyError:
        pass
    await message.answer('Вот основное меню', keyboard=main_kb(message.from_id))


@main_labeler.private_message(text=["Начать", "Start"])
async def start(message: Message):
    if not await is_user_registered(message.from_id):
        await message.answer('Привет, для начала, мы хотели бы познакомиться с тобой получше. '
                             'Введи свое ФИО \n\nНапример: Иванов Иван Иванович')
        await state_dispenser.set(message.peer_id, BotStates.REG_GET_FULL_NAME)
    else:
        await message.answer("Привет, я главный помощник студентов рэу!\n"
                             "Вот моё основное меню", keyboard=main_kb(message.from_id))


async def is_user_registered(user_id) -> bool:
    """ Проверка на регистрацию """
    async with engine.connect() as connection:
        result = await connection.execute(select(AlmostCurator).where(AlmostCurator.vk_id == user_id))
        rows = result.fetchall()
        return True if bool(rows) else False


@main_labeler.private_message(state=BotStates.REG_GET_FULL_NAME)
async def register_user_get_name(message: Message):
    """ Блок функций для регистрации пользователя """
    user_full_name = message.text
    if not (len(user_full_name.split()) == 3 and all(
            list(filter(lambda x: str(x[0]).isupper(), user_full_name.split())))):
        await message.answer('Похоже, что ты написал ФИО не в том формате. Попробуй еще раз')
        await state_dispenser.delete(message.from_id)
        await state_dispenser.set(message.from_id, BotStates.REG_GET_FULL_NAME)
    else:
        await message.answer(f'Приятно познакомиться, теперь введи номер группы \n\nНапример: 15.27Д-ИСТ02/24б')
        ctx.set(str(message.from_id) + '_full_name', user_full_name)
        await state_dispenser.set(message.peer_id, BotStates.REG_GET_GROUP)


@main_labeler.private_message(state=BotStates.REG_GET_GROUP)
async def register_user_get_group(message: Message):
    user_group = message.text
    if not bool(re.fullmatch('\d\d.\d\d[А-Я]-[\w\W]+\d\d/\d\dб', user_group)):
        await message.answer('Похоже, что ты написал группу не в том формате. Попробуй еще раз')
        await state_dispenser.delete(message.from_id)
        await state_dispenser.set(message.from_id, BotStates.REG_GET_GROUP)
    else:
        await message.answer('Напиши свой номер телефона \n\nНапример: 88005553535')
        ctx.set(str(message.from_id) + '_user_group', user_group)
        await state_dispenser.set(message.from_id, BotStates.REG_GET_PHONE)


@main_labeler.private_message(state=BotStates.REG_GET_PHONE)
async def register_user_get_phone(message: Message):
    phone_number = message.text
    if not bool(re.fullmatch('\d\d\d\d\d\d\d\d\d\d\d', phone_number)):
        await message.answer('Похоже, что ты написал телефон не в том формате. Попробуй еще раз')
        await state_dispenser.delete(message.from_id)
        await state_dispenser.set(message.from_id, BotStates.REG_GET_PHONE)
    else:
        await message.answer('Отлично, теперь напиши свой день рождения в формате дд.мм.гггг \n\nНапример: 31.12.2003')
        ctx.set(str(message.from_id) + '_user_phone', phone_number)
        await state_dispenser.set(message.from_id, BotStates.REG_GET_BIRTH_DATE)


@main_labeler.private_message(state=BotStates.REG_GET_BIRTH_DATE)
async def register_user_get_birth_date(message: Message):
    user_birth_date = message.text
    date_format = '%d.%m.%Y'
    ctx.set(str(message.from_id) + 'flag_for_reg', 0)
    try:
        user_birth_date = datetime.datetime.strptime(user_birth_date, date_format)
        ctx.set(str(message.from_id) + 'flag_for_reg', 1)
    except ValueError:
        await message.answer('Похоже, что ты написал день рождения не в том формате. Попробуй еще раз')
        await state_dispenser.delete(message.from_id)
        await state_dispenser.set(message.from_id, BotStates.REG_GET_BIRTH_DATE)
    if ctx.get(str(message.from_id) + 'flag_for_reg') == 1:
        ctx.set(str(message.from_id) + '_birth_date', user_birth_date)
        await message.answer('Ну и наконец, напиши свой тг или инст в свободном формате')
        await state_dispenser.set(message.from_id, BotStates.REG_GET_INST)
        ctx.delete(str(message.from_id) + 'flag_for_reg')


@main_labeler.private_message(state=BotStates.REG_GET_INST)
async def register_user_get_inst(message: Message):
    """ Конец регистрации """
    user_inst = message.text
    user_full_name = ctx.get(str(message.from_id) + '_full_name')
    user_group = ctx.get(str(message.from_id) + '_user_group')
    birth_date = ctx.get(str(message.from_id) + '_birth_date')
    phone = ctx.get(str(message.from_id) + '_user_phone')
    vk_id = message.from_id

    ac = AlmostCurator(vk_id=vk_id, name=user_full_name.split()[0], group_number=user_group,
                       birthday_date=birth_date, inst_or_tg=user_inst, phone_number=phone, full_name=user_full_name)

    ctx.delete(str(message.from_id) + '_full_name')
    ctx.delete(str(message.from_id) + '_user_group')
    ctx.delete(str(message.from_id) + '_birth_date')
    ctx.delete(str(message.from_id) + '_user_phone')

    async with async_session as session:
        session.add(ac)
        await session.commit()
        comp_act = CompetitionActivity(almost_curator_id=ac.id)
        comp_resp = CompetitionResponsibility(almost_curator_id=ac.id)
        comp_rule = CompetitionRules(almost_curator_id=ac.id)
        comp_inter = CompetitionInteractions(almost_curator_id=ac.id)
        comp_add = CompetitionAdditional(almost_curator_id=ac.id)
        birthday_reminder = Deadline(time=birth_date, name=f'День рождения {user_full_name}', birthday=True)
        session.add(birthday_reminder)
        session.add(comp_act)
        session.add(comp_resp)
        session.add(comp_rule)
        session.add(comp_inter)
        session.add(comp_add)
        await session.commit()

    add_deadline_to_schedule(birthday_reminder.id,
                             birth_date,
                             True,
                             f'День рождения {user_full_name}')

    await message.answer('Поздравляю, ты успешно зарегистрировался! \n\nВот моё основное меню',
                         keyboard=main_kb(message.from_id))
    await state_dispenser.delete(message.from_id)


@main_labeler.private_message(text=["get_id"])
async def get_id(message: Message):
    await message.answer(f'Твой id: {message.from_id}')


@main_labeler.private_message(text=['Мой профиль'])
async def get_my_profile(message: Message):
    async with async_session as session:
        result = await session.execute(select(AlmostCurator).where(AlmostCurator.vk_id == message.from_id))
        ac = result.fetchall()[0][0]
        await message.answer(str(ac))


@main_labeler.private_message(text=['Найти человека'])
async def get_other_profile(message: Message):
    await message.answer('Введи Фамилию человека, которого хочешь найти',
                         keyboard=back_kb())
    await state_dispenser.set(message.from_id, BotStates.GET_OTHER_PROFILE)


@main_labeler.private_message(state=BotStates.GET_OTHER_PROFILE)
async def get_other_profile_surname(message: Message):
    fullname = message.text
    async with async_session as session:
        result = await session.execute(select(AlmostCurator).where(AlmostCurator.name == fullname))
        try:
            ac = result.fetchall()[0][0]
        except IndexError:
            await message.answer('Данный человек не найден. Возможно ты где-то ошибся. Попробуй еще раз ',
                                 keyboard=main_kb(message.from_id))
            await state_dispenser.delete(message.from_id)
            return
        if message.from_id in predsed_team_ids:
            await message.answer(repr(ac), keyboard=main_kb(message.from_id))
            result = await session.execute(select(CompetitionAdditional)
                                           .where(CompetitionAdditional.almost_curator_id == ac.id))
            comp = result.scalars().first()
            await message.answer(f'Комментарии:\n{str(comp)}')
        else:
            await message.answer(str(ac), keyboard=main_kb(message.from_id))
    await state_dispenser.delete(message.from_id)


@main_labeler.private_message(text=['Календарь'])
async def get_calendar(message: Message):
    doc = await doc_uploader.upload(
        file_source="photo.png",
        peer_id=message.peer_id,
    )
    await message.answer(attachment=doc)


@main_labeler.private_message(text=['Сдать домашку'])
async def pass_hw(message: Message):
    async with async_session as session:
        deadlines = await session.execute(select(Deadline).where(Deadline.birthday == False))  # noqa
        deadlines = [deadline.name for deadline in deadlines.scalars().all()]
    if deadlines:
        await message.answer('Выбери дедлайн из доступных:', keyboard=choose_deadline_kb(*deadlines))
        await state_dispenser.set(message.from_id, BotStates.HW_GET_NAME)
    else:
        await message.answer('Текущих заданий нет!')


@main_labeler.private_message(state=BotStates.HW_GET_NAME)
async def get_homework_name(message: Message):
    deadline_name = message.text
    ctx.set(str(message.from_id) + '_homework_name', deadline_name)
    await message.answer('Пришли своё задание в формате ФАЙЛА. Если у тебя несколько фото/видео и т.д. '
                         'пришли ссылку на них (я.диск и пр) или объединенный файл', keyboard=back_kb())
    await state_dispenser.set(message.from_id, BotStates.HW_PASS)


@main_labeler.private_message(state=BotStates.HW_PASS)
async def get_homework_file(message: Message):
    deadline_name = ctx.get(str(message.from_id) + '_homework_name')
    ctx.delete(str(message.from_id) + '_homework_name')
    if message.attachments:
        for attachment in message.attachments:
            doc_url = attachment.doc.url
            ext = attachment.doc.ext
            async with async_session as session:
                ac = await session.execute(select(AlmostCurator).where(AlmostCurator.vk_id == message.from_id))
                ac_obj = ac.scalar()
                ac_name = ac_obj.name
            async with aiohttp.ClientSession() as http_session:
                async with http_session.get(doc_url) as response:
                    if response.status == 200:
                        path = f"homework\\{deadline_name}"
                        await asyncio.to_thread(os.makedirs, path, exist_ok=True)
                        async with aiofiles.open(path + f'\\{ac_name}.{ext}', "wb") as file:
                            await file.write(await response.read())
                        await message.answer("Домашка успешно загружена!", keyboard=main_kb(message.from_id))
                        async with async_session as session:
                            await session.execute(update(AlmostCurator)
                                                  .where(AlmostCurator.vk_id == message.from_id)
                                                  .values(hw_completion=True))
                            await session.commit()
                    else:
                        await message.answer("Не удалось загрузить домашку. Попробуй заново", keyboard=main_kb(message.from_id))
                        return
    else:
        if 'http' in message.text:
            async with async_session as session:
                ac = await session.execute(select(AlmostCurator).where(AlmostCurator.vk_id == message.from_id))
                ac_obj = ac.scalar()
                ac_name = ac_obj.name
            path = f"homework\\{deadline_name}"
            await asyncio.to_thread(os.makedirs, path, exist_ok=True)
            async with aiofiles.open(path + f'\\{ac_name}.txt', "wt") as file:
                await file.write(message.text)
            await message.answer("Домашка успешно загружена!", keyboard=main_kb(message.from_id))
            async with async_session as session:
                await session.execute(update(AlmostCurator)
                                      .where(AlmostCurator.vk_id == message.from_id)
                                      .values(hw_completion=True))
                await session.commit()
        else:
            await message.answer('Похоже твоя ссылка некорректна, попробуй еще раз', keyboard=main_kb(message.from_id))
            return
        await state_dispenser.delete(message.from_id)
