from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

from db.base import products_db

inline_router = Router()


@inline_router.inline_query()
async def inline_search(inline_query: InlineQuery):
    query = inline_query.query.strip().lower()
    offset = offset if (offset := inline_query.offset) else 0
    limit = 10
    products = products_db.get_all()
    filtered_products = [product for product in products if query in product['name'].lower()] if query else products
    paged_products = filtered_products[int(offset):int(offset) + limit]
    results = [
        InlineQueryResultArticle(
            id=f"product_{product['id']}",
            title=product["name"],
            description=f"Narxi: {product['price']:,} so'm | Omborda: {product['amount']} dona",
            thumbnail_url=product["photo"],
            input_message_content=InputTextMessageContent(
                message_text=f"""
🛍 <b>{product['name']}</b>

💰 <b>Narx:</b> {product['price']:,} so'm
📦 <b>Omborda:</b> {product['amount']} dona
🏷 <b>Chegirma:</b> {'Mavjud ✅' if product['is_discount'] else 'Mavjud emas ❌'}

✨ Tanlangan mahsulot haqida ma'lumot.
🛒 Xarid qilish uchun tugmani bosing.
""".strip(),
                parse_mode=ParseMode.HTML
            )
        )
        for product in paged_products
    ]

    next_offset = str(int(offset) + limit) if (int(offset) + limit) < len(filtered_products) else ""
    await inline_query.answer(
        results=results,
        cache_time=1,
        is_personal=True,
        next_offset=next_offset
    )
