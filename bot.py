import os
import logging
from openai import AsyncOpenAI

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
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# AI PERSONALITY
# =========================================================

SYSTEM_PROMPT = """
তুমি একটি বন্ধুসুলভ Telegram AI assistant।

ব্যবহারকারীর SMS-এর ধরন বুঝে উত্তর দেবে।

RULES:

1. সাধারণ প্রশ্ন হলে সরাসরি, পরিষ্কার ও বন্ধুসুলভ উত্তর দাও।

2. মজার SMS হলে মজার, playful এবং হাস্যকর ভঙ্গিতে উত্তর দাও।
প্রয়োজনে 😂 😄 🤣 😆 ব্যবহার করতে পারো।

3. Emotional SMS হলে আন্তরিক, সুন্দর ও emotional ভঙ্গিতে উত্তর দাও।
প্রয়োজনে ❤️ 🥺 😔 💔 ব্যবহার করতে পারো।

4. দুঃখের SMS হলে সহানুভূতিশীল হও।

5. ভালোবাসা বা romantic SMS হলে কোমল ও সুন্দরভাবে উত্তর দাও।

6. রাগের SMS হলে শান্ত ও ভদ্রভাবে উত্তর দাও।

7. সব SMS-কে emotional বানাবে না।
শুধু সত্যিই emotional SMS হলে emotional tone ব্যবহার করবে।

8. প্রশ্ন করলে প্রশ্নের উত্তর সরাসরি দাও।
অযথা emotional কথা যোগ করবে না।

9. ব্যবহারকারী যে ভাষায় লিখেছে, সম্ভব হলে সেই ভাষাতেই উত্তর দাও।

10. বাংলা হলে বাংলা, English হলে English।
Banglish হলে প্রয়োজন অনুযায়ী Banglish/বাংলায় উত্তর দিতে পারো।

11. উত্তর natural এবং মানুষের মতো হবে।

12. সাধারণ SMS-এর উত্তর খুব বড় করবে না।

13. প্রয়োজন অনুযায়ী 1-3টি emoji ব্যবহার করো।

14. একই reply বারবার হুবহু ব্যবহার করবে না।

15. গুরুতর বিষয়ে মজা করবে না।

16. ব্যবহারকারীর মূল বক্তব্য বুঝে reply করবে।
শুধু keyword দেখে উত্তর দেবে না।

17. ব্যবহারকারী translation চাইলে শুধু translation-এর কাজ করবে।
অপ্রয়োজনীয় explanation দেবে না।
"""


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "👋 হ্যালো বন্ধু! ❤️\n\n"
        "আমাকে যেকোনো SMS পাঠাও।\n\n"
        "😂 মজার SMS → মজার reply\n"
        "❤️ Emotional SMS → emotional reply\n"
        "🤔 প্রশ্ন → সুন্দর উত্তর\n"
        "🌐 Translate → যেকোনো ভাষায় অনুবাদ\n\n"
        "📝 Translate করতে:\n"
        "/translate Hello, how are you?"
    )


# =========================================================
# HELP
# =========================================================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🤖 Bot Help\n\n"
        "💬 যেকোনো SMS পাঠাও।\n"
        "😂 মজার হলে মজার reply\n"
        "❤️ Emotional হলে emotional reply\n"
        "🤔 প্রশ্ন হলে উত্তর\n"
        "🌐 Translate করতে:\n"
        "/translate Your text\n\n"
        "উদাহরণ:\n"
        "/translate I love you ❤️"
    )


# =========================================================
# OPENAI AI REPLY
# =========================================================

async def ai_reply(text):

    try:

        response = await client.responses.create(
            model="gpt-5-mini",
            instructions=SYSTEM_PROMPT,
            input=text,
            max_output_tokens=500,
        )

        answer = response.output_text.strip()

        if not answer:
            return "😅 আবার SMS টা পাঠাও তো ❤️"

        return answer

    except Exception as e:

        logger.exception("OpenAI error: %s", e)

        return (
            "😅 একটু সমস্যা হয়েছে!\n"
            "কিছুক্ষণ পরে আবার চেষ্টা করো ❤️"
        )


# =========================================================
# TRANSLATE
# =========================================================

async def translate_text(text):

    try:

        prompt = f"""
Translate the following text naturally.

Automatically detect the source language.

If the user did not specify a target language,
translate it into Bangla.

If the user explicitly says a target language,
translate into that language.

Do not explain.
Return only the translated text.

Text:
{text}
"""

        response = await client.responses.create(
            model="gpt-5-mini",
            input=prompt,
            max_output_tokens=500,
        )

        result = response.output_text.strip()

        if not result:
            return "❌ Translation পাওয়া যায়নি।"

        return result

    except Exception as e:

        logger.exception("Translation error: %s", e)

        return "❌ Translation করতে সমস্যা হয়েছে।"


# =========================================================
# TRANSLATE COMMAND
# =========================================================

async def translate_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.args:

        await update.message.reply_text(
            "🌐 Translate ব্যবহার করার নিয়ম:\n\n"
            "/translate Hello, how are you?\n\n"
            "বাংলা চাইলে:\n"
            "/translate I love you ❤️"
        )

        return

    text = " ".join(context.args)

    try:
        await update.message.chat.send_action("typing")
    except Exception:
        pass

    result = await translate_text(text)

    await update.message.reply_text(
        "🌐 Translation:\n\n" + result
    )


# =========================================================
# TRANSLATE BUTTON
# =========================================================

async def translate_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    original_text = query.message.text

    # Remove previous bot prefix if present
    if original_text.startswith("🤖"):
        original_text = original_text[2:].strip()

    result = await translate_text(original_text)

    await query.message.reply_text(
        "🌐 Translation:\n\n" + result
    )


# =========================================================
# MESSAGE HANDLER
# =========================================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    if not update.message.text:
        return

    text = update.message.text.strip()

    if not text:
        return

    try:
        await update.message.chat.send_action("typing")
    except Exception:
        pass

    answer = await ai_reply(text)

    # Translate button
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
        reply_markup=reply_markup,
        disable_web_page_preview=True,
    )


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    logger.exception(
        "Telegram error: %s",
        context.error
    )


# =========================================================
# MAIN
# =========================================================

def main():

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Commands
    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("help", help_command)
    )

    application.add_handler(
        CommandHandler("translate", translate_command)
    )

    # Translate button
    application.add_handler(
        CallbackQueryHandler(
            translate_button,
            pattern="^translate$"
        )
    )

    # Messages
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    # Errors
    application.add_error_handler(error_handler)

    # =====================================================
    # RENDER
    # =====================================================

    port = int(os.getenv("PORT", "10000"))

    render_url = os.getenv("RENDER_EXTERNAL_URL")

    if render_url:

        webhook_url = (
            render_url.rstrip("/")
            + "/telegram/"
            + BOT_TOKEN
        )

        logger.info("Starting Render webhook...")

        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path="telegram/" + BOT_TOKEN,
            webhook_url=webhook_url,
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
        )

    else:

        logger.info("Starting polling...")

        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
        )


# =========================================================
# START BOT
# =========================================================

if __name__ == "__main__":
    main()