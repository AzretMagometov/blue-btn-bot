import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.base import KeyBuilder, DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

import setup.onboarding
import channel.channel

from utils import setup_logging_base_config

setup_logging_base_config()


async def main():
    redis = Redis()

    bot = Bot(token="7103087769:AAFihsxCMpwe16FRaSuNCwbB4bE4jjAEtwc")
    dp = Dispatcher(storage=RedisStorage(redis=redis, key_builder=DefaultKeyBuilder(with_destiny=True)))

    dp.include_routers(
        setup.onboarding.router,
        channel.channel.router
    )
    dp['redis'] = redis

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
