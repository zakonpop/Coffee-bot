from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from callbacks import MenuCallback
from database import get_user, get_categories, get_item_by_cat, get_item, get_update_field
from handlers.user import get_number

router = Router()


@router.message(F.text.lower() == "меню")
@router.message(Command("menu"))
async def cmd_menu(message: Message):
	categories = await get_categories()
	user = await get_user(message.from_user.id)
	
	if not user:
		await get_number(message)
		return
	
	if user["banned"] == 1:
		await message.answer("Извините, но вас заблокировала администрация!")
		return
	
		
	if not categories:
		await message.answer("😔 Пока что товаров нет")
		return

	builder = InlineKeyboardBuilder()
	for cat in categories:
		builder.button(text=cat, callback_data=MenuCallback(level='category', value=cat))
	builder.adjust(2)

	await message.answer("🍽 <b>Выберите категорию:</b>", reply_markup=builder.as_markup())



@router.callback_query(MenuCallback.filter(F.level == "category"))
async def show_item(callback: CallbackQuery, callback_data: MenuCallback):
	cat = callback_data.value
	items = await get_item_by_cat(cat)

	if not items:
		await callback.answer("В этой категории пока что пусто", show_alert=True)
		return

	builder = InlineKeyboardBuilder()
	for item in items:
		builder.button(text=f"{item['name']}", callback_data=MenuCallback(level="item", value=item["name"]))
	builder.button(text="⬅ Назад", callback_data=MenuCallback(level="back", value=""))
	builder.adjust(2)

	await callback.message.edit_text(f"📂 <b>Категория:</b> {cat}", reply_markup=builder.as_markup())
	await callback.answer()



@router.callback_query(MenuCallback.filter(F.level == "item"))
async def info_item(callback: CallbackQuery, callback_data: MenuCallback):
	item = callback_data.value
	data_item = await get_item(item)

	if not data_item:
		await callback.answer("Товар не найден", show_alert=True)
		return

	builder = InlineKeyboardBuilder()
	builder.button(text="⬅ Назад", callback_data=MenuCallback(level="category", value=data_item['category']))
	builder.button(text="💰 Купить", callback_data=MenuCallback(level="buy_item", value=str(data_item['price'])))
	text = (
		f"☕ <b>{item}</b>\n\n"
		f"💰 Цена: <b>{data_item['price']}🌟</b>\n\n"
		f"<blockquote><i>{data_item['info']}</i></blockquote>"
	)

	await callback.message.edit_text(text, reply_markup=builder.as_markup())
	await callback.answer()

@router.callback_query(MenuCallback.filter(F.level == "buy_item"))
async def buy_item_cmd(callback: CallbackQuery, callback_data: MenuCallback):
  item = await get_item(callback_data.value)
amount = item['price']
  user_id = callback.from_user.id
  user = await get_user(user_id)
  
  if user["points"] < amount:
    await callback.answer("Недостаточно средств для покупки.")
    return
  
  
  await get_update_field(user_id,"points", user["points"] - amount)
  await callback.answer("Успешно ✅")
 
@router.callback_query(MenuCallback.filter(F.level == "back"))
async def back_to_categories(callback: CallbackQuery, callback_data: MenuCallback):
	categories = await get_categories()
	if not categories:
		await callback.answer("😔 Пока что товаров нет")
		return

	builder = InlineKeyboardBuilder()
	for cat in categories:
		builder.button(text=cat, callback_data=MenuCallback(level='category', value=cat))
	builder.adjust(2)

	await callback.message.edit_text("🍽 <b>Выберите категорию:</b>", reply_markup=builder.as_markup())
	await callback.answer()
