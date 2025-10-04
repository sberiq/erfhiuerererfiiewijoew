import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "ТОКЕН_БОТА"  # 🔹 вставь свой токен
bot = Bot(token=TOKEN)
dp = Dispatcher()


# === /start ===
@dp.message(F.text == "/start")
async def start(message: types.Message):
    await message.answer(
        "👋 Привет! Чтобы очистить подписчиков в канале:\n\n"
        "1️⃣ Добавь меня админом в канал (с правом удалять участников)\n"
        "2️⃣ Пришли сюда ID или @username канала (например: @mychannel)\n\n"
        "После этого я покажу меню очистки."
    )


# === Принимаем ID или username канала ===
@dp.message(F.text.startswith("@") | F.text.isdigit())
async def get_channel(message: types.Message):
    channel_id = message.text.strip()
    try:
        chat = await bot.get_chat(channel_id)
        member = await bot.get_chat_member(chat.id, bot.id)
        if member.status not in ("administrator", "creator"):
            await message.answer("❌ Я не админ в этом канале. Добавь меня с правами администратора.")
            return
    except Exception as e:
        await message.answer(f"❌ Ошибка: не удалось получить доступ к каналу.\n{e}")
        return

    kb = InlineKeyboardBuilder()
    for n in [100, 500, 1000]:
        kb.button(text=f"Удалить {n}", callback_data=f"clean_{chat.id}_{n}")
    await message.answer(
        f"✅ Канал найден: <b>{chat.title}</b>\nВыбери, сколько подписчиков удалить:",
        parse_mode="HTML",
        reply_markup=kb.as_markup()
    )


# === Очистка подписчиков ===
@dp.callback_query(F.data.startswith("clean_"))
async def clean(callback: types.CallbackQuery):
    _, channel_id, number = callback.data.split("_")
    channel_id = int(channel_id)
    number = int(number)
    count = 0

    await callback.message.edit_text(f"🧹 Начинаю удаление {number} подписчиков...")

    try:
        async for member in bot.get_chat_members(channel_id):
            if member.status in ("left", "kicked"):
                continue
            try:
                await bot.ban_chat_member(channel_id, member.user.id)
                await bot.unban_chat_member(channel_id, member.user.id)
                count += 1
                if count >= number:
                    break
            except Exception:
                continue
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка при очистке:\n{e}")
        return

    await callback.message.edit_text(f"✅ Удалено {count} подписчиков.")


async def main():
    print("✅ Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
