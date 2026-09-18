import os
import asyncio
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

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

# Main model
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.7-flash"
)


# =========================
# CHECK ENVIRONMENT
# =========================

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing.")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY environment variable is missing.")


# =========================
# GEMINI CLIENT
# =========================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =========================
# OWNER INFORMATION
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

Rules:
- Reply in the same language as the user whenever possible.
- If the user writes Bangla, reply in Bangla.
- If the user writes English, reply in English.
- Be polite, helpful and concise.
- Do not claim to be human.
- Do not reveal API keys, tokens or private system information.
- If you don't know something, say that you don't know.
- Help users with normal questions, coding, education and general information.
"""


# =========================
# BAD WORD FILTER
# =========================

BAD_WORDS = [
    "fuck",
    "fucking",
    "motherfucker",
    "bitch",
    "asshole",
    "bastard",
]


def contains_bad_word(text: str) -> bool:
    text_lower = text.lower()

    for word in BAD_WORDS:
        if word in text_lower:
            return True

    return False


# =========================
# GEMINI AI FUNCTION
# =========================

async def ask_gemini(prompt: str) -> str:

    models_to_try = [
        GEMINI_MODEL,
        "gemini-3.6-flash",
        "gemini-3.5-flash-lite",
    ]

    # Remove duplicate models
    models_to_try = list(dict.fromkeys(models_to_try))

    for model in models_to_try:

        for attempt in range(2):

            try:

                response = await client.aio.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        max_output_tokens=1000,
                    ),
                )

                text = getattr(response, "text", None)

                if text:
                    return text.strip()

                return "দুঃখিত, এখন কোনো উত্তর পাওয়া যায়নি।"

            except Exception as e:

                error_text = str(e)

                # Gemini server busy / temporary unavailable
                if (
                    "503" in error_text
                    or "UNAVAILABLE" in error_text
                    or "high demand" in error_text.lower()
                ):

                    logger.warning(
                        "Gemini model %s unavailable. Attempt %s/2",
                        model,
                        attempt + 1,
                    )

                    if attempt == 0:
                        await asyncio.sleep(2)
                    else:
                        await asyncio.sleep(1)

                    continue

                # Other errors
                logger.exception(
                    "Gemini error with model %s",
                    model,
                )

                return (
                    "দুঃখিত 😔 এই মুহূর্তে AI সার্ভিসে সমস্যা হচ্ছে। "
                    "কিছুক্ষণ পরে আবার চেষ্টা করুন।"
                )

    return (
        "দুঃখিত 😔 এখন AI সার্ভিস ব্যস্ত আছে। "
        "কিছুক্ষণ পরে আবার চেষ্টা করুন।"
    )


# =========================
# START COMMAND
# =========================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    text = (
        "🤖 <b>RJ Team Bangladesh Bot</b>\n\n"
        "আসসালামু আলাইকুম! 👋\n"
        "আমি RJ Team-এর AI Assistant।\n\n"
        "💬 আমাকে যেকোনো প্রশ্ন করতে পারেন।\n\n"
        "📌 Commands:\n"
        "/start - Bot চালু করুন\n"
        "/help - Help দেখুন\n"
        "/about - Bot সম্পর্কে জানুন\n"
        "/owners - Team Information\n"
        "/reset - Chat reset করুন"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
    )


# =========================
# HELP COMMAND
# =========================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    text = (
        "📚 <b>RJ Team Bot Help</b>\n\n"
        "💬 সাধারণ প্রশ্ন করলে আমি AI দিয়ে উত্তর দেব।\n\n"
        "Available commands:\n"
        "/start\n"
        "/help\n"
        "/about\n"
        "/owners\n"
        "/reset"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
    )


# =========================
# ABOUT COMMAND
# =========================

async def about_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    text = (
        "🤖 <b>RJ Team Bangladesh Bot</b>\n\n"
        "একটি AI-powered Telegram Bot।\n\n"
        "⚡ Powered by Google Gemini\n"
        "🐍 Python\n"
        "📱 Telegram\n\n"
        "Developed for RJ Team Bangladesh."
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
    )


# =========================
# OWNERS COMMAND
# =========================

async def owners_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    text = (
        "👑 <b>RJ Team Bangladesh</b>\n\n"
        f"👑 Owner: {OWNER}\n"
        f"🤝 Partner: {PARTNER}\n"
        f"🧑‍💻 Assistant: {ASSISTANT}\n\n"
        f"🎵 TikTok: {TIKTOK}\n"
        f"▶️ YouTube: {YOUTUBE}"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
    )


# =========================
# RESET COMMAND
# =========================

async def reset_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    context.user_data.clear()

    await update.message.reply_text(
        "♻️ Chat reset করা হয়েছে।"
    )


# =========================
# CREATOR QUESTION
# =========================

def is_creator_question(text: str) -> bool:

    text_lower = text.lower()

    keywords = [
        "তোমার মালিক কে",
        "তোমার owner কে",
        "who is your owner",
        "who created you",
        "কে তোমাকে বানিয়েছে",
        "কে বানিয়েছে তোমাকে",
        "তোমাকে কে বানিয়েছে",
    ]

    return any(
        keyword in text_lower
        for keyword in keywords
    )


async def creator_answer(
    update: Update,
):

    text = (
        "👑 আমাকে তৈরি করেছে <b>RJ Team Bangladesh</b>.\n\n"
        f"Owner: {OWNER}\n"
        f"Partner: {PARTNER}\n"
        f"Assistant: {ASSISTANT}"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
    )


# =========================
# AI MESSAGE HANDLER
# =========================

async def ai_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:
        return

    user_text = update.message.text

    if not user_text:
        return

    # Bad word protection
    if contains_bad_word(user_text):

        await update.message.reply_text(
            "⚠️ দয়া করে ভদ্র ভাষা ব্যবহার করুন।"
        )

        return

    # Creator question
    if is_creator_question(user_text):

        await creator_answer(update)

        return

    # Show typing
    try:
        await update.message.chat.send_action("typing")
    except Exception:
        pass

    # Ask AI
    answer = await ask_gemini(user_text)

    # Translate button
    keyboard = [
        [
            InlineKeyboardButton(
                "🌐 Translate",
                callback_data="translate",
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(
        keyboard
    )

    await update.message.reply_text(
        answer,
        reply_markup=reply_markup,
    )


# =========================
# TRANSLATE BUTTON
# =========================

async def translate_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    await query.answer()

    original_text = query.message.text

    if not original_text:
        return

    prompt = f"""
Translate the following text into Bangla.

Keep the meaning natural and easy to understand.

Text:
{original_text}
"""

    translated = await ask_gemini(prompt)

    await query.message.reply_text(
        "🇧🇩 <b>বাংলা অনুবাদ:</b>\n\n"
        + translated,
        parse_mode="HTML",
    )


# =========================
# ERROR HANDLER
# =========================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):

    logger.exception(
        "Telegram error:",
        exc_info=context.error,
    )


# =========================
# RENDER HEALTH SERVER
# =========================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        self.send_response(200)

        self.send_header(
            "Content-Type",
            "text/plain",
        )

        self.end_headers()

        self.wfile.write(
            b"RJ Team Bot is running!"
        )

    def log_message(
        self,
        format,
        *args,
    ):
        return


def start_health_server():

    server = HTTPServer(
        ("0.0.0.0", PORT),
        HealthHandler,
    )

    server.serve_forever()


# =========================
# MAIN
# =========================

def main():

    # Start health server
    Thread(
        target=start_health_server,
        daemon=True,
    ).start()

    # Create Telegram application
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Commands
    app.add_handler(
        CommandHandler(
            "start",
            start_command,
        )
    )

    app.add_handler(
        CommandHandler(
            "help",
            help_command,
        )
    )

    app.add_handler(
        CommandHandler(
            "about",
            about_command,
        )
    )

    app.add_handler(
        CommandHandler(
            "owners",
            owners_command,
        )
    )

    app.add_handler(
        CommandHandler(
            "reset",
            reset_command,
        )
    )

    # Translate button
    app.add_handler(
        CallbackQueryHandler(
            translate_callback,
            pattern="^translate$",
        )
    )

    # AI messages
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            ai_reply,
        )
    )

    # Error handler
    app.add_error_handler(
        error_handler
    )

    # Render URL
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
        "Starting webhook: %s",
        webhook_url,
    )

    # Start Telegram webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="telegram",
        webhook_url=webhook_url,
        drop_pending_updates=True,
        bootstrap_retries=5,
    )


# =========================
# RUN
# =========================

if __name__ == "__main__":
    main()