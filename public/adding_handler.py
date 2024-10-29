import logging

from aiogram import Router, F
from aiogram.enums import ParseMode, ChatType
from aiogram.filters import Command, ChatMemberUpdatedFilter, PROMOTED_TRANSITION, LEAVE_TRANSITION
from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message, InlineKeyboardButton, ChatMemberUpdated
from aiogram.utils.keyboard import InlineKeyboardBuilder

# -1002210982753

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(F.chat.type != ChatType.PRIVATE)


class AddingConfirmed(CallbackData, prefix='ch_conf'):
    id: int
    name: str


@router.my_chat_member(ChatMemberUpdatedFilter(PROMOTED_TRANSITION))
async def on_bot_promoted(event: ChatMemberUpdated):
    logger.info("on_bot_promoted - %s", event.model_dump_json(indent=4, exclude_none=True))

    chat_id = event.chat.id
    chat_name = f"@{event.chat.username}" if event.chat.username else event.chat.title

    user_id = event.from_user.id

    markup = (InlineKeyboardBuilder()
              .add(InlineKeyboardButton(text="Да!",
                                        callback_data=AddingConfirmed(id=chat_id, name=chat_name).pack()))
              .as_markup())
    in_type = {
        ChatType.GROUP: "в группе",
        ChatType.SUPERGROUP: "в группе",
        ChatType.CHANNEL: "в канале",
    }

    await event.bot.send_message(
        chat_id=user_id,
        text=f"Похоже, что ты сделал бота админом {in_type[event.chat.type]} <b>{chat_name}</b>.\n"
             f"Нажми на кнопку, чтобы продолжить",
        parse_mode=ParseMode.HTML,
        reply_markup=markup
    )


async def handle_bot_kicked(id: int):
    pass


@router.my_chat_member(ChatMemberUpdatedFilter(LEAVE_TRANSITION))
async def on_bot_kicked(event: ChatMemberUpdated):
    logger.info("on_bot_kicked - %s", event.model_dump_json(indent=4, exclude_none=True))
    await handle_bot_kicked(event.chat.id)

# channel_id = -1002210982753


# @router.message(Command("send"))
# async def on_send(message: Message):
#
#     builder = InlineKeyboardBuilder()
#     builder.add(InlineKeyboardButton(text="Дальше", callback_data="chat_btn"))
#
#     new_message = await message.bot.send_message(
#         chat_id=channel_id, text="тук тук тук", reply_markup=builder.as_markup()
#     )
#
#     # пин, чтобы получить синюю кнопку в посте
#     await message.bot.pin_chat_message(chat_id=channel_id, message_id=new_message.message_id,
#                                        disable_notification=True)
#
#
# @router.callback_query(F.data == "chat_btn")
# async def on_chat_btn(callback: CallbackQuery):
#     user_id = callback.from_user.id
#     chat_id = callback.message.chat.id
#
#     result = await callback.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
#     if result.status == ChatMemberStatus.LEFT:
#         await callback.answer(text="Подпишись!", show_alert=True)
#     else:
#         link = await create_start_link(callback.bot, "subscribed")
#         await callback.answer(url=link)