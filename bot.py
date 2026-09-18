import os
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from openai import AsyncOpenAI

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PORT = int(os.getenv("PORT", "10000"))

OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-5-mini"
)

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing.")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing.")

client = AsyncOpenAI(
    api_key=OPENAI_API_KEY
)

OWNER = "@RJteam1"
PARTNER = "@Apple20237"
ASSISTANT = "@Apple20237"
TIKTOK = "lyrics.song333"
YOUTUBE = "https://youtube.com/@rakib22"

SYSTEM_PROMPT = """
You are RJ Team Bangladesh Bot.

You are a friendly Telegram AI assistant.

Rules:
- Reply in the same language as the user.
- If the user writes Bangla, reply in Bangla.
- If the user writes English, reply in English.
- Be helpful, polite and concise.
- Never reveal API keys or private information.
"""


async def ask_openai(prompt: str) -> str:
    try:
        response = await client.responses.create(
            model=OPENAI_MODEL,
            instructions=SYSTEM_PROMPT,
            input=prompt,
            max_output_tokens=1000,
        )

        answer = response.output_text

        if answer:
            return answer.strip()

        return "দুঃখিত, কোনো উত্তর পাওয়া যায়নি।"

    except Exception:
        logger.exception("OpenAI error")

        return (
            "দুঃখিত 😔 এই মুহূর্তে AI সার্ভিসে সমস্যা হচ্ছে। "
            "কিছুক্ষণ পরে আবার চেষ্টা করুন।"
        )


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
        "/help - Help\n"
        "/about - Bot সম্পর্কে\n"
        "/owners - Team Information\n"
        "/reset - Chat reset"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "📚 <b>RJ Team Bot Help</b>\n\n"
        "যেকোনো প্রশ্ন লিখুন, আমি AI দিয়ে উত্তর দেব।\n\n"
        "/start\n"
        "/help\n"
        "/about\n"
        "/owners\n"
        "/reset",
        parse_mode="HTML",
    )


async def about_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "🤖 <b>RJ Team Bangladesh Bot</b>\n\n"
        "⚡ Powered by OpenAI\n"
        "🐍 Python\n"
        "📱 Telegram\n\n"
        "Developed for RJ Team Bangladesh.",
        parse_mode="HTML",
    )


async def owners_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "👑 <b>RJ Team Bangladesh</b>\n\n"
        f"👑 Owner: {OWNER}\n"
        f"🤝 Partner: {PARTNER}\n"
        f"🧑‍💻 Assistant: {ASSISTANT}\n\n"
        f"🎵 TikTok: {TIKTOK}\n"
        f"▶️ YouTube: {YOUTUBE}",
        parse_mode="HTML",
    )


async def reset_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data.clear()

    await update.message.reply_text(
        "♻️ Chat reset করা হয়েছে।"
    )


async def ai_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message:
        return

    user_text = update.message.text

    if not user_text:
        return

    try:
        await update.message.chat.send_action("typing")
    except Exception:
        pass

    answer = await ask_openai(user_text)

    keyboard = [
        [
            InlineKeyboardButton(
                "🌐 Translate",
                callback_data="translate",
            )
        ]
    ]

    await update.message.reply_text(
        answer,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


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
Translate this text into Bangla.
Keep the meaning natural and easy to understand.

Text:
{original_text}
"""

    translated = await ask_openai(prompt)

    await query.message.reply_text(
        "🇧🇩 <b>বাংলা অনুবাদ:</b>\n\n"
        + translated,
        parse_mode="HTML",
    )


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):
    logger.exception(
        "Telegram error:",
        exc_info=context.error,
    )


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

    def log_message(self, format, *args):
        return


def start_health_server():
    server = HTTPServer(
        ("0.0.0.0", PORT),
        HealthHandler,
    )

    server.serve_forever()


def main():

    Thread(
        target=start_health_server,
        daemon=True,
    ).start()

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

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

    app.add_handler(
        CallbackQueryHandler(
            translate_callback,
            pattern="^translate$",
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            ai_reply,
        )
    )

    app.add_error_handler(error_handler)

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
            "Render URL is missing."
        )

    webhook_url = (
        f"{render_url}/telegram"
    )

    logger.info(
        "Webhook URL: %s",
        webhook_url,
    )

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="telegram",
        webhook_url=webhook_url,
        drop_pending_updates=True,
        bootstrap_retries=5,
    )


if __name__ == "__main__":
    main()