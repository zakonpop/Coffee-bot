from aiogram.fsm.state import State, StatesGroup
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, CallbackQuery 
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from database import get_user, create_user, add_donat, get_update_field
from bot_instance import bot
from aiogram.fsm.context import FSMContext
from aiogram.types import LabeledPrice, PreCheckoutQuery
from callbacks import BuyPointsCallback
from states import BuyPointsState

router = Router()





def normalize_phone(phone: str) -> str:
	digits = ''.join(c for c in phone if c.isdigit())
	if digits.startswith('8') and len(digits) == 11:
		digits = '7' + digits[1:]
	elif len(digits) == 10:
		digits = '7' + digits
	return digits


async def get_number(event):
	keyboard_num = ReplyKeyboardMarkup(
		keyboard=[
			[KeyboardButton(text="📱 Поделиться номером", request_contact=True)]
		],
		resize_keyboard=True,
		one_time_keyboard=True
	)
	await event.answer("📱 Чтобы пользоваться ботом, поделись номером телефона:", reply_markup=keyboard_num)

def get_main_keyboard(is_admin: bool) -> ReplyKeyboardMarkup:
	buttons = [
		[KeyboardButton(text="Меню"), KeyboardButton(text="Профиль")],
		[KeyboardButton(text="Помощь")]
	]
	if is_admin:
		buttons.append([KeyboardButton(text="Админ-понель")])
	return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
	
@router.message(F.contact)
async def add_contact(message: Message):
	user_id = message.from_user.id
	num = normalize_phone(str(message.contact.phone_number))
	user = await get_user(user_id)
	if user:
		await message.answer("ℹ️ Вы уже привязывали свой номер телефона", reply_markup=get_main_keyboard(user["admin"] == 1 ))
		return
	if message.contact.user_id != user_id:
		await message.answer("⚠️ Пожалуйста, поделитесь <b>именно своим</b> номером телефона.", reply_markup=ReplyKeyboardRemove())
		return

	user = await create_user(num, user_id)
	await message.answer("✅ <b>Готово!</b> Теперь вы можете пользоваться ботом.", reply_markup=get_main_keyboard(user["admin"] == 1 ))
	return user

@router.message(F.text.lower() == "помощь")
async def cmd_help(message: Message):
	user = await get_user(message.from_user.id)
	if not user:
		await get_number(message)
		return
		
	if user["banned"] == 1:
		await message.answer("Извините, но вас заблокировала администрация!")
		return

	text = ("ℹ️ <b>Помощь</b>\n\n"
    "📋 <b>Меню</b> — посмотреть товары кофейни\n"
    "👤 <b>Профиль</b> — твои баллы и история покупок\n\n"
    "Баллы можно пополнить прямо в профиле через Telegram Stars.")
	if user["admin"] == 1:
		text = text + ( "\n\n🔧 <b>Админ-панель</b>\n"
    "Доступна кнопкой ниже. Там ты можешь:\n"
    "— искать пользователей (перешли сообщение)\n"
    "— начислять/списывать бонусы\n"
    "— банить/разбанивать\n"
    "— добавлять, редактировать и удалять товары")
	
	await message.answer(text)
@router.message(Command('start'))
async def cmd_start(message: Message):
	user = await get_user(message.from_user.id)
	
	if not user:
		await message.answer("👋 <b>Добро пожаловать в кофейню!</b>\n\nЧтобы продолжить, привяжите номер телефона:")
		await get_number(message)
		return
		
	if user["banned"] == 1:
		await message.answer("Извините, но вас заблокировала администрация!")
		return
	await message.answer("☕ <b>Рады видеть тебя снова!</b>", reply_markup=get_main_keyboard(user["admin"] == 1 ))

@router.message(F.text.lower() == "профиль")
@router.message(Command("profile"))
async def cmd_profile(message: Message):
	user = await get_user(message.from_user.id)
	
	if not user:
		
		await get_number(message)
		return
	
	if user["banned"] == 1:
		await message.answer("Извините, но вас заблокировала администрация!")
		return
	
	name = message.from_user.first_name
	phone = user['number'] if user['number'] else "не указан"
	status = "Администратор" if user['admin'] == 1 else "Клиент"

	text = (
		f"👤 <b>Профиль</b>\n"
		f"<blockquote>"
		f"<b>Имя:</b> {name}\n"
		f"<b>Телефон:</b> <code>{phone}</code>\n"
		f"<b>Баллы:</b> {user['points']} ⭐\n"
		f"<b>Статус:</b> {status}"
		f"</blockquote>"
	)

	photos = await bot.get_user_profile_photos(message.from_user.id, limit=1)
	builder = InlineKeyboardBuilder()
	builder.button(text="Пополнить баланс 💳", callback_data=BuyPointsCallback(status="buy_points"))
	if photos.total_count > 0:
		photo_id = photos.photos[0][-1].file_id
		await message.answer_photo(photo=photo_id, caption=text, reply_markup= builder.as_markup())
	else:
		await message.answer(text, reply_markup=get_main_keyboard(user["admin"] == 1 ))


@router.callback_query(BuyPointsCallback.filter(F.status == "buy_points"))
async def button_buy_points(callback: CallbackQuery, callback_data: BuyPointsCallback, state: FSMContext):
  user_id = callback.from_user.id
  user = await get_user(user_id)
  
  if not user:
    await get_number(callback.message)
    return
  
  if user["banned"] == 1:
    await callback.message.answer("Извините, но вас заблокировала администрация!")
    return
  
  await callback.message.answer("Напишите насколько вы хотите пополнить баланс:")
  await state.set_state(BuyPointsState.amount)
  
@router.message(F.text,BuyPointsState.amount)
async def add_points(message: Message, state: FSMContext):
  user_id = message.from_user.id
  user = await get_user(user_id)
  
  if not user:
    await get_number(callback.message)
    return
  
  if user["banned"] == 1:
    await callback.message.edit_text("Извините, но вас заблокировала администрация!")
    return
  
  
  if message.text.isdigit():
    val = int(message.text)
  else:
     await message.answer("Введите пожалуйста положительное число...")
     return
  await message.answer_invoice(
  title = "Пополнение баланса",
  description = f"Пополнение баланса на сумму: {val}",
  payload = f"donate_{val}",
  provider_token="",
	currency="XTR",
	prices=[LabeledPrice(label="Донат", amount=val)]
  )

@router.pre_checkout_query()
async def pre_checkout(query:PreCheckoutQuery):
  await query.answer(ok=True)

@router.message(F.successful_payment)
async def successful_add_points(message: Message, state: StatesGroup):
  user = await get_user(message.from_user.id)
  if not user:
    await get_number(callback.message)
  
  payload = message.successful_payment.invoice_payload
  amout = message.successful_payment.total_amount
  
  await add_donat(message.from_user.id, user["number"],payload,amout)
  await get_update_field(message.from_user.id, "points",user["points"] + amout)
  await message.answer("Успешно! На ваш аккаунт поступили бонусы")
  now = datetime.now(timezone.utc)
  async with aiosqlite.connect(file_name) as db:
    await db.execute(
      "INSERT INTO purchases (user_id, item_name, price, date, time) VALUES (?,?,?,?,?)",
      (user_id, item['name'], amount, now.strftime("%Y-%m-%d"), now.strftime("%H:%M"))
    )
    await db.commit()
  await state.clear()
  
  
  
def get_main_keyboard(is_admin: bool) -> ReplyKeyboardMarkup:
	buttons = [
		[KeyboardButton(text="Меню"), KeyboardButton(text="Профиль")]
	]
	if is_admin:
		buttons.append([KeyboardButton(text="Админ-понель")])
	return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
	
@router.message(F.contact)
async def add_contact(message: Message):
	user_id = message.from_user.id
	num = normalize_phone(str(message.contact.phone_number))
	user = await get_user(user_id)
	if user:
		await message.answer("ℹ️ Вы уже привязывали свой номер телефона", reply_markup=get_main_keyboard(user["admin"] == 1 ))
		return
	if message.contact.user_id != user_id:
		await message.answer("⚠️ Пожалуйста, поделитесь <b>именно своим</b> номером телефона.", reply_markup=ReplyKeyboardRemove())
		return

	user = await create_user(num, user_id)
	await message.answer("✅ <b>Готово!</b> Теперь вы можете пользоваться ботом.", reply_markup=get_main_keyboard(user["admin"] == 1 ))
	return user

@router.message(Command('start'))
async def cmd_start(message: Message):
	user = await get_user(message.from_user.id)
	
	if not user:
		await message.answer("👋 <b>Добро пожаловать в кофейню!</b>\n\nЧтобы продолжить, привяжите номер телефона:")
		await get_number(message)
		return
		
	if user["banned"] == 1:
		await message.answer("Извините, но вас заблокировала администрация!")
		return
	await message.answer("☕ <b>Рады видеть тебя снова!</b>", reply_markup=get_main_keyboard(user["admin"] == 1 ))

@router.message(F.text.lower() == "профиль")
@router.message(Command("profile"))
async def cmd_profile(message: Message):
	user = await get_user(message.from_user.id)
	
	if not user:
		
		await get_number(message)
		return
	
	if user["banned"] == 1:
		await message.answer("Извините, но вас заблокировала администрация!")
		return
	
	name = message.from_user.first_name
	phone = user['number'] if user['number'] else "не указан"
	status = "Администратор" if user['admin'] == 1 else "Клиент"

	text = (
		f"👤 <b>Профиль</b>\n"
		f"<blockquote>"
		f"<b>Имя:</b> {name}\n"
		f"<b>Телефон:</b> <code>{phone}</code>\n"
		f"<b>Баллы:</b> {user['points']} ⭐\n"
		f"<b>Статус:</b> {status}"
		f"</blockquote>"
	)

	photos = await bot.get_user_profile_photos(message.from_user.id, limit=1)
	builder = InlineKeyboardBuilder()
	builder.button(text="Пополнить баланс 💳", callback_data=BuyPointsCallback(status="buy_points"))
	if photos.total_count > 0:
		photo_id = photos.photos[0][-1].file_id
		await message.answer_photo(photo=photo_id, caption=text, reply_markup= builder.as_markup())
	else:
		await message.answer(text, reply_markup=get_main_keyboard(user["admin"] == 1 ))


@router.callback_query(BuyPointsCallback.filter(F.status == "buy_points"))
async def button_buy_points(callback: CallbackQuery, callback_data: BuyPointsCallback, state: FSMContext):
  user_id = callback.from_user.id
  user = await get_user(user_id)
  
  if not user:
    await get_number(callback.message)
    return
  
  if user["banned"] == 1:
    await callback.message.answer("Извините, но вас заблокировала администрация!")
    return
  
  await callback.message.answer("Напишите насколько вы хотите пополнить баланс:")
  await state.set_state(BuyPointsState.amount)
  
@router.message(F.text,BuyPointsState.amount)
async def add_points(message: Message, state: FSMContext):
  user_id = message.from_user.id
  user = await get_user(user_id)
  
  if not user:
    await get_number(callback.message)
    return
  
  if user["banned"] == 1:
    await callback.message.edit_text("Извините, но вас заблокировала администрация!")
    return
  
  
  if message.text.isdigit():
    val = int(message.text)
  else:
     await message.answer("Введите пожалуйста положительное число...")
     return
  await message.answer_invoice(
  title = "Пополнение баланса",
  description = f"Пополнение баланса на сумму: {val}",
  payload = f"donate_{val}",
  provider_token="",
	currency="XTR",
	prices=[LabeledPrice(label="Донат", amount=val)]
  )

@router.pre_checkout_query()
async def pre_checkout(query:PreCheckoutQuery):
  await query.answer(ok=True)

@router.message(F.successful_payment)
async def successful_add_points(message: Message, state: StatesGroup):
  user = await get_user(message.from_user.id)
  if not user:
    await get_number(callback.message)
  
  payload = message.successful_payment.invoice_payload
  amout = message.successful_payment.total_amount
  
  await add_donat(message.from_user.id, user["number"],payload,amout)
  await get_update_field(message.from_user.id, "points",user["points"] + amout)
  await message.answer("Успешно! На ваш аккаунт поступили бонусы")
  now = datetime.now(timezone.utc)
  async with aiosqlite.connect(file_name) as db:
    await db.execute(
      "INSERT INTO purchases (user_id, item_name, price, date, time) VALUES (?,?,?,?,?)",
      (user_id, item['name'], amount, now.strftime("%Y-%m-%d"), now.strftime("%H:%M"))
    )
    await db.commit()
  await state.clear()
  
  
  
