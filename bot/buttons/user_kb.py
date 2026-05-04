from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def main_menu_user_kb():
    kb = ReplyKeyboardBuilder()
    buttons = [
        KeyboardButton(text="🛍Maxsulotlar"),
        KeyboardButton(text="📜Buyurtmalarim"),
    ]
    kb.add(*buttons)
    kb.adjust(1, 1)
    return kb.as_markup(resize_keyboard=True)
