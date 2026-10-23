import os
import asyncio
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from faster_whisper import WhisperModel
from deep_translator import GoogleTranslator
import edge_tts


# ==================== CONFIGURATION ====================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
MAX_VIDEO_MB = int(os.getenv("MAX_VIDEO_MB", "20"))
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL", "base")
MAX_TRANSCRIPT_CHARS = int(os.getenv("MAX_TRANSCRIPT_CHARS", "4500"))

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("video-translator")


# Language name: (translation language code, TTS voice)
LANGUAGES = {
    "বাংলা": ("bn", "bn-BD-NabanitaNeural"),
    "English": ("en", "en-US-AriaNeural"),
    "हिन्दी": ("hi", "hi-IN-SwaraNeural"),
    "العربية": ("ar", "ar-SA-ZariyahNeural"),
    "Español": ("es", "es-ES-ElviraNeural"),
    "Français": ("fr", "fr-FR-DeniseNeural"),
    "日本語": ("ja", "ja-JP-NanamiNeural"),
    "Português": ("pt", "pt-BR-FranciscaNeural"),
    "Русский": ("ru", "ru-RU-SvetlanaNeural"),
    "中文": ("zh-CN", "zh-CN-XiaoxiaoNeural"),
}

# Whisper model is loaded only when needed.
whisper_model = None


# ==================== HELPER FUNCTIONS ====================

def run_command(args):
    """Run an external command and report errors."""
    result = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr[-1800:] or "External command failed."
        )

    return result.stdout


def ensure_ffmpeg():
    """Check that FFmpeg is installed."""
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "FFmpeg পাওয়া যায়নি। FFmpeg ইনস্টল করে PATH-এ যোগ করুন।"
        )


def get_whisper():
    """Load the speech recognition model."""
    global whisper_model

    if whisper_model is None:
        whisper_model = WhisperModel(
            WHISPER_MODEL_SIZE,
            device="cpu",
            compute_type="int8",
        )

    return whisper_model


def extract_audio(video_path: Path, wav_path: Path):
    """Extract audio from the uploaded video."""
    run_command([
        "ffmpeg",
        "-y",
        "-i", str(video_path),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        str(wav_path),
    ])


def transcribe_audio(wav_path: Path) -> str:
    """Convert spoken audio into text."""
    model = get_whisper()

    segments, _info = model.transcribe(
        str(wav_path),
        vad_filter=True,
        beam_size=1,
    )

    transcript = " ".join(
        segment.text.strip() for segment in segments
    ).strip()

    if not transcript:
        raise RuntimeError(
            "ভিডিওতে পরিষ্কার কথা শনাক্ত করা যায়নি।"
        )

    return transcript


def translate_text(text: str, target_lang: str) -> str:
    """Translate text into the selected language."""
    chunks = []
    remaining = text.strip()

    while remaining:
        if len(remaining) <= 3500:
            chunks.append(remaining)
            break

        split_at = remaining.rfind(" ", 0, 3500)

        if split_at < 1000:
            split_at = 3500

        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()

    translated_chunks = []

    for chunk in chunks:
        if chunk:
            translated = GoogleTranslator(
                source="auto",
                target=target_lang,
            ).translate(chunk)

            if translated:
                translated_chunks.append(translated)

    result = " ".join(translated_chunks).strip()

    if not result:
        raise RuntimeError("অনুবাদ তৈরি করা যায়নি।")

    return result


async def synthesize_speech(
    text: str,
    voice: str,
    output_path: Path,
):
    """Generate translated speech using Edge TTS."""
    if not text:
        raise RuntimeError("অনুবাদ করা লেখা খালি।")

    communicator = edge_tts.Communicate(text, voice)
    await communicator.save(str(output_path))


def mux_video(
    video_path: Path,
    audio_path: Path,
    output_path: Path,
):
    """Replace the video's original audio with translated speech."""
    run_command([
        "ffmpeg",
        "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "28",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        str(output_path),
    ])


async def process_video(
    video_path: Path,
    output_path: Path,
    target_lang: str,
    voice: str,
):
    """Extract, transcribe, translate, synthesize, and combine."""
    ensure_ffmpeg()

    work_dir = video_path.parent
    wav_path = work_dir / "source_audio.wav"
    tts_path = work_dir / "translated_voice.mp3"

    # Run CPU-heavy processing in worker threads.
    await asyncio.to_thread(
        extract_audio,
        video_path,
        wav_path,
    )

    original_text = await asyncio.to_thread(
        transcribe_audio,
        wav_path,
    )

    original_text = original_text[:MAX_TRANSCRIPT_CHARS]

    translated_text = await asyncio.to_thread(
        translate_text,
        original_text,
        target_lang,
    )

    await synthesize_speech(
        translated_text,
        voice,
        tts_path,
    )

    await asyncio.to_thread(
        mux_video,
        video_path,
        tts_path,
        output_path,
    )

    return original_text, translated_text


# ==================== TELEGRAM COMMANDS ====================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Handle /start."""
    await update.effective_message.reply_text(
        "🎬 AI Video Voice Translator Bot-এ স্বাগতম!\n\n"
        "কীভাবে ব্যবহার করবেন:\n"
        "১. ২০ MB-এর কম একটি ভিডিও পাঠান।\n"
        "২. পছন্দের অনুবাদের ভাষা বেছে নিন।\n"
        "৩. প্রসেসিং শেষ হলে নতুন অডিওসহ ভিডিও পাবেন।\n\n"
        "⚠️ এটি একটি প্রাথমিক সংস্করণ।\n"
        "এটি সাধারণ AI voice ব্যবহার করে; মূল বক্তার কণ্ঠ "
        "ক্লোন করে না। অনুবাদ করা অডিওর টাইমিং মূল ভিডিওর "
        "সঙ্গে পুরোপুরি মিলবে না।"
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Handle /help."""
    await start(update, context)


# ==================== VIDEO HANDLER ====================

async def video_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Receive a video and ask the user to select a language."""
    message = update.effective_message

    item = message.video

    if (
        item is None
        and message.document
        and (message.document.mime_type or "").startswith("video/")
    ):
        item = message.document

    if item is None:
        await message.reply_text(
            "দয়া করে একটি ভিডিও ফাইল পাঠান।"
        )
        return

    size = item.file_size or 0

    if size > MAX_VIDEO_MB * 1024 * 1024:
        await message.reply_text(
            f"ভিডিওটি {MAX_VIDEO_MB} MB-এর বেশি। "
            "ছোট ভিডিও দিয়ে আবার চেষ্টা করুন।"
        )
        return

    context.user_data["pending_video_file_id"] = item.file_id

    keyboard = [
        [
            InlineKeyboardButton(
                label,
                callback_data=f"lang|{code}|{voice}",
            )
        ]
        for label, (code, voice) in LANGUAGES.items()
    ]

    await message.reply_text(
        "✅ ভিডিও পেয়েছি।\n\n"
        "কোন ভাষায় ভয়েস চান?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ==================== LANGUAGE SELECTION ====================

async def language_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Process the video after a language is selected."""
    query = update.callback_query
    await query.answer()

    file_id = context.user_data.get("pending_video_file_id")

    if not file_id:
        await query.edit_message_text(
            "আগে একটি ভিডিও পাঠান, তারপর ভাষা নির্বাচন করুন।"
        )
        return

    try:
        _prefix, target_lang, voice = query.data.split("|", 2)
    except ValueError:
        await query.edit_message_text(
            "ভাষা নির্বাচন বুঝতে পারিনি। আবার চেষ্টা করুন।"
        )
        return

    await query.edit_message_text(
        "⏳ ভিডিও প্রসেস হচ্ছে।\n\n"
        "প্রথমবার AI মডেল ডাউনলোড হতে পারে, তাই সময় লাগতে পারে।"
    )

    temp_dir = Path(
        tempfile.mkdtemp(prefix="video_translator_")
    )

    try:
        telegram_file = await context.bot.get_file(file_id)

        input_path = temp_dir / "input_video.mp4"
        output_path = temp_dir / "translated_video.mp4"

        await telegram_file.download_to_drive(
            custom_path=str(input_path)
        )

        _original, translated = await process_video(
            input_path,
            output_path,
            target_lang,
            voice,
        )

        if not output_path.exists():
            raise RuntimeError("আউটপুট ভিডিও তৈরি হয়নি।")

        if output_path.stat().st_size > 49 * 1024 * 1024:
            await query.message.reply_text(
                "ভিডিও তৈরি হয়েছে, কিন্তু ফাইলটি Telegram-এ "
                "পাঠানোর জন্য অনেক বড়। ছোট ভিডিও দিয়ে চেষ্টা করুন।"
            )
            return

        await query.message.reply_text(
            "✅ অনুবাদ সম্পন্ন! ভিডিও পাঠাচ্ছি..."
        )

        with output_path.open("rb") as video_file:
            await query.message.reply_video(
                video=video_file,
                caption="অনুবাদ করা ভিডিও 🎧",
                supports_streaming=True,
                read_timeout=120,
                write_timeout=120,
                connect_timeout=30,
            )

        await query.message.reply_text(
            "📝 অনুবাদ করা কথার নমুনা:\n\n"
            + translated[:3000]
        )

    except Exception as exc:
        log.exception("Video processing failed")

        error_text = str(exc)

        if TOKEN:
            error_text = error_text.replace(TOKEN, "[TOKEN]")

        await query.message.reply_text(
            "দুঃখিত, ভিডিও প্রসেস করা যায়নি।\n\n"
            "সম্ভাব্য কারণ:\n"
            "• FFmpeg ইনস্টল করা নেই\n"
            "• ইন্টারনেট বা অনুবাদ পরিষেবার সমস্যা\n"
            "• কম RAM বা ডিস্ক স্পেস\n"
            "• ভিডিওতে পরিষ্কার কথা নেই\n\n"
            "বিস্তারিত ত্রুটি:\n"
            + error_text[:900]
        )

    finally:
        context.user_data.pop(
            "pending_video_file_id",
            None,
        )

        shutil.rmtree(
            temp_dir,
            ignore_errors=True,
        )


# ==================== ERROR HANDLER ====================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Log unexpected Telegram errors."""
    log.error(
        "Unhandled Telegram error",
        exc_info=context.error,
    )


# ==================== START BOT ====================

def main():
    """Start the Telegram bot."""
    if not TOKEN:
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN সেট করা নেই।\n\n"
            "Linux/macOS:\n"
            "export TELEGRAM_BOT_TOKEN='YOUR_TOKEN'\n\n"
            "Windows PowerShell:\n"
            '$env:TELEGRAM_BOT_TOKEN="YOUR_TOKEN"'
        )

    ensure_ffmpeg()

    app = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("help", help_command)
    )

    app.add_handler(
        MessageHandler(
            filters.VIDEO | filters.Document.VIDEO,
            video_handler,
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            language_handler,
            pattern=r"^lang\|",
        )
    )

    app.add_error_handler(error_handler)

    log.info("AI Video Voice Translator Bot is starting...")

    app.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
