import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats
from environs import Env
from redis.asyncio import Redis

import public.adding_handler
import private.onboarding_handler
import private.sending_handler
from utils import setup_logging_base_config

log_file_path = 'logs/app.log'
setup_logging_base_config(log_file_path)

env = Env()
env.read_env()


async def main():
    bot = Bot(token=env('BOT_TOKEN'))
    await bot.set_my_commands([
        BotCommand(command="/send", description="Отправить сообщение"),
        BotCommand(command="/help", description="Поддержка"),
    ], BotCommandScopeAllPrivateChats())

    redis = Redis(host=env('REDIS_HOST'), port=env('REDIS_PORT'))

    dp = Dispatcher(storage=RedisStorage(redis=redis, key_builder=DefaultKeyBuilder(with_destiny=True)))
    dp.include_routers(
        private.onboarding_handler.router,
        private.sending_handler.router,
        public.adding_handler.router
    )
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
