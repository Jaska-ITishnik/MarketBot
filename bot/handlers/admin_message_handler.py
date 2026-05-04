import json
from pathlib import Path

from aiogram import Router, F
from aiogram.types import InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

admin_message_router = Router()
BASE_DB_URL = Path(__file__).parent.parent.parent


@admin_message_router.message(F.text == "🛍Maxsulotlar")
async def products_admin_handler(message: Message):
    with open(f"{BASE_DB_URL}/db/products.json", 'r') as f:
        products = json.load(f)
    ikb = InlineKeyboardBuilder()
    buttons = []
    for product in products:
        buttons.append(
            InlineKeyboardButton(text=product['name'], callback_data=product['name'])
        )
    ikb.add(*buttons)
    ikb.adjust(3, repeat=True)
    await message.answer("Maxsulotlar👇", reply_markup=ikb.as_markup())
