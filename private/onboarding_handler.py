import asyncio
import logging

from aiogram import Router, F
from aiogram.enums import ChatType, ParseMode
from aiogram.filters import CommandStart, ChatMemberUpdatedFilter, LEAVE_TRANSITION, Command
from aiogram.types import Message, CallbackQuery, ChatMemberUpdated

from database.repo import add_user, add_chat_to_user, AddChatStatus, set_user_blocked
from public.adding_handler import AddingConfirmed

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(F.chat.type == ChatType.PRIVATE)


@router.message(CommandStart())
async def on_start_command(message: Message):
    name = message.from_user.username if message.from_user.username else message.from_user.first_name
    await add_user(message.from_user.id, name)

    text = ("Привет!\n"
            "Этот бот поможет добавить закрепленный пост с синей кнопкой в твой канал или группу.\n"
            "Просто действуй по инструкции и всё получится!")
    await message.answer(text)

    text = ("Сделай этого бота (@blue_btn_bot) администратором.\n"
            "Дай ему право писать и закреплять сообщения.\n"
            "Вот видеоинструкция.\n")

    add_bot_as_admin_file_id = "BAACAgIAAxkBAAMDZx6POUN3y-nQCT3fQmnFnkebo0YAAspVAAJ80fBIOSwF0jZaiE82BA"
    add_bot_as_admin_file_unique_id = "AgADylUAAnzR8Eg"

    await asyncio.sleep(5)
    await message.answer_video(video=add_bot_as_admin_file_id, caption=text)


@router.callback_query(AddingConfirmed.filter())
async def on_channel_confirmed(callback: CallbackQuery, callback_data: AddingConfirmed):
    await callback.message.delete_reply_markup()
    status = await add_chat_to_user(user_tg_id=callback.from_user.id,
                                    chat_tg_id=callback_data.id,
                                    chat_name=callback_data.name)

    if status == AddChatStatus.USER_NOT_FOUND:
        await callback.bot.send_message(chat_id=callback.from_user.id, text="Ошибка. Вызови /start")
    elif status == AddChatStatus.CHAT_ALREADY_EXISTS:
        await callback.bot.send_message(chat_id=callback.from_user.id, text="Оказывается, такой чат уже есть")
    elif status == AddChatStatus.CHAT_ADDED:
        await callback.bot.send_message(chat_id=callback.from_user.id,
                                        text=f"Канал {callback_data.name} добавлен!\n"
                                             f"Вызови команду /send для отправки сообщения в канал!")
    elif status == AddChatStatus.ERROR_OCCURRED:
        await callback.bot.send_message(chat_id=callback.from_user.id, text="Ошибка. Попробуй сделать все заново")


@router.my_chat_member(ChatMemberUpdatedFilter(LEAVE_TRANSITION), F.chat.type == ChatType.PRIVATE)
async def on_user_block_bot(event: ChatMemberUpdated):
    logger.info(f"on_user_block_bot - {event.chat.id}")
    await set_user_blocked(event.chat.id)


@router.message(Command('help'))
async def on_help_command(message: Message):
    await message.answer(
        text="Автор: <b>Азрет Магометов</b>\n"
             "Пиши в <a href='https://t.me/azret_magometov'>личку</a>, если есть вопросы, пожелания "
             "или идеи для сотрудничества.\n"
             "Заходи за эксклюзивами и подписывайся на мой <a href='https://t.me/itshifter'>канал</a>, "
             "мне будет приятно!",
        parse_mode=ParseMode.HTML
    )
