import logging
import secrets
import re
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command, CommandStart
from aiogram.enums import ParseMode
from aiogram.types import Message
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

# --- Username helpers ---
def generate_short_username():
    """Generate a short, unique username like 'anon1234'."""
    return f"anon{secrets.randbelow(100000):05d}"

async def get_or_create_user(user_id):
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        # generate unique short username
        while True:
            short_username = generate_short_username()
            if not await db.users.find_one({"short_username": short_username}):
                break
        link_id = secrets.token_urlsafe(8)
        await db.users.insert_one({
            "user_id": user_id,
            "link_id": link_id,
            "short_username": short_username
        })
        return short_username
    return user.get("short_username") or user.get("link_id")

async def get_user_by_link_id(link_id):
    # Can be short_username or legacy link_id
    return await db.users.find_one({"$or": [{"short_username": link_id}, {"link_id": link_id}]})

def extract_ask_link_id(start_param):
    if start_param and start_param.startswith("ask_"):
        return start_param.split("ask_")[1]
    return None

# --- Handlers ---
@router.message(CommandStart(deep_link=True))
async def start_with_param(message: Message, command: CommandStart, state: FSMContext):
    link_id = extract_ask_link_id(command.args)
    if link_id:
        user = await get_user_by_link_id(link_id)
        if not user:
            await message.answer("Invalid or expired link.")
            return
        await state.update_data(target_link_id=link_id)
        await message.answer(
            "✉️ <b>Send your anonymous message to this user.</b>\n\n"
            "Just type and send your message now."
        )
    else:
        user_short_username = await get_or_create_user(message.from_user.id)
        bot_username = (await bot.me()).username
        link = f"https://t.me/{bot_username}?start=ask_{user_short_username}"
        await message.answer(
            f"👋 <b>Welcome to Ask Out!</b>\n\n"
            f"Your anonymous question link:\n<code>{link}</code>\n\n"
            "Anyone can send you anonymous messages via this link.\nShare it anywhere!"
        )

@router.message(CommandStart(deep_link=False))
async def start_no_param(message: Message, state: FSMContext):
    user_short_username = await get_or_create_user(message.from_user.id)
    bot_username = (await bot.me()).username
    link = f"https://t.me/{bot_username}?start=ask_{user_short_username}"
    await message.answer(
        f"👋 <b>Welcome to Ask Out!</b>\n\n"
        f"Your anonymous question link:\n<code>{link}</code>\n\n"
        "Anyone can send you anonymous messages via this link.\nShare it anywhere!"
    )
    await state.clear()

@router.message(Command("setusername"))
async def set_custom_username(message: Message):
    args = message.text.strip().split()
    if len(args) != 2:
        await message.answer("Usage: <b>/setusername yourname</b>\nAllowed: a-z, 0-9, 3-20 chars.")
        return
    new_username = args[1].lower()
    if not re.fullmatch(r"[a-z0-9_]{3,20}", new_username):
        await message.answer("❌ Invalid username. Use only a-z, 0-9, underscores, 3-20 chars.")
        return
    # Check if taken
    existing = await db.users.find_one({"short_username": new_username})
    if existing:
        if existing["user_id"] == message.from_user.id:
            await message.answer("You already have this username.")
        else:
            await message.answer("❌ This username is already taken. Try another.")
        return
    # Update or set
    await db.users.update_one(
        {"user_id": message.from_user.id},
        {"$set": {"short_username": new_username}},
        upsert=True
    )
    bot_username = (await bot.me()).username
    link = f"https://t.me/{bot_username}?start=ask_{new_username}"
    await message.answer(
        f"✅ Your custom username is set to <b>{new_username}</b>!\n"
        f"Your new link:\n<code>{link}</code>"
    )

@router.message(F.text)
async def handle_anonymous_message(message: Message, state: FSMContext):
    data = await state.get_data()
    target_link_id = data.get("target_link_id")
    if target_link_id:
        user = await get_user_by_link_id(target_link_id)
        if not user:
            await message.answer("User not found. Maybe their link expired?")
            return
        await bot.send_message(
            user["user_id"],
            f"📩 <b>You received an anonymous message:</b>\n\n{message.text}"
        )
        await message.answer("✅ Your anonymous message has been sent anonymously!")
        await state.clear()
    else:
        user_short_username = await get_or_create_user(message.from_user.id)
        bot_username = (await bot.me()).username
        link = f"https://t.me/{bot_username}?start=ask_{user_short_username}"
        await message.answer(
            f"👋 <b>Welcome to Ask Out!</b>\n\n"
            f"Your anonymous question link:\n<code>{link}</code>\n\n"
            "Anyone can send you anonymous messages via this link.\nShare it anywhere!"
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
