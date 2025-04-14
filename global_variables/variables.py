from vkbottle import BuiltinStateDispenser, CtxStorage, KeyboardButtonColor, PhotoMessageUploader, DocMessagesUploader
from vkbottle.framework.labeler import BotLabeler
from orm.models import CompetitionRules, CompetitionInteractions, CompetitionAdditional, CompetitionResponsibility, \
    CompetitionActivity, AlmostCurator
from global_variables.token import api
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

state_dispenser = BuiltinStateDispenser()
labeler = BotLabeler()
ctx = CtxStorage()
deadline_scheduler = AsyncIOScheduler()
photo_uploader = PhotoMessageUploader(api)
doc_uploader = DocMessagesUploader(api)

user_accounting = set()

green = KeyboardButtonColor.POSITIVE
red = KeyboardButtonColor.NEGATIVE
blue = KeyboardButtonColor.PRIMARY

predsed_team_ids = [280856836, 270739574, 495741575, 357311779, 183013715, 378539623]


comp_dict = {'activity': [CompetitionActivity, 'competition_activity_rate'],
             'responsibility': [CompetitionResponsibility, 'competition_responsibility_rate'],
             'additional': [CompetitionAdditional, 'competition_additional_rate'],
             'interactions': [CompetitionInteractions, 'competition_interactions_rate'],
             'rules': [CompetitionRules, 'competition_rules_rate']
             }

top_tags_dict = {'По страйкам': 'strikes_number',
                 'По рейтингу': 'rating',
                 'По пропускам': 'meeting_attendance'
                 }

predsed_team_dict = {
    '378539623': 'fedas_rate',
    '183013715': 'iras_rate',
    '270739574': 'sashas_rate',
    '280856836': 'katyas_rate',
    '495741575': 'artems_rate',
    '357311779': 'alinas_rate'
}
