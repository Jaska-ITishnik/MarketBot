from aiogram import F, Router
from aiogram.types import Message

from bot.buttons import MainMenu, main_menu_keyboard

router = Router(name="settings")


@router.message(F.text == MainMenu.SETTINGS)
async def settings_handler(message: Message) -> None:
    await message.answer(
        "⚙️ <b>Sozlamalar</b>\n\n"
        "🌐 Keyinchalik til tanlash va 🔔 bildirishnoma sozlamalarini qo'shamiz.",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
