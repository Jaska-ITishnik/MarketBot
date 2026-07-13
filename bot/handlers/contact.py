from aiogram import F, Router
from aiogram.types import Message

from bot.buttons import MainMenu, main_menu_keyboard

router = Router(name="contact")


@router.message(F.text == MainMenu.CONTACT)
async def contact_handler(message: Message) -> None:
    await message.answer(
        "Aloqa bo'limi.\n\n"
        "Operator bilan bog'lanish, do'kon manzili va qo'llab-quvvatlash "
        "ma'lumotlari shu yerda bo'ladi.",
        reply_markup=main_menu_keyboard(),
    )
