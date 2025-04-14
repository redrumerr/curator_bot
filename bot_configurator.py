from handlers.main_handlers import main_labeler
from handlers.predsed_team import admin_labeler
from handlers.deadlines import load_deadline

from middlewares.main_middleware import NoBotMiddleware, AdminMiddleware

from global_variables.variables import state_dispenser, labeler, deadline_scheduler
from global_variables.token import api
from loguru import logger
from vkbottle import Bot
from orm.database import init_models, select, insert
import asyncio
import random
import sys


def start_bot(loop):
    # Настройка логов
    logger.remove()
    logger.add(sink=sys.stderr,
               format="{time:YYYY-MM-DD HH:mm:ss} {level} {message}",
               backtrace=False,
               level="ERROR",
               diagnose=True)

    # Подключение перехватчиков
    labeler.load(main_labeler)
    labeler.load(admin_labeler)

    # Подключение middleware
    labeler.message_view.register_middleware(NoBotMiddleware)
    labeler.message_view.register_middleware(AdminMiddleware)

    bot = Bot(api=api,
              labeler=labeler,
              state_dispenser=state_dispenser)

    deadline_scheduler.start()

    try:
        # result_2 = loop.run_until_complete(init_models())
        result = loop.run_until_complete(load_deadline())
    finally:
        pass

    print("Bot is started!")

    bot.run_forever()
