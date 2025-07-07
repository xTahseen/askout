import logging
import secrets
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import CommandStart
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

def extract_ask_link_id(start_param):
    if start_param and start_param.startswith("ask_"):
        return start_param.split("ask_")[1]
    return None

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
        user_link_id = await get_or_create_user(message.from_user.id)
        bot_username = (await bot.me()).username
        link = f"https://t.me/{bot_username}?start=ask_{user_link_id}"
        await message.answer(
            f"👋 <b>Welcome to Ask Out!</b>\n\n"
            f"Share your anonymous question link:\n<code>{link}</code>\n\n"
            "Anyone can send you anonymous messages via this link.\nShare it anywhere!"
        )

@router.message(CommandStart(deep_link=False))
async def start_no_param(message: Message, state: FSMContext):
    user_link_id = await get_or_create_user(message.from_user.id)
    bot_username = (await bot.me()).username
    link = f"https://t.me/{bot_username}?start=ask_{user_link_id}"
    await message.answer(
        f"👋 <b>Welcome to Ask Out!</b>\n\n"
        f"Share your anonymous question link:\n<code>{link}</code>\n\n"
        "Anyone can send you anonymous messages via this link.\nShare it anywhere!"
    )
    await state.clear()

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
        user_link_id = await get_or_create_user(message.from_user.id)
        bot_username = (await bot.me()).username
        link = f"https://t.me/{bot_username}?start=ask_{user_link_id}"
        await message.answer(
            f"👋 <b>Welcome to Ask Out!</b>\n\n"
            f"Share your anonymous question link:\n<code>{link}</code>\n\n"
            "Anyone can send you anonymous messages via this link.\nShare it anywhere!"
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
