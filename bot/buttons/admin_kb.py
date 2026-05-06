from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def main_menu_admin_kb():
    kb = ReplyKeyboardBuilder()
    buttons = [
        KeyboardButton(text="🛍Maxsulotlar✏"),
    ]
    kb.add(*buttons)
    kb.adjust(1, 1)
    return kb.as_markup(resize_keyboard=True)
