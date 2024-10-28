import asyncio
import json
import logging

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from channel.channel import ChannelConfirmed

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(F.chat.type == "private")


@router.message(CommandStart())
async def on_start_command(message: Message):
    text = ("Привет!\n"
            "Этот бот поможет добавить закрепленный пост с синей кнопкой в твой канал.\n"
            "Просто действуй по инструкции и всё получится!")
    await message.answer(text)

    text = ("Сделай этого бота - @blue_btn_bot - администратором своего канала.\n"
            "Дай ему возможность писать сообщения.\n"
            "Вот видеоинструкция.\n")

    add_bot_as_admin_file_id = "BAACAgIAAxkBAAMDZx6POUN3y-nQCT3fQmnFnkebo0YAAspVAAJ80fBIOSwF0jZaiE82BA"
    add_bot_as_admin_file_unique_id = "AgADylUAAnzR8Eg"

    await asyncio.sleep(5)
    await message.answer_video(video=add_bot_as_admin_file_id, caption=text)


@router.callback_query(ChannelConfirmed.filter())
async def on_channel_confirmed(callback: CallbackQuery, callback_data: ChannelConfirmed, state: FSMContext):
    await callback.message.delete_reply_markup()
    state_data = await state.get_data()
    channels = state_data.setdefault('channels', [])
    channels.append(callback_data.model_dump_json())
    await state.update_data(channels=channels)

    await callback.bot.send_message(
        chat_id=callback.from_user.id,
        text=f"Канал {callback_data.channel_name} добавлен!\n"
             f"Вызови команду /send для отправки сообщения в канал!"
    )


class ChannelSelected(CallbackData, prefix='ch_sel'):
    channel_id: int
    channel_name: str


@router.message(Command('cancel'))
async def on_cancel_command(message: Message, state: FSMContext):
    await clear_send_data(state)
    await message.answer("Отменено")


@router.message(Command('send'))
async def on_send_command(message: Message, state: FSMContext):
    data = await state.get_data()
    channels = data.setdefault('channels', [])
    if not channels:
        await message.answer("Нет добавленных каналов - сделай бота администратором канала, чтобы публиковать посты")
    else:
        builder = InlineKeyboardBuilder()
        for ch in channels:
            channel = json.loads(ch)
            builder.button(
                text=channel['channel_name'],
                callback_data=ChannelSelected(channel_id=channel['channel_id'], channel_name=channel['channel_name'])
            )
        builder.adjust(1, 1)

        text = ("Сейчас выберем канал, отправим в него пост, закрепим его и добавим кнопку.\n"
                "Ты в любой момент можешь вызвать команду /cancel чтобы отменить процесс.\n"
                "В каком канале нужно создать пост?")

        await message.answer(text, reply_markup=builder.as_markup())


class SendMessageToChannelStates(StatesGroup):
    enter_message = State()
    enter_btn_text = State()
    enter_btn_link = State()
    confirm_send = State()


@router.callback_query(ChannelSelected.filter())
async def on_channel_for_send_selected(callback: CallbackQuery, callback_data: ChannelSelected, state: FSMContext):
    await callback.message.delete_reply_markup()

    await state.update_data(send_channel_id=callback_data.channel_id, send_channel_name=callback_data.channel_name)
    await state.set_state(SendMessageToChannelStates.enter_message)

    await callback.message.answer(text="Теперь пришли мне текст поста")


@router.message(SendMessageToChannelStates.enter_message)
async def on_message_entered(message: Message, state: FSMContext):
    await state.update_data(send_message_id=message.message_id)
    await state.set_state(SendMessageToChannelStates.enter_btn_text)

    await message.answer(text="Теперь пришли мне текст на кнопке.\n"
                              "Лучше покороче, чтобы не обрезался")


@router.message(SendMessageToChannelStates.enter_btn_text)
async def on_btn_text_entered(message: Message, state: FSMContext):
    await state.update_data(send_btn_text=message.text)
    await state.set_state(SendMessageToChannelStates.enter_btn_link)

    await message.answer(text="Теперь пришли мне ссылку для кнопки.\n"
                              "Это должна быть обычная ссылка формата <i>http://www.google.ru</i>\n",
                         parse_mode=ParseMode.HTML,
                         disable_web_page_preview=True)


@router.message(SendMessageToChannelStates.enter_btn_link)
async def on_btn_link_entered(message: Message, state: FSMContext):
    try:
        data = await state.update_data(send_btn_link=message.text)
        await state.set_state(SendMessageToChannelStates.confirm_send)

        message_id = await message.bot.copy_message(
            chat_id=message.from_user.id,
            from_chat_id=message.from_user.id,
            message_id=data['send_message_id'],
            reply_markup=InlineKeyboardBuilder().add(
                InlineKeyboardButton(text=data['send_btn_text'], url=data['send_btn_link'])).as_markup()
        )

        await message.bot.pin_chat_message(message.from_user.id, message_id.message_id)

        await message.answer(
            "Сообщение и закреп будут выглядеть вот так ⬆️ ⬆️ ⬆️\n"
            "Отправляю в канал?",
            reply_markup=InlineKeyboardBuilder().add(
                InlineKeyboardButton(text="Да!", callback_data="send_message_confirm")).as_markup()
        )
    except Exception as e:
        await message.answer(f"Отмена, что-то пошло не так:\n{str(e)}")
        await clear_send_data(state)


@router.callback_query(F.data == 'send_message_confirm')
async def on_send_message_confirmed(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete_reply_markup()
    try:
        data = await state.get_data()
        message_id = await callback.bot.copy_message(
            chat_id=data['send_channel_id'],
            from_chat_id=callback.from_user.id,
            message_id=data['send_message_id'],
            reply_markup=InlineKeyboardBuilder().add(
                InlineKeyboardButton(text=data['send_btn_text'], url=data['send_btn_link'])).as_markup()
        )

        await callback.bot.pin_chat_message(data['send_channel_id'], message_id.message_id)

        await callback.message.answer(f"Готово, можно проверять - {data['send_channel_name']}")
    except Exception as e:
        await callback.message.answer(f"Что-то пошло не так:\n{str(e)}")
    finally:
        await clear_send_data(state)


async def clear_send_data(state: FSMContext):
    await state.update_data(send_channel_id=None, send_btn_text=None, send_message_id=None, send_channel_name=None)
    await state.set_state()
