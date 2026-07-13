from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.buttons import main_menu_keyboard

router = Router(name="help")


@router.message(Command(commands=["help"]))
async def help_command_handler(message: Message) -> None:
    await message.answer(
        "/start -> Asosiy menyuni ochish\n"
        "/catalog -> Mahsulotlar katalogi\n"
        "/cart -> Savatni ko'rish\n"
        "/orders -> Buyurtmalarim\n"
        "/help -> Bot haqida yordam",
        reply_markup=main_menu_keyboard(),
    )
