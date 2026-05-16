import asyncio
import logging
import os
import sqlite3

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
# DATABASE
# =========================

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    points INTEGER DEFAULT 0
)
""")

conn.commit()

# =========================
# BOT
# =========================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

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
# DATABASE FUNCTIONS
# =========================

def add_user(user_id, username):

    cursor.execute(
        "SELECT * FROM users WHERE user_id = ?",
        (user_id,)
    )

    user = cursor.fetchone()

    if not user:
        cursor.execute(
            "INSERT INTO users (user_id, username, points) VALUES (?, ?, ?)",
            (user_id, username, 0)
        )
        conn.commit()


def add_points(user_id, points):

    cursor.execute(
        "UPDATE users SET points = points + ? WHERE user_id = ?",
        (points, user_id)
    )

    conn.commit()


def get_points(user_id):

    cursor.execute(
        "SELECT points FROM users WHERE user_id = ?",
        (user_id,)
    )

    result = cursor.fetchone()

    if result:
        return result[0]

    return 0


def get_top_users():

    cursor.execute("""
    SELECT username, points
    FROM users
    ORDER BY points DESC
    LIMIT 5
    """)

    return cursor.fetchall()

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
        print(e)
        return False

# =========================
# START REFERRAL
# =========================

@dp.message(CommandStart(deep_link=True))
async def start_ref(message: Message, command):

    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"

    add_user(user_id, username)

    try:
        referrer_id = int(command.args)
    except:
        referrer_id = None

    if referrer_id and referrer_id != user_id:

        add_points(referrer_id, 5)

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

    points = get_points(user_id)

    await message.answer(
        f"🎉 Referral tizimiga xush kelibsiz!\n\n"
        f"🔗 Sizning referral linkingiz:\n"
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

    add_user(user_id, username)

    cursor.execute("SELECT COUNT(*) FROM users")

    total_users = cursor.fetchone()[0]

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

    points = get_points(user_id)

    await message.answer(
        f"🎉 Xush kelibsiz!\n\n"
        f"🔗 Sizning referral linkingiz:\n"
        f"{referral_link}\n\n"
        f"⭐ Ballaringiz: {points}",
        reply_markup=menu_keyboard()
    )

# =========================
# CHECK SUB
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

    points = get_points(callback.from_user.id)

    await callback.message.answer(
        f"⭐ Sizning ballaringiz: {points}"
    )

    await callback.answer()

# =========================
# TOP USERS
# =========================

@dp.callback_query(F.data == "top_users")
async def top_users(callback: CallbackQuery):

    top = get_top_users()

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

    text = "🏆 TOP Referralchilar:\n\n"

    if not top:
        text += "Hozircha userlar yo‘q"

    for index, user in enumerate(top):

        username = user[0]
        points = user[1]

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

    await bot.delete_webhook(
        drop_pending_updates=True
    )

    await dp.start_polling(bot)

# =========================
# RUN
# =========================

if __name__ == "__main__":
    asyncio.run(main())