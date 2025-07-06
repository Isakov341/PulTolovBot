import logging
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.exceptions import ChatAdminRequired
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    raise ValueError("BOT_TOKEN .env faylga o‘rnatilmagan!")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

admin_cards = {}
user_access = {}

@dp.message_handler(commands=['setcard'])
async def set_card(message: types.Message):
    if message.chat.type != "supergroup":
        return await message.reply("Bu buyruq faqat guruhda ishlaydi.")
    admins = await bot.get_chat_administrators(message.chat.id)
    if message.from_user.id not in [adm.user.id for adm in admins]:
        return await message.reply("Faqat adminlar kartani o'rnata oladi.")
    args = message.text.split()
    if len(args) != 2:
        return await message.reply("Foydalanish: /setcard 8600xxxx")
    admin_cards.setdefault(message.chat.id, {})[message.from_user.id] = args[1]
    await message.reply(f"✅ Karta raqam o'rnatildi: {args[1]}")

@dp.message_handler(content_types=types.ContentType.PHOTO)
async def payment_screenshot(message: types.Message):
    if message.chat.type != "private":
        return
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Guruhga yuborish", callback_data="send_to_admins")
    )
    await message.reply("✅ To'lov tasvir qabul qilindi. Qaysi guruhga yuboraylik?", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'send_to_admins')
async def send_screenshot(callback: types.CallbackQuery):
    user = callback.from_user
    sent = False
    for chat_id, admins in admin_cards.items():
        for admin_id in admins:
            try:
                await bot.send_photo(
                    admin_id,
                    callback.message.photo[-1].file_id,
                    caption=f"🧾 @{user.username or user.full_name} tomonidan to‘lov"
                )
                sent = True
            except Exception:
                pass
    await callback.message.reply("✅ Adminlarga yuborildi" if sent else "❌ Adminlar topilmadi")

@dp.message_handler(commands=['tasdiqlash'])
async def approve_user(message: types.Message):
    if message.chat.type != "supergroup":
        return
    admins = await bot.get_chat_administrators(message.chat.id)
    if message.from_user.id not in [adm.user.id for adm in admins]:
        return await message.reply("Faqat adminlar tasdiqlashi mumkin")
    args = message.text.split()
    if len(args) != 2 or not args[1].startswith("@"):
        return await message.reply("Foydalanish: /tasdiqlash @username")
    username = args[1][1:]
    members = await bot.get_chat_members(message.chat.id)
    user_id = next((m.user.id for m in members if m.user.username == username), None)
    if not user_id:
        return await message.reply("Foydalanuvchi topilmadi")
    expire = datetime.now() + timedelta(days=30)
    user_access.setdefault(message.chat.id, {})[user_id] = expire
    try:
        await bot.restrict_chat_member(
            message.chat.id, user_id,
            permissions=types.ChatPermissions(can_send_messages=True)
        )
    except ChatAdminRequired:
        return await message.reply("Botni guruhda admin qiling!")
    await message.reply(f"✅ @{username} 1 oyga ruxsat oldi")

async def check_expired():
    now = datetime.now()
    for chat_id, ulist in list(user_access.items()):
        for user_id, exp in list(ulist.items()):
            if exp < now:
                try:
                    await bot.restrict_chat_member(
                        chat_id, user_id,
                        permissions=types.ChatPermissions(can_send_messages=False)
                    )
                    del user_access[chat_id][user_id]
                except:
                    pass

scheduler.add_job(check_expired, 'interval', minutes=10)

async def on_startup(_):
    scheduler.start()
    logging.info("Bot ishga tushdi va schedulerni boshladi")

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, on_startup=on_startup)
