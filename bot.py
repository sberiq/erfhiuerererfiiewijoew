import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "ТОКЕН_БОТА"  # 🔹 замени на токен, выданный BotFather

bot = Bot(token=TOKEN)
dp = Dispatcher()


# === Команда /start ===
@dp.message(F.text == "/start")
async def start(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="Очистить подписчиков", callback_data="choose_channel")
    await message.answer(
        "👋 Привет! Добавь меня администратором в свой канал (с правом удалять пользователей), "
        "а затем нажми кнопку ниже, чтобы выбрать канал и удалить подписчиков.",
        reply_markup=kb.as_markup()
    )


# === Выбор канала ===
@dp.callback_query(F.data == "choose_channel")
async def choose_channel(callback: types.CallbackQuery):
    channels = []
    async for dialog in bot.get_dialogs():
        if dialog.chat.type in ["channel", "supergroup"]:
            try:
                member = await bot.get_chat_member(dialog.chat.id, bot.id)
                if member.status in ["administrator", "creator"]:
                    channels.append(dialog.chat)
            except Exception:
                continue

    if not channels:
        await callback.message.edit_text(
            "❌ Я не администратор ни в одном канале.\n\nДобавь меня в свой канал с правом *Удалять участников* и попробуй снова.",
            parse_mode="Markdown"
        )
        return

    kb = InlineKeyboardBuilder()
    for ch in channels:
        kb.button(text=ch.title, callback_data=f"channel_{ch.id}")
    await callback.message.edit_text("📢 Выбери канал:", reply_markup=kb.as_markup())


# === Выбор количества подписчиков ===
@dp.callback_query(F.data.startswith("channel_"))
async def select_amount(callback: types.CallbackQuery):
    channel_id = int(callback.data.split("_")[1])
    kb = InlineKeyboardBuilder()
    for n in [100, 500, 1000]:
        kb.button(text=f"Удалить {n}", callback_data=f"clean_{channel_id}_{n}")
    kb.button(text="Отмена", callback_data="cancel")
    await callback.message.edit_text(
        f"Выбран канал:\n<b>{(await bot.get_chat(channel_id)).title}</b>\n\nСколько подписчиков удалить?",
        parse_mode="HTML",
        reply_markup=kb.as_markup()
    )


# === Отмена ===
@dp.callback_query(F.data == "cancel")
async def cancel(callback: types.CallbackQuery):
    await callback.message.edit_text("❎ Отменено.")


# === Очистка ===
@dp.callback_query(F.data.startswith("clean_"))
async def clean(callback: types.CallbackQuery):
    _, channel_id, number = callback.data.split("_")
    channel_id = int(channel_id)
    number = int(number)

    await callback.message.edit_text(f"🧹 Начинаю удаление {number} подписчиков из канала...")

    count = 0
    try:
        async for member in bot.get_chat_administrators(channel_id):
            pass
    except Exception:
        await callback.message.edit_text("❌ Ошибка: я не админ в этом канале.")
        return

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

    await callback.message.edit_text(f"✅ Удалено {count} подписчиков.")


async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
