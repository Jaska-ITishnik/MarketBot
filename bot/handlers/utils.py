from aiogram.enums import ParseMode
from aiogram.types import Message

from bot.buttons import main_menu_user_kb, main_menu_admin_kb
from config import ADMINS


async def start_menu(message: Message):
    if message.from_user.id not in ADMINS:
        await message.answer("""
    Assalomu aleykum dokonimizga xush kelibsiz😊
    <blockquote>Buyurtma uchun👇</blockquote>
        """, parse_mode=ParseMode.HTML, reply_markup=main_menu_user_kb())
    else:
        await message.answer("""
            Assalomu aleykum <b>ADMIN</b> xush kelibsiz😊
            <blockquote>Boshqarish uchun👇</blockquote>
                """, parse_mode=ParseMode.HTML, reply_markup=main_menu_admin_kb())
