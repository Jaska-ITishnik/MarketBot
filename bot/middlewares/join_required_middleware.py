from typing import Any

from aiogram import BaseMiddleware, Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.handlers import start_menu


class JoinChannelGroupMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.CHAT_IDES = [-1003779710392, -1003931875778]

    async def __call__(self, handler, event: Message | CallbackQuery, data) -> Any:
        bot: Bot = data["bot"]
        if event.callback_query or event.message:
            if event.callback_query:
                user = event.callback_query.from_user
            else:
                user = event.message.from_user
            unsubscribes = []
            for channel in self.CHAT_IDES:
                member = await bot.get_chat_member(channel, user.id)
                if member.status == ChatMemberStatus.LEFT:
                    unsubscribes.append(channel)
            if unsubscribes:
                ikb = InlineKeyboardBuilder()
                for channel_id in unsubscribes:
                    channel = (await bot.get_chat(channel_id)).model_dump()
                    ikb.add(InlineKeyboardButton(text=channel["title"], url=channel["invite_link"]))
                ikb.add(InlineKeyboardButton(text="A'zo bo'ldim✅", callback_data="check_if_subscribed"))
                ikb.adjust(1, repeat=True)
                if event.callback_query:
                    try:
                        await event.callback_query.message.edit_reply_markup(reply_markup=ikb.as_markup())
                    except TelegramBadRequest:
                        await event.callback_query.answer("Hali hammasiga a'zo bo'lmadingiz!")
                else:
                    await event.message.answer("Oldin kanallarga a'zo bo'ling!", reply_markup=ikb.as_markup())
                    return
            else:
                if event.callback_query:
                    await event.callback_query.message.delete()
                    await start_menu(event.callback_query.message)
        return await handler(event, data)
