import os
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from openai import AsyncOpenAI
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing.")

client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"RJ Team Bot is running!")

    def log_message(self, format, *args):
        return


def start_web_server():
    port = int(os.getenv("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 RJ Team Bangladesh AI Bot\n\n"
        "বাংলা বা ইংরেজিতে প্রশ্ন করুন। আমি উত্তর দেওয়ার চেষ্টা করব।"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 সাহায্য\n\n"
        "/start — বট চালু করুন\n"
        "/help — সাহায্য\n"
        "/about — বট সম্পর্কে তথ্য\n\n"
        "সাধারণ প্রশ্ন সরাসরি লিখে পাঠান।"
    )


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 RJ Team Bangladesh AI Bot\n\n"
        "Owner: @RJteam1\n"
        "বাংলা ভাষায় প্রশ্নের উত্তর দেওয়ার জন্য তৈরি।"
    )


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    if client is None:
        await update.message.reply_text(
            "⚠️ OPENAI_API_KEY সেট করা হয়নি। আগে API key যোগ করুন।"
        )
        return

    user_text = update.message.text.strip()

    try:
        response = await client.responses.create(
            model=MODEL,
            instructions=(
                "তুমি RJ Team Bangladesh AI Bot। "
                "ব্যবহারকারীর সাথে ভদ্রভাবে বাংলায় উত্তর দেবে। "
                "প্রয়োজনে ইংরেজিও ব্যবহার করতে পারো।"
            ),
            input=user_text,
        )
        answer = response.output_text.strip()
        if not answer:
            answer = "দুঃখিত, এখন উত্তর তৈরি করা যায়নি।"
        await update.message.reply_text(answer[:4096])
    except Exception:
        logging.exception("OpenAI request failed")
        await update.message.reply_text(
            "⚠️ এই মুহূর্তে উত্তর দিতে সমস্যা হচ্ছে। একটু পরে আবার চেষ্টা করুন।"
        )


def main():
    # Keeps a simple web endpoint alive on hosts that require an HTTP service.
    Thread(target=start_web_server, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, chat)
    )

    logging.info("RJ Team Bot started.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
