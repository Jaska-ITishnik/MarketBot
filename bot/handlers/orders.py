from decimal import Decimal
from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from bot.buttons import MainMenu, main_menu_keyboard
from db import database
from db.models import Order, User

router = Router(name="orders")

STATUS_LABELS = {
    "pending": "Kutilmoqda",
    "paid": "To'langan",
    "shipped": "Yetkazilmoqda",
    "delivered": "Yetkazildi",
    "cancelled": "Bekor qilingan",
}

PAYMENT_STATUS_LABELS = {
    "pending": "Kutilmoqda",
    "paid": "To'langan",
    "failed": "Muvaffaqiyatsiz",
    "refunded": "Qaytarilgan",
}


def _format_money(value: Decimal) -> str:
    return f"{value:,.0f}".replace(",", " ")


def _fetch_orders(telegram_id: int) -> list[Order]:
    query = (
        select(Order)
        .join(User)
        .where(User.telegram_id == telegram_id)
        .order_by(Order.created_at.desc())
        .limit(10)
    )
    return list(database.execute(query).scalars().all())


def _order_items_text(order: Order) -> str:
    lines = []
    for item in order.items[:3]:
        product_name = item.product.name if item.product else "Mahsulot"
        lines.append(f"{escape(product_name)} x {item.quantity}")

    remaining_count = len(order.items) - len(lines)
    if remaining_count > 0:
        lines.append(f"yana {remaining_count} ta mahsulot")

    return ", ".join(lines) if lines else "Mahsulotlar topilmadi"


@router.message(Command(commands=["orders"]))
@router.message(F.text == MainMenu.ORDERS)
async def orders_handler(message: Message) -> None:
    if message.from_user is None:
        await message.answer(
            "Foydalanuvchi aniqlanmadi.",
            reply_markup=main_menu_keyboard(),
        )
        return

    orders = _fetch_orders(message.from_user.id)
    if not orders:
        await message.answer(
            "📦 Sizning buyurtmalaringiz hali yo'q.",
            reply_markup=main_menu_keyboard(),
        )
        return

    lines = ["📦 <b>Buyurtmalarim</b>\n"]
    for order in orders:
        payment_status = order.payment.status if order.payment else "pending"
        created_at = order.created_at.strftime("%d.%m.%Y %H:%M")
        lines.append(
            f"🧾 <b>#{order.id}</b> - {created_at}\n"
            f"📌 <b>Status:</b> {STATUS_LABELS.get(order.status, order.status)}\n"
            f"💳 <b>To'lov:</b> {PAYMENT_STATUS_LABELS.get(payment_status, payment_status)}\n"
            f"💰 <b>Jami:</b> {_format_money(order.total_amount)} so'm\n"
            f"📦 <b>Mahsulotlar:</b> {_order_items_text(order)}"
        )

    await message.answer(
        "\n\n".join(lines),
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
