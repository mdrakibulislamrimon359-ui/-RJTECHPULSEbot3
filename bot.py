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

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# ENVIRONMENT
# =========================================================

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


# =========================================================
# GEMINI CLIENT
# =========================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =========================================================
# RJ TEAM INFORMATION
# =========================================================

OWNER = "@RJteam1"
PARTNER = "@Apple20237"
ASSISTANT = "@Apple20237"

TIKTOK = "lyrics.song333"
YOUTUBE = "https://youtube.com/@rakib22"


# =========================================================
# AI INSTRUCTION
# =========================================================

SYSTEM_INSTRUCTION = """
You are RJ Team Bangladesh Bot.

You are a friendly Telegram AI assistant.

Rules:

1. Reply naturally and helpfully.
2. If the user writes Bangla or Banglish, reply in Bangla.
3. If the user writes English, reply in English.
4. Keep normal answers reasonably short.
5. Do not claim to be the owner.
6. Do not invent owner information.

RJ Team information:

Owner: @RJteam1
Partner: @Apple20237
Assistant: @Apple20237
TikTok: lyrics.song333
YouTube: https://youtube.com/@rakib22
"""


# =========================================================
# BAD WORD FILTER
# =========================================================

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
        if re.search(
            r"\b" + re.escape(word) + r"\b",
            text_lower
        ):
            return True

    return False


# =========================================================
# GEMINI AI
# =========================================================

async def ask_gemini(prompt: str) -> str:

    try:

        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                max_output_tokens=1000,
            ),
        )

        answer = (response.text or "").strip()

        if not answer:
            return (
                "দুঃখিত 😔\n"
                "এই মুহূর্তে কোনো উত্তর পাওয়া যায়নি।"
            )

        return answer

    except Exception:

        logger.exception("Gemini API error")

        return (
            "দুঃখিত 😔\n"
            "এই মুহূর্তে AI সার্ভিসে সমস্যা হচ্ছে।\n"
            "কিছুক্ষণ পরে আবার চেষ্টা করুন।"
        )


# =========================================================
# /START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    user = update.effective_user

    name = (
        user.first_name
        if user
        else "বন্ধু"
    )

    text = (
        f"👋 হ্যালো {name}!\n\n"
        "🤖 আমি RJ Team Bangladesh Bot.\n\n"
        "💬 আমাকে যেকোনো প্রশ্ন করতে পারেন।\n\n"
        "📌 Commands:\n"
        "/start - Bot শুরু করুন\n"
        "/help - Help দেখুন\n"
        "/about - Bot সম্পর্কে জানুন\n"
        "/owners - Owner/Team তথ্য\n"
        "/reset - Chat reset করুন"
    )

    await update.message.reply_text(text)


# =========================================================
# /HELP
# =========================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    text = (
        "📚 RJ Team Bot Help\n\n"
        "💬 সাধারণ প্রশ্ন করলে আমি Gemini AI দিয়ে উত্তর দেব।\n\n"
        "Commands:\n"
        "/start\n"
        "/help\n"
        "/about\n"
        "/owners\n"
        "/reset\n\n"
        "🌐 Bangla, Banglish অথবা English-এ কথা বলতে পারেন।"
    )

    await update.message.reply_text(text)


# =========================================================
# /ABOUT
# =========================================================

async def about(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    text = (
        "🤖 RJ Team Bangladesh Bot\n\n"
        "একটি AI-powered Telegram Bot.\n\n"
        "⚡ AI: Gemini\n"
        "🐍 Language: Python\n"
        "📱 Platform: Telegram\n\n"
        "👑 Owner: @RJteam1"
    )

    await update.message.reply_text(text)


# =========================================================
# /OWNERS
# =========================================================

async def owners(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    text = (
        "👑 RJ TEAM\n\n"
        f"👑 Owner: {OWNER}\n"
        f"🤝 Partner: {PARTNER}\n"
        f"🧑‍💻 Assistant: {ASSISTANT}\n\n"
        f"🎵 TikTok: {TIKTOK}\n"
        f"▶️ YouTube: {YOUTUBE}"
    )

    await update.message.reply_text(text)


# =========================================================
# /RESET
# =========================================================

async def reset(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    context.user_data.clear()

    await update.message.reply_text(
        "♻️ Chat reset করা হয়েছে।\n\n"
        "এখন নতুন করে প্রশ্ন করতে পারেন।"
    )


# =========================================================
# CREATOR QUESTION
# =========================================================

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

    return any(
        keyword in text
        for keyword in keywords
    )


# =========================================================
# CREATOR ANSWER
# =========================================================

async def creator_answer(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    text = (
        "🤖 আমাকে RJ Team-এর জন্য তৈরি করা হয়েছে।\n\n"
        f"👑 Owner: {OWNER}"
    )

    await update.message.reply_text(text)


# =========================================================
# AI MESSAGE
# =========================================================

async def ai_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    if not update.message.text:
        return

    user_text = update.message.text.strip()

    if not user_text:
        return

    # Bad language protection
    if contains_bad_word(user_text):

        await update.message.reply_text(
            "⚠️ দয়া করে খারাপ ভাষা ব্যবহার করবেন না।"
        )

        return

    # Creator question
    if is_creator_question(user_text):

        await creator_answer(
            update,
            context
        )

        return

    # Typing indicator
    try:
        await update.message.chat.send_action(
            "typing"
        )
    except Exception:
        pass

    # Gemini
    answer = await ask_gemini(
        user_text
    )

    # Translate button
    keyboard = [
        [
            InlineKeyboardButton(
                "🌐 Translate",
                callback_data="translate"
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(
        keyboard
    )

    await update.message.reply_text(
        answer,
        reply_markup=reply_markup
    )


# =========================================================
# TRANSLATE BUTTON
# =========================================================

async def translate_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    if not query.message:
        return

    original_text = query.message.text

    if not original_text:
        await query.message.reply_text(
            "❌ অনুবাদ করার মতো text পাওয়া যায়নি।"
        )
        return

    prompt = f"""
Translate the following text into Bangla.

Keep the meaning natural and clear.

Do not add extra explanation.

Text:

{original_text}
"""

    translated = await ask_gemini(
        prompt
    )

    await query.message.reply_text(
        "🌐 বাংলা অনুবাদ:\n\n"
        + translated
    )


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    logger.error(
        "Unhandled exception: %s",
        context.error,
        exc_info=context.error
    )


# =========================================================
# MAIN
# =========================================================

def main():

    logger.info(
        "Starting RJ Team Bangladesh Bot..."
    )

    logger.info(
        "PORT = %s",
        PORT
    )

    # Create Telegram application
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # -----------------------------------------------------
    # COMMANDS
    # -----------------------------------------------------

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "help",
            help_command
        )
    )

    app.add_handler(
        CommandHandler(
            "about",
            about
        )
    )

    app.add_handler(
        CommandHandler(
            "owners",
            owners
        )
    )

    app.add_handler(
        CommandHandler(
            "reset",
            reset
        )
    )

    # -----------------------------------------------------
    # TRANSLATE BUTTON
    # -----------------------------------------------------

    app.add_handler(
        CallbackQueryHandler(
            translate_callback,
            pattern="^translate$"
        )
    )

    # -----------------------------------------------------
    # NORMAL TEXT / AI
    # -----------------------------------------------------

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            ai_reply
        )
    )

    # -----------------------------------------------------
    # ERROR HANDLER
    # -----------------------------------------------------

    app.add_error_handler(
        error_handler
    )

    # -----------------------------------------------------
    # RENDER URL
    # -----------------------------------------------------

    render_url = os.getenv(
        "RENDER_EXTERNAL_URL"
    )

    render_hostname = os.getenv(
        "RENDER_EXTERNAL_HOSTNAME"
    )

    if render_url:

        render_url = render_url.rstrip("/")

    elif render_hostname:

        render_url = (
            f"https://{render_hostname}"
        )

    else:

        raise RuntimeError(
            "Render URL environment variable is missing."
        )

    webhook_url = (
        f"{render_url}/telegram"
    )

    logger.info(
        "Webhook URL = %s",
        webhook_url
    )

    # -----------------------------------------------------
    # START WEBHOOK SERVER
    # -----------------------------------------------------

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="telegram",
        webhook_url=webhook_url,
        drop_pending_updates=True,
        bootstrap_retries=5,
    )


# =========================================================
# START PROGRAM
# =========================================================

if __name__ == "__main__":
    main()