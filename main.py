import asyncio
import logging 
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat 

from config import admin_id 
from bot_instance import bot, dp 
from database import init_db, init_eats , init_donate_db


from handlers.user import router as user_router
from handlers.menu import router as menu_router
from handlers.admin_panel import router as admin_panel_router
from handlers.admin_users import router as admin_users_router
from handlers.admin_items import router as admin_items_router

async def set_commands(bot):
	user_commands = [
		BotCommand(command="start", description="Запустить бота"),
		BotCommand(command="menu", description="Посмотреть меню"),
		BotCommand(command="profile", description="Открыть профиль"),
	]
	await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())

	admin_commands = user_commands + [
		BotCommand(command="add_eat", description="Добавить блюдо"),
		BotCommand(command="cancel", description="Отменить действие")
	]
	await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=admin_id))

async def main():
    await init_db() 
    await init_eats() 
    await init_donate_db()
    await set_commands(bot)

    dp.include_routers(
        user_router,
        menu_router,
        admin_panel_router,
        admin_users_router,
        admin_items_router
    )
    
    logging.info("Бот запущен")
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())