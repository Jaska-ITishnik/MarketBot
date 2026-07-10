"""
Finite State Machine (FSM), Routers
"""

import asyncio
import logging
import os
import sys
from db import database
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, BotCommand, CallbackQuery
from aiogram.utils.i18n import I18n, FSMI18nMiddleware
from dotenv import load_dotenv

from bot.middlewares import JoinChannelGroupMiddleware
from db.base import db

load_dotenv(".env")
dp = Dispatcher()
TOKEN = os.getenv('BOT_TOKEN')


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
    pass


async def on_startup(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Botni ishga tushirish"),
        BotCommand(command="/help", description="Yordam"),
    ]
    # await bot.send_message()
    database.create_all()
    await bot.set_my_commands(commands)


async def on_shutdown(bot: Bot):
    await bot.delete_my_commands()


async def main() -> None:
    bot = Bot(token=TOKEN)  # noqa
    i18 = I18n(path='locales', default_locale='uz', domain="messages")
    dp.update.outer_middleware.register(FSMI18nMiddleware(i18))
    dp.update.outer_middleware.register(JoinChannelGroupMiddleware())
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
