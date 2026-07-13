from aiogram import F, Router
from aiogram.types import Message

from bot.buttons import MainMenu, main_menu_keyboard

router = Router(name="profile")


@router.message(F.text == MainMenu.PROFILE)
async def profile_handler(message: Message) -> None:
    await message.answer(
        "Profil bo'limi.\n\n"
        "Bu yerda telefon raqam, manzil va shaxsiy ma'lumotlar saqlanadi.",
        reply_markup=main_menu_keyboard(),
    )
