# Coffee Bot — Telegram-бот лояльности для кофейни

Бот для сети кофеен: регистрация по номеру телефона, бонусные баллы, оплата Telegram Stars, админ-панель для управления меню и пользователями.

## Стек
- Python 3, [aiogram 3](https://docs.aiogram.dev/) (async, FSM)
- aiosqlite — работа с БД
- Telegram Bot Payments API (Stars)

## Функционал

**Для пользователя:**
- Регистрация через шеринг номера телефона
- Меню товаров по категориям
- Профиль с балансом бонусных баллов
- Пополнение баллов через Telegram Stars
- История покупок

**Для админа:**
- Панель управления, доступная по `admin_id`
- Поиск пользователя по пересланному сообщению
- Начисление/списание бонусов
- Добавление, редактирование и удаление товаров меню
- Бан/разбан пользователей

## Архитектура

Модульная структура вместо монолита:


main.py            # точка входа, регистрация роутеров
config.py           # токен, admin_id, имена БД
bot_instance.py      # инициализация Bot/Dispatcher
database.py          # вся работа с aiosqlite
states.py            # FSM-состояния
callbacks.py          # CallbackData классы
handlers/
  user.py           # пользовательские сценарии
  menu.py            # меню и покупки
  admin_panel.py       # вход в админку
  admin_users.py       # управление пользователями
  admin_items.py       # управление товарами


## Настройка

1. Установи зависимости:
   
   pip install aiogram aiosqlite
   
2. Получи токен бота у [@BotFather](https://t.me/BotFather)
3. Открой `config.py` и укажи свои данные:
   
   token_bot = "твой_токен_от_BotFather"
   admin_id = 123456789  # твой Telegram ID (узнать у @userinfobot)
   file_name = "users.db"
   donate_file_name = "donates.db"
   
4. Запусти:
   
   python main.py

Базы `users.db` и `donates.db` создаются автоматически при первом запуске — вручную создавать не нужно.

## Автор

**zakonpop**
Telegram: @zakonpop (https://t.me/zakonpop)
