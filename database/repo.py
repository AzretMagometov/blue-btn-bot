import logging
from enum import Enum, auto
from typing import Optional, List

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from database.engine import session_maker
from database.models import User, Chat

logger = logging.getLogger(__name__)


async def add_user(tg_id: int, name: str):
    async with session_maker() as session:
        try:
            async with session.begin():
                stmt = select(User).where(User.tg_id == tg_id).limit(1)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                if user:
                    user.is_blocked = False
                else:
                    user = User(tg_id=tg_id, tg_name=name)
                    session.add(user)
        except SQLAlchemyError as e:
            await session.rollback()


async def set_user_blocked(tg_id: int):
    logger.info(f'set_user_blocked - {tg_id}')
    async with session_maker() as session:
        try:
            async with session.begin():
                stmt = select(User).where(User.tg_id == tg_id).limit(1)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                if user:
                    user.is_blocked = True

        except SQLAlchemyError as e:
            await session.rollback()


class AddChatStatus(Enum):
    USER_NOT_FOUND = auto()
    CHAT_ALREADY_EXISTS = auto()
    CHAT_ADDED = auto()
    ERROR_OCCURRED = auto()


async def add_chat_to_user(user_tg_id: int, chat_tg_id: int, chat_name: str) -> AddChatStatus:
    async with session_maker() as session:
        try:
            async with session.begin():
                # Поиск пользователя по tg_id
                stmt = select(User).where(User.tg_id == user_tg_id).limit(1)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                if not user:
                    logger.info(f"Пользователь с tg_id={user_tg_id} не найден.")
                    return AddChatStatus.USER_NOT_FOUND

                # Проверка, существует ли уже чат для этого пользователя
                stmt_chat = select(Chat).where(
                    Chat.tg_id == chat_tg_id,
                    Chat.fk_user_id == user.id
                ).limit(1)
                result_chat = await session.execute(stmt_chat)
                existing_chat = result_chat.scalar_one_or_none()

                if existing_chat:
                    logger.info(f"Чат с tg_id={chat_tg_id} уже существует для пользователя id={user.id}.")
                    return AddChatStatus.CHAT_ALREADY_EXISTS

                # Создание и добавление нового чата
                chat = Chat(
                    tg_id=chat_tg_id,
                    tg_name=chat_name
                    # fk_user_id устанавливается автоматически через отношение
                )
                user.chats.add(chat)
                logger.info(f"Добавлен чат с tg_id={chat_tg_id} для пользователя id={user.id}.")
                return AddChatStatus.CHAT_ADDED
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при добавлении чата: {e}")
            # Откат транзакции выполняется автоматически при исключении внутри session.begin()
            return AddChatStatus.ERROR_OCCURRED


async def get_user_chats(user_tg_id: int) -> List[Chat]:
    """
    Получает список чатов, связанных с пользователем по его Telegram ID.

    :param user_tg_id: Telegram ID пользователя.
    :return: Список объектов Chat. Пустой список, если пользователь не найден или у него нет чатов.
    """
    async with session_maker() as session:
        try:
            async with session.begin():
                stmt = select(User).where(User.tg_id == user_tg_id).limit(1)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                if not user:
                    logger.info(f"Пользователь с tg_id={user_tg_id} не найден.")
                    return []

                chats = list(user.chats)
                logger.info(f"Найдено {len(chats)} чатов для пользователя tg_id={user_tg_id}.")
                return chats
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении чатов пользователя tg_id={user_tg_id}: {e}")
            return []


async def remove_chat_from_user(chat_tg_id: int) -> list[int]:
    async with session_maker() as session:
        try:
            async with session.begin():
                stmt = select(Chat).options(selectinload(Chat.user)).where(Chat.tg_id == chat_tg_id)
                result = await session.execute(stmt)
                chats = result.scalars().all()
                if not chats:
                    return []

                user_ids = [chat.user.tg_id for chat in chats if not chat.user.is_blocked]

                for chat in chats:
                    await session.delete(chat)
                return user_ids
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при удалении чата = {chat_tg_id}: {e}")
            return []
