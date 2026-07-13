from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.buttons import main_menu_keyboard

router = Router(name="start")


async def show_main_menu(message: Message) -> None:
    await message.answer(
        "Assalomu alaykum! Online do'kon botiga xush kelibsiz.\n\n"
        "Quyidagi menyulardan birini tanlang:",
        reply_markup=main_menu_keyboard(),
    )


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await show_main_menu(message)
