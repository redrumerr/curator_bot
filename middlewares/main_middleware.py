import os

from vkbottle_types.objects import UsersUserFull
from vkbottle import BaseMiddleware
from vkbottle.bot import Message

from orm.database import select
from orm.models import Student

from handlers.predsed_team import admin_labeler

from global_variables.variables import predsed_team_ids


class NoBotMiddleware(BaseMiddleware[Message]):
    async def pre(self):
        if self.event.from_id < 0:
            self.stop("Groups are not allowed to use bot")


class AdminMiddleware(BaseMiddleware[Message]):
    async def pre(self):
        if not any([type(await handler.filter(self.event)) is dict for handler in admin_labeler.message_view.handlers]):
            return None

        if self.event.from_id in predsed_team_ids:
            return

        await self.event.answer("Нельзя тебе сюда!")
        self.stop(f'vk_id: {self.event.from_id} пытался попасть в Админ-панель')
