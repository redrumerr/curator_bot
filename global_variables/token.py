from envparse import env
from vkbottle import API

env.read_envfile('.env')

TOKEN = env.str('TOKEN')
POSTGRES_HOST = env.str('POSTGRES_HOST', default='localhost')
POSTGRES_PORT = env.str('POSTGRES_PORT', default=5432)
POSTGRES_PASSWORD = env.str('POSTGRES_PASSWORD')
POSTGRES_USER = env.str('POSTGRES_USER')
POSTGRES_DB = env.str('POSTGRES_DB')
SQLALCHEMY_DATABASE_URL = f'postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'  # noqa
SQLALCHEMY_TRACK_MODIFICATIONS = False

db_auth_data = {
    'database': POSTGRES_DB,
    'user': POSTGRES_USER,
    'password': POSTGRES_PASSWORD,
    'host': POSTGRES_HOST,
    'port': POSTGRES_PORT
}

api = API(token=TOKEN)
