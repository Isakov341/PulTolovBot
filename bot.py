import logging
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.exceptions import ChatAdminRequired
from apscheduler.schedulers.asyncio import AsyncIOScheduler

API_TOKEN = os.getenv("BOT_TOKEN")  # Render.com uchun
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

logging.basicConfig(level=logging.INFO)

# Adminlar kartalari va foydalanuvchi ma'lumotlari
admin_cards = {}  # {chat_id: {admin_id: card_number}}
user_access = {}  # {chat_id: {user_id: expire_date}}


# Guruh admini kartani o'rnatadi
@dp.message_handler(commands=['setcard'])
async def set_card(message: types.Message):
    if message.chat.type != "supergroup":
        return await message.reply("Bu buyruq faqat guruhda ishlaydi.")

    if not message.from_user.id in [admin.user.id async for admin in await bot.get_chat_administrators(message.chat.id)]:
        return await message.reply("Faqat adminlar kartani o'rnata oladi.")

    args = message.text.split()
    if len(args) != 2:
        return await message.reply("Foydalanish: /setcard 8600xxxx")

    card = args[1]
    admin_cards.setdefault(message.chat.id, {})[message.from_user.id] = card
    await message.reply(f"✅ Karta raqam o'rnatildi: {card}")


# Foydalanuvchi screenshot yuboradi
@dp.message_handler(content_types=types.ContentType.PHOTO)
async def payment_screenshot(message: types.Message):
    if message.chat.type != "private":
        return

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Guruhga yuborish", callback_data="send_to_admins")
    )
    await message.reply("✅ To'lov tasvir qabul qilindi. Qaysi guruhga yuboraylik?", reply_markup=keyboard)


# Screenshotni guruh adminiga yuborish
@dp.callback_query_handler(lambda c: c.data == 'send_to_admins')
async def send_screenshot_to_admins(callback: types.CallbackQuery):
    user = callback.from_user
    sent = False
    for chat_id, admins in admin_cards.items():
        for admin_id, card in admins.items():
            try:
                await bot.send_photo(
                    admin_id,
                    callback.message.photo[-1].file_id,
                    caption=f"🧾 @{user.username} tomonidan to'lov tasviri"
                )
                sent = True
            except:
                pass
    if sent:
        await callback.message.reply("✅ Adminlarga yuborildi")
    else:
        await callback.message.reply("❌ Adminlar topilmadi")


# Admin foydalanuvchiga ruxsat beradi
@dp.message_handler(commands=['tasdiqlash'])
async def approve_user(message: types.Message):
    if message.chat.type != "supergroup":
        return

    if not message.from_user.id in [admin.user.id async for admin in await bot.get_chat_administrators(message.chat.id)]:
        return await message.reply("Faqat adminlar tasdiqlashi mumkin")

    args = message.text.split()
    if len(args) != 2:
        return await message.reply("Foydalanish: /tasdiqlash @username")

    username = args[1].lstrip("@")
    members = await bot.get_chat_members(message.chat.id)
    user_id = None
    for m in members:
        if m.user.username == username:
            user_id = m.user.id
            break

    if not user_id:
        return await message.reply("Foydalanuvchi topilmadi")

    expire = datetime.now() + timedelta(days=30)
    user_access.setdefault(message.chat.id, {})[user_id] = expire

    try:
        await bot.restrict_chat_member(
            message.chat.id,
            user_id,
            permissions=types.ChatPermissions(can_send_messages=True)
        )
    except ChatAdminRequired:
        await message.reply("Botni admin qiling")
        return

    await message.reply(f"✅ @{username} 1 oyga ruxsat oldi")


# 1 oydan keyin ruxsatni olib tashlash
async def check_expired():
    now = datetime.now()
    for chat_id in list(user_access.keys()):
        for user_id, expire in list(user_access[chat_id].items()):
            if expire < now:
                try:
                    await bot.restrict_chat_member(
                        chat_id,
                        user_id,
                        permissions=types.ChatPermissions(can_send_messages=False)
                    )
                    del user_access[chat_id][user_id]
                except:
                    pass

scheduler.add_job(check_expired, 'interval', minutes=10)


async def on_startup(_):
    scheduler.start()

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)




