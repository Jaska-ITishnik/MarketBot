from aiogram import Bot
from aiogram.types import BotCommand


async def set_default_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="/start", description="Botni ishga tushirish"),
        BotCommand(command="/catalog", description="Mahsulotlar katalogi"),
        BotCommand(command="/cart", description="Savatni ko'rish"),
        BotCommand(command="/orders", description="Buyurtmalarim"),
        BotCommand(command="/help", description="Yordam"),
    ]
    await bot.set_my_commands(commands)


async def delete_default_commands(bot: Bot) -> None:
    await bot.delete_my_commands()
