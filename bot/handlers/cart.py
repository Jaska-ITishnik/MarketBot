from decimal import Decimal
from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from bot.buttons import MainMenu, main_menu_keyboard
from db import database
from db.models import Basket

router = Router(name="cart")


def _format_money(value: Decimal) -> str:
    return f"{value:,.0f}".replace(",", " ")


def _fetch_basket_items(telegram_id: int) -> list[Basket]:
    query = select(Basket).where(Basket.telegram_id == telegram_id).order_by(Basket.id)
    return list(database.execute(query).scalars().all())


@router.message(Command(commands=["cart"]))
@router.message(F.text == MainMenu.CART)
async def cart_handler(message: Message) -> None:
    if message.from_user is None:
        await message.answer(
            "Foydalanuvchi aniqlanmadi.",
            reply_markup=main_menu_keyboard(),
        )
        return

    items = _fetch_basket_items(message.from_user.id)
    if not items:
        await message.answer(
            "Savat hozircha bo'sh.\n\n"
            "Katalogdan mahsulot tanlab savatga qo'shishingiz mumkin.",
            reply_markup=main_menu_keyboard(),
        )
        return

    lines = ["<b>Savat</b>\n"]
    total = Decimal("0")

    for index, item in enumerate(items, start=1):
        product = item.product
        item_total = product.price * item.quantity
        total += item_total
        lines.append(
            f"{index}. {escape(product.name)}\n"
            f"   {item.quantity} x {_format_money(product.price)} so'm = "
            f"{_format_money(item_total)} so'm"
        )

    lines.append(f"\n<b>Jami:</b> {_format_money(total)} so'm")

    await message.answer(
        "\n\n".join(lines),
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
