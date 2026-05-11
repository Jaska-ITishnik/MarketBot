# from aiogram import Router
# from aiogram.enums import ParseMode
# from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
#
# from db.base import products_db
#
# inline_router = Router()
#
#
# @inline_router.inline_query()
# async def inline_search(inline_query: InlineQuery):
#     query = inline_query.query.strip().lower()
#     offset = offset if (offset := inline_query.offset) else 0
#     limit = 10
#     products = products_db.get_all()
#     filtered_products = [product for product in products if query in product['name'].lower()] if query else products
#     paged_products = filtered_products[int(offset):int(offset) + limit]
#     results = [
#         InlineQueryResultArticle(
#             id=f"product_{product['id']}",
#             title=product["name"],
#             description=f"Narxi: {product['price']:,} so'm | Omborda: {product['amount']} dona",
#             thumbnail_url=product["photo"],
#             input_message_content=InputTextMessageContent(
#                 message_text=f"""
# 🛍 <b>{product['name']}</b>
#
# 💰 <b>Narx:</b> {product['price']:,} so'm
# 📦 <b>Omborda:</b> {product['amount']} dona
# 🏷 <b>Chegirma:</b> {'Mavjud ✅' if product['is_discount'] else 'Mavjud emas ❌'}
#
# ✨ Tanlangan mahsulot haqida ma'lumot.
# 🛒 Xarid qilish uchun tugmani bosing.
# """.strip(),
#                 parse_mode=ParseMode.HTML
#             )
#         )
#         for product in paged_products
#     ]
#
#     next_offset = str(int(offset) + limit) if (int(offset) + limit) < len(filtered_products) else ""
#     await inline_query.answer(
#         results=results,
#         cache_time=1,
#         is_personal=True,
#         next_offset=next_offset
#     )


# Middle ware example

from typing import Callable, Dict, Any, Awaitable, List

from aiogram import BaseMiddleware, Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import TelegramObject, Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.handlers import start_function


class JoinChannelMiddleware(BaseMiddleware):
    CHANNEL_IDES: List[int] = [-1003783462850]

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: CallbackQuery | Message,
            data: Dict[str, Any]
    ) -> Any:
        if event.callback_query and event.callback_query.data == "check_if_subscribed" or event.message:
            bot: Bot = data['bot']
            if event.message:
                user = event.message.from_user
            else:
                user = event.callback_query.from_user

            unsubscribers = []
            for channel_id in self.CHANNEL_IDES:
                member = await bot.get_chat_member(channel_id, user.id)
                if member.status == ChatMemberStatus.LEFT:
                    unsubscribers.append(channel_id)
            if unsubscribers:
                ikb = InlineKeyboardBuilder()
                for channel_id in unsubscribers:
                    channel = (await bot.get_chat(channel_id)).model_dump()
                    ikb.add(InlineKeyboardButton(
                        text=channel['title'],
                        url=channel['invite_link']
                    ))
                ikb.add(InlineKeyboardButton(text="Tekshirish✅", callback_data="check_if_subscribed"))
                ikb.adjust(2, 1)
                if event.callback_query:
                    try:
                        await event.callback_query.message.edit_reply_markup(reply_markup=ikb.as_markup())
                    except TelegramBadRequest:
                        await event.callback_query.answer("Hali a'zo bo'lmadingiz🤨", show_alert=True)
                else:
                    await event.message.answer("Oldin kanallarga a'zo bo'ling👇", reply_markup=ikb.as_markup())
                return
            else:
                if event.callback_query:
                    await event.callback_query.message.delete()
                    await start_function(event.callback_query.message)
        return await handler(event, data)
