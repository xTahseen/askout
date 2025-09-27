from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext

class NewsletterStates(StatesGroup):
    waiting_for_content = State()
    waiting_for_caption = State()
    waiting_for_buttons = State()
    confirm = State()

def get_buttons_markup(buttons):
    if not buttons:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=btn["text"], url=btn["url"])] for btn in buttons
        ]
    )

def step_keyboard(prev_step=False, next_step=False, confirm=False):
    row = []
    if prev_step:
        row.append(InlineKeyboardButton(text="⬅️ Previous", callback_data="newsletter_prev"))
    if next_step:
        row.append(InlineKeyboardButton(text="➡️ Next", callback_data="newsletter_next"))
    if confirm:
        row.append(InlineKeyboardButton(text="✅ Confirm & Send", callback_data="newsletter_confirm"))
    row.append(InlineKeyboardButton(text="❌ Cancel", callback_data="newsletter_cancel"))
    return InlineKeyboardMarkup(inline_keyboard=[row])

def button_add_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add Button", callback_data="newsletter_addbtn")],
        [InlineKeyboardButton(text="➡️ Next", callback_data="newsletter_next")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="newsletter_cancel")]
    ])

# ====== HANDLER HELPERS TO USE IN MAIN.PY ======

async def ask_for_content(message: Message, state: FSMContext):
    await message.answer(
        "📰 <b>Newsletter Mode</b>\nSend the content of your newsletter:\n\n"
        "- Send a text message _or_\n"
        "- Send a photo, video, or document.",
        parse_mode="HTML"
    )
    await state.set_state(NewsletterStates.waiting_for_content)

async def handle_waiting_for_content(message: Message, state: FSMContext):
    # Text
    if message.text:
        await state.update_data(text=message.text, media=None, caption=None, buttons=[])
        await ask_for_buttons(message, state)
        return
    # Media (photo/video/document)
    if message.photo or message.video or message.document:
        media_type = None
        file_id = None
        if message.photo:
            media_type = "photo"
            file_id = message.photo[-1].file_id
        elif message.video:
            media_type = "video"
            file_id = message.video.file_id
        elif message.document:
            media_type = "document"
            file_id = message.document.file_id
        await state.update_data(media={"type": media_type, "file_id": file_id}, text=None, caption=None, buttons=[])
        await ask_for_caption(message, state)
        return
    await message.answer("❌ Only text, photo, video, or document are supported. Please send again.")

async def ask_for_caption(message: Message, state: FSMContext):
    await message.answer("Please send a caption for your media (or send - to skip):")
    await state.set_state(NewsletterStates.waiting_for_caption)

async def handle_waiting_for_caption(message: Message, state: FSMContext):
    caption = message.text if message.text != "-" else ""
    await state.update_data(caption=caption)
    await ask_for_buttons(message, state)

async def ask_for_buttons(message: Message, state: FSMContext):
    await message.answer(
        "Would you like to add buttons?\nSend buttons in the format:\n<code>Button Text - https://example.com</code>\n"
        "Send one per message, or click ➡️ Next to continue.",
        parse_mode="HTML",
        reply_markup=button_add_keyboard()
    )
    await state.set_state(NewsletterStates.waiting_for_buttons)

async def handle_waiting_for_buttons(message: Message, state: FSMContext):
    data = await state.get_data()
    buttons = data.get("buttons", [])
    # Parse button: "Text - URL"
    parts = message.text.split(" - ", 1)
    if len(parts) == 2 and parts[1].startswith("http"):
        buttons.append({"text": parts[0].strip(), "url": parts[1].strip()})
        await state.update_data(buttons=buttons)
        await message.answer(f"Button added: <b>{parts[0]}</b>", parse_mode="HTML")
    else:
        await message.answer("❌ Invalid button format. Use: <code>Button Text - https://example.com</code>", parse_mode="HTML")

async def preview_newsletter(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    media = data.get("media")
    text = data.get("text")
    caption = data.get("caption")
    buttons = data.get("buttons", [])
    markup = get_buttons_markup(buttons) if buttons else None
    # Compose preview
    if media:
        try:
            if media["type"] == "photo":
                await message.answer_photo(
                    photo=media["file_id"],
                    caption=caption or "",
                    reply_markup=markup
                )
            elif media["type"] == "video":
                await message.answer_video(
                    video=media["file_id"],
                    caption=caption or "",
                    reply_markup=markup
                )
            elif media["type"] == "document":
                await message.answer_document(
                    document=media["file_id"],
                    caption=caption or "",
                    reply_markup=markup
                )
        except Exception as e:
            await message.answer("❌ Failed to preview media: " + str(e))
            return
    elif text:
        await message.answer(text, reply_markup=markup)
    await message.answer(
        "⬆️ This is a preview of your newsletter.\nClick ✅ Confirm & Send to broadcast or ❌ Cancel.",
        reply_markup=step_keyboard(prev_step=True, confirm=True)
    )
    await state.set_state(NewsletterStates.confirm)

async def broadcast_newsletter(message: Message, state: FSMContext, db, bot):
    data = await state.get_data()
    media = data.get("media")
    text = data.get("text")
    caption = data.get("caption")
    buttons = data.get("buttons", [])
    markup = get_buttons_markup(buttons) if buttons else None
    total = await db.users.count_documents({})
    sent = 0
    errors = 0
    users_cursor = db.users.find({}, {"user_id": 1})
    await message.answer(f"Sending newsletter to {total} users...")
    async for user in users_cursor:
        try:
            if media:
                if media["type"] == "photo":
                    await bot.send_photo(user["user_id"], media["file_id"], caption=caption or "", reply_markup=markup)
                elif media["type"] == "video":
                    await bot.send_video(user["user_id"], media["file_id"], caption=caption or "", reply_markup=markup)
                elif media["type"] == "document":
                    await bot.send_document(user["user_id"], media["file_id"], caption=caption or "", reply_markup=markup)
            elif text:
                await bot.send_message(user["user_id"], text, reply_markup=markup)
            sent += 1
        except Exception:
            errors += 1
    await message.answer(f"✅ Newsletter sent to {sent} users. {errors} failed.")
    await state.clear()

# --- CALLBACK HELPERS ---

async def addbtn_callback(callback: CallbackQuery):
    await callback.answer("Send a button in format: Button Text - https://example.com", show_alert=True)

async def next_callback(callback: CallbackQuery, state: FSMContext, bot):
    await preview_newsletter(callback.message, state, bot)
    await callback.answer()

async def prev_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data.get("media"):
        await ask_for_caption(callback.message, state)
    elif data.get("text"):
        await ask_for_buttons(callback.message, state)
    await callback.answer()

async def cancel_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("❌ Newsletter cancelled.")

async def confirm_callback(callback: CallbackQuery, state: FSMContext, db, bot):
    await broadcast_newsletter(callback.message, state, db, bot)
    await callback.answer()
