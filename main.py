"""
Finite State Machine (FSM), Routers
"""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, BotCommand, CallbackQuery
from dotenv import load_dotenv

from bot.buttons import main_menu_user_kb, main_menu_admin_kb
from bot.handlers import admin_message_router, admin_callback_router, inline_router
from config import TOKEN, ADMINS

load_dotenv(".env")
dp = Dispatcher()


@dp.callback_query(F.text == "check_if_subscribed")
async def handle_check_if_subscribed(callback_query: CallbackQuery):
    await callback_query.answer("Tekshirish bosildi ✅")


@dp.message(Command(commands=['help']))
async def help_command_handler(message: Message):
    await message.answer("""
/start -> Botni ishga tushurish
/help -> Bot hadia batafsil ma'lumot
    """)


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    if message.from_user.id not in ADMINS:
        await message.answer("""
    Assalomu aleykum dokonimizga xush kelibsiz😊
    <blockquote>Buyurtma uchun👇</blockquote>
        """, parse_mode=ParseMode.HTML, reply_markup=main_menu_user_kb())
    else:
        await message.answer("""
            Assalomu aleykum <b>ADMIN</b> xush kelibsiz😊
            <blockquote>Boshqarish uchun👇</blockquote>
                """, parse_mode=ParseMode.HTML, reply_markup=main_menu_admin_kb())


async def on_startup(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Botni ishga tushirish"),
        BotCommand(command="/help", description="Yordam"),
    ]
    # await bot.send_message()
    await bot.set_my_commands(commands)


async def on_shutdown(bot: Bot):
    await bot.delete_my_commands()


async def main() -> None:
    bot = Bot(token=TOKEN)  # noqa
    dp.include_routers(admin_message_router, admin_callback_router, inline_router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
