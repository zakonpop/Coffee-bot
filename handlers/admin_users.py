from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot_instance import bot
from callbacks import AdminCallback
from states import AdminStateUser
from database import get_user, get_update_field


router = Router()


@router.callback_query(AdminCallback.filter(F.status == "full_info"))
async def forward_wait(callback: CallbackQuery, callback_data: AdminCallback, state: FSMContext):
    admin_id = callback.from_user.id
    admin = await get_user(admin_id)


    if not admin or admin.get("admin") != 1:
        await callback.answer("❌ У вас нет прав для этой команды.", show_alert=True)
        return

    await callback.message.edit_text(
        "🔍 Пришлите любое сообщение от пользователя (перешлите его сюда), чтобы получить его профиль."
    )
    await callback.answer()

    await state.set_state(AdminStateUser.wff)


@router.message(F.forward_from, AdminStateUser.wff)
async def handle_forwarded(message: Message, state: FSMContext):
	admin_id = message.from_user.id
	admin = await get_user(admin_id)


	if not admin or admin.get("admin") != 1:
		await state.clear()
		return
	
	target = message.forward_from
	
	target_id = target.id
	if not message.forward_from and message.text.isdigit():
		target_id = int(message.text)
	user = await get_user(target_id)
	info = f"👤 Инфо о пользователе\n━━━━━━━━━━━━━━━━━━━\n"
	info += f"ID: <code>{target_id}</code>\n"
	
	if user:

		info += "Статус: ✅ Зарегистрирован в боте\n"
		name = user.get("name") or target.first_name or "-"
		username = user.get("username") or (f"@{target.username}" if target.username else "-")
		number = user.get("number") or "-"
		date = user.get("date") or "-"
		time_val = user.get("time") or "-"
		points = user.get("points", 0)

		is_admin = "Да" if user.get("admin") == 1 else "Нет"
		is_banned = "Да" if user.get("banned") == 1 else "Нет"
		info += f"👤 <b>Прямая ссылка:</b> <a href='tg://user?id={target_id}'>{name}</a>\n"
		info += f"""ID: {target_id} 
Имя: {name}
Username: {username}
Номер: {number}
Дата регистрации: {date}
Время регистрации: {time_val}
Баллы: {points}
Админ: {is_admin}
Заблокирован: {is_banned}\n"""
	else:
		info += "Статус: ❌ Не зарегистрирован в боте\n"

		name = target.first_name or "-"
		username = f"@{target.username}" if target.username else "-"

		info += f"""👤 <b>Прямая ссылка:</b> <a href='tg://user?id={target_id}'>{name}</a>
ID: {target_id} 
Имя (из Telegram): {name}
Username (из Telegram): {username}
Номер: -
Дата регистрации в боте: -
Время регистрации в боте: -
Баллы: -
Админ: -
Заблокирован: -\n"""

	info += "━━━━━━━━━━━━━━━━━━━"
	builder =InlineKeyboardBuilder()
	builder.button(text="Пополнить/Отнять", callback_data=AdminCallback(status="add_bonus",value=str(target_id)))
	
	builder.button(text="Снять/Повысить в админам", callback_data=AdminCallback(status="toggle_admin", value=str(target_id)))
	
	builder.adjust(1)
	photos = await bot.get_user_profile_photos(target_id, limit=1)
	if photos.total_count > 0:
		photo_id = photos.photos[0][-1].file_id
		await message.answer_photo(photo=photo_id, caption=info, reply_markup=builder.as_markup())
	else:
		await message.answer(info, reply_markup=builder.as_markup())
	await state.clear()

@router.callback_query(AdminCallback.filter(F.status == "add_bonus"))
async def add_bonus(callback: CallbackQuery, callback_data: AdminCallback, state: FSMContext):
	admin = await get_user(callback.from_user.id)
	if not admin or admin.get("admin") != 1:
		await state.clear()
		return
	await state.update_data(target_id=callback_data.value)
	await state.set_state(AdminStateUser.bonus_amount)
	await callback.message.answer("Введи число (можно с минусом чтобы отнять):")
	await callback.answer()


@router.message(F.text, AdminStateUser.bonus_amount)
async def handler_add_bonus(message: Message, state: FSMContext):
	admin = await get_user(message.from_user.id)
	if not admin or admin["admin"] != 1:
		await state.clear()
		return
	try:
		amout = round(float(message.text.replace(",", ".")), 2)
	except ValueError:
		await message.answer("Введите число")
		return
	if amout == 0:
		await message.answer("Нельзя вводить 0")
		return

	target_id = int((await state.get_data()).get("target_id"))
	user = await get_user(target_id)
	if not user:
		await message.answer("Похоже, этот пользователь не зарегистрирован.")
		await state.clear()
		return

	await get_update_field(target_id, "points", amout + user['points'])
	what = "зачислили" if amout > 0 else "забрали"
	await message.answer(f"Успешно, вы {what} ему: {amout}")
	await state.clear()

@router.callback_query(AdminCallback.filter(F.status == "toggle_admin"))
async def toggle_admin(callback: CallbackQuery, callback_data: AdminCallback):
	admin = await get_user(callback.from_user.id)
	if not admin or admin.get("admin") != 1:
		await callback.answer("Нет прав.", show_alert=True)
		return

	target_id = int(callback_data.value)
	user = await get_user(target_id)
	if not user:
		await callback.answer("Пользователь не зарегистрирован.", show_alert=True)
		return

	new_status = 0 if user["admin"] == 1 else 1
	await get_update_field(target_id, "admin", new_status)
	action = "назначен админом" if new_status == 1 else "снят с админки"
	await callback.answer(f"Пользователь {action}", show_alert=True)

