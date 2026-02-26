import asyncio
import os
import aiosqlite
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")  # токен бота из Railway Variables
ADMIN_ID = 888130657  # <-- Вставь сюда свой числовой Telegram ID
GUIDE_VIDEO_ID = "BAACAgQAAxkBAAMjaaC_slYqu3k9Z7CzphdkF8SLClEAAp4eAAKbCghRF0U1Yj2NUrw6BA"  # <-- File ID видео для Qo'llanma
WELCOME_PHOTO_ID = "PUT_WELCOME_PHOTO_FILE_ID_HERE"  # <-- File ID фото для приветствия
# ==========================================

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ================= DATABASE =================
async def init_db():
    async with aiosqlite.connect("users.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY
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

# ================= STATES =================
class BroadcastState(StatesGroup):
    waiting_for_content = State()
    waiting_for_button_text = State()
    waiting_for_button_link = State()
    confirm = State()

# ================= KEYBOARDS =================
def main_keyboard(user_id: int):
    is_admin = user_id == ADMIN_ID
    keyboard = [
        [
            InlineKeyboardButton(
                text="🛒 AligatorGameShop",
                web_app=WebAppInfo(url="https://aligatorgameshop.com")
            )
        ],
        [
            InlineKeyboardButton(
                text="Qo'llanma ❓",
                callback_data="guide"
            ),
            InlineKeyboardButton(
                text="📢 Telegram Kanalimiz",
                url="https://t.me/aligatorgameshop"
            )
        ],
        [
            InlineKeyboardButton(
                text="👤 Admin",
                url="https://t.me/MobileLegendsDiamondUz"
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
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="broadcast")]
    ])

# ================= START =================
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await add_user(message.from_user.id)
    is_admin = message.from_user.id == ADMIN_ID

    # Персонализированное приветствие
    caption = (
        f"Assalomu aleykum {message.from_user.full_name} 👋\n\n"
        "Ushbu bot orqali bizning xizmatlarimizdan to'g'ridan to'g'ri telegram orqali kirib foydalanishingiz mumkin ✅.\n\n"
        "Botimizga xush kelibsiz, bizni tanlaganingiz uchun raxmat 🤝"
    )

    await message.answer_photo(
        photo=WELCOME_PHOTO_ID,
        caption=caption,
        reply_markup=main_keyboard(message.from_user.id)
    )

# ================= GUIDE =================
@dp.callback_query(F.data == "guide")
async def send_guide(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛒 Открыть магазин",
                    web_app=WebAppInfo(url="https://aligatorgameshop.com")
                )
            ]
        ]
    )
    # Отправляем видео с кнопкой, кнопки не пропадают
    await callback.message.answer_video(
        video=GUIDE_VIDEO_ID,
        caption="📖 Qo'llanma\n\nBu videoda qanday buyurtma qilish ko‘rsatilgan.",
        reply_markup=keyboard
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
async def get_file_id(message: types.Message):
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

# ================= RUN =================
async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
