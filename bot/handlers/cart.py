from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.buttons import MainMenu, main_menu_keyboard

router = Router(name="cart")


@router.message(Command(commands=["cart"]))
@router.message(F.text == MainMenu.CART)
async def cart_handler(message: Message) -> None:
    await message.answer(
        "Savat hozircha bo'sh.\n\n"
        "Mahsulot tanlaganingizdan keyin u savatga qo'shiladi.",
        reply_markup=main_menu_keyboard(),
    )
