from pathlib import Path

from aiogram import Router, F
from aiogram.types import Message

from bot.buttons import admin_categories_ikb
from config import ADMINS
from db.base import categories_db

admin_message_router = Router()
BASE_DB_URL = Path(__file__).parent.parent.parent


@admin_message_router.message(F.text == "🛍Maxsulotlar✏")
async def products_admin_handler(message: Message):
    if message.from_user.id not in ADMINS:
        return
    categories = categories_db.get_all()
    await message.answer("Kategoriyalar👇", reply_markup=admin_categories_ikb(categories))
