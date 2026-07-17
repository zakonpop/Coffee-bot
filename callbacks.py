from aiogram.filters.callback_data import CallbackData


class AdminCallbackItem(CallbackData, prefix="admin_item"):
		status: str
		value: str = ""
class AdminCallback(CallbackData, prefix="admin"):
	status: str
	value: str = "" 




class MenuCallback(CallbackData, prefix="menu"):
	level: str
	value: str
	
class BuyPointsCallback(CallbackData, prefix="BuyPoints"):
	status: "str"
	