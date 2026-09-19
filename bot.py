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
# BOT INFORMATION
# =========================================================

ABOUT_TEXT = """
🤖 About AI Assistant

আমি তোমার AI Assistant। ❤️

আমি RJ Team Bangladesh Hacker Community-এর পক্ষ থেকে
তোমার বন্ধু হিসেবে তোমার বিভিন্ন প্রশ্নের উত্তর দেওয়ার চেষ্টা করি। 😊

💬 সাধারণ প্রশ্ন → সুন্দর উত্তর
😂 মজার SMS → মজার reply
❤️ Emotional SMS → emotional reply
🌐 Translation → যেকোনো ভাষার অনুবাদ

👑 Owner: @RJteam1
📢 Channel: @RJteam123890

🤝 RJ Team Bangladesh Hacker Community
"""


# =========================================================
# AI PERSONALITY
# =========================================================

SYSTEM_PROMPT = """
তুমি একটি বন্ধুসুলভ Telegram AI assistant।

তুমি RJ Team Bangladesh Hacker Community-এর পক্ষ থেকে
ব্যবহারকারীর সাথে বন্ধুর মতো কথা বলবে।

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

17. Translation চাইলে শুধু translation করবে।
অপ্রয়োজনীয় explanation দেবে না।
"""


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "ℹ️ About",
                callback_data="about"
            ),
            InlineKeyboardButton(
                "🌐 Translate",
                callback_data="translate_help"
            ),
        ],
        [
            InlineKeyboardButton(
                "📢 Channel",
                url="https://t.me/RJteam123890"
            ),
            InlineKeyboardButton(
                "👑 Owner",
                url="https://t.me/RJteam1"
            ),
        ],
    ]

    await update.message.reply_text(
        "👋 হ্যালো বন্ধু! ❤️\n\n"
        "আমি তোমার AI Assistant। 🤖\n\n"
        "💬 যেকোনো SMS পাঠাও।\n"
        "😂 মজার হলে মজার reply\n"
        "❤️ Emotional হলে emotional reply\n"
        "🤔 প্রশ্ন হলে সুন্দর উত্তর\n"
        "🌐 Translation-ও করা যাবে।\n\n"
        "নিচের Button ব্যবহার করতে পারো 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================================================
# HELP
# =========================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🤖 Bot Help\n\n"
        "💬 যেকোনো SMS পাঠাও।\n"
        "😂 মজার হলে মজার reply\n"
        "❤️ Emotional হলে emotional reply\n"
        "🤔 প্রশ্ন হলে উত্তর\n"
        "🌐 Translate করতে:\n\n"
        "/translate Hello, how are you?\n\n"
        "ℹ️ About দেখতে /about ব্যবহার করো।"
    )


# =========================================================
# ABOUT COMMAND
# =========================================================

async def about_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    keyboard = [
        [
            InlineKeyboardButton(
                "👑 Owner",
                url="https://t.me/RJteam1"
            ),
            InlineKeyboardButton(
                "📢 Channel",
                url="https://t.me/RJteam123890"
            ),
        ]
    ]

    await update.message.reply_text(
        ABOUT_TEXT,
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True,
    )


# =========================================================
# AI REPLY
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

If no target language is specified,
translate into Bangla.

If a target language is explicitly mentioned,
translate into that language.

Return only the translated text.
Do not explain.

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
            "উত্তর বাংলায় পাওয়া যাবে। ❤️"
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
# BUTTON HANDLER
# =========================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    # About button
    if query.data == "about":

        keyboard = [
            [
                InlineKeyboardButton(
                    "👑 Owner",
                    url="https://t.me/RJteam1"
                ),
                InlineKeyboardButton(
                    "📢 Channel",
                    url="https://t.me/RJteam123890"
                ),
            ]
        ]

        await query.message.reply_text(
            ABOUT_TEXT,
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True,
        )

        return

    # Translate help button
    if query.data == "translate_help":

        await query.message.reply_text(
            "🌐 Translate\n\n"
            "যেকোনো ভাষার লেখা translate করতে পারো।\n\n"
            "উদাহরণ:\n"
            "/translate Hello, how are you?\n\n"
            "ডিফল্টভাবে বাংলা translation দেওয়া হবে। ❤️"
        )

        return

    # Translate reply button
    if query.data.startswith("translate_reply:"):

        original_text = query.data.replace(
            "translate_reply:",
            "",
            1
        )

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

    # Telegram callback_data has a small size limit.
    # Therefore use a short token stored in user context.
    context.user_data["last_ai_reply"] = answer

    keyboard = [
        [
            InlineKeyboardButton(
                "🌐 Translate",
                callback_data="translate_last"
            )
        ]
    ]

    await update.message.reply_text(
        answer,
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True,
    )


# =========================================================
# LAST REPLY TRANSLATION
# =========================================================

async def translate_last(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    text = context.user_data.get("last_ai_reply")

    if not text:
        await query.message.reply_text(
            "❌ আগের reply পাওয়া যাচ্ছে না।"
        )
        return

    result = await translate_text(text)

    await query.message.reply_text(
        "🌐 Translation:\n\n" + result
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
        CommandHandler("about", about_command)
    )

    application.add_handler(
        CommandHandler("translate", translate_command)
    )

    # Buttons
    application.add_handler(
        CallbackQueryHandler(
            translate_last,
            pattern="^translate_last$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            button_handler,
            pattern="^(about|translate_help|translate_reply:)"
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
    # RENDER WEBHOOK
    # =====================================================

    port = int(
        os.getenv("PORT", "10000")
    )

    render_url = os.getenv(
        "RENDER_EXTERNAL_URL"
    )

    if render_url:

        webhook_url = (
            render_url.rstrip("/")
            + "/telegram/"
            + BOT_TOKEN
        )

        logger.info(
            "Starting Render webhook..."
        )

        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path="telegram/" + BOT_TOKEN,
            webhook_url=webhook_url,
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
        )

    else:

        logger.info(
            "Starting polling..."
        )

        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
        )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()