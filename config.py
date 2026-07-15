import os

from dotenv import load_dotenv

load_dotenv(".env")


class Settings:
    USERNAME = os.getenv('USERNAME')
    SECRET_KEY = os.getenv('SECRET_KEY')

    def __init__(self, database, user, password, host, port):
        self.database = database
        self.user = user
        self.password = password
        self.host = host
        self.port = port

    def postgresql_url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


settings = Settings(
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
