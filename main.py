import logging
import secrets
import re
from datetime import datetime
from aiogram import Bot, Dispatcher, Router, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from motor.motor_asyncio import AsyncIOMotorClient

API_TOKEN = "8032679205:AAHFMO9t-T7Lavbbf_noiePQoniDSHzSuVA"
MONGODB_URL = "mongodb+srv://itxcriminal:qureshihashmI1@cluster0.jyqy9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "askout"

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

client = AsyncIOMotorClient(MONGODB_URL)
db = client[DB_NAME]

# --- Translation dictionary ---
TRANSLATIONS = {
    "en": {
        "welcome": "👋 <b>Welcome to Ask Out!</b>\n\nYour anonymous question link:\n<code>{link}</code>\n\nAnyone can send you anonymous messages via this link.\nShare it anywhere!",
        "share_btn": "🔗 Share your link",
        "send_anon": "✉️ <b>Send your anonymous message to this user.</b>\n\nJust type and send your message now.",
        "msg_sent": "✅ Your anonymous message has been sent anonymously!",
        "invalid_link": "Invalid or expired link.",
        "not_registered": "You are not registered yet. Use /start to get your anonymous link.",
        "username_usage": "Usage: <b>/setusername yourname</b>\nAllowed: a-z, 0-9, 3-20 chars.",
        "username_invalid": "❌ Invalid username. Use only a-z, 0-9, underscores, 3-20 chars.",
        "username_taken": "❌ This username is already taken. Try another.",
        "username_set": "✅ Your custom username is set to <b>{username}</b>!\nYour new link:\n<code>{link}</code>",
        "already_username": "You already have this username.",
        "stats": "📊 <b>Your Stats</b>\n\n<b>Messages received:</b> <code>{msgs}</code>\n<b>Messages received today:</b> <code>{msgs_today}</code>\n\n<b>Link clicks:</b> <code>{clicks}</code>\n<b>Link clicks today:</b> <code>{clicks_today}</code>",
        "lang_usage": "Usage: /language <code>\nExample: /language en or /language ur",
        "lang_set": "✅ Language set to {lang_name}.",
        "lang_not_supported": "❌ Language not supported. Available: {langs}"
    },
    "ur": {
        "welcome": "👋 <b>خوش آمدید! یہ آپ کا اینانیمس سوال کا لنک ہے:</b>\n<code>{link}</code>\n\nاب کوئی بھی آپ کو گمنام پیغام بھیج سکتا ہے۔ اس کو کہیں بھی شیئر کریں!",
        "share_btn": "🔗 اپنا لنک شیئر کریں",
        "send_anon": "✉️ <b>اس صارف کو اپنا گمنام پیغام بھیجیں۔</b>\n\nبس اپنا پیغام لکھ کر بھیج دیں۔",
        "msg_sent": "✅ آپ کا گمنام پیغام بھیج دیا گیا ہے!",
        "invalid_link": "غلط یا ختم شدہ لنک۔",
        "not_registered": "آپ رجسٹرڈ نہیں ہیں۔ /start استعمال کریں۔",
        "username_usage": "استعمال: <b>/setusername آپکانام</b>\nصرف a-z، 0-9، 3-20 حروف استعمال کریں۔",
        "username_invalid": "❌ غلط یوزر نیم۔ صرف a-z، 0-9، انڈر اسکور، 3-20 حروف۔",
        "username_taken": "❌ یہ یوزر نیم پہلے سے موجود ہے۔ نیا کوشش کریں۔",
        "username_set": "✅ آپکا یوزر نیم <b>{username}</b> سیٹ ہو گیا!\nآپکا نیا لنک:\n<code>{link}</code>",
        "already_username": "آپکا یوزر نیم پہلے سے یہی ہے۔",
        "stats": "📊 <b>آپکے اعداد و شمار</b>\n\n<b>موصول شدہ پیغامات:</b> <code>{msgs}</code>\n<b>آج موصولہ پیغامات:</b> <code>{msgs_today}</code>\n\n<b>لنک کلکس:</b> <code>{clicks}</code>\n<b>آج کے لنک کلکس:</b> <code>{clicks_today}</code>",
        "lang_usage": "استعمال: /language <code>\nمثال: /language en یا /language ur",
        "lang_set": "✅ زبان تبدیل ہو گئی: {lang_name}",
        "lang_not_supported": "❌ یہ زبان دستیاب نہیں۔ دستیاب زبانیں: {langs}"
    }
}
LANG_NAMES = {'en': 'English', 'ur': 'اردو'}

def t(user, key, **kwargs):
    lang = user.get("language", "en") if user else "en"
    msg = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, TRANSLATIONS["en"][key])
    return msg.format(**kwargs)

def generate_short_username():
    return f"anon{secrets.randbelow(100000):05d}"

def today_str():
    return datetime.utcnow().strftime("%Y-%m-%d")

async def get_or_create_user(user_id):
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        while True:
            short_username = generate_short_username()
            if not await db.users.find_one({"short_username": short_username}):
                break
        link_id = secrets.token_urlsafe(8)
        user = {
            "user_id": user_id,
            "link_id": link_id,
            "short_username": short_username,
            "messages_received": 0,
            "link_clicks": 0,
            "messages_received_daily": {},
            "link_clicks_daily": {},
            "language": "en"
        }
        await db.users.insert_one(user)
    return user.get("short_username") or user.get("link_id")

async def get_user_by_link_id(link_id):
    return await db.users.find_one({"$or": [{"short_username": link_id}, {"link_id": link_id}]})

def extract_link_id(start_param):
    return start_param if start_param else None

def get_share_keyboard(link, user, short_username):
    btn = InlineKeyboardButton(
        text=t(user, "share_btn"),
        switch_inline_query=f"Ask me anything! It's anonymous: {link}"
    )
    return InlineKeyboardMarkup(inline_keyboard=[[btn]])

@router.message(CommandStart(deep_link=True))
async def start_with_param(message: Message, command: CommandStart, state: FSMContext):
    link_id = extract_link_id(command.args)
    user = await db.users.find_one({"user_id": message.from_user.id})
    if link_id:
        target_user = await get_user_by_link_id(link_id)
        if not target_user:
            await message.answer(t(user, "invalid_link"))
            return
        if target_user["user_id"] != message.from_user.id:
            today = today_str()
            await db.users.update_one(
                {"user_id": target_user["user_id"]},
                {
                    "$inc": {"link_clicks": 1},
                    "$set": {f"link_clicks_daily.{today}": (target_user.get("link_clicks_daily", {}).get(today, 0) + 1)}
                }
            )
        await state.update_data(target_link_id=link_id)
        await message.answer(t(user, "send_anon"))
    else:
        user_short_username = await get_or_create_user(message.from_user.id)
        user = await db.users.find_one({"user_id": message.from_user.id})
        bot_username = (await bot.me()).username
        link = f"https://t.me/{bot_username}?start={user_short_username}"
        await message.answer(
            t(user, "welcome", link=link),
            reply_markup=get_share_keyboard(link, user, user_short_username)
        )

@router.message(CommandStart(deep_link=False))
async def start_no_param(message: Message, state: FSMContext):
    user_short_username = await get_or_create_user(message.from_user.id)
    user = await db.users.find_one({"user_id": message.from_user.id})
    bot_username = (await bot.me()).username
    link = f"https://t.me/{bot_username}?start={user_short_username}"
    await message.answer(
        t(user, "welcome", link=link),
        reply_markup=get_share_keyboard(link, user, user_short_username)
    )
    await state.clear()

@router.message(Command("setusername"))
async def set_custom_username(message: Message):
    user = await db.users.find_one({"user_id": message.from_user.id})
    args = message.text.strip().split()
    if len(args) != 2:
        await message.answer(t(user, "username_usage"))
        return
    new_username = args[1].lower()
    if not re.fullmatch(r"[a-z0-9_]{3,20}", new_username):
        await message.answer(t(user, "username_invalid"))
        return
    existing = await db.users.find_one({"short_username": new_username})
    if existing:
        if existing["user_id"] == message.from_user.id:
            await message.answer(t(user, "already_username"))
        else:
            await message.answer(t(user, "username_taken"))
        return
    await db.users.update_one(
        {"user_id": message.from_user.id},
        {"$set": {"short_username": new_username}},
        upsert=True
    )
    bot_username = (await bot.me()).username
    link = f"https://t.me/{bot_username}?start={new_username}"
    await message.answer(
        t(user, "username_set", username=new_username, link=link),
        reply_markup=get_share_keyboard(link, user, new_username)
    )

@router.message(Command("stats"))
async def stats_command(message: Message):
    user = await db.users.find_one({"user_id": message.from_user.id})
    if not user:
        await message.answer(t(user, "not_registered"))
        return
    today = today_str()
    messages_received = user.get("messages_received", 0)
    link_clicks = user.get("link_clicks", 0)
    messages_received_daily = user.get("messages_received_daily", {})
    link_clicks_daily = user.get("link_clicks_daily", {})
    messages_today = messages_received_daily.get(today, 0)
    clicks_today = link_clicks_daily.get(today, 0)
    await message.answer(
        t(user, "stats",
          msgs=messages_received,
          msgs_today=messages_today,
          clicks=link_clicks,
          clicks_today=clicks_today)
    )

@router.message(Command("language"))
async def language_command(message: Message):
    args = message.text.strip().split()
    user = await db.users.find_one({"user_id": message.from_user.id})
    if len(args) != 2:
        await message.answer(t(user, "lang_usage"))
        return
    lang = args[1].lower()
    if lang not in TRANSLATIONS:
        langs = ", ".join([f"<code>{code}</code>" for code in TRANSLATIONS])
        await message.answer(t(user, "lang_not_supported", langs=langs))
        return
    await db.users.update_one(
        {"user_id": message.from_user.id},
        {"$set": {"language": lang}},
        upsert=True
    )
    await message.answer(t({"language": lang}, "lang_set", lang_name=LANG_NAMES[lang]))

@router.message(F.text)
async def handle_anonymous_message(message: Message, state: FSMContext):
    data = await state.get_data()
    user = await db.users.find_one({"user_id": message.from_user.id})
    target_link_id = data.get("target_link_id")
    if target_link_id:
        target_user = await get_user_by_link_id(target_link_id)
        if not target_user:
            await message.answer(t(user, "invalid_link"))
            return
        await bot.send_message(
            target_user["user_id"],
            t(target_user, "msg_sent") + "\n\n" + message.text
        )
        today = today_str()
        await db.users.update_one(
            {"user_id": target_user["user_id"]},
            {
                "$inc": {"messages_received": 1},
                "$set": {f"messages_received_daily.{today}": (target_user.get("messages_received_daily", {}).get(today, 0) + 1)}
            }
        )
        await message.answer(t(user, "msg_sent"))
        await state.clear()
    else:
        user_short_username = await get_or_create_user(message.from_user.id)
        user = await db.users.find_one({"user_id": message.from_user.id})
        bot_username = (await bot.me()).username
        link = f"https://t.me/{bot_username}?start={user_short_username}"
        await message.answer(
            t(user, "welcome", link=link),
            reply_markup=get_share_keyboard(link, user, user_short_username)
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
