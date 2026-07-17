from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.buttons import main_menu_keyboard

router = Router(name="help")


@router.message(Command(commands=["help"]))
async def help_command_handler(message: Message) -> None:
    await message.answer(
        "ℹ️ <b>Yordam</b>\n\n"
        "🏠 /start - Asosiy menyuni ochish\n"
        "🛍 /catalog - Mahsulotlar katalogi\n"
        "🔎 /search - Mahsulot qidirish\n"
        "🛒 /cart - Savatni ko'rish\n"
        "📦 /orders - Buyurtmalarim\n"
        "ℹ️ /help - Bot haqida yordam",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
