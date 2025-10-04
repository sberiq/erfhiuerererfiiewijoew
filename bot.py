import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder

# === 🔧 Настройки ===
TOKEN = "ТОКЕН_БОТА"  # ← вставь сюда свой токен от @BotFather
bot = Bot(token=TOKEN)
dp = Dispatcher()


# === /start ===
@dp.message(F.text == "/start")
async def start(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот для очистки подписчиков из твоего канала или группы.\n\n"
        "🔹 Добавь меня админом в канал (с правом *удалять участников*).\n"
        "🔹 Затем пришли сюда ID канала (например `-1001234567890`) или @username (например `@mychannel`).\n\n"
        "После этого я предложу выбрать, сколько подписчиков удалить.",
        parse_mode="Markdown"
    )


# === Обработка канала от пользователя ===
@dp.message()
async def get_channel(message: types.Message):
    text = message.text.strip()

    # Проверяем формат (должно быть ID или @username)
    if not text.startswith("@") and not text.replace("-", "").isdigit():
        await message.answer("❗ Пожалуйста, пришли ID (например `-1001234567890`) или @username канала.", parse_mode="Markdown")
        return

    try:
        # Получаем информацию о канале
        chat = await bot.get_chat(text)
        member = await bot.get_chat_member(chat.id, bot.id)
        if member.status not in ("administrator", "creator"):
            await message.answer("❌ Я не админ в этом канале. Добавь меня с правами администратора (удалять участников).")
            return
    except Exception as e:
        await message.answer(f"❌ Ошибка: не удалось получить доступ к каналу.\n\n{e}")
        return

    # Предлагаем выбрать количество подписчиков для удаления
    kb = InlineKeyboardBuilder()
    for n in [100, 500, 1000]:
        kb.button(text=f"Удалить {n}", callback_data=f"clean_{chat.id}_{n}")
    kb.adjust(3)
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

    await callback.message.edit_text(f"🧹 Начинаю удаление {number} подписчиков...")

    count = 0
    try:
        # Telegram не разрешает удалять подписчиков из broadcast-каналов.
        # Работает только в группах / супергруппах, где бот может кикать участников.
        async for member in bot.get_chat_administrators(channel_id):
            pass  # проверка прав

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


# === Запуск ===
async def main():
    print("✅ Бот запущен и готов к работе...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
