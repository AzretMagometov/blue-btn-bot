import logging

from aiogram import Router, F, Bot
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.repo import get_user_chats

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(F.chat.type == "private")


class ChatSelected(CallbackData, prefix='ch_sel'):
    chat_id: int
    chat_name: str


@router.message(Command('cancel'))
async def on_cancel_command(message: Message, state: FSMContext):
    await clear_send_data(state)
    await message.answer("Отменено")


@router.message(Command('send'))
async def on_send_command(message: Message):
    chats = await get_user_chats(message.from_user.id)

    if not chats:
        await message.answer("Нет добавленных каналов и групп - сделай бота администратором, чтобы публиковать посты")
    else:
        builder = InlineKeyboardBuilder()
        for chat in chats:
            builder.button(
                text=chat.tg_name,
                callback_data=ChatSelected(chat_id=chat.tg_id, chat_name=chat.tg_name)
            )
        builder.adjust(1, 1)

        text = ("Сейчас выберем канал или группу.\n"
                "Ты в любой момент можешь вызвать команду /cancel чтобы отменить процесс.\n"
                "В каком чате нужно создать пост?")

        await message.answer(text, reply_markup=builder.as_markup())


class SendMessageToChannelStates(StatesGroup):
    enter_message = State()
    enter_btn_text = State()
    enter_btn_link = State()
    confirm_send = State()


@router.callback_query(ChatSelected.filter())
async def on_channel_for_send_selected(callback: CallbackQuery, callback_data: ChatSelected, state: FSMContext):
    await callback.message.delete_reply_markup()

    await state.update_data(send_channel_id=callback_data.chat_id, send_channel_name=callback_data.chat_name)
    await state.set_state(SendMessageToChannelStates.enter_message)

    await callback.message.answer(text="Теперь пришли мне текст сообщения, который нужно закрепить")


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
                              "Это должна быть обычная ссылка формата <i>http://...</i>\n",
                         parse_mode=ParseMode.HTML,
                         disable_web_page_preview=True)


@router.message(SendMessageToChannelStates.enter_btn_link)
async def on_btn_link_entered(message: Message, state: FSMContext):
    try:
        data = await state.update_data(send_btn_link=message.text)
        await state.set_state(SendMessageToChannelStates.confirm_send)

        await send_and_pin_message(
            bot=message.bot,
            from_chat_id=message.from_user.id,
            destination_chat_id=message.from_user.id,
            data=data
        )

        await message.answer(
            "Сообщение и закреп будут выглядеть вот так ⬆️ ⬆️ ⬆️\n"
            "Отправляю?",
            reply_markup=InlineKeyboardBuilder()
            .add(InlineKeyboardButton(text="Да!", callback_data="send_message_confirm"),
                 InlineKeyboardButton(text="Нет", callback_data="send_message_cancel"))
            .as_markup()
        )
    except Exception as e:
        await message.answer(f"Отмена, что-то пошло не так:\n{str(e)}")
        await clear_send_data(state)


@router.callback_query(F.data == 'send_message_cancel')
async def on_send_message_canceled(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete_reply_markup()
    await clear_send_data(state)
    await callback.message.answer("Отменено")


@router.callback_query(F.data == 'send_message_confirm')
async def on_send_message_confirmed(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete_reply_markup()
    try:
        data = await state.get_data()
        await send_and_pin_message(
            bot=callback.bot,
            from_chat_id=callback.from_user.id,
            destination_chat_id=data['send_channel_id'],
            data=data)

        await callback.message.answer(f"Готово, можно проверять - {data['send_channel_name']}")
    except Exception as e:
        await callback.message.answer(f"Что-то пошло не так:\n{str(e)}")
    finally:
        await clear_send_data(state)


async def clear_send_data(state: FSMContext):
    await state.update_data(send_channel_id=None, send_btn_text=None, send_message_id=None, send_channel_name=None)
    await state.set_state()


async def send_and_pin_message(
        bot: Bot,
        from_chat_id: int,
        destination_chat_id: int,
        data: dict):
    message_id = await bot.copy_message(
        chat_id=destination_chat_id,
        from_chat_id=from_chat_id,
        message_id=data['send_message_id'],
        reply_markup=InlineKeyboardBuilder().add(
            InlineKeyboardButton(text=data['send_btn_text'], url=data['send_btn_link'])).as_markup()
    )
    await bot.pin_chat_message(destination_chat_id, message_id.message_id, disable_notification=True)
