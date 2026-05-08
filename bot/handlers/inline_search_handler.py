from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

from db.base import products_db

inline_router = Router()


@inline_router.inline_query()
async def inline_query_handler(inline: InlineQuery):
    key_words = inline.query.strip().lower()
    limit = 10
    offset = inline.offset if inline.offset else 0
    products = products_db.get_all()
    filtered_products = []

    for product in products:
        if key_words in product['name'].lower():
            filtered_products.append(product)
    paged_products = filtered_products[int(offset):int(offset) + limit]
    results = [
        InlineQueryResultArticle(
            id=str(product['id']),
            title=f"\n{product['name']}",
            input_message_content=InputTextMessageContent(
                message_text=f"""
🏭 <b>{product['name']}</b>

💰 <b>Narxi:</b> {product['price']:,} so'm
📦 <b>Omborda:</b> {product['amount']} dona
🏷 <b>Chegirma:</b> {"Bor ✅" if product['is_discount'] else "Yo'q ❌"}

ℹ️ Batafsil ma'lumot uchun pastdagi tugmani bosing.
                """,
                parse_mode=ParseMode.HTML
            ),
            thumbnail_url=product['photo'],
            description=f"""

💸Narxi: {product['price']}
"""
        )
        for product in paged_products
    ]
    next_offset = str(int(offset) + limit) if int(offset) + limit < len(filtered_products) else ""
    await inline.answer(
        results=results,
        cache_time=3,
        is_personal=True,
        next_offset=next_offset
    )


"""
offset=0 -> (limit + offset)
limit=5
| | | | | | | | | | | | | | | | | | | | | | 
"""
