import os
import logging
import re

from google import genai
from google.genai import types

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# =========================
# LOGGING
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================
# ENVIRONMENT VARIABLES
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

PORT = int(os.getenv("PORT", "10000"))

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.8-flash"
)

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN environment variable is missing."
    )

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY environment variable is missing."
    )


# =========================
# GEMINI CLIENT
# =========================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =========================
# BOT INFORMATION
# =========================

OWNER = "@RJteam1"

PARTNER = "@Apple20237"

ASSISTANT = "@Apple20237"

TIKTOK = "lyrics.song333"

YOUTUBE = "https://youtube.com/@rakib22"


# =========================
# AI SYSTEM INSTRUCTION
# =========================

SYSTEM_INSTRUCTION = """
You are RJ Team Bangladesh Bot.

You are a friendly Telegram AI assistant.

Reply naturally and helpfully.

Use Bangla when the user writes Bangla or Banglish.
Use English when the user writes English.

Keep replies reasonably short and easy to understand.

Do not claim to be the owner of the bot.

Bot owner:
@RJteam1

Partner:
@Apple20237

Assistant:
@Apple20237
"""


# =========================
# BAD WORD FILTER
# =========================

BAD_WORDS = [
    "fuck",
    "fucking",
    "motherfucker",
    "bitch",
    "bastard",
    "asshole",
    "shit",
]


def contains_bad_word(text: str) -> bool:
    text_lower = text.lower()

    for word in BAD_WORDS:
        if re.search(r"\b" + re.escape(word) + r"\b", text_lower):
            return True

    return False


# =========================
# GEMINI FUNCTION
# =========================

async def ask_gemini(prompt: str) -> str:

    try:

        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.7,
                max_output_tokens=1000,
            ),
        )

        answer = (response.text or "").strip()

        if not answer:
            return "দুঃখিত, এখন কোনো উত্তর তৈরি করতে পারছি না।"

        return answer

    except Exception as e:

        logger.exception("Gemini error: %s", e)

        return (
            "দুঃখিত 😔\n"
            "এই মুহূর্তে AI সার্ভিসে সমস্যা হচ্ছে। "
            "কিছুক্ষণ পরে আবার চেষ্টা করুন।"
        )


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    name = user.first_name if user else "বন্ধু"

    text = (
        f"👋 হ্যালো {name}!\n\n"
        "🤖 আমি RJ Team Bangladesh Bot.\n\n"
        "আপনি আমাকে যেকোনো প্রশ্ন করতে পারেন।\n\n"
        "📌 Available Commands:\n"
        "/start - Bot শুরু করুন\n"
        "/help - Help দেখুন\n"
        "/about - Bot সম্পর্কে জানুন\n"
        "/owners - Owner/Team তথ্য\n"
        "/reset - Chat reset করুন"
    )

    await update.message.reply_text(text)


# =========================
# HELP
# =========================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        "📚 RJ Team Bot Help\n\n"
        "💬 সাধারণ প্রশ্ন করলে আমি AI দিয়ে উত্তর দেব।\n\n"
        "Commands:\n"
        "/start\n"
        "/help\n"
        "/about\n"
        "/owners\n"
        "/reset\n\n"
        "🌐 আপনি Bangla, Banglish বা English-এ "
        "কথা বলতে পারেন।"
    )

    await update.message.reply_text(text)


# =========================
# ABOUT
# =========================

async def about(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        "🤖 RJ Team Bangladesh Bot\n\n"
        "একটি AI-powered Telegram bot.\n\n"
        "⚡ Powered by Gemini AI\n"
        "🐍 Python\n"
        "📱 Telegram Bot API\n\n"
        "👑 Owner: @RJteam1"
    )

    await update.message.reply_text(text)


# =========================
# OWNERS
# =========================

async def owners(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        "👑 RJ Team\n\n"
        f"Owner: {OWNER}\n"
        f"Partner: {PARTNER}\n"
        f"Assistant: {ASSISTANT}\n\n"
        f"🎵 TikTok: {TIKTOK}\n"
        f"▶️ YouTube: {YOUTUBE}"
    )

    await update.message.reply_text(text)


# =========================
# RESET
# =========================

async def reset(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    await update.message.reply_text(
        "♻️ Chat reset করা হয়েছে।\n\n"
        "এখন নতুন করে প্রশ্ন করতে পারেন।"
    )


# =========================
# CREATOR QUESTION
# =========================

def is_creator_question(text: str) -> bool:

    text = text.lower()

    keywords = [
        "who created you",
        "who made you",
        "who is your owner",
        "who is the owner",
        "creator",
        "কে তোমাকে বানিয়েছে",
        "কে বানিয়েছে",
        "তোমার মালিক কে",
        "তোমার owner কে",
    ]

    return any(keyword in text for keyword in keywords)


async def creator_answer(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        "🤖 আমাকে RJ Team-এর জন্য তৈরি করা হয়েছে।\n\n"
        f"👑 Owner: {OWNER}"
    )

    await update.message.reply_text(text)


# =========================
# AI MESSAGE
# =========================

async def ai_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message or not update.message.text:
        return

    user_text = update.message.text.strip()

    if not user_text:
        return

    # Bad word protection
    if contains_bad_word(user_text):

        await update.message.reply_text(
            "⚠️ দয়া করে খারাপ ভাষা ব্যবহার করবেন না।"
        )

        return

    # Creator question
    if is_creator_question(user_text):

        await creator_answer(update, context)

        return

    # Show typing
    try:
        await update.message.chat.send_action("typing")
    except Exception:
        pass

    answer = await ask_gemini(user_text)

    # Translation button
    keyboard = [
        [
            InlineKeyboardButton(
                "🌐 Translate",
                callback_data="translate"
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        answer,
        reply_markup=reply_markup
    )


# =========================
# TRANSLATE
# =========================

async def translate_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    original_text = query.message.text

    if not original_text:
        await query.edit_message_text(
            "❌ অনুবাদ করার মতো text পাওয়া যায়নি।"
        )
        return

    prompt = f"""
Translate the following text into Bangla.

Keep the meaning natural and clear.

Text:
{original_text}
"""

    translated = await ask_gemini(prompt)

    await query.message.reply_text(
        "🌐 বাংলা অনুবাদ:\n\n" + translated
    )


# =========================
# ERROR HANDLER
# =========================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    logger.exception(
        "Unhandled exception:",
        exc_info=context.error
    )


# =========================
# MAIN
# =========================

def main():

    logger.info("Starting RJ Team Bangladesh Bot...")

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Commands
    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("help", help_command)
    )

    app.add_handler(
        CommandHandler("about", about)
    )

    app.add_handler(
        CommandHandler("owners", owners)
    )

    app.add_handler(
        CommandHandler("reset", reset)
    )

    # Translate button
    app.add_handler(
        CallbackQueryHandler(
            translate_callback,
            pattern="^translate$"
        )
    )

    # AI message
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            ai_reply
        )
    )

    # Error handler
    app.add_error_handler(error_handler)

    # Render URL
    render_url = os.getenv("RENDER_EXTERNAL_URL")

    if not render_url:
        raise RuntimeError(
            "RENDER_EXTERNAL_URL is missing."
        )

    render_url = render_url.rstrip("/")

    webhook_url = (
        f"{render_url}/telegram"
    )

    logger.info(
        "Webhook URL: %s",
        webhook_url
    )

    # Render Webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="telegram",
        webhook_url=webhook_url,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()