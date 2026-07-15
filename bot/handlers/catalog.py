from collections import defaultdict
from decimal import Decimal
from html import escape
from math import ceil
from pathlib import Path

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import select

from bot.buttons import MainMenu, main_menu_keyboard
from db import database
from db.models import Basket, Category, Product

router = Router(name="catalog")

CATEGORY_PAGE_SIZE = 8
PRODUCT_PAGE_SIZE = 7
MAX_PRODUCT_BUTTON_TEXT_LENGTH = 52
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _format_money(value: Decimal) -> str:
    return f"{value:,.0f}".replace(",", " ")


def _short_text(value: str, max_length: int = MAX_PRODUCT_BUTTON_TEXT_LENGTH) -> str:
    if len(value) <= max_length:
        return value
    return f"{value[:max_length - 1]}..."


def _page_bounds(total_items: int, page_size: int, page: int) -> tuple[int, int]:
    total_pages = max(ceil(total_items / page_size), 1)
    page = max(0, min(page, total_pages - 1))
    return page, total_pages


def _fetch_categories() -> list[Category]:
    query = select(Category).order_by(Category.name)
    return list(database.execute(query).scalars().all())


def _fetch_category(category_id: int) -> Category | None:
    query = select(Category).where(Category.id == category_id)
    return database.execute(query).scalars().first()


def _fetch_product(product_id: int) -> Product | None:
    query = select(Product).where(Product.id == product_id)
    return database.execute(query).scalars().first()


def _category_ids_with_descendants(category_id: int) -> list[int]:
    rows = database.execute(select(Category.id, Category.parent_id)).all()
    children_by_parent: dict[int | None, list[int]] = defaultdict(list)

    for row in rows:
        children_by_parent[row.parent_id].append(row.id)

    category_ids = []
    stack = [category_id]
    while stack:
        current_id = stack.pop()
        category_ids.append(current_id)
        stack.extend(children_by_parent.get(current_id, []))

    return category_ids


def _fetch_products_for_category(category_id: int) -> list[Product]:
    category_ids = _category_ids_with_descendants(category_id)
    query = (
        select(Product)
        .where(Product.is_active.is_(True), Product.category_id.in_(category_ids))
        .order_by(Product.name)
    )
    return list(database.execute(query).scalars().all())


def _categories_keyboard(categories: list[Category], page: int) -> InlineKeyboardMarkup:
    page, total_pages = _page_bounds(len(categories), CATEGORY_PAGE_SIZE, page)
    start = page * CATEGORY_PAGE_SIZE
    page_items = categories[start:start + CATEGORY_PAGE_SIZE]

    rows = [
        [
            InlineKeyboardButton(
                text=category.name,
                callback_data=f"pl:{category.id}:0",
            )
        ]
        for category in page_items
    ]

    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton(text="Oldingi", callback_data=f"cp:{page - 1}"))
        nav_row.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton(text="Keyingi", callback_data=f"cp:{page + 1}"))
        rows.append(nav_row)

    return InlineKeyboardMarkup(inline_keyboard=rows)


def _products_keyboard(
        products: list[Product],
        category_id: int,
        page: int,
) -> InlineKeyboardMarkup:
    page, total_pages = _page_bounds(len(products), PRODUCT_PAGE_SIZE, page)
    start = page * PRODUCT_PAGE_SIZE
    page_items = products[start:start + PRODUCT_PAGE_SIZE]

    rows = [
        [
            InlineKeyboardButton(
                text=_short_text(product.name),
                callback_data=f"pd:{product.id}:{category_id}:{page}",
            )
        ]
        for product in page_items
    ]

    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton(text="Oldingi", callback_data=f"pl:{category_id}:{page - 1}"))
        nav_row.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton(text="Keyingi", callback_data=f"pl:{category_id}:{page + 1}"))
        rows.append(nav_row)

    rows.append([InlineKeyboardButton(text="Kategoriyalarga qaytish", callback_data="cp:0")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _product_detail_keyboard(
        product: Product,
        category_id: int,
        page: int,
        quantity: int,
) -> InlineKeyboardMarkup:
    rows = []

    if product.stock_quantity > 0:
        quantity = max(1, min(quantity, product.stock_quantity))
        rows.append(
            [
                InlineKeyboardButton(text="-", callback_data=f"q:{product.id}:{category_id}:{page}:{quantity}:-1"),
                InlineKeyboardButton(text=str(quantity), callback_data="noop"),
                InlineKeyboardButton(text="+", callback_data=f"q:{product.id}:{category_id}:{page}:{quantity}:1"),
            ]
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text="Savatga qo'shish",
                    callback_data=f"add:{product.id}:{quantity}",
                )
            ]
        )
    else:
        rows.append([InlineKeyboardButton(text="Omborda yo'q", callback_data="noop")])

    rows.append([InlineKeyboardButton(text="Mahsulotlarga qaytish", callback_data=f"pl:{category_id}:{page}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _product_detail_text(product: Product) -> str:
    description = product.description or "Tavsif kiritilmagan."
    category_name = product.category.name if product.category else "Kategoriyasiz"

    return (
        f"<b>{escape(product.name)}</b>\n\n"
        f"<b>Narx:</b> {_format_money(product.price)} so'm\n"
        f"<b>Omborda:</b> {product.stock_quantity} dona\n"
        f"<b>Kategoriya:</b> {escape(category_name)}\n\n"
        f"<b>Mahsulot haqida</b>\n"
        f"{escape(description)}"
    )


def _product_photo(product: Product) -> str | FSInputFile | None:
    photo = (product.photo or "").strip()
    if not photo:
        return None

    if photo.startswith(("http://", "https://")):
        return photo

    photo_path = Path(photo)
    if not photo_path.is_absolute():
        photo_path = PROJECT_ROOT / photo_path

    if not photo_path.is_file():
        return None

    return FSInputFile(photo_path)


def _callback_chat_id(callback_query: CallbackQuery) -> int:
    if callback_query.message is not None:
        return callback_query.message.chat.id
    return callback_query.from_user.id


async def _replace_callback_message(
        callback_query: CallbackQuery,
        text: str,
        reply_markup: InlineKeyboardMarkup | None = None,
        parse_mode: str | None = None,
) -> None:
    if callback_query.message is not None:
        try:
            await callback_query.message.edit_text(
                text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
            return
        except TelegramBadRequest as error:
            if "message is not modified" in str(error):
                return
            try:
                await callback_query.message.delete()
            except TelegramBadRequest:
                pass

    await callback_query.bot.send_message(
        chat_id=_callback_chat_id(callback_query),
        text=text,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
    )


def _upsert_basket_item(telegram_id: int, product: Product, quantity: int) -> int:
    quantity = max(1, quantity)
    if product.stock_quantity <= 0:
        return 0

    query = select(Basket).where(
        Basket.telegram_id == telegram_id,
        Basket.product_id == product.id,
    )
    basket_item = database.execute(query).scalars().first()

    try:
        if basket_item is None:
            basket_item = Basket(
                telegram_id=telegram_id,
                product=product,
                quantity=min(quantity, product.stock_quantity),
            )
            database.add(basket_item)
        else:
            basket_item.quantity = min(
                basket_item.quantity + quantity,
                product.stock_quantity,
            )

        database.commit()
    except Exception:
        database.rollback()
        raise

    return basket_item.quantity


async def _send_categories(message: Message, page: int = 0) -> None:
    categories = _fetch_categories()
    if not categories:
        await message.answer(
            "Kategoriyalar hozircha mavjud emas.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await message.answer(
        "Kategoriyani tanlang:",
        reply_markup=_categories_keyboard(categories, page),
    )


async def _edit_categories(callback_query: CallbackQuery, page: int = 0) -> None:
    categories = _fetch_categories()
    if not categories:
        await _replace_callback_message(callback_query, "Kategoriyalar hozircha mavjud emas.")
        await callback_query.answer()
        return

    await _replace_callback_message(
        callback_query,
        "Kategoriyani tanlang:",
        reply_markup=_categories_keyboard(categories, page),
    )
    await callback_query.answer()


async def _edit_products(callback_query: CallbackQuery, category_id: int, page: int = 0) -> None:
    category = _fetch_category(category_id)
    if category is None:
        await callback_query.answer("Kategoriya topilmadi.", show_alert=True)
        return

    products = _fetch_products_for_category(category_id)
    if not products:
        await _replace_callback_message(
            callback_query,
            f"<b>{escape(category.name)}</b>\n\nBu kategoriyada hozircha mahsulot yo'q.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Kategoriyalarga qaytish", callback_data="cp:0")]
                ]
            ),
            parse_mode="HTML",
        )
        await callback_query.answer()
        return

    page, total_pages = _page_bounds(len(products), PRODUCT_PAGE_SIZE, page)
    await _replace_callback_message(
        callback_query,
        f"<b>{escape(category.name)}</b>\n"
        f"Mahsulotlar: {len(products)} ta\n"
        f"Sahifa: {page + 1}/{total_pages}\n\n"
        "Mahsulotni tanlang:",
        reply_markup=_products_keyboard(products, category_id, page),
        parse_mode="HTML",
    )
    await callback_query.answer()


async def _edit_product_detail(
        callback_query: CallbackQuery,
        product_id: int,
        category_id: int,
        page: int,
        quantity: int = 1,
) -> None:
    product = _fetch_product(product_id)
    if product is None:
        await callback_query.answer("Mahsulot topilmadi.", show_alert=True)
        return

    text = _product_detail_text(product)
    reply_markup = _product_detail_keyboard(product, category_id, page, quantity)
    photo = _product_photo(product)

    if photo is None:
        await _replace_callback_message(
            callback_query,
            text,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
        await callback_query.answer()
        return

    if callback_query.message is not None:
        try:
            await callback_query.message.delete()
        except TelegramBadRequest:
            pass

    try:
        await callback_query.bot.send_photo(
            chat_id=_callback_chat_id(callback_query),
            photo=photo,
            caption=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
    except TelegramBadRequest:
        await callback_query.bot.send_message(
            chat_id=_callback_chat_id(callback_query),
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
    await callback_query.answer()


@router.message(Command(commands=["catalog"]))
@router.message(F.text == MainMenu.CATALOG)
async def catalog_handler(message: Message) -> None:
    await _send_categories(message)


@router.message(F.text == MainMenu.SEARCH)
async def search_handler(message: Message) -> None:
    await message.answer(
        "Qidirish bo'limi.\n\n"
        "Keyingi bosqichda mahsulot nomi bo'yicha qidiruv qo'shamiz.",
        reply_markup=main_menu_keyboard(),
    )


@router.callback_query(F.data == "noop")
async def noop_handler(callback_query: CallbackQuery) -> None:
    await callback_query.answer()


@router.callback_query(F.data.startswith("cp:"))
async def category_page_handler(callback_query: CallbackQuery) -> None:
    _, page = callback_query.data.split(":")
    await _edit_categories(callback_query, int(page))


@router.callback_query(F.data.startswith("pl:"))
async def product_list_handler(callback_query: CallbackQuery) -> None:
    _, category_id, page = callback_query.data.split(":")
    await _edit_products(callback_query, int(category_id), int(page))


@router.callback_query(F.data.startswith("pd:"))
async def product_detail_handler(callback_query: CallbackQuery) -> None:
    _, product_id, category_id, page = callback_query.data.split(":")
    await _edit_product_detail(
        callback_query,
        product_id=int(product_id),
        category_id=int(category_id),
        page=int(page),
    )


@router.callback_query(F.data.startswith("q:"))
async def product_quantity_handler(callback_query: CallbackQuery) -> None:
    _, product_id, category_id, page, quantity, delta = callback_query.data.split(":")
    product = _fetch_product(int(product_id))
    if product is None:
        await callback_query.answer("Mahsulot topilmadi.", show_alert=True)
        return

    old_quantity = int(quantity)
    new_quantity = max(1, min(old_quantity + int(delta), product.stock_quantity))
    if new_quantity == old_quantity:
        await callback_query.answer("Miqdor chegarasiga yetdi.")
        return

    await _edit_product_detail(
        callback_query,
        product_id=product.id,
        category_id=int(category_id),
        page=int(page),
        quantity=new_quantity,
    )


@router.callback_query(F.data.startswith("add:"))
async def add_to_basket_handler(callback_query: CallbackQuery) -> None:
    if callback_query.from_user is None:
        await callback_query.answer("Foydalanuvchi aniqlanmadi.", show_alert=True)
        return

    _, product_id, quantity = callback_query.data.split(":")
    product = _fetch_product(int(product_id))
    if product is None:
        await callback_query.answer("Mahsulot topilmadi.", show_alert=True)
        return

    saved_quantity = _upsert_basket_item(
        telegram_id=callback_query.from_user.id,
        product=product,
        quantity=int(quantity),
    )
    if saved_quantity == 0:
        await callback_query.answer("Bu mahsulot hozir omborda yo'q.", show_alert=True)
        return

    await callback_query.answer(
        f"Savatga qo'shildi. Savatda: {saved_quantity} dona.",
        show_alert=False,
    )
