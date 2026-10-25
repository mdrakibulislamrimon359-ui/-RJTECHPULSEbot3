import os
import time
import logging
import requests
from google import genai
from google.genai import types

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

BOT_TOKEN = os.environ["BUSINESS_BOT_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
telegram = requests.Session()
ai = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
তুমি RJ TEAM BANGLADESH-এর সহায়ক AI অ্যাসিস্ট্যান্ট।
ব্যবহারকারীর প্রশ্ন বুঝে সংক্ষিপ্ত, ভদ্র ও প্রাসঙ্গিক উত্তর দেবে।
বাংলায় প্রশ্ন করলে বাংলায়, বাংলিশে করলে সহজ বাংলায়,
ইংরেজিতে করলে ইংরেজিতে উত্তর দেবে।
অজানা তথ্য বানিয়ে বলবে না।
অ্যাকাউন্টের মালিকের পরিচয়, ব্যক্তিগত তথ্য বা
অনুমোদনহীন প্রতিশ্রুতি বানিয়ে বলবে না।
শুধু ব্যবহারকারীর প্রশ্নের উত্তর দেবে।
"""

def tg(method, data=None, timeout=60):
    response = telegram.post(
        f"{TELEGRAM_API}/{method}",
        json=data or {},
        timeout=timeout
    )
    response.raise_for_status()
    result = response.json()
    if not result.get("ok"):
        raise RuntimeError(str(result))
    return result["result"]

def make_answer(question):
    response = ai.models.generate_content(
        model=GEMINI_MODEL,
        contents=question,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=500,
        ),
    )
    answer = (response.text or "").strip()
    if not answer:
        raise RuntimeError("Gemini returned an empty response")
    return answer[:4000]

def handle_business_message(message):
    # শুধু ব্যক্তিগত চ্যাটের টেক্সট মেসেজ
    chat = message.get("chat", {})
    sender = message.get("from", {})

    if chat.get("type") != "private":
        return

    if sender.get("is_bot"):
        return

    # ইনকামিং ব্যক্তিগত মেসেজে sender ID ও chat ID একই।
    # নিজের পাঠানো মেসেজ পুনরায় উত্তর দেওয়া এড়ানো।
    if sender.get("id") != chat.get("id"):
        return

    question = (message.get("text") or "").strip()
    if not question:
        return

    connection_id = message.get("business_connection_id")
    if not connection_id:
        logging.warning("Business connection ID missing")
        return

    # সংক্ষিপ্ত ও নিরাপদ প্রশ্নের উত্তর তৈরি
    try:
        answer = make_answer(question)
        tg("sendMessage", {
            "business_connection_id": connection_id,
            "chat_id": chat["id"],
            "text": answer,
            "reply_parameters": {
                "message_id": message["message_id"]
            }
        })
        logging.info("Auto-replied to private business message")
    except Exception:
        # প্রশ্ন বা ব্যক্তিগত বার্তা লগে প্রকাশ করা হবে না
        logging.exception("Auto-reply failed")

def main():
    offset = None
    logging.info("RJ Business AI Auto-Reply starting")

    while True:
        try:
            data = {
                "timeout": 50,
                "allowed_updates": [
                    "business_connection",
                    "business_message"
                ]
            }
            if offset is not None:
                data["offset"] = offset

            updates = tg("getUpdates", data, timeout=60)

            for update in updates:
                offset = update["update_id"] + 1

                message = update.get("business_message")
                if message:
                    handle_business_message(message)

        except KeyboardInterrupt:
            break
        except Exception:
            logging.exception("Polling error")
            time.sleep(5)

if __name__ == "__main__":
    main()
