import os
import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InputFile
from datetime import datetime, timedelta
from dotenv import load_dotenv

# .env файлидан токенни юклаш
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")

# Бот ва диспетчерни яратиш
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Хотирада админ карталари ва фойдаланувчи рухсатлари
admin_cards = {}
user_access = {}

# /start буйруғи
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.reply(
        "👋 Пул Тўлов ботга хуш келибсиз!\n"
        "Бу бот орқали гуруҳга реклама бериш учун тўлов қилинг.\n\n"
        "/setcard - карта қўшиш\n"
        "/pay - тўлов скриншотини юбориш"
    )

# /setcard буйруғи: админ картани қўшади
@dp.message_handler(commands=['setcard'])
async def set_card(message: types.Message):
    if message.chat.type != "supergroup":
        await message.reply("❗ Бу буйруқни фақат гуруҳда ишлатинг.")
        return
    args = message.get_args()
    if not args:
        await message.reply("Илтимос, картани /setcard 1234xxxx... шаклида киритинг.")
        return
    admin_cards[message.chat.id] = {
        "admin_id": message.from_user.id,
        "card_number": args
    }
    await message.reply(f"💳 Карта сақланди: {args}")

# /pay буйруғи: фойдаланувчи скриншот юбориш
@dp.message_handler(commands=['pay'])
async def pay_handler(message: types.Message):
    if message.chat.type != "supergroup":
        await message.reply("❗ Бу буйруқни фақат гуруҳда ишлатинг.")
        return
    if message.reply_to_message and message.reply_to_message.photo:
        if message.chat.id in admin_cards:
            admin_id = admin_cards[message.chat.id]["admin_id"]
            file_id = message.reply_to_message.photo[-1].file_id
            await bot.send_photo(admin_id, file_id, caption=f"🧾 Янги тўлов скриншоти: @{message.from_user.username or message.from_user.id}")
            await message.reply("✅ Скриншот юборилди, админ тасдиғини кутиб туринг.")
        else:
            await message.reply("❌ Админ ҳали карта ўрнатмаган.")
    else:
        await message.reply("📸 Илтимос, расмга жавоб сифатида /pay буйруғини ёзинг.")

# /approve буйруғи: админ томонидан тасдиқлаш
@dp.message_handler(commands=['approve'])
async def approve_user(message: types.Message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        user_access[user_id] = datetime.now() + timedelta(days=30)
        await message.reply("✅ Фойдаланувчига 1 ойлик ҳуқуқ берилди.")
    else:
        await message.reply("⚠️ Илтимос, кимгадир жавоб қилиб /approve ёзинг.")

# Ҳар қандай хабарда фойдаланувчи рухсатини текшириш
@dp.message_handler()
async def check_access(message: types.Message):
    if message.chat.type == "supergroup":
        user_id = message.from_user.id
        if user_id in user_access:
            if datetime.now() > user_access[user_id]:
                del user_access[user_id]
                await message.reply("❌ Сизнинг 1 ойлик ҳуқуқингиз тугади.")
        else:
            await message.reply("⛔ Реклама бериш учун аввал тўлов қилинг ва тасдиқ кутиб туринг.")

# Ботни ишга тушириш
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)

