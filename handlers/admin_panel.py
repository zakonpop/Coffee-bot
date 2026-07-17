from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from callbacks import AdminCallback
from database import get_user
from handlers.user import get_number

router = Router()



@router.message(F.text.lower() == "админ-понель")
@router.message(Command("admin_ponel"))
async def admin_ponel(message: Message):
	user = await get_user(message.from_user.id)	
	if not user:	
		await get_number(message)
		return
	if user["admin"] != 1:
		return
	
	builder = InlineKeyboardBuilder()
	builder.button(text="Информация пользователя", callback_data=AdminCallback(status="full_info"))
	builder.button(text="Удалить/Редактировать товар",callback_data=AdminCallback(status="item"))
	builder.button(text="Добавить товар",callback_data=AdminCallback(status="add_item"))
	builder.adjust(1)
	
	await message.answer(f"""
	======Админ панель======\n
	Выберите действие из ниже прндложеных:
	""", reply_markup=builder.as_markup())

