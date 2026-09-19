import os
import asyncio
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from openai import AsyncOpenAI

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.constants import ChatMemberStatus

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ChatMemberHandler,
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
# CONFIGURATION
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI GPT-5.6 Luna
OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-5.6-luna"
)

PORT = int(
    os.getenv("PORT", "10000")
)


# =========================================================
# RJ TEAM INFORMATION
# =========================================================

COMMUNITY_NAME = "RJ Team Bangladesh Community"
CREATOR_NAME = "Rakib Sar"

OWNER_USERNAME = "@RJteam1"
PARTNER_USERNAME = "@Apple20237"
ASSISTANT_USERNAME = "@Apple20237"

TIKTOK_USERNAME = "lyrics.song333"
YOUTUBE_LINK = "https://youtube.com/@rakib22"


# =========================================================
# REQUIRED ENVIRONMENT VARIABLES
# =========================================================

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN is missing"
    )

if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY is missing"
    )


# =========================================================
# OPENAI CLIENT
# =========================================================

client = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    timeout=45.0,
    max_retries=2,
)


# =========================================================
# RENDER HEALTH SERVER
# =========================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        self.send_response(200)

        self.send_header(
            "Content-Type",
            "text/plain; charset=utf-8"
        )

        self.end_headers()

        self.wfile.write(
            b"RJ Team Bot is running!"
        )

    def do_HEAD(self):

        self.send_response(200)

        self.send_header(
            "Content-Type",
            "text/plain; charset=utf-8"
        )

        self.end_headers()

    def log_message(
        self,
        format,
        *args
    ):
        pass


def start_health_server():

    server = HTTPServer(
        ("0.0.0.0", PORT),
        HealthHandler
    )

    logger.info(
        "Health server started on port %s",
        PORT
    )

    server.serve_forever()


# =========================================================
# TRANSLATE BUTTON
# =========================================================

def translate_keyboard():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🌐 Translate",
                callback_data="translate"
            )
        ]
    ])


# =========================================================
# LANGUAGE MENU
# =========================================================

def language_keyboard():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "🇬🇧 English",
                callback_data="lang_English"
            ),
            InlineKeyboardButton(
                "🇮🇳 Hindi",
                callback_data="lang_Hindi"
            ),
        ],

        [
            InlineKeyboardButton(
                "🇸🇦 Arabic",
                callback_data="lang_Arabic"
            ),
            InlineKeyboardButton(
                "🇵🇰 Urdu",
                callback_data="lang_Urdu"
            ),
        ],

        [
            InlineKeyboardButton(
                "🇨🇳 Chinese",
                callback_data="lang_Chinese"
            ),
            InlineKeyboardButton(
                "🇯🇵 Japanese",
                callback_data="lang_Japanese"
            ),
        ],

        [
            InlineKeyboardButton(
                "🇰🇷 Korean",
                callback_data="lang_Korean"
            ),
            InlineKeyboardButton(
                "🇧🇩 Bangla",
                callback_data="lang_Bangla"
            ),
        ],

        [
            InlineKeyboardButton(
                "🇫🇷 French",
                callback_data="lang_French"
            ),
            InlineKeyboardButton(
                "🇩🇪 German",
                callback_data="lang_German"
            ),
        ],

        [
            InlineKeyboardButton(
                "🇪🇸 Spanish",
                callback_data="lang_Spanish"
            ),
            InlineKeyboardButton(
                "🇹🇷 Turkish",
                callback_data="lang_Turkish"
            ),
        ],

        [
            InlineKeyboardButton(
                "❌ Close",
                callback_data="close_translate"
            )
        ]

    ])


# =========================================================
# GROUP NOTICE
# =========================================================

GROUP_NOTICE = """
🌙 RJ TEAM BANGLADESH COMMUNITY 🇧🇩

🤝 আসুন, সবাই সুন্দর ভাষায় কথা বলি।

❌ গালাগালি
❌ অশ্লীল কথা
❌ কাউকে অপমান করা
❌ খারাপ নামে ডাকা
❌ হেয় করা বা বিদ্রূপ করা
❌ অশালীন/অসম্মানজনক আচরণ

✅ ভদ্রভাবে কথা বলুন
✅ সবাইকে সম্মান করুন
✅ মতের অমিল হলেও সুন্দরভাবে কথা বলুন
✅ ভালো কথা বলুন, ভালো পরিবেশ তৈরি করুন 🌸

📖 ইসলামের শিক্ষা:

আল্লাহ তাআলা বলেন, একে অপরকে উপহাস করো না এবং একে অপরকে অপমান করো না বা মন্দ নামে ডেকো না।

— সূরা আল-হুজুরাত ৪৯:১১

🕌 রাসুলুল্লাহ ﷺ বলেছেন:

“মুমিন গালিদাতা, অভিশাপদাতা, অশ্লীলভাষী বা কুরুচিপূর্ণ ভাষার মানুষ নয়।”

— জামে তিরমিজি ১৯৭৭

⚠️ RJ Team Group Rule:

🥇 ১ম বার → ⚠️ সতর্কবার্তা

🥈 ২য় বার → 🚫 Group থেকে Kick

🌸 মনে রাখুন—
আপনার কথা আপনার চরিত্রের পরিচয় দেয়।

🤲 সুন্দর কথা বলুন, অন্যকে সম্মান করুন।

🇧🇩 RJ Team Bangladesh Community
"""


# =========================================================
# BAD WORD DETECTION
# =========================================================

BAD_WORDS = [

    # Bangla
    "চোদা",
    "চোদন",
    "চুদ",
    "চুদা",
    "চুদতে",
    "চুদবি",
    "চুদবো",
    "চুদমারানি",
    "খানকি",
    "খানকির",
    "বাঞ্চোদ",
    "বাল",
    "বালের",
    "হারামজাদা",
    "হারামি",
    "শুয়োর",
    "কুত্তা",
    "কুত্তার",
    "মাদারচোদ",
    "বেশ্যা",
    "জারজ",

    # Banglish
    "chod",
    "choda",
    "chudan",
    "chud",
    "chodbi",
    "chodbo",
    "madarchod",
    "banchod",
    "khanki",
    "haramjada",
    "harami",
    "bal",
    "kutta",
    "shuar",
    "beshya",
    "jaraj",

    # English
    "fuck",
    "fucking",
    "motherfucker",
    "bitch",
    "asshole",
    "bastard",
    "shit",
    "dick",
    "pussy",
]


def normalize_text(text):

    text = text.lower()

    separators = [
        " ",
        "\n",
        "\t",
        ".",
        ",",
        "!",
        "?",
        "-",
        "_",
        "*",
        "#",
        "@",
    ]

    for char in separators:
        text = text.replace(
            char,
            ""
        )

    return text


def contains_bad_language(text):

    if not text:
        return False

    original = text.lower()

    normalized = normalize_text(
        text
    )

    for word in BAD_WORDS:

        if word in original:
            return True

        if word in normalized:
            return True

    return False


# =========================================================
# ADMIN CHECK
# =========================================================

async def is_admin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.effective_chat:
        return False

    if not update.effective_user:
        return False

    try:

        member = await context.bot.get_chat_member(
            chat_id=update.effective_chat.id,
            user_id=update.effective_user.id,
        )

        return member.status in [
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        ]

    except Exception as e:

        logger.error(
            "ADMIN CHECK ERROR: %r",
            e
        )

        return False


# =========================================================
# WELCOME NEW MEMBERS
# =========================================================

async def welcome_new_member(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.chat_member:
        return

    chat_member = update.chat_member

    old_status = (
        chat_member.old_chat_member.status
    )

    new_status = (
        chat_member.new_chat_member.status
    )

    joined_statuses = [
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.RESTRICTED,
    ]

    if new_status not in joined_statuses:
        return

    if old_status in joined_statuses:
        return

    user = (
        chat_member.new_chat_member.user
    )

    name = user.first_name or "বন্ধু"

    welcome_text = (
        f"👋 স্বাগতম {name}! 🌸\n\n"
        f"🇧🇩 {COMMUNITY_NAME}-এ আপনাকে স্বাগতম!\n\n"
        "🤝 আশা করি আপনি আমাদের সাথে সুন্দরভাবে সময় কাটাবেন।\n"
        "💬 সবাইকে সম্মান করুন এবং সুন্দর ভাষায় কথা বলুন।\n\n"
        "📜 আমাদের Group Rules ও Islamic Notice নিচে দেওয়া হলো 👇"
    )

    try:

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=welcome_text,
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=GROUP_NOTICE,
        )

    except Exception as e:

        logger.error(
            "WELCOME ERROR: %r",
            e
        )


# =========================================================
# ANTI ABUSE
# =========================================================

async def anti_abuse(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return False

    if not update.message.text:
        return False

    if update.effective_chat.type not in [
        "group",
        "supergroup",
    ]:
        return False

    user = update.effective_user

    if not user:
        return False

    # Adminদের শাস্তি দেওয়া হবে না
    if await is_admin(update, context):
        return False

    text = update.message.text

    if not contains_bad_language(text):
        return False

    warnings = context.application.bot_data.setdefault(
        "bad_language_warnings",
        {}
    )

    key = (
        update.effective_chat.id,
        user.id,
    )

    warnings[key] = (
        warnings.get(key, 0) + 1
    )

    count = warnings[key]

    # Delete message
    try:

        await update.message.delete()

    except Exception as e:

        logger.warning(
            "DELETE ERROR: %r",
            e
        )

    # First warning
    if count == 1:

        try:

            await context.bot.send_message(

                chat_id=update.effective_chat.id,

                text=(
                    f"⚠️ সতর্কবার্তা!\n\n"
                    f"👤 {user.first_name}\n\n"
                    "❌ Group-এ গালাগালি বা অশালীন ভাষা ব্যবহার করা যাবে না।\n"
                    "🌸 দয়া করে ভদ্র ও সম্মানজনক ভাষায় কথা বলুন।\n\n"
                    "📌 আর একবার এমন হলে আপনাকে Group থেকে Kick করা হবে।"
                ),
            )

        except Exception as e:

            logger.error(
                "WARNING MESSAGE ERROR: %r",
                e
            )

        return True

    # Second offense
    if count >= 2:

        try:

            await context.bot.ban_chat_member(
                chat_id=update.effective_chat.id,
                user_id=user.id,
            )

            # Ban + immediately unban = kick
            await context.bot.unban_chat_member(
                chat_id=update.effective_chat.id,
                user_id=user.id,
                only_if_banned=True,
            )

            await context.bot.send_message(

                chat_id=update.effective_chat.id,

                text=(
                    "🚫 Group থেকে Kick করা হয়েছে\n\n"
                    f"👤 User: {user.first_name}\n\n"
                    "⚠️ একই ধরনের খারাপ ভাষা দ্বিতীয়বার ব্যবহার করা হয়েছে।\n"
                    "🌸 আমাদের Group-এ ভদ্র ও সম্মানজনক আচরণ বজায় রাখুন।"
                ),
            )

            warnings.pop(
                key,
                None
            )

        except Exception as e:

            logger.error(
                "KICK ERROR: %r",
                e
            )

            try:

                await context.bot.send_message(

                    chat_id=update.effective_chat.id,

                    text=(
                        "⚠️ খারাপ ভাষা শনাক্ত হয়েছে।\n\n"
                        "❌ User-কে Kick করা যায়নি।\n"
                        "🛡️ Bot-কে Group Admin করুন এবং "
                        "Ban Users permission দিন।"
                    ),
                )

            except Exception as send_error:

                logger.error(
                    "KICK ERROR MESSAGE: %r",
                    send_error
                )

        return True

    return True


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "👋 আসসালামু আলাইকুম! 🌸\n\n"

        "🤖 আমি RJ Team Bot\n\n"

        "💬 আপনি আমাকে যেকোনো প্রশ্ন করতে পারেন।\n"
        "🇧🇩 আমি সাধারণভাবে বাংলায় উত্তর দেব।\n\n"

        "✨ প্রশ্নের বিষয় অনুযায়ী সুন্দর ও উপযুক্ত Emoji ব্যবহার করব।\n\n"

        "🌐 প্রতিটি AI উত্তরের নিচে Translate বাটন থাকবে।\n\n"

        "🚀 শুরু করতে আপনার প্রশ্ন লিখে Send করুন।"
    )


# =========================================================
# HELP
# =========================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "🤖 RJ Team Bot Help\n\n"

        "💬 যেকোনো প্রশ্ন সরাসরি লিখুন\n"
        "🇧🇩 উত্তর সাধারণভাবে বাংলায় পাবেন\n"
        "✨ প্রশ্ন অনুযায়ী সুন্দর Emoji থাকবে\n"
        "🌐 Translate দিয়ে বিভিন্ন ভাষায় অনুবাদ করতে পারবেন\n\n"

        "📌 Commands:\n\n"

        "▶️ /start — Bot চালু\n"
        "▶️ /help — Help\n"
        "▶️ /about — Bot সম্পর্কে\n"
        "▶️ /owners — Team Information\n"
        "▶️ /reset — Conversation memory reset"
    )


# =========================================================
# ABOUT
# =========================================================

async def about(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "🤖 RJ Team Bot\n\n"

        f"🏠 Community: {COMMUNITY_NAME}\n"
        f"👤 Creator: {CREATOR_NAME}\n\n"

        f"👑 Owner: {OWNER_USERNAME}\n"
        f"🤝 Partner: {PARTNER_USERNAME}\n"
        f"🛠️ Assistant: {ASSISTANT_USERNAME}\n\n"

        f"🎵 TikTok: {TIKTOK_USERNAME}\n"
        f"▶️ YouTube: {YOUTUBE_LINK}\n\n"

        "🇧🇩 RJ Team Bangladesh Community\n"
        "✨ Smart • Friendly • Helpful"
    )


# =========================================================
# OWNERS
# =========================================================

async def owners(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    keyboard = InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "👑 Owner",
                url="https://t.me/RJteam1"
            )
        ],

        [
            InlineKeyboardButton(
                "🤝 Partner",
                url="https://t.me/Apple20237"
            )
        ],

        [
            InlineKeyboardButton(
                "🛠️ Assistant",
                url="https://t.me/Apple20237"
            )
        ],

        [
            InlineKeyboardButton(
                "▶️ YouTube",
                url=YOUTUBE_LINK
            )
        ],

    ])

    await update.message.reply_text(

        "👑 RJ Team Information\n\n"

        f"👑 Owner: {OWNER_USERNAME}\n"
        f"🤝 Partner: {PARTNER_USERNAME}\n"
        f"🛠️ Assistant: {ASSISTANT_USERNAME}\n\n"

        f"🎵 Owner TikTok: {TIKTOK_USERNAME}\n"
        f"▶️ Owner YouTube: {YOUTUBE_LINK}\n\n"

        f"🤖 Community: {COMMUNITY_NAME}\n"
        f"👤 Creator: {CREATOR_NAME}\n\n"

        "✨ RJ Team-এর পক্ষ থেকে আপনাকে স্বাগতম! 🇧🇩",

        reply_markup=keyboard
    )


# =========================================================
# RESET
# =========================================================

async def reset(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["history"] = []

    await update.message.reply_text(

        "🧹 Conversation memory reset করা হয়েছে।\n\n"
        "✨ এখন নতুন করে কথা বলতে পারেন।"
    )


# =========================================================
# CREATOR QUESTION
# =========================================================

def is_creator_question(text):

    text = text.lower().strip()

    keywords = [

        "আপনাকে কে বানিয়েছে",
        "কে বানিয়েছে",
        "কে তৈরি করেছে",
        "কে তোমাকে বানিয়েছে",
        "কে তোমাকে তৈরি করেছে",
        "তোমাকে কে বানিয়েছে",
        "তোমাকে কে তৈরি করেছে",

        "who made you",
        "who created you",
        "who built you",
        "who is your creator",
        "who created this bot",

        "bot কে বানিয়েছে",
        "bot কে তৈরি করেছে",
        "creator কে",
    ]

    return any(
        keyword in text
        for keyword in keywords
    )


def creator_answer():

    return (

        "🤖 আমাকে তৈরি করেছে RJ Team Bangladesh Community 🇧🇩\n\n"

        "👤 Creator: Rakib Sar\n"
        "👑 Owner: @RJteam1\n"
        "🤝 Partner: @Apple20237\n"
        "🛠️ Assistant: @Apple20237\n\n"

        "🎵 TikTok: lyrics.song333\n"
        "▶️ YouTube: https://youtube.com/@rakib22\n\n"

        "✨ আমি RJ Team-এর AI Assistant।"
    )


# =========================================================
# AI SYSTEM INSTRUCTIONS
# =========================================================

SYSTEM_INSTRUCTIONS = """

You are RJ Team Bot, a helpful, friendly and smart Telegram AI assistant.

LANGUAGE:
Always answer in natural Bangla/Bengali by default.
Even if the user writes English or Banglish, answer in Bangla.
Only use another language when the user explicitly asks for it.

STYLE:
- Be helpful and accurate.
- Keep answers clear and easy to understand.
- Use short paragraphs.
- Use headings or bullet points when useful.
- Use beautiful and relevant emojis naturally.
- Do not use too many emojis.
- Do not put random emojis everywhere.

PERSONALITY:
Friendly, respectful, helpful and simple.

CREATOR INFORMATION:
If the user asks who created, made, built or owns this bot, use:

Created by RJ Team Bangladesh Community.
Creator: Rakib Sar.
Owner: @RJteam1.
Partner: @Apple20237.
Assistant: @Apple20237.
TikTok: lyrics.song333.
YouTube: https://youtube.com/@rakib22.

Do not invent other creator information.

If a question requires current information, explain that your knowledge may not be current unless current information is provided through available tools.

Never claim to have performed an action that you did not perform.
"""


# =========================================================
# AI RESPONSE
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

    # Group abuse protection
    if (
        update.effective_chat
        and update.effective_chat.type in [
            "group",
            "supergroup",
        ]
        and not await is_admin(update, context)
        and contains_bad_language(user_text)
    ):
        return

    # Creator question
    if is_creator_question(user_text):

        answer = creator_answer()

        sent = await update.message.reply_text(
            answer,
            reply_markup=translate_keyboard()
        )

        context.user_data[
            "last_answer"
        ] = answer

        context.user_data[
            "last_message_id"
        ] = sent.message_id

        return

    # User conversation history
    history = context.user_data.setdefault(
        "history",
        []
    )

    history.append({
        "role": "user",
        "content": user_text,
    })

    # Keep memory small
    if len(history) > 20:
        history[:] = history[-20:]

    try:

        response = await client.responses.create(

            model=OPENAI_MODEL,

            instructions=SYSTEM_INSTRUCTIONS,

            input=history,
        )

        answer = (
            response.output_text or ""
        ).strip()

        if not answer:

            answer = (
                "😔 দুঃখিত, এখন কোনো উত্তর পাওয়া যায়নি।"
            )

        history.append({
            "role": "assistant",
            "content": answer,
        })

        context.user_data[
            "last_answer"
        ] = answer

        # Telegram max message size
        chunks = [
            answer[i:i + 4000]
            for i in range(
                0,
                len(answer),
                4000
            )
        ]

        for index, chunk in enumerate(chunks):

            # Translate button only on last chunk
            keyboard = (
                translate_keyboard()
                if index == len(chunks) - 1
                else None
            )

            sent = await update.message.reply_text(
                chunk,
                reply_markup=keyboard
            )

            context.user_data[
                "last_message_id"
            ] = sent.message_id

    except Exception as e:

        logger.exception(
            "AI ERROR"
        )

        try:

            await update.message.reply_text(

                "❌ দুঃখিত, AI উত্তর দিতে সমস্যা হচ্ছে।\n\n"
                "⏳ কয়েক সেকেন্ড পরে আবার চেষ্টা করুন।"
            )

        except Exception as send_error:

            logger.error(
                "AI ERROR MESSAGE FAILED: %r",
                send_error
            )


# =========================================================
# TEXT ROUTER
# =========================================================

async def text_message_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    if not update.message.text:
        return

    # Anti abuse first
    was_abuse = await anti_abuse(
        update,
        context
    )

    if was_abuse:
        return

    await ai_reply(
        update,
        context
    )


# =========================================================
# TRANSLATE BUTTON
# =========================================================

async def translate_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    await query.message.reply_text(

        "🌐 কোন ভাষায় Translate করতে চান?\n\n"
        "👇 আপনার পছন্দের ভাষায় চাপ দিন।",

        reply_markup=language_keyboard()
    )


# =========================================================
# TRANSLATE TEXT
# =========================================================

async def translate_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    language = query.data.replace(
        "lang_",
        ""
    )

    answer = context.user_data.get(
        "last_answer"
    )

    if not answer:

        await query.message.reply_text(

            "❌ Translate করার মতো কোনো "
            "সাম্প্রতিক উত্তর পাওয়া যায়নি।"
        )

        return

    try:

        response = await client.responses.create(

            model=OPENAI_MODEL,

            instructions=(
                f"Translate the following text accurately "
                f"into {language}. "
                "Keep the original meaning and important details. "
                "Do not add extra information. "
                "Make the translation natural and easy to understand."
            ),

            input=answer,
        )

        translated = (
            response.output_text or ""
        ).strip()

        if not translated:

            translated = (
                "❌ Translation পাওয়া যায়নি।"
            )

        await query.message.reply_text(

            f"🌐 {language} Translation\n\n"
            f"{translated}"
        )

    except Exception as e:

        logger.exception(
            "TRANSLATE ERROR"
        )

        await query.message.reply_text(

            "❌ Translation করতে সমস্যা হয়েছে।\n"
            "⏳ একটু পরে আবার চেষ্টা করুন।"
        )


# =========================================================
# CLOSE TRANSLATE
# =========================================================

async def close_translate(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    try:

        await query.message.delete()

    except Exception:

        try:

            await query.message.edit_text(
                "❌ Translate menu বন্ধ করা হয়েছে।"
            )

        except Exception:
            pass


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    logger.error(
        "BOT ERROR: %r",
        context.error,
        exc_info=context.error,
    )


# =========================================================
# BUILD APPLICATION
# =========================================================

def build_application():

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Commands
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

    # Welcome
    app.add_handler(
        ChatMemberHandler(
            welcome_new_member,
            ChatMemberHandler.CHAT_MEMBER
        )
    )

    # Translate
    app.add_handler(
        CallbackQueryHandler(
            translate_button,
            pattern=r"^translate$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            translate_text,
            pattern=r"^lang_"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            close_translate,
            pattern=r"^close_translate$"
        )
    )

    # Text messages
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_message_router
        )
    )

    # Global error handler
    app.add_error_handler(
        error_handler
    )

    return app


# =========================================================
# MAIN
# =========================================================

def main():

    # Start Render HTTP server
    health_thread = Thread(
        target=start_health_server,
        daemon=True
    )

    health_thread.start()

    # Build bot
    app = build_application()

    logger.info(
        "======================================"
    )

    logger.info(
        "RJ TEAM BOT STARTING..."
    )

    logger.info(
        "OpenAI model: %s",
        OPENAI_MODEL
    )

    logger.info(
        "Render port: %s",
        PORT
    )

    logger.info(
        "Telegram polling enabled"
    )

    logger.info(
        "======================================"
    )

    # Stable Telegram polling
    app.run_polling(
        drop_pending_updates=False,
        allowed_updates=Update.ALL_TYPES,
        close_loop=True,
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()