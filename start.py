import asyncio
from bot_configurator import start_bot
from orm.database import init_models
from handlers.deadlines import load_deadline

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    start_bot(loop)
