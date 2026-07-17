from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


class MainMenu:
    CATALOG = "🛍 Katalog"
    CART = "🛒 Savat"
    ORDERS = "📦 Buyurtmalarim"
    SEARCH = "🔎 Qidirish"
    PROFILE = "👤 Profil"
    CONTACT = "📞 Aloqa"
    SETTINGS = "⚙️ Sozlamalar"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=MainMenu.CATALOG),
                KeyboardButton(text=MainMenu.CART),
            ],
            [
                KeyboardButton(text=MainMenu.ORDERS),
                KeyboardButton(text=MainMenu.SEARCH),
            ],
            [
                KeyboardButton(text=MainMenu.PROFILE),
                KeyboardButton(text=MainMenu.CONTACT),
            ],
            [
                KeyboardButton(text=MainMenu.SETTINGS),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="👇 Kerakli bo'limni tanlang",
    )
