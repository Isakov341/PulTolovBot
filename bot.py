async def check_subscription(user_id, group_id):
    if user_id in users_db and group_id in users_db[user_id]['groups']:
        del users_db[user_id]['groups'][group_id]
        
        await bot.restrict_chat_member(
            group_id, user_id,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_polls=False,
                can_send_other_messages=False
            )
        )
        
        try:
            await bot.send_message(
                user_id,
                "❌ Сизнинг обунангиз тугади! Яна харид қилиш учун тугмани босинг:",
                reply_markup=payment_keyboard(group_id)
            )
        except:
            pass
if __name__ == '__main__':
    scheduler.start()
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
