import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
from aiogram.enums import ChatType
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.markdown import hbold
from aiogram.client.session.aiohttp import AiohttpSession

load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")

# Storage & Bot setup
storage = MemoryStorage()
session = AiohttpSession()
bot = Bot(token=API_TOKEN, session=session)
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# Ma'lumotlar
admin_cards = {}  # group_id -> {'admin_id': int, 'card_number': str}
user_access = {}  # user_id -> expiry_date (datetime)

# /start
@router.message(F.text.startswith("/start"))
async def start_handler(message: Message):
    await message.answer(
        "👋 Пул Тўлов ботга хуш келибсиз!\n"
        "Бу бот орқали гуруҳга реклама бериш учун тўлов қилинг.\n\n"
        "/setcard - карта қўшиш\n"
        "/pay - тўлов скриншотини юбориш"
    )

# /setcard
@router.message(F.text.startswith("/setcard"))
async def set_card(message: Message):
    if message.chat.type != ChatType.SUPERGROUP:
        await message.reply("Бу буйруқни фақат гуруҳда ишлатинг.")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Карта рақамини ҳам ёзинг. Масалан: /setcard 8600...")
        return
    admin_cards[message.chat.id] = {
        "admin_id": message.from_user.id,
        "card_number": args[1]
    }
    await message.reply(f"💳 Карта сақланди: {args[1]}")

# /pay
@router.message(F.text.startswith("/pay"))
async def pay_handler(message: Message):
    if message.chat.type != ChatType.SUPERGROUP:
        await message.reply("Бу буйруқни фақат гуруҳда ишлатинг.")
        return
    if message.reply_to_message and message.reply_to_message.photo:
        admin_data = admin_cards.get(message.chat.id)
        if admin_data:
            file_id = message.reply_to_message.photo[-1].file_id
            caption = f"🧾 Янги тўлов скриншоти @{message.from_user.username or message.from_user.full_name}"
            await bot.send_photo(admin_data["admin_id"], file_id, caption=caption)
            await message.reply("✅ Скриншот юборилди, админ тасдиғини кутиб туринг.")
        else:
            await message.reply("❌ Админ ҳали карта ўрнатмаган.")
    else:
        await message.reply("Илтимос, скриншотни расмга жавоб сифатида юборинг.")

# /approve
@router.message(F.text.startswith("/approve"))
async def approve_user(message: Message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        user_access[user_id] = datetime.now() + timedelta(days=30)
        await message.reply("✅ Фойдаланувчига 1 ойлик ҳуқуқ берилди.")
    else:
        await message.reply("Кимгадир жавоб қилиб /approve ёзинг.")

# Foydalanuvchi xabarлари
@router.message()
async def check_access(message: Message):
    if message.chat.type == ChatType.SUPERGROUP:
        expiry = user_access.get(message.from_user.id)
        if expiry:
            if datetime.now() > expiry:
                del user_access[message.from_user.id]
                await message.reply("❌ Сизнинг 1 ойлик муҳлатиңиз тугади.")
        else:
            await message.reply("⛔ Реклама бериш учун админга тўлов қилинг.")

# Ishga tushirish
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())


