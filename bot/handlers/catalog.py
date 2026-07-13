from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.buttons import MainMenu, main_menu_keyboard

router = Router(name="catalog")


@router.message(Command(commands=["catalog"]))
@router.message(F.text == MainMenu.CATALOG)
async def catalog_handler(message: Message) -> None:
    await message.answer(
        "Katalog bo'limi.\n\n"
        "Keyingi bosqichda bu yerda kategoriyalar va mahsulotlar chiqadi.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text == MainMenu.SEARCH)
async def search_handler(message: Message) -> None:
    await message.answer(
        "Qidirish bo'limi.\n\n"
        "Keyingi bosqichda mahsulot nomi bo'yicha qidiruv qo'shamiz.",
        reply_markup=main_menu_keyboard(),
    )
