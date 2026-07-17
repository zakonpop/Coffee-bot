from aiogram.fsm.state import State, StatesGroup


class AdminStateUser(StatesGroup):
	wff = State()
	bonus_amount = State()
	
class AdminStateItem(StatesGroup):
	wfn = State()
	edit_field = State() 



class AddEat(StatesGroup):
	cat = State()
	name = State()
	price = State()
	info = State()
	
	
class BuyPointsState(StatesGroup):
	amount = State()