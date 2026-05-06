from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.buttons import admin_products_ikb
from db.base import products_db, categories_db

admin_callback_router = Router()


@admin_callback_router.callback_query(F.data.startswith("category_"))
async def admin_category_handler(callback: CallbackQuery):
    category_id = int(callback.data.split("_")[-1])
    products = products_db.get_all()
    filtered_products = [product for product in products if product['category_id'] == category_id]
    category_name = categories_db.get_by_id(category_id)['name']
    await callback.message.edit_text(f"{category_name}👇", reply_markup=admin_products_ikb(filtered_products))
