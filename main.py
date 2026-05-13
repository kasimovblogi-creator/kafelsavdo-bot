import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import (
    add_user,
    add_points,
    get_points,
    get_top_users,
    get_all_users
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

broadcast_mode = False

scheduler = AsyncIOScheduler()


def subscribe_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Gruppaga qo‘shilish",
                    url=f"https://t.me/{CHANNEL.replace('@', '')}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Tekshirish",
                    callback_data="check_sub",
                )
            ],
        ]
    )
    return keyboard


def menu_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⭐ Ballarim",
                    callback_data="my_points",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏆 TOP 5",
                    callback_data="top_users",
                )
            ]
        ]
    )
    return keyboard


async def check_subscription(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)

        if member.status in ["member", "administrator", "creator"]:
            return True

    except:
        return False

    return False


@dp.message(CommandStart(deep_link=True))
async def start_with_ref(message: Message, command):

    user_id = message.from_user.id
    username = message.from_user.username

    referrer_id = int(command.args)

    if user_id != referrer_id:

        new_user = add_user(
            user_id,
            username,
            referrer_id
        )

        if new_user:

            await bot.send_message(
                ADMIN_ID,
                f"👤 Yangi user referral orqali kirdi:\n\n"
                f"🆔 ID: {user_id}\n"
                f"👤 Username: @{username}\n"
                f"👥 Refer: {referrer_id}"
            )

            add_points(referrer_id, 5)

    is_subscribed = await check_subscription(user_id)

    if not is_subscribed:
        await message.answer(
            "❌ Avval gruppaga qo‘shiling.",
            reply_markup=subscribe_keyboard(),
        )
        return

    bot_info = await bot.get_me()

    referral_link = (
        f"https://t.me/{bot_info.username}"
        f"?start={user_id}"
    )

    points = get_points(user_id)

    await message.answer(
        f"✅ Xush kelibsiz!\n\n"
        f"👥 Referal linkingiz:\n{referral_link}\n\n"
        f"⭐ Ballingiz: {points}",
        reply_markup=menu_keyboard()
    )


@dp.message(CommandStart())
async def start_handler(message: Message):

    user_id = message.from_user.id
    username = message.from_user.username

    new_user = add_user(
        user_id,
        username
    )

    if new_user:

        await bot.send_message(
            ADMIN_ID,
            f"👤 Yangi user kirdi:\n\n"
            f"🆔 ID: {user_id}\n"
            f"👤 Username: @{username}"
        )

    is_subscribed = await check_subscription(user_id)

    if not is_subscribed:
        await message.answer(
            "❌ Avval gruppaga qo‘shiling.",
            reply_markup=subscribe_keyboard(),
        )
        return

    bot_info = await bot.get_me()

    referral_link = (
        f"https://t.me/{bot_info.username}"
        f"?start={user_id}"
    )

    points = get_points(user_id)

    await message.answer(
        f"✅ Xush kelibsiz!\n\n"
        f"👥 Referal linkingiz:\n{referral_link}\n\n"
        f"⭐ Ballingiz: {points}",
        reply_markup=menu_keyboard()
    )


@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):

    is_subscribed = await check_subscription(callback.from_user.id)

    if not is_subscribed:
        await callback.answer(
            "❌ Siz hali gruppaga qo‘shilmagansiz.",
            show_alert=True,
        )
        return

    await callback.message.answer(
        "✅ Obuna tasdiqlandi."
    )

    await callback.answer()


@dp.callback_query(F.data == "my_points")
async def my_points_callback(callback: CallbackQuery):

    points = get_points(callback.from_user.id)

    await callback.message.answer(
        f"⭐ Sizning ballaringiz: {points}"
    )

    await callback.answer()


@dp.callback_query(F.data == "top_users")
async def top_users_callback(callback: CallbackQuery):

    top_users = get_top_users()

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

    text = "🏆 TOP 5 Referralchilar:\n\n"

    for index, user in enumerate(top_users):

        username = user[0]
        points = user[1]

        if username:
            username_text = f"@{username}"
        else:
            username_text = "Username yo‘q"

        text += (
            f"{medals[index]} "
            f"{username_text} "
            f"— ⭐ {points} ball\n"
        )

    await callback.message.answer(text)

    await callback.answer()


@dp.message(Command("reklama"))
async def reklama_command(message: Message):

    global broadcast_mode

    if message.from_user.id != ADMIN_ID:
        return

    broadcast_mode = True

    await message.answer(
        "📢 Reklama xabarini yuboring."
    )


@dp.message()
async def broadcast_handler(message: Message):

    global broadcast_mode

    if not broadcast_mode:
        return

    if message.from_user.id != ADMIN_ID:
        return

    users = get_all_users()

    success = 0

    for user in users:

        user_id = user[0]

        try:
            await message.copy_to(user_id)
            success += 1

        except:
            pass

    broadcast_mode = False

    await message.answer(
        f"✅ Reklama yuborildi.\n\n"
        f"👥 Yuborildi: {success}"
    )


async def weekly_top():

    top_users = get_top_users()

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

    text = "🏆 Haftalik TOP Referralchilar:\n\n"

    for index, user in enumerate(top_users):

        username = user[0]
        points = user[1]

        if username:
            username_text = f"@{username}"
        else:
            username_text = "Username yo‘q"

        text += (
            f"{medals[index]} "
            f"{username_text} "
            f"— ⭐ {points} ball\n"
        )

    await bot.send_message(
        ADMIN_ID,
        text
    )


async def main():

    scheduler.add_job(
        weekly_top,
        trigger="cron",
        day_of_week="sun",
        hour=20,
        minute=0
    )

    scheduler.start()

    print("Bot ishga tushdi...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())