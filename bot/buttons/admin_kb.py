from aiogram.types import KeyboardButton
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def main_menu_admin_kb():
    kb = ReplyKeyboardBuilder()
    buttons = [
        KeyboardButton(text=_("🛍Maxsulotlar✏")),
        KeyboardButton(text=_("🔧Sozlamalar"))
    ]
    kb.add(*buttons)
    kb.adjust(1, 1)
    return kb.as_markup(resize_keyboard=True)


def settings_menu_kb():
    kb = ReplyKeyboardBuilder()
    buttons = [
        KeyboardButton(text=_("🛍Maxsulotlar✏")),
        KeyboardButton(text=_("🔧Sozlamalar"))
    ]
    kb.add(*buttons)
    kb.adjust(1, 1)
    return kb.as_markup(resize_keyboard=True)
