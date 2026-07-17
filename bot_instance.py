from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from config import token_bot
bot = Bot(
    token=token_bot,
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher()
