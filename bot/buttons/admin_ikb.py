from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_categories_ikb(categories: list):
    ikb = InlineKeyboardBuilder()
    buttons = []

    for category in categories:
        buttons.extend([
            InlineKeyboardButton(text=category['name'], callback_data=f"category_{category['id']}"),
            InlineKeyboardButton(text="✏", callback_data=f"edit_{category['id']}"),
            InlineKeyboardButton(text="🗑", callback_data=f"delete_{category['id']}"),
        ])
    ikb.add(*buttons)
    ikb.adjust(3, repeat=True)
    return ikb.as_markup()


def admin_products_ikb(products: list):
    ikb = InlineKeyboardBuilder()
    buttons = []
    for product in products:
        buttons.append(
            InlineKeyboardButton(text=product['name'], callback_data=f"product_{product['id']}")
        )
    ikb.add(*buttons)
    ikb.adjust(3, repeat=True)
    return ikb.as_markup()
