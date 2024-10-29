import asyncio
import logging

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from public.adding_handler import AddingConfirmed

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(F.chat.type == "private")


@router.message(CommandStart())
async def on_start_command(message: Message):
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
async def on_channel_confirmed(callback: CallbackQuery, callback_data: AddingConfirmed, state: FSMContext):
    await callback.message.delete_reply_markup()
    state_data = await state.get_data()
    channels = state_data.setdefault('channels', [])
    channels.append(callback_data.model_dump_json())
    await state.update_data(channels=channels)

    await callback.bot.send_message(
        chat_id=callback.from_user.id,
        text=f"Канал {callback_data.name} добавлен!\n"
             f"Вызови команду /send для отправки сообщения в канал!"
    )
