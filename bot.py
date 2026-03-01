import asyncio
import os
import aiosqlite
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
import datetime

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")  # токен бота из Railway Variables
ADMIN_ID = 888130657
GUIDE_VIDEO_ID = "BAACAgQAAxkBAAPnaaS872U2tN15_9jt7TgqdSjgGxAAAoUfAAKS3SFRGpJEBZ9eT9o6BA"
WELCOME_PHOTO_ID = "AgACAgQAAxkBAANNaaDF6KIxz_YX9YnABXs791Ls940AAusMaxubCghRJC2sUOfksW4BAAMCAAN4AAM6BA"

# Premium Emoji IDs
DIAMOND_ID = "5471952986970267163"            # AligatorGameShop
GUIDE_EMOJI_ID = "5467596412663372909"       # Qo'llanma
BACK_MENU_EMOJI_ID = "5264727218734524899"  # Asosiy Menu
ADMIN_BUTTON_EMOJI_ID = "5431449001532594346" # Adminga yozish
NEWS_CHANNEL_EMOJI_ID = "5436153923457009904" # MLBB yangiliklar kanali
# ==========================================

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ================= DATABASE =================
async def init_db():
    async with aiosqlite.connect("users.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_join TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS button_clicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                button_name TEXT,
                click_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def add_user(user_id: int):
    async with aiosqlite.connect("users.db") as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        await db.commit()

async def get_all_users():
    async with aiosqlite.connect("users.db") as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            return await cursor.fetchall()

async def log_button_click(user_id: int, button_name: str):
    async with aiosqlite.connect("users.db") as db:
        await db.execute(
            "INSERT INTO button_clicks (user_id, button_name) VALUES (?, ?)",
            (user_id, button_name)
        )
        await db.commit()

# ================= STATES =================
class BroadcastState(StatesGroup):
    waiting_for_content = State()
    waiting_for_button_text = State()
    waiting_for_button_link = State()
    confirm = State()

class GetFileState(StatesGroup):
    waiting_for_file = State()

# ================= KEYBOARDS =================
def main_keyboard(user_id: int):
    is_admin = user_id == ADMIN_ID
    keyboard = [
        [
            InlineKeyboardButton(
                text="AligatorGameShop",
                web_app=WebAppInfo(url="https://aligatorgameshop.com"),
                icon_custom_emoji_id=DIAMOND_ID
            )
        ],
        [
            InlineKeyboardButton(
                text=f"Qo'llanma",
                callback_data="guide",
                icon_custom_emoji_id=GUIDE_EMOJI_ID
            ),
            InlineKeyboardButton(
                text="📢 Telegram Kanalimiz",
                url="https://t.me/aligatorgameshop"
            )
        ],
        [
            InlineKeyboardButton(
                text="MLBB yangiliklar kanali",
                url="https://t.me/mobilelegendsuznews",
                icon_custom_emoji_id=NEWS_CHANNEL_EMOJI_ID
            ),
            InlineKeyboardButton(
                text="Adminga yozish",
                url="https://t.me/MobileLegendsDiamondUz",
                icon_custom_emoji_id=ADMIN_BUTTON_EMOJI_ID
            )
        ]
    ]
    if is_admin:
        keyboard.append(
            [InlineKeyboardButton(text="🛠 Admin Panel", callback_data="admin_panel")]
        )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="broadcast")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")]
    ])

# ================= START =================
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await add_user(message.from_user.id)

    caption = (
        f"Assalomu aleykum {str(message.from_user.full_name)} 👋\n\n"
        "Ushbu bot orqali bizning xizmatlarimizdan to'g'ridan to'g'ri telegram orqali "
        "kirib foydalanishingiz mumkin ✅.\n\n"
        "Botimizga xush kelibsiz, bizni tanlaganingiz uchun raxmat 🤝"
    )

    await message.answer_photo(
        photo=WELCOME_PHOTO_ID,
        caption=caption,
        reply_markup=main_keyboard(message.from_user.id)
    )

# ================= GUIDE HANDLER =================
@dp.callback_query(F.data == "guide")
async def send_guide(callback: types.CallbackQuery):
    await log_button_click(callback.from_user.id, "Qo'llanma")

    guide_text = (
        "✨Ushbu videoda bizning saytimizdan qanday foydalanish kerakligi ko'rsatilgan "
        "agar savollaringiz bo'lsa yoki qiyinchiliklarga duch kelsangiz @MobileLegendsDiamondUz ga murojaat qiling✊."
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="AligatorGameShop",
                    web_app=WebAppInfo(url="https://aligatorgameshop.com"),
                    icon_custom_emoji_id=DIAMOND_ID
                )
            ],
            [
                InlineKeyboardButton(
                    text="Asosiy Menu",
                    callback_data="main_menu",
                    icon_custom_emoji_id=BACK_MENU_EMOJI_ID
                )
            ]
        ]
    )

    await callback.message.answer_video(
        video=GUIDE_VIDEO_ID,
        caption=guide_text,
        reply_markup=keyboard
    )
    await callback.answer()

# ================= "Asosiy Menu" =================
@dp.callback_query(F.data == "main_menu")
async def go_to_main_menu(callback: types.CallbackQuery):
    caption = (
        f"Assalomu aleykum {str(callback.from_user.full_name)} 👋\n\n"
        "Ushbu bot orqali bizning xizmatlarimizdan to'g'ridan to'g'ri telegram orqali "
        "kirib foydalanishingiz mumkin ✅.\n\n"
        "Botimizga xush kelibsiz, bizni tanlaganingiz uchun raxmat 🤝"
    )

    await callback.message.answer_photo(
        photo=WELCOME_PHOTO_ID,
        caption=caption,
        reply_markup=main_keyboard(callback.from_user.id)
    )
    await callback.answer()

# ================= ADMIN PANEL =================
@dp.callback_query(F.data == "admin_panel")
async def admin_panel(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещён")
        return
    await callback.message.answer(
        "🛠 Админ панель",
        reply_markup=admin_keyboard()
    )

# ================= BROADCAST =================
@dp.callback_query(F.data == "broadcast")
async def start_broadcast(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await state.set_state(BroadcastState.waiting_for_content)
    await callback.message.answer(
        "Выберите тип рассылки и отправьте сообщение:\n"
        "1️⃣ Текст → просто отправь сообщение\n"
        "2️⃣ Фото → отправь фото с подписью\n"
        "3️⃣ Видео → отправь видео с подписью"
    )

@dp.message(BroadcastState.waiting_for_content)
async def get_content(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    if message.photo:
        content_type = "photo"
        content_id = message.photo[-1].file_id
        caption = message.caption or ""
    elif message.video:
        content_type = "video"
        content_id = message.video.file_id
        caption = message.caption or ""
    elif message.text:
        content_type = "text"
        content_id = message.text
        caption = None
    else:
        await message.answer("❌ Неверный формат. Отправьте текст, фото или видео.")
        return

    await state.update_data(
        content_type=content_type,
        content_id=content_id,
        caption=caption
    )
    await state.set_state(BroadcastState.waiting_for_button_text)
    await message.answer(
        "Введите текст кнопки.\nЕсли кнопка не нужна — отправьте: -"
    )

@dp.message(BroadcastState.waiting_for_button_text)
async def get_button_text(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    if message.text == "-":
        await state.update_data(button_text=None)
        await preview_broadcast(message, state)
        return
    await state.update_data(button_text=message.text)
    await state.set_state(BroadcastState.waiting_for_button_link)
    await message.answer(
        "Введите ссылку для кнопки.\nМожно вставить обычную ссылку (https://…) или Mini App URL"
    )

@dp.message(BroadcastState.waiting_for_button_link)
async def get_button_link(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.update_data(button_link=message.text)
    await preview_broadcast(message, state)

async def preview_broadcast(message: types.Message, state: FSMContext):
    data = await state.get_data()
    keyboard = None
    if data.get("button_text"):
        if "http" in data["button_link"]:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text=data["button_text"], url=data["button_link"])]]
            )
        else:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text=data["button_text"], web_app=WebAppInfo(url=data["button_link"]))]]
            )

    confirm_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_broadcast"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_broadcast")
            ]
        ]
    )

    await message.answer("🔍 Предварительный просмотр:")
    if data["content_type"] == "photo":
        await message.answer_photo(photo=data["content_id"], caption=data["caption"], reply_markup=keyboard)
    elif data["content_type"] == "video":
        await message.answer_video(video=data["content_id"], caption=data["caption"], reply_markup=keyboard)
    else:
        await message.answer(text=data["content_id"], reply_markup=keyboard)

    await message.answer("Отправить эту рассылку?", reply_markup=confirm_keyboard)
    await state.set_state(BroadcastState.confirm)

@dp.callback_query(F.data == "cancel_broadcast")
async def cancel_broadcast(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("❌ Рассылка отменена.")

@dp.callback_query(F.data == "confirm_broadcast")
async def confirm_broadcast(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    data = await state.get_data()
    users = await get_all_users()
    count = 0

    keyboard = None
    if data.get("button_text"):
        if "http" in data["button_link"]:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text=data["button_text"], url=data["button_link"])]]
            )
        else:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text=data["button_text"], web_app=WebAppInfo(url=data["button_link"]))]]
            )

    for user in users:
        try:
            if data["content_type"] == "photo":
                await bot.send_photo(chat_id=user[0], photo=data["content_id"], caption=data["caption"], reply_markup=keyboard)
            elif data["content_type"] == "video":
                await bot.send_video(chat_id=user[0], video=data["content_id"], caption=data["caption"], reply_markup=keyboard)
            else:
                await bot.send_message(chat_id=user[0], text=data["content_id"], reply_markup=keyboard)
            count += 1
            await asyncio.sleep(0.05)  # антиспам
        except:
            pass

    await callback.message.answer(f"✅ Рассылка завершена.\nОтправлено: {count}")
    await state.clear()

# ================= UNIVERSAL GET FILE_ID =================
@dp.message(Command("getvideoid"))
async def start_get_file(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.set_state(GetFileState.waiting_for_file)
    await message.reply("📤 Пожалуйста, отправьте фото, видео или документ, чтобы получить file_id.")

@dp.message(GetFileState.waiting_for_file)
async def handle_file(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    if message.photo:
        file_id = message.photo[-1].file_id
        await message.reply(f"✅ File ID вашего фото:\n`{file_id}`", parse_mode="Markdown")
    elif message.video:
        file_id = message.video.file_id
        await message.reply(f"✅ File ID вашего видео:\n`{file_id}`", parse_mode="Markdown")
    elif message.document:
        file_id = message.document.file_id
        await message.reply(f"✅ File ID вашего документа:\n`{file_id}`", parse_mode="Markdown")
    else:
        await message.reply("❌ Это не фото, видео или документ. Пожалуйста, отправьте подходящий файл.")
        return

    await state.clear()

# ================= STATISTICS =================
async def get_stats(period: str = "day"):
    now = datetime.datetime.now()
    if period == "day":
        start_time = now.strftime("%Y-%m-%d 00:00:00")
    elif period == "month":
        start_time = now.strftime("%Y-%m-01 00:00:00")
    else:
        start_time = "1970-01-01 00:00:00"

    async with aiosqlite.connect("users.db") as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            total_users = (await cursor.fetchone())[0]

        async with db.execute(
            "SELECT button_name, COUNT(*) FROM button_clicks WHERE click_time >= ? GROUP BY button_name",
            (start_time,)
        ) as cursor:
            button_stats = await cursor.fetchall()

        async with db.execute(
            "SELECT COUNT(DISTINCT user_id) FROM button_clicks WHERE click_time >= ?",
            (start_time,)
        ) as cursor:
            active_users = (await cursor.fetchone())[0]

    return {
        "total_users": total_users,
        "active_users": active_users,
        "button_stats": button_stats
    }

@dp.callback_query(F.data == "stats")
async def show_stats(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещён")
        return

    stats = await get_stats("day")

    text = f"📊 Статистика бота:\n\n" \
           f"Всего пользователей: {stats['total_users']}\n" \
           f"Активных сегодня: {stats['active_users']}\n\n" \
           f"Нажатия кнопок:\n"

    for btn_name, count in stats["button_stats"]:
        text += f"- {btn_name}: {count}\n"

    await callback.message.answer(text)

# ================= RUN =================
async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
