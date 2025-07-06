
import os
import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InputFile
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Memory storage
admin_cards = {}
user_access = {}

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.reply("👋 Пул Тўлов ботга хуш келибсиз!
/setcard - карта қўшиш
/pay - тўлов скриншотини юбориш")

@dp.message_handler(commands=['setcard'])
async def set_card(message: types.Message):
    if message.chat.type != "supergroup":
        await message.reply("Бу буйруқни фақат гуруҳда ишлатинг.")
        return
    admin_cards[message.chat.id] = {
        "admin_id": message.from_user.id,
        "card_number": message.get_args()
    }
    await message.reply(f"💳 Карта сақланди: {message.get_args()}")

@dp.message_handler(commands=['pay'])
async def pay_handler(message: types.Message):
    if message.chat.type != "supergroup":
        await message.reply("Бу буйруқни фақат гуруҳда ишлатинг.")
        return
    if message.reply_to_message and message.reply_to_message.photo:
        if message.chat.id in admin_cards:
            admin_id = admin_cards[message.chat.id]["admin_id"]
            file_id = message.reply_to_message.photo[-1].file_id
            await bot.send_photo(admin_id, file_id, caption=f"🧾 Янги тўлов скриншоти @{message.from_user.username}")
            await message.reply("✅ Скриншот юборилди, админ тасдиғини кутиб туринг.")
        else:
            await message.reply("❌ Админ ҳали карта ўрнатмаган.")
    else:
        await message.reply("Илтимос, скриншотни расмга жавоб сифатида юборинг.")

@dp.message_handler(commands=['approve'])
async def approve_user(message: types.Message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        user_access[user_id] = datetime.now() + timedelta(days=30)
        await message.reply("✅ Фойдаланувчига 1 ойлик ҳуқуқ берилди.")
    else:
        await message.reply("Кимгадир жавоб қилиб /approve ёзинг.")

@dp.message_handler()
async def check_access(message: types.Message):
    if message.chat.type == "supergroup":
        if message.from_user.id in user_access:
            if datetime.now() > user_access[message.from_user.id]:
                del user_access[message.from_user.id]
                await message.reply("❌ Сизнинг 1 ойлик муҳлатиңиз тугади.")
        else:
            await message.reply("⛔ Реклама бериш учун админга тўлов қилинг.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
