from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.buttons import MainMenu, main_menu_keyboard

router = Router(name="orders")


@router.message(Command(commands=["orders"]))
@router.message(F.text == MainMenu.ORDERS)
async def orders_handler(message: Message) -> None:
    await message.answer(
        "Sizning buyurtmalaringiz hali yo'q.",
        reply_markup=main_menu_keyboard(),
    )
