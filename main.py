import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

@dp.message(Command("eslat"))
async def set_reminder(message: types.Message):
    # Buyruq formati: /eslat 14:30 Dasturlashni mashq qilish
    try:
        args = message.text.split(maxsplit=2)
        time_str = args[1]  # Masalan: "14:30"
        text = args[2]      # Eslatma matni

        # Hozirgi vaqt va belgilangan vaqtni hisoblash
        now = datetime.now()
        target_time = datetime.strptime(time_str, "%H:%M").replace(
            year=now.year, month=now.month, day=now.day
        )

        # Agar belgilangan vaqt o'tib ketgan bo'lsa, ertangi kunga o'tkaziladi
        if target_time < now:
            target_time = target_time.replace(day=now.day + 1)

        wait_seconds = (target_time - now).total_seconds()

        await message.answer(f"⏳ **Eslatma oʻrnatildi!**\nSoat **{time_str}** da sizga xabar yuboraman.")

        # Belgilangan vaqtgacha kutish
        await asyncio.sleep(wait_seconds)

        # Vaqt bo'lganda yuboriladigan xabar
        await message.answer(f"🔔 **ESLATMA!**\n\n📌 *{text}*")

    except (IndexError, ValueError):
        await message.answer(
            "⚠️ **Toʻgʻri formatda kiriting:**\n"
            "`/eslat HH:MM [eslatma matni]`\n\n"
            "**Misol:** `/eslat 18:30 Mini App o'yinini tekshirish`"
        )
