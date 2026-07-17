from datetime import date
from decimal import Decimal
from html import escape
import logging

from aiogram import F, Router
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from sqlalchemy import delete, select

from bot.buttons import MainMenu, main_menu_keyboard
from config import settings
from db import database
from db.models import Basket, Order, OrderItem, Payment, User

router = Router(name="cart")
logger = logging.getLogger(__name__)

CANCEL_TEXT = "❌ Bekor qilish"
PAYMENT_METHODS = {
    "cash": "💵 Naqd to'lov",
    "card": "💳 Karta orqali",
    "click": "Click",
    "payme": "Payme",
}


class Checkout(StatesGroup):
    waiting_full_name = State()
    waiting_phone = State()
    waiting_shipping_address = State()
    waiting_payment_method = State()


class CheckoutError(Exception):
    pass


def _format_money(value: Decimal) -> str:
    return f"{value:,.0f}".replace(",", " ")


def _fetch_basket_items(telegram_id: int) -> list[Basket]:
    query = select(Basket).where(Basket.telegram_id == telegram_id).order_by(Basket.id)
    return list(database.execute(query).scalars().all())


async def _send_callback_message(
        callback_query: CallbackQuery,
        text: str,
        reply_markup=None,
        parse_mode: str | None = None,
) -> None:
    chat_id = callback_query.from_user.id
    if callback_query.message is not None:
        chat_id = callback_query.message.chat.id

    await callback_query.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
    )


def _cart_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Buyurtma rasmiylashtirish",
                    callback_data="cart:checkout",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🧹 Savatni tozalash",
                    callback_data="cart:clear",
                )
            ],
        ]
    )


def _cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CANCEL_TEXT)]],
        resize_keyboard=True,
        input_field_placeholder="Bekor qilish uchun tugmani bosing",
    )


def _phone_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Telefon raqamni yuborish", request_contact=True)],
            [KeyboardButton(text=CANCEL_TEXT)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Telefon raqamingiz",
    )


def _payment_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"checkout:pay:{method}",
                )
            ]
            for method, label in PAYMENT_METHODS.items()
        ] + [[InlineKeyboardButton(text=CANCEL_TEXT, callback_data="checkout:cancel")]]
    )


def _basket_summary(items: list[Basket]) -> tuple[str, Decimal]:
    lines = ["🛒 <b>Savat</b>\n"]
    total = Decimal("0")

    for index, item in enumerate(items, start=1):
        product = item.product
        item_total = product.price * item.quantity
        total += item_total
        lines.append(
            f"{index}. 📦 {escape(product.name)}\n"
            f"   🔢 {item.quantity} x {_format_money(product.price)} so'm = "
            f"{_format_money(item_total)} so'm"
        )

    lines.append(f"\n💰 <b>Jami:</b> {_format_money(total)} so'm")
    return "\n\n".join(lines), total


def _split_full_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split(maxsplit=1)
    first_name = parts[0][:30]
    last_name = parts[1][:30] if len(parts) > 1 else "-"
    return first_name, last_name


def _normalize_phone(value: str) -> str:
    phone = value.strip().replace(" ", "")
    digits = "".join(char for char in phone if char.isdigit())
    if len(digits) < 7:
        raise CheckoutError("Telefon raqam noto'g'ri kiritildi.")
    return phone[:30]


def _phone_conflict_exists(phone: str, telegram_id: int) -> bool:
    phone_owner = database.execute(
        select(User).where(User.phone == phone)
    ).scalars().first()
    if phone_owner is None:
        return False
    if phone_owner.telegram_id == telegram_id:
        return False

    current_user = database.execute(
        select(User).where(User.telegram_id == telegram_id)
    ).scalars().first()
    if current_user is not None and current_user.id != phone_owner.id:
        return True

    return phone_owner.telegram_id is not None


def _checkout_email(telegram_id: int) -> str:
    return f"telegram_{telegram_id}@marketbot.local"


def _get_or_create_user(
        telegram_id: int,
        first_name: str,
        last_name: str,
        phone: str,
) -> User:
    user = database.execute(
        select(User).where(User.telegram_id == telegram_id)
    ).scalars().first()
    phone_owner = database.execute(
        select(User).where(User.phone == phone)
    ).scalars().first()

    if user is not None and phone_owner is not None and user.id != phone_owner.id:
        raise CheckoutError("Bu telefon raqam boshqa profilga biriktirilgan.")

    if phone_owner is not None and phone_owner.telegram_id not in (None, telegram_id):
        raise CheckoutError("Bu telefon raqam boshqa profilga biriktirilgan.")

    if user is None:
        user = phone_owner

    if user is None:
        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            gender="other",
            phone=phone,
            email=_checkout_email(telegram_id),
            dob=date(1970, 1, 1),
        )
        database.add(user)
    else:
        user.telegram_id = telegram_id
        user.first_name = first_name
        user.last_name = last_name
        user.phone = phone
        if not user.gender:
            user.gender = "other"
        if not user.email:
            user.email = _checkout_email(telegram_id)
        if not user.dob:
            user.dob = date(1970, 1, 1)

    return user


def _create_order_from_basket(telegram_id: int, checkout_data: dict) -> Order:
    items = _fetch_basket_items(telegram_id)
    if not items:
        raise CheckoutError("Savat hozircha bo'sh.")

    total = Decimal("0")
    for item in items:
        product = item.product
        if product is None or not product.is_active:
            raise CheckoutError("Savatdagi mahsulotlardan biri hozir mavjud emas.")
        if item.quantity > product.stock_quantity:
            raise CheckoutError(
                f"{product.name} uchun omborda faqat {product.stock_quantity} dona bor."
            )
        total += product.price * item.quantity

    try:
        user = _get_or_create_user(
            telegram_id=telegram_id,
            first_name=checkout_data["first_name"],
            last_name=checkout_data["last_name"],
            phone=checkout_data["phone"],
        )
        order = Order(
            user=user,
            total_amount=total,
            shipping_address=checkout_data["shipping_address"],
        )
        database.add(order)
        database.flush()

        for item in items:
            product = item.product
            item_total = product.price * item.quantity
            database.add(
                OrderItem(
                    order=order,
                    product=product,
                    quantity=item.quantity,
                    unit_price=product.price,
                    total_price=item_total,
                )
            )
            product.stock_quantity -= item.quantity

        database.add(
            Payment(
                order=order,
                amount=total,
                method=checkout_data["payment_method"],
                status="pending",
            )
        )

        for item in items:
            database.delete(item)

        database.commit()
    except Exception:
        database.rollback()
        raise

    return order


def _clear_basket(telegram_id: int) -> None:
    try:
        database.execute(delete(Basket).where(Basket.telegram_id == telegram_id))
        database.commit()
    except Exception:
        database.rollback()
        raise


def _order_success_text(order: Order) -> str:
    payment_method = order.payment.method if order.payment else "cash"
    return (
        f"✅ <b>Buyurtma qabul qilindi</b>\n\n"
        f"🧾 <b>Buyurtma raqami:</b> #{order.id}\n"
        f"💰 <b>Jami:</b> {_format_money(order.total_amount)} so'm\n"
        f"💳 <b>To'lov usuli:</b> {escape(PAYMENT_METHODS.get(payment_method, payment_method))}\n"
        f"📍 <b>Manzil:</b> {escape(order.shipping_address)}\n\n"
        "📞 Operator buyurtmani tasdiqlash uchun siz bilan bog'lanadi."
    )


def _admin_order_text(order: Order, telegram_id: int) -> str:
    user = order.user
    phone = user.phone if user else "-"
    full_name = f"{user.first_name} {user.last_name}".strip() if user else "-"
    payment_method = order.payment.method if order.payment else "cash"

    item_lines = []
    for index, item in enumerate(order.items, start=1):
        product_name = item.product.name if item.product else "Mahsulot"
        item_lines.append(
            f"{index}. 📦 {escape(product_name)}\n"
            f"   🔢 {item.quantity} x {_format_money(item.unit_price)} so'm = "
            f"{_format_money(item.total_price)} so'm"
        )

    return (
        f"🆕 <b>Yangi buyurtma</b>\n\n"
        f"🧾 <b>Buyurtma:</b> #{order.id}\n"
        f"👤 <b>Mijoz:</b> {escape(full_name)}\n"
        f"🆔 <b>Telegram ID:</b> <code>{telegram_id}</code>\n"
        f"📞 <b>Telefon:</b> {escape(phone)}\n"
        f"📍 <b>Manzil:</b> {escape(order.shipping_address)}\n"
        f"💳 <b>To'lov:</b> {escape(PAYMENT_METHODS.get(payment_method, payment_method))}\n"
        f"💰 <b>Jami:</b> {_format_money(order.total_amount)} so'm\n\n"
        f"<b>Mahsulotlar:</b>\n" + "\n".join(item_lines)
    )


async def _notify_admins(bot: Bot, order: Order, telegram_id: int) -> None:
    if not settings.admin_ids:
        logger.warning("Order %s accepted, but no admin IDs are configured.", order.id)
        return

    text = _admin_order_text(order, telegram_id)
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=text,
                parse_mode="HTML",
            )
        except TelegramAPIError as error:
            logger.warning("Could not notify admin %s about order %s: %s", admin_id, order.id, error)


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
            "🛒 Savat hozircha bo'sh.\n\n"
            "🛍 Katalogdan mahsulot tanlab savatga qo'shishingiz mumkin.",
            reply_markup=main_menu_keyboard(),
        )
        return

    text, _ = _basket_summary(items)

    await message.answer(
        text,
        reply_markup=_cart_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "cart:clear")
async def clear_cart_handler(callback_query: CallbackQuery) -> None:
    if callback_query.from_user is None:
        await callback_query.answer("Foydalanuvchi aniqlanmadi.", show_alert=True)
        return

    _clear_basket(callback_query.from_user.id)
    if callback_query.message is not None:
        await callback_query.message.edit_text("🧹 Savat tozalandi.")
    await callback_query.answer("Savat tozalandi.")


@router.callback_query(F.data == "cart:checkout")
async def checkout_start_handler(callback_query: CallbackQuery, state: FSMContext) -> None:
    if callback_query.from_user is None:
        await callback_query.answer("Foydalanuvchi aniqlanmadi.", show_alert=True)
        return

    items = _fetch_basket_items(callback_query.from_user.id)
    if not items:
        await callback_query.answer("Savat hozircha bo'sh.", show_alert=True)
        return

    await state.clear()
    await state.set_state(Checkout.waiting_full_name)
    await _send_callback_message(
        callback_query,
        "👤 Buyurtmani rasmiylashtirish uchun ism va familiyangizni kiriting.",
        reply_markup=_cancel_keyboard(),
    )
    await callback_query.answer()


@router.message(
    StateFilter(
        Checkout.waiting_full_name,
        Checkout.waiting_phone,
        Checkout.waiting_shipping_address,
    ),
    F.text == CANCEL_TEXT,
)
async def checkout_cancel_message_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "❌ Buyurtma rasmiylashtirish bekor qilindi.",
        reply_markup=main_menu_keyboard(),
    )


@router.callback_query(F.data == "checkout:cancel")
async def checkout_cancel_callback_handler(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await _send_callback_message(
        callback_query,
        "❌ Buyurtma rasmiylashtirish bekor qilindi.",
        reply_markup=main_menu_keyboard(),
    )
    await callback_query.answer()


@router.message(Checkout.waiting_full_name)
async def checkout_full_name_handler(message: Message, state: FSMContext) -> None:
    full_name = (message.text or "").strip()
    if len(full_name) < 3:
        await message.answer("👤 Ism va familiyani to'liqroq kiriting.")
        return

    first_name, last_name = _split_full_name(full_name)
    await state.update_data(first_name=first_name, last_name=last_name)
    await state.set_state(Checkout.waiting_phone)
    await message.answer(
        "📞 Telefon raqamingizni yuboring yoki matn ko'rinishida kiriting.",
        reply_markup=_phone_keyboard(),
    )


@router.message(Checkout.waiting_phone)
async def checkout_phone_handler(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        await message.answer("Foydalanuvchi aniqlanmadi.")
        return

    raw_phone = message.contact.phone_number if message.contact else message.text
    if not raw_phone:
        await message.answer("Telefon raqamni yuboring.")
        return

    try:
        phone = _normalize_phone(raw_phone)
    except CheckoutError as error:
        await message.answer(str(error))
        return

    if _phone_conflict_exists(phone, message.from_user.id):
        await message.answer("Bu telefon raqam boshqa profilga biriktirilgan. Boshqa raqam kiriting.")
        return

    await state.update_data(phone=phone)
    await state.set_state(Checkout.waiting_shipping_address)
    await message.answer(
        "📍 Yetkazib berish manzilini kiriting.",
        reply_markup=_cancel_keyboard(),
    )


@router.message(Checkout.waiting_shipping_address)
async def checkout_shipping_address_handler(message: Message, state: FSMContext) -> None:
    address = (message.text or "").strip()
    if len(address) < 5:
        await message.answer("📍 Manzilni to'liqroq kiriting.")
        return

    await state.update_data(shipping_address=address)
    await state.set_state(Checkout.waiting_payment_method)
    await message.answer(
        "💳 To'lov usulini tanlang.",
        reply_markup=_payment_keyboard(),
    )


@router.callback_query(
    StateFilter(Checkout.waiting_payment_method),
    F.data.startswith("checkout:pay:"),
)
async def checkout_payment_handler(callback_query: CallbackQuery, state: FSMContext) -> None:
    if callback_query.from_user is None:
        await callback_query.answer("Foydalanuvchi aniqlanmadi.", show_alert=True)
        return

    method = callback_query.data.rsplit(":", maxsplit=1)[-1]
    if method not in PAYMENT_METHODS:
        await callback_query.answer("To'lov usuli topilmadi.", show_alert=True)
        return

    checkout_data = await state.get_data()
    checkout_data["payment_method"] = method

    try:
        order = _create_order_from_basket(callback_query.from_user.id, checkout_data)
    except CheckoutError as error:
        await _send_callback_message(
            callback_query,
            str(error),
            reply_markup=main_menu_keyboard(),
        )
        await state.clear()
        await callback_query.answer()
        return

    await state.clear()
    await _send_callback_message(
        callback_query,
        _order_success_text(order),
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
    await _notify_admins(callback_query.bot, order, callback_query.from_user.id)
    await callback_query.answer("Buyurtma qabul qilindi.")
