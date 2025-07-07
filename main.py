import logging
import secrets
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from motor.motor_asyncio import AsyncIOMotorClient

# === CONFIG ===
API_TOKEN = "8032679205:AAHFMO9t-T7Lavbbf_noiePQoniDSHzSuVA"
MONGODB_URL = "mongodb+srv://itxcriminal:qureshihashmI1@cluster0.jyqy9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "askout"

# === LOGGING ===
logging.basicConfig(level=logging.INFO)

# === BOT INITIALIZATION ===
bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# === MONGODB ===
client = AsyncIOMotorClient(MONGODB_URL)
db = client[DB_NAME]

# === UTILS ===
async def get_or_create_user(user_id):
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        link_id = secrets.token_urlsafe(8)
        await db.users.insert_one({
            "user_id": user_id,
            "link_id": link_id
        })
        return link_id
    return user["link_id"]

async def get_user_by_link_id(link_id):
    return await db.users.find_one({"link_id": link_id})

# === HANDLERS ===

@router.message(Command("start"))
async def start(message: Message):
    link_id = await get_or_create_user(message.from_user.id)
    bot_username = (await bot.me()).username
    link = f"https://t.me/{bot_username}?start=ask_{link_id}"
    await message.answer(
        f"👋 <b>Welcome to Ask Out!</b>\n\n"
        f"Share your anonymous question link:\n<code>{link}</code>\n\n"
        "Anyone can send you anonymous messages via this link.\n"
        "Share it anywhere!"
    )

@router.message(F.text.regexp(r"^/start ask_([a-zA-Z0-9_\-]+)$"))
async def ask_entry(message: Message, regexp_command):
    link_id = regexp_command.group(1)
    user = await get_user_by_link_id(link_id)
    if not user:
        await message.answer("Invalid or expired link.")
        return
    # Store in FSM context for this chat
    await message.chat.set_data({"target_link_id": link_id})
    await message.answer(
        f"Send your anonymous message to this user.\n\n"
        "Just type and send your message now."
    )

@router.message(F.text)
async def handle_anonymous_message(message: Message):
    chat_data = await message.chat.get_data()
    target_link_id = chat_data.get("target_link_id")
    if target_link_id:
        user = await get_user_by_link_id(target_link_id)
        if not user:
            await message.answer("User not found. Maybe their link expired?")
            return
        await bot.send_message(
            user["user_id"],
            f"📩 <b>You received an anonymous message:</b>\n\n{message.text}"
        )
        await message.answer("✅ Your anonymous message has been sent!")
        await message.chat.set_data({})
    else:
        await message.answer(
            "Welcome! Use /start to get your own anonymous question link, "
            "or open a user's link to send them a message."
        )

# === MAIN ===
if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
