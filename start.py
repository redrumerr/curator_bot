import asyncio
from bot_configurator import start_bot
from orm.database import init_models
from global_variables.variables import init_schedule

if __name__ == "__main__":
    # asyncio.run(init_models())
    start_bot()
