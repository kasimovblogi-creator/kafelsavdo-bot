
import asyncio
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

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

users = {}
points_db = {}


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


async def check_subscription(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)

        if member.status in [
            "member",
            "administrator",
            "creator"
        ]:
            return True

    except:
        return False

    return False


@dp.message(CommandStart(deep_link=True))
async def start_ref(message: Message, command):

    user_id = message.from_user.id
    username = message.from_user.username

    try:
        referrer_id = int(command.args)
    except:
        referrer_id = None

    users[user_id] = username

    if referrer_id and user_id != referrer_id:

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
        f"https://t.me/"
        f"{bot_info.username}?start={user_id}"
    )

    points = points_db.get(user_id, 0)

    await message.answer(
        f"🎉 Aksiyada ishtirok etib sovg‘aga ega bo‘ling!\n\n"
        f"📢 Quyidagi maxsus linkingiz orqali "
        f"yaqinlaringizni botga taklif qiling va "
        f"har bir a’zo uchun 5 ball qo‘lga kiriting.\n\n"
        f"🏆 Eng ko‘p ball to‘plagan "
        f"ishtirokchi sovg‘a egasiga aylanadi!\n\n"
        f"🔗 Sizning maxsus linkingiz:\n"
        f"{referral_link}\n\n"
        f"⭐ Jami ballaringiz: {points}",
        reply_markup=menu_keyboard()
    )


@dp.message(CommandStart())
async def start_handler(message: Message):

    user_id = message.from_user.id
    username = message.from_user.username

    users[user_id] = username

    total_users = len(users)

    await bot.send_message(
        ADMIN_ID,
        f"👤 Yangi user kirdi!\n\n"
        f"🆔 ID: {user_id}\n"
        f"👤 Username: @{username}\n\n"
        f"📊 Jami foydalanuvchilar: {total_users}"
    )

    is_subscribed = await check_subscription(user_id)

    if not is_subscribed:
        await message.answer(
            "❌ Avval kanalga qo‘shiling.",
            reply_markup=subscribe_keyboard()
        )
        return

    bot_info = await bot.get_me()

    referral_link = (
        f"https://t.me/"
        f"{bot_info.username}?start={user_id}"
    )

    points = points_db.get(user_id, 0)

    await message.answer(
        f"🎉 Aksiyada ishtirok etib sovg‘aga ega bo‘ling!\n\n"
        f"📢 Quyidagi maxsus linkingiz orqali "
        f"yaqinlaringizni botga taklif qiling va "
        f"har bir a’zo uchun 5 ball qo‘lga kiriting.\n\n"
        f"🏆 Eng ko‘p ball to‘plagan "
        f"ishtirokchi sovg‘a egasiga aylanadi!\n\n"
        f"🔗 Sizning maxsus linkingiz:\n"
        f"{referral_link}\n\n"
        f"⭐ Jami ballaringiz: {points}",
        reply_markup=menu_keyboard()
    )


@dp.callback_query(F.data == "check_sub")
async def check_sub(callback: CallbackQuery):

    is_subscribed = await check_subscription(
        callback.from_user.id
    )

    if not is_subscribed:
        await callback.answer(
            "❌ Siz hali kanalga qo‘shilmagansiz.",
            show_alert=True
        )
        return

    await callback.message.answer(
        "✅ Obuna tasdiqlandi."
    )

    await callback.answer()


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


@dp.callback_query(F.data == "top_users")
async def top_users(callback: CallbackQuery):

    sorted_users = sorted(
        points_db.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    medals = [
        "🥇",
        "🥈",
        "🥉",
        "4️⃣",
        "5️⃣"
    ]

    text = "🏆 TOP Referralchilar:\n\n"

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


@dp.message()
async def delete_service_messages(message: Message):

    if (
        message.new_chat_members
        or message.left_chat_member
    ):
        await message.delete()


async def main():

    print("Bot ishga tushdi ✅")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
```
