from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
import aiosqlite
from config import file_name
from callbacks import AdminCallback, AdminCallbackItem
from states import AdminStateItem, AddEat
from database import get_user, get_item, eat_exists, get_update_field_item


router = Router()






@router.callback_query(AdminCallback.filter(F.status== "item"))
async def  delete_item(callback: CallbackQuery, callback_data: AdminCallback, state: FSMContext):
	admin_id = callback.from_user.id
	admin = await get_user(admin_id)
	if not admin or admin.get("admin") != 1:
		return
	await callback.message.edit_text(
		"🔍 Пришлите Название товара чтобы получить его информацию.(Напишите так как он был записан, если есть эмоджи то с ними)"
	)
	await callback.answer()
	await state.set_state(AdminStateItem.wfn)

@router.message(F.text,AdminStateItem.wfn)
async def what_edit_item(message: Message, state: FSMContext):
	admin_id = message.from_user.id
	admin = await get_user(admin_id)
	
	
	if not admin or admin.get("admin") != 1:
		await state.clear()
		return
		
	if not await eat_exists(message.text):
		await message.answer("Такого товара нет в Базе Данных")
		return
	data_item = await get_item(message.text)
	text = (
		f"☕ <b>{data_item['name']}</b>\n\n"
		f"💰 Цена: <b>{data_item['price']}₽</b>\n\n"
		f"<blockquote><i>{data_item['info']}</i></blockquote>\n\n"
		f"Нажмите на кнопки ниже что хотите редактировать или удалить товар:"
	)
	builder =InlineKeyboardBuilder()
	builder.button(text="Категория",callback_data=AdminCallbackItem(status="category", value= data_item["name"]))
	builder.button(text="Название",callback_data=AdminCallbackItem(status="name", value= data_item["name"]))
	builder.button(text="Цена",callback_data=AdminCallbackItem(status="price", value= data_item["name"]))
	builder.button(text="Информация",callback_data=AdminCallbackItem(status="info", value= data_item["name"]))
	builder.button(text="Удалить товар",callback_data=AdminCallbackItem(status="delete_item", value= data_item["name"]))
	
	builder.adjust(4)
	await message.answer(text,reply_markup=builder.as_markup())

@router.callback_query(AdminCallbackItem.filter())
async def edit_item(callback: CallbackQuery, callback_data: AdminCallbackItem, state: FSMContext):
	
	admin_id = callback.from_user.id
	admin = await get_user(admin_id)


	if not admin or admin.get("admin") != 1:
		await callback.answer("❌ У вас нет прав для этой команды.", show_alert=True)
		return
	
	if callback_data.status == "delete_item":
		async with aiosqlite.connect(file_name) as db:
			await db.execute("DELETE FROM eats WHERE name = ?", (callback_data.value,))
			await db.commit()
		await callback.message.answer("✅ Товар удалён.")
		await state.clear()	
		return
			
			
	await callback.message.edit_text("Напишите на что хотите изменить в данной колонке:")
	await state.update_data(item_name= callback_data.value)
	await state.update_data(field= callback_data.status)
	await state.set_state(AdminStateItem.edit_field)
	
@router.message(F.text,AdminStateItem.edit_field)
async def finale_edit_item(message: Message, state: FSMContext):
	data = await state.get_data()
	name = data.get("item_name")
	field = data.get("field")
	try:
		new_value = round(float(message.text),2)
	except ValueError:
		new_value = message.text
	if not name or not field:
		await message.answer("Произошла ошибка: потеряны данные редактирования. Начните заново.")
		await state.clear()
		return
	
	await get_update_field_item(name, field, new_value)
	await message.answer("✅ Товар обновлён.")
	
	await state.clear()	

async def start_add_eat(event, state: FSMContext):
	user = await get_user(event.from_user.id)
	if not user or user['admin'] != 1:
		return
	await state.clear()
	await state.set_state(AddEat.cat)
	target_message = event.message if isinstance(event, CallbackQuery) else event
	await target_message.answer("📝 Напишите, какая <b>категория</b> будет у продукта:")
	
@router.message(Command("add_eat"))
async def add_item_command(message: Message, state: FSMContext):
	await start_add_eat(message, state)

@router.callback_query(AdminCallback.filter(F.status == "add_item"))
async def add_item_button(callback: CallbackQuery, state: FSMContext):
	await start_add_eat(callback, state)
	await callback.answer()
	

@router.message(AddEat.cat, F.text)
async def step_cat(message: Message, state: FSMContext):
	if message.text == '/cancel':
		await state.clear()
		await message.answer("❌ Добавление блюда отменено.")
		return

	await state.update_data(cat=message.text)
	await state.set_state(AddEat.name)
	await message.answer("✅ Отлично! Теперь напишите <b>название</b> продукта:")


@router.message(AddEat.name, F.text)
async def step_name(message: Message, state: FSMContext):
	if message.text == '/cancel':
		await state.clear()
		await message.answer("❌ Добавление блюда отменено.")
		return

	if await eat_exists(message.text):
		await message.answer("⚠️ Такое имя уже есть. Введите другое:")
		return

	await state.update_data(name=message.text)
	await state.set_state(AddEat.price)
	await message.answer("✅ Записал! Теперь напиши <b>цену</b>:")


@router.message(AddEat.price, F.text)
async def step_price(message: Message, state: FSMContext):
	if message.text == '/cancel':
		await state.clear()
		await message.answer("❌ Добавление блюда отменено.")
		return

	try:
		pricen = float(message.text.replace(",", "."))
		if pricen < 0:
			raise ValueError
	except ValueError:
		await message.answer("⚠️ Цена должна быть неотрицательным числом. Например: <code>250</code> или <code>199.99</code>")
		return

	await state.update_data(price=pricen)
	await state.set_state(AddEat.info)
	await message.answer("📄 Теперь напишите <b>описание</b> продукта:")


@router.message(AddEat.info, F.text)
async def step_info(message: Message, state: FSMContext):
	if message.text == '/cancel':
		await state.clear()
		await message.answer("❌ Добавление блюда отменено.")
		return

	d = await state.get_data()
	async with aiosqlite.connect(file_name) as db:
		await db.execute("INSERT INTO eats (category, name, price, info) VALUES (?,?,?,?)", (d['cat'], d['name'], d['price'], message.text))
		await db.commit()

	await state.clear()
	await message.answer(
		f"✅ <b>Продукт добавлен!</b>\n\n"
		f"📂 Категория: {d['cat']}\n"
		f"☕ Название: {d['name']}\n"
		f"💰 Цена: {d['price']} ₽\n"
		f"📄 Описание:\n<blockquote><i>{message.text}</i></blockquote>")