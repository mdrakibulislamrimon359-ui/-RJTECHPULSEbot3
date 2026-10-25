# ==========================================================
# RJ TEAM BANGLADESH - BUSINESS AI AUTO REPLY
# Render Web Service + Telegram Business + Gemini AI
# ==========================================================

import os
import time
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import requests
from google import genai
from google.genai import types

# -------------------- LOGGING --------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

# -------------------- ENVIRONMENT --------------------

BOT_TOKEN = os.getenv("BUSINESS_BOT_TOKEN", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
PORT = int(os.getenv("PORT", "10000"))

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL", "gemini-3.8-flash"
).strip()

if not BOT_TOKEN:
    raise RuntimeError("BUSINESS_BOT_TOKEN is missing")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

telegram = requests.Session()
ai = genai.Client(api_key=GEMINI_API_KEY)

# -------------------- AI SETTINGS --------------------

SYSTEM_PROMPT = """
তুমি RJ TEAM BANGLADESH-এর সহায়ক AI অ্যাসিস্ট্যান্ট।

নিয়ম:
১. বাংলায় প্রশ্ন করলে বাংলায় উত্তর দেবে।
২. বাংলিশে প্রশ্ন করলে সহজ বাংলায় উত্তর দেবে।
৩. ইংরেজিতে প্রশ্ন করলে ইংরেজিতে উত্তর দেবে।
৪. ভদ্র, সংক্ষিপ্ত ও প্রাসঙ্গিক উত্তর দেবে।
৫. অজানা তথ্য বানিয়ে বলবে না।
৬. অ্যাকাউন্টের মালিকের হয়ে মিথ্যা প্রতিশ্রুতি দেবে না।
৭. ব্যক্তিগত তথ্য, পাসওয়ার্ড বা গোপন তথ্য চাইবে না।
৮. ব্যবহারকারীর প্রশ্নের উত্তর দেওয়াই তোমার কাজ।
"""

MODEL_FALLBACKS = [
    GEMINI_MODEL,
    "gemini-3.8-flash",
    "gemini-2.5-flash",
]

# Duplicate model names বাদ
MODEL_FALLBACKS = list(dict.fromkeys(MODEL_FALLBACKS))

# -------------------- TELEGRAM API --------------------

def tg(method, data=None, timeout=60):
    response = telegram.post(
        f"{TELEGRAM_API}/{method}",
        json=data or {},
        timeout=timeout
    )

    response.raise_for_status()
    result = response.json()

    if not result.get("ok"):
        raise RuntimeError(
            f"Telegram API error: {result.get('description', 'Unknown error')}"
        )

    return result["result"]


# -------------------- GEMINI AI --------------------

def make_answer(question):
    last_error = None

    for model in MODEL_FALLBACKS:
        try:
            response = ai.models.generate_content(
                model=model,
                contents=question,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens=500,
                ),
            )

            answer = (response.text or "").strip()

            if answer:
                logging.info("Gemini response generated")
                return answer[:4000]

            last_error = RuntimeError("Gemini returned empty response")

        except Exception as exc:
            last_error = exc
            # প্রশ্ন বা API key লগে প্রকাশ করা হবে না
            logging.warning(
                "Gemini model failed: %s (%s)",
                model,
                type(exc).__name__,
            )

    raise RuntimeError(
        f"All Gemini models failed: {type(last_error).__name__}"
    )


# -------------------- MESSAGE HANDLER --------------------

def handle_business_message(message):
    chat = message.get("chat", {})
    sender = message.get("from", {})

    # শুধু ব্যক্তিগত চ্যাট
    if chat.get("type") != "private":
        return

    # বটের নিজের মেসেজ উপেক্ষা
    if sender.get("is_bot"):
        return

    # ব্যক্তিগত ইনকামিং মেসেজ যাচাই
    if sender.get("id") != chat.get("id"):
        return

    question = (message.get("text") or "").strip()

    # শুধু টেক্সট মেসেজ; ছবি/ভয়েস এখনো সমর্থিত নয়
    if not question:
        return

    connection_id = message.get("business_connection_id")

    if not connection_id:
        logging.warning("Business connection ID missing")
        return

    try:
        answer = make_answer(question)

        tg(
            "sendMessage",
            {
                "business_connection_id": connection_id,
                "chat_id": chat["id"],
                "text": answer,
                "reply_parameters": {
                    "message_id": message["message_id"]
                },
            },
            timeout=30,
        )

        logging.info("Business auto-reply sent")

    except Exception as exc:
        logging.error(
            "Auto-reply failed: %s",
            type(exc).__name__,
        )


# -------------------- WEB SERVER --------------------

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/health"):
            body = b"RJ Business AI Auto-Reply is running"

            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass


def start_web_server():
    server = ThreadingHTTPServer(
        ("0.0.0.0", PORT),
        HealthHandler,
    )

    logging.info("Web server listening on port %s", PORT)
    server.serve_forever()


# -------------------- TELEGRAM POLLING --------------------

def main():
    offset = None

    logging.info("RJ Business AI Auto-Reply starting")

    # একই Token-এর অন্য প্রোগ্রাম যেন getUpdates ব্যবহার না করে
    # নিশ্চিত করুন যে অন্য কোথাও এই Bot Token-এর polling চলছে না।

    while True:
        try:
            params = {
                "timeout": 50,
                "allowed_updates": [
                    "business_connection",
                    "business_message",
                ],
            }

            if offset is not None:
                params["offset"] = offset

            updates = tg(
                "getUpdates",
                params,
                timeout=60,
            )

            for update in updates:
                # প্রতিটি Update-এর offset এগিয়ে নিন
                offset = update["update_id"] + 1

                # নতুন Business Connection-এর খবর
                if "business_connection" in update:
                    logging.info(
                        "Business connection update received"
                    )

                message = update.get("business_message")

                if message:
                    handle_business_message(message)

        except KeyboardInterrupt:
            logging.info("Service stopping")
            break

        except Exception as exc:
            logging.error(
                "Telegram polling failed: %s",
                type(exc).__name__,
            )
            time.sleep(5)


# -------------------- START --------------------

if __name__ == "__main__":
    threading.Thread(
        target=start_web_server,
        daemon=True,
    ).start()

    main()
