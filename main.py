import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from dotenv import load_dotenv

# =========================
# ENV
# =========================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# =========================
# LOGGING
# =========================

logging.basicConfig(level=logging.INFO)

# =========================
# BOT
# =========================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =========================
# DATABASE
# =========================

users = {}
points_db = {}

# =========================
# KEYBOARDS
# =========================

def subscribe_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Kanalga qo‘shilish",
                    url=f"https://t.me/{CHANNEL.replace('@', '')}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Tekshirish",
                    callback_data="check_sub"
                )
            ]
        ]
    )


def menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⭐ Ballarim",
                    callback_data="my_points"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏆 TOP",
                    callback_data="top_users"
                )
            ]
        ]
    )

# =========================
# CHECK SUB
# =========================

async def check_subscription(user_id):

    try:
        member = await bot.get_chat_member(
            chat_id=CHANNEL,
            user_id=user_id
        )

        return member.status in [
            "member",
            "administrator",
            "creator"
        ]

    except Exception as e:
        print(f"Subscription error: {e}")
        return False

# =========================
# START WITH REF
# =========================

@dp.message(CommandStart(deep_link=True))
async def start_ref(message: Message, command):

    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"

    users[user_id] = username

    try:
        referrer_id = int(command.args)
    except:
        referrer_id = None

    if referrer_id and referrer_id != user_id:

        if referrer_id not in points_db:
            points_db[referrer_id] = 0

        points_db[referrer_id] += 5

    is_subscribed = await check_subscription(user_id)

    if not is_subscribed:
        await message.answer(
            "❌ Avval kanalga qo‘shiling.",
            reply_markup=subscribe_keyboard()
        )
        return

    bot_info = await bot.get_me()

    referral_link = (
        f"https://t.me/{bot_info.username}?start={user_id}"
    )

    points = points_db.get(user_id, 0)

    await message.answer(
        f"🎉 Aksiyada ishtirok etib sovg‘aga ega bo‘ling!\n\n"
        f"📢 Quyidagi linkingiz orqali "
        f"yaqinlaringizni taklif qiling.\n\n"
        f"👥 Har bir odam uchun: 5 ball\n"
        f"🏆 Eng ko‘p ball yig‘gan odam sovg‘a oladi.\n\n"
        f"🔗 Sizning linkingiz:\n"
        f"{referral_link}\n\n"
        f"⭐ Ballaringiz: {points}",
        reply_markup=menu_keyboard()
    )

# =========================
# NORMAL START
# =========================

@dp.message(CommandStart())
async def start_handler(message: Message):

    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"

    users[user_id] = username

    total_users = len(users)

    try:
        await bot.send_message(
            ADMIN_ID,
            f"👤 Yangi foydalanuvchi\n\n"
            f"🆔 ID: {user_id}\n"
            f"👤 Username: @{username}\n\n"
            f"📊 Jami users: {total_users}"
        )
    except:
        pass

    is_subscribed = await check_subscription(user_id)

    if not is_subscribed:
        await message.answer(
            "❌ Avval kanalga qo‘shiling.",
            reply_markup=subscribe_keyboard()
        )
        return

    bot_info = await bot.get_me()

    referral_link = (
        f"https://t.me/{bot_info.username}?start={user_id}"
    )

    points = points_db.get(user_id, 0)

    await message.answer(
        f"🎉 Aksiyada ishtirok eting!\n\n"
        f"🔗 Sizning referral linkingiz:\n"
        f"{referral_link}\n\n"
        f"⭐ Ballaringiz: {points}",
        reply_markup=menu_keyboard()
    )

# =========================
# CHECK BUTTON
# =========================

@dp.callback_query(F.data == "check_sub")
async def check_sub(callback: CallbackQuery):

    is_subscribed = await check_subscription(
        callback.from_user.id
    )

    if not is_subscribed:
        await callback.answer(
            "❌ Siz hali kanalga qo‘shilmagansiz",
            show_alert=True
        )
        return

    await callback.message.answer(
        "✅ Obuna tasdiqlandi"
    )

    await callback.answer()

# =========================
# MY POINTS
# =========================

@dp.callback_query(F.data == "my_points")
async def my_points(callback: CallbackQuery):

    points = points_db.get(
        callback.from_user.id,
        0
    )

    await callback.message.answer(
        f"⭐ Sizning ballaringiz: {points}"
    )

    await callback.answer()

# =========================
# TOP USERS
# =========================

@dp.callback_query(F.data == "top_users")
async def top_users(callback: CallbackQuery):

    sorted_users = sorted(
        points_db.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

    text = "🏆 TOP referralchilar:\n\n"

    if not sorted_users:
        text += "Hozircha userlar yo‘q"

    for index, user in enumerate(sorted_users):

        user_id = user[0]
        points = user[1]

        username = users.get(
            user_id,
            "NoName"
        )

        text += (
            f"{medals[index]} "
            f"@{username} "
            f"— ⭐ {points} ball\n"
        )

    await callback.message.answer(text)

    await callback.answer()

# =========================
# DELETE SERVICE MSG
# =========================

@dp.message()
async def delete_service_messages(message: Message):

    try:
        if (
            message.new_chat_members
            or message.left_chat_member
        ):
            await message.delete()

    except:
        pass

# =========================
# MAIN
# =========================

async def main():

    print("✅ Bot ishga tushdi")

    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(bot)

# =========================
# START
# =========================

if __name__ == "__main__":
    asyncio.run(main())