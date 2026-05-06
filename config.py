import os

from dotenv import load_dotenv

load_dotenv(".env")
TOKEN = os.getenv("BOT_TOKEN")
ADMINS = [int(admin) for admin in os.getenv("ADMINS").split()]
