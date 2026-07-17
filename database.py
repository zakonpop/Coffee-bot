import aiosqlite
from datetime import datetime, timezone
from typing import Any
from config import file_name, donate_file_name


async def init_donate_db():
  async with aiosqlite.connect(donate_file_name) as db:
    await db.execute('''
      CREATE TABLE IF NOT EXISTS donate(
        user_id INTEGER DEFAULT 0,
        number TEXT,
        donate TEXT,
        amount TEXT
      )
    ''')
    await db.commit()

async def add_donat(user_id, num, donate, amount):
  	async with aiosqlite.connect(donate_file_name) as db:
  	  await db.execute('INSERT INTO donate (user_id, number, donate, amount) VALUES (?,?,?,?)', (user_id,num, donate, amount))
  	  await db.commit()

async def init_db():
	async with aiosqlite.connect(file_name) as db:
		await db.execute('''
			CREATE TABLE IF NOT EXISTS users(
				id INTEGER PRIMARY KEY,
				number TEXT,
				points INTEGER DEFAULT 0,
				admin INTEGER DEFAULT 0 CHECK(admin IN (0, 1)),
				banned INTEGER DEFAULT 0 CHECK(banned IN (0, 1)),
				date TEXT,
				time TEXT
			)
		''')
		await db.commit()



async def get_user(user_id:int):
	async with aiosqlite.connect(file_name) as db:
		db.row_factory = aiosqlite.Row
		async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
			user = await cursor.fetchone()
		if user:
			return dict(user)
		return {}

async def create_user(num, user_id):
	async with aiosqlite.connect(file_name) as db:
		now = datetime.now(timezone.utc)
		date_now = now.strftime("%Y-%m-%d")
		time_now = now.strftime("%H:%M")
		await db.execute('INSERT INTO users (id, number, points, admin, banned, date, time) VALUES (?,?,?,?,?,?,?)', (user_id,num, 0, 0, 0, date_now, time_now))
		await db.commit()
	return {
		"id": user_id,
		"number": num,
		"points": 0,
		"admin": 0,
		"banned": 0,
		"date": date_now,
		"time": time_now
	}




async def get_update_field(user_id, field: str, value: Any):
	async with aiosqlite.connect(file_name) as db:
		await db.execute(f"UPDATE users SET {field} = ? WHERE id = ?", (value, user_id))
		await db.commit()


async def init_eats():
	async with aiosqlite.connect(file_name) as db:
		await db.execute('''
			CREATE TABLE IF NOT EXISTS eats(
				category TEXT,
				name TEXT,
				price REAL DEFAULT 0,
				info TEXT
			)
		''')
		await db.commit()


async def get_item(name_eat):
	async with aiosqlite.connect(file_name) as db:
		db.row_factory = aiosqlite.Row
		async with db.execute("SELECT * FROM eats WHERE name = ?", (name_eat,)) as cursor:
			eat = await cursor.fetchone()
		if eat:
			return dict(eat)
		return {}


async def eat_exists(name_eat: str) -> bool:
	async with aiosqlite.connect(file_name) as db:
		async with db.execute("SELECT 1 FROM eats WHERE name = ?", (name_eat,)) as cursor:
			return await cursor.fetchone() is not None

async def get_update_field_item(name, field: str, value: Any):
	async with aiosqlite.connect(file_name) as db:
		await db.execute(f"UPDATE eats SET {field} = ? WHERE name = ?", (value, name))
		await db.commit()



async def get_categories() -> list[str]:
	async with aiosqlite.connect(file_name) as db:
		async with db.execute("SELECT DISTINCT category FROM eats") as cursor:
			rows = await cursor.fetchall()
			return [row[0] for row in rows]


async def get_item_by_cat(cat: str) -> list[dict]:
	async with aiosqlite.connect(file_name) as db:
		db.row_factory = aiosqlite.Row
		async with db.execute("SELECT * FROM eats WHERE category = ?", (cat,)) as cursor:
			rows = await cursor.fetchall()
			return [dict(row) for row in rows]

async def init_purchases():
	async with aiosqlite.connect(file_name) as db:
		await db.execute('''
			CREATE TABLE IF NOT EXISTS purchases(
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				user_id INTEGER,
				item_name TEXT,
				price REAL,
				date TEXT,
				time TEXT
			)
		''')
		await db.commit()
 