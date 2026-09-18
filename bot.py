import os
import sqlite3
import logging
from datetime import datetime

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

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))

BKASH_NUMBER = os.getenv("BKASH_NUMBER", "01XXXXXXXXX")
NAGAD_NUMBER = os.getenv("NAGAD_NUMBER", "01XXXXXXXXX")
ROCKET_NUMBER = os.getenv("ROCKET_NUMBER", "01XXXXXXXXX")

SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@RJteam1")

DB_NAME = "orders.db"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


# =========================================================
# DATABASE
# =========================================================

def db():
    return sqlite3.connect(DB_NAME)


def init_db():
    con = db()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            service TEXT,
            link TEXT,
            quantity INTEGER,
            payment_method TEXT,
            transaction_id TEXT,
            status TEXT DEFAULT 'Pending Payment',
            created_at TEXT
        )
    """)

    con.commit()
    con.close()


def create_order(
    user_id,
    username,
    service,
    link,
    quantity,
    payment_method,
    transaction_id,
):
    con = db()
    cur = con.cursor()

    cur.execute("""
        INSERT INTO orders
        (user_id, username, service, link, quantity,
         payment_method, transaction_id, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        username,
        service,
        link,
        quantity,
        payment_method,
        transaction_id,
        "Pending Verification",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    ))

    order_id = cur.lastrowid

    con.commit()
    con.close()

    return order_id


def get_user_orders(user_id):
    con = db()
    cur = con.cursor()

    cur.execute("""
        SELECT id, service, quantity, status, created_at
        FROM orders
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 10
    """, (user_id,))

    rows = cur.fetchall()
    con.close()

    return rows


def get_order(order_id):
    con = db()
    cur = con.cursor()

    cur.execute("""
        SELECT *
        FROM orders
        WHERE id=?
    """, (order_id,))

    row = cur.fetchone()
    con.close()

    return row


def update_status(order_id, status):
    con = db()
    cur = con.cursor()

    cur.execute("""
        UPDATE orders
        SET status=?
        WHERE id=?
    """, (status, order_id))

    con.commit()
    con.close()


def all_pending_orders():
    con = db()
    cur = con.cursor()

    cur.execute("""
        SELECT id, user_id, username, service,
               quantity, payment_method,
               transaction_id, status, created_at
        FROM orders
        WHERE status='Pending Verification'
        ORDER BY id DESC
    """)

    rows = cur.fetchall()
    con.close()

    return rows


# =========================================================
# SERVICES
# =========================================================

SERVICES = {
    "youtube": [
        "YouTube Promotion",
        "YouTube Advertising",
        "YouTube Channel Promotion",
    ],
    "facebook": [
        "Facebook Page Promotion",
        "Facebook Post Promotion",
        "Facebook Video Promotion",
    ],
    "instagram": [
        "Instagram Profile Promotion",
        "Instagram Post Promotion",
        "Instagram Reel Promotion",
    ],
    "tiktok": [
        "TikTok Profile Promotion",
        "TikTok Video Promotion",
    ],
}


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    keyboard = [
        [
            InlineKeyboardButton(
                "📱 Services",
                callback_data="services"
            ),
            InlineKeyboardButton(
                "🛒 Order Now",
                callback_data="services"
            ),
        ],
        [
            InlineKeyboardButton(
                "📦 My Orders",
                callback_data="my_orders"
            ),
            InlineKeyboardButton(
                "🔎 Order Status",
                callback_data="order_status"
            ),
        ],
        [
            InlineKeyboardButton(
                "💳 Payment",
                callback_data="payment"
            ),
            InlineKeyboardButton(
                "🛠️ Support",
                callback_data="support"
            ),
        ],
    ]

    if user.id == ADMIN_ID:
        keyboard.append([
            InlineKeyboardButton(
                "👑 Admin Panel",
                callback_data="admin"
            )
        ])

    await update.message.reply_text(
        f"""
👋 Welcome {user.first_name}!

🤖 *RJ Team Social Media Service*

📱 TikTok
📘 Facebook
▶️ YouTube
📸 Instagram

🛒 এখান থেকে promotion/advertising service-এর order করতে পারবেন।

👇 নিচের Menu থেকে একটি অপশন নির্বাচন করুন।
""",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


# =========================================================
# SERVICES MENU
# =========================================================

async def services_menu(query):

    keyboard = [
        [
            InlineKeyboardButton(
                "▶️ YouTube",
                callback_data="service_youtube"
            )
        ],
        [
            InlineKeyboardButton(
                "📘 Facebook",
                callback_data="service_facebook"
            )
        ],
        [
            InlineKeyboardButton(
                "📸 Instagram",
                callback_data="service_instagram"
            )
        ],
        [
            InlineKeyboardButton(
                "🎵 TikTok",
                callback_data="service_tiktok"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 Back",
                callback_data="home"
            )
        ],
    ]

    await query.edit_message_text(
        "📱 *Select Platform*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def platform_services(query, platform):

    items = SERVICES.get(platform, [])

    keyboard = []

    for i, service in enumerate(items):
        keyboard.append([
            InlineKeyboardButton(
                service,
                callback_data=f"choose_{platform}_{i}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 Back",
            callback_data="services"
        )
    ])

    await query.edit_message_text(
        f"📱 *{platform.title()} Services*\n\n"
        "আপনার প্রয়োজনীয় service নির্বাচন করুন:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


# =========================================================
# PAYMENT
# =========================================================

async def payment_menu(query):

    text = f"""
💳 *Payment Methods*

━━━━━━━━━━━━━━━━━━

🟣 *bKash*
`{BKASH_NUMBER}`

🟢 *Nagad*
`{NAGAD_NUMBER}`

🔵 *Rocket*
`{ROCKET_NUMBER}`

━━━━━━━━━━━━━━━━━━

Payment করার পরে Transaction ID সংরক্ষণ করুন।

Order করার সময় Transaction ID দিতে হবে।
"""

    keyboard = [
        [
            InlineKeyboardButton(
                "🔙 Back",
                callback_data="home"
            )
        ]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


# =========================================================
# SUPPORT
# =========================================================

async def support_menu(query):

    keyboard = [
        [
            InlineKeyboardButton(
                "👨‍💼 Contact Support",
                url=f"https://t.me/{SUPPORT_USERNAME.replace('@', '')}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 Back",
                callback_data="home"
            )
        ],
    ]

    await query.edit_message_text(
        f"""
🛠️ *Customer Support*

যেকোনো সমস্যা বা প্রশ্নের জন্য আমাদের Support-এ যোগাযোগ করুন।

👤 Support: {SUPPORT_USERNAME}
""",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


# =========================================================
# MY ORDERS
# =========================================================

async def my_orders(query, user_id):

    rows = get_user_orders(user_id)

    if not rows:
        await query.edit_message_text(
            "📦 আপনার এখনো কোনো order নেই।",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🛒 Order Now",
                        callback_data="services"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 Back",
                        callback_data="home"
                    )
                ],
            ]),
        )
        return

    text = "📦 *Your Orders*\n\n"

    for row in rows:
        order_id, service, quantity, status, created = row

        text += (
            f"🆔 Order: `#{order_id}`\n"
            f"📱 Service: {service}\n"
            f"🔢 Quantity: {quantity}\n"
            f"📊 Status: {status}\n"
            f"🕐 {created}\n"
            f"━━━━━━━━━━━━━━\n"
        )

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 Back",
                    callback_data="home"
                )
            ]
        ]),
        parse_mode="Markdown",
    )


# =========================================================
# ORDER STATUS
# =========================================================

async def ask_order_status(query, context):

    context.user_data["waiting_status_id"] = True

    await query.edit_message_text(
        """
🔎 *Order Status*

আপনার Order ID পাঠান।

উদাহরণ:
`123`
""",
        parse_mode="Markdown",
    )


# =========================================================
# ADMIN PANEL
# =========================================================

async def admin_panel(query, user_id):

    if user_id != ADMIN_ID:
        await query.answer(
            "❌ আপনি Admin নন।",
            show_alert=True
        )
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "📦 Pending Orders",
                callback_data="pending_orders"
            )
        ],
        [
            InlineKeyboardButton(
                "🔎 Search Order",
                callback_data="admin_search"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 Back",
                callback_data="home"
            )
        ],
    ]

    await query.edit_message_text(
        """
👑 *RJ Team Admin Panel*

নিচের Menu থেকে একটি অপশন নির্বাচন করুন।
""",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def pending_orders(query, user_id):

    if user_id != ADMIN_ID:
        return

    rows = all_pending_orders()

    if not rows:
        await query.edit_message_text(
            "✅ কোনো Pending Order নেই।",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Admin Panel",
                        callback_data="admin"
                    )
                ]
            ]),
        )
        return

    for row in rows[:10]:

        (
            order_id,
            customer_id,
            username,
            service,
            quantity,
            payment,
            transaction,
            status,
            created,
        ) = row

        text = f"""
📦 *New Order*

🆔 Order: `#{order_id}`
👤 User: @{username or 'N/A'}
🆔 User ID: `{customer_id}`

📱 Service: {service}
🔢 Quantity: {quantity}

💳 Payment: {payment}
🧾 Transaction ID:
`{transaction}`

📊 Status: {status}
🕐 {created}
"""

        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Approve",
                    callback_data=f"approve_{order_id}"
                ),
                InlineKeyboardButton(
                    "❌ Reject",
                    callback_data=f"reject_{order_id}"
                ),
            ]
        ]

        await query.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    await query.edit_message_text(
        "📦 Pending orders উপরে দেখানো হয়েছে।",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 Admin Panel",
                    callback_data="admin"
                )
            ]
        ]),
    )


# =========================================================
# CALLBACK HANDLER
# =========================================================

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id

    # HOME
    if data == "home":

        keyboard = [
            [
                InlineKeyboardButton(
                    "📱 Services",
                    callback_data="services"
                ),
                InlineKeyboardButton(
                    "🛒 Order Now",
                    callback_data="services"
                ),
            ],
            [
                InlineKeyboardButton(
                    "📦 My Orders",
                    callback_data="my_orders"
                ),
                InlineKeyboardButton(
                    "🔎 Order Status",
                    callback_data="order_status"
                ),
            ],
            [
                InlineKeyboardButton(
                    "💳 Payment",
                    callback_data="payment"
                ),
                InlineKeyboardButton(
                    "🛠️ Support",
                    callback_data="support"
                ),
            ],
        ]

        if user_id == ADMIN_ID:
            keyboard.append([
                InlineKeyboardButton(
                    "👑 Admin Panel",
                    callback_data="admin"
                )
            ])

        await query.edit_message_text(
            "🏠 *RJ Team Main Menu*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return

    # SERVICES
    if data == "services":
        await services_menu(query)
        return

    # PLATFORM
    if data.startswith("service_"):

        platform = data.replace("service_", "")
        await platform_services(query, platform)
        return

    # CHOOSE SERVICE
    if data.startswith("choose_"):

        parts = data.split("_")

        platform = parts[1]
        index = int(parts[2])

        service = SERVICES[platform][index]

        context.user_data.clear()
        context.user_data["service"] = service

        await query.edit_message_text(
            f"""
🛒 *New Order*

📱 Service:
*{service}*

এখন আপনার পোস্ট/ভিডিও/profile-এর **link** পাঠান।
""",
            parse_mode="Markdown",
        )

        context.user_data["waiting_link"] = True
        return

    # PAYMENT
    if data == "payment":
        await payment_menu(query)
        return

    # SUPPORT
    if data == "support":
        await support_menu(query)
        return

    # MY ORDERS
    if data == "my_orders":
        await my_orders(query, user_id)
        return

    # ORDER STATUS
    if data == "order_status":
        await ask_order_status(query, context)
        return

    # ADMIN
    if data == "admin":
        await admin_panel(query, user_id)
        return

    # PENDING
    if data == "pending_orders":
        await pending_orders(query, user_id)
        return

    # APPROVE
    if data.startswith("approve_"):

        if user_id != ADMIN_ID:
            return

        order_id = int(data.split("_")[1])

        order = get_order(order_id)

        if not order:
            await query.answer(
                "Order পাওয়া যায়নি।",
                show_alert=True
            )
            return

        update_status(
            order_id,
            "Approved"
        )

        customer_id = order[1]

        try:
            await context.bot.send_message(
                customer_id,
                f"""
✅ *Order Approved*

🆔 Order ID: `#{order_id}`

আপনার payment verification সম্পন্ন হয়েছে।

📊 Status: *Approved*
""",
                parse_mode="Markdown",
            )
        except Exception:
            pass

        await query.edit_message_text(
            f"✅ Order `#{order_id}` Approved.",
            parse_mode="Markdown",
        )
        return

    # REJECT
    if data.startswith("reject_"):

        if user_id != ADMIN_ID:
            return

        order_id = int(data.split("_")[1])

        order = get_order(order_id)

        if not order:
            await query.answer(
                "Order পাওয়া যায়নি।",
                show_alert=True
            )
            return

        update_status(
            order_id,
            "Rejected"
        )

        customer_id = order[1]

        try:
            await context.bot.send_message(
                customer_id,
                f"""
❌ *Order Rejected*

🆔 Order ID: `#{order_id}`

আপনার payment/order verification reject করা হয়েছে।

Support: {SUPPORT_USERNAME}
""",
                parse_mode="Markdown",
            )
        except Exception:
            pass

        await query.edit_message_text(
            f"❌ Order `#{order_id}` Rejected.",
            parse_mode="Markdown",
        )
        return


# =========================================================
# MESSAGE HANDLER
# =========================================================

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    text = update.message.text.strip()

    # ORDER STATUS SEARCH
    if context.user_data.get("waiting_status_id"):

        context.user_data.pop("waiting_status_id", None)

        if not text.isdigit():
            await update.message.reply_text(
                "❌ সঠিক Order ID দিন।"
            )
            return

        order_id = int(text)
        order = get_order(order_id)

        if not order:
            await update.message.reply_text(
                "❌ এই Order ID পাওয়া যায়নি।"
            )
            return

        if order[1] != user.id and user.id != ADMIN_ID:
            await update.message.reply_text(
                "❌ এই Order আপনার নয়।"
            )
            return

        await update.message.reply_text(
            f"""
🔎 *Order Information*

🆔 Order: `#{order[0]}`
📱 Service: {order[3]}
🔗 Link: {order[4]}
🔢 Quantity: {order[5]}

💳 Payment: {order[6]}
🧾 Transaction ID: `{order[7]}`

📊 Status: *{order[8]}*
🕐 {order[9]}
""",
            parse_mode="Markdown",
        )
        return

    # ORDER LINK
    if context.user_data.get("waiting_link"):

        context.user_data["link"] = text
        context.user_data.pop("waiting_link", None)
        context.user_data["waiting_quantity"] = True

        await update.message.reply_text(
            """
🔢 এখন Quantity লিখুন।

উদাহরণ:
`100`

শুধু সংখ্যা লিখবেন।
"""
        )
        return

    # QUANTITY
    if context.user_data.get("waiting_quantity"):

        if not text.isdigit():
            await update.message.reply_text(
                "❌ Quantity হিসেবে শুধু সংখ্যা দিন।"
            )
            return

        quantity = int(text)

        if quantity <= 0:
            await update.message.reply_text(
                "❌ সঠিক Quantity দিন।"
            )
            return

        context.user_data["quantity"] = quantity
        context.user_data.pop("waiting_quantity", None)
        context.user_data["waiting_payment"] = True

        keyboard = [
            [
                InlineKeyboardButton(
                    "🟣 bKash",
                    callback_data="pay_bkash"
                )
            ],
            [
                InlineKeyboardButton(
                    "🟢 Nagad",
                    callback_data="pay_nagad"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔵 Rocket",
                    callback_data="pay_rocket"
                )
            ],
        ]

        await update.message.reply_text(
            """
💳 *Payment Method*

একটি Payment Method নির্বাচন করুন।
""",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return

    # TRANSACTION ID
    if context.user_data.get("waiting_transaction"):

        transaction_id = text

        service = context.user_data.get("service")
        link = context.user_data.get("link")
        quantity = context.user_data.get("quantity")
        payment = context.user_data.get("payment")

        order_id = create_order(
            user.id,
            user.username or "",
            service,
            link,
            quantity,
            payment,
            transaction_id,
        )

        await update.message.reply_text(
            f"""
✅ *Order Submitted*

🆔 Order ID:
`#{order_id}`

📱 Service: {service}
🔢 Quantity: {quantity}
💳 Payment: {payment}

🧾 Transaction ID:
`{transaction_id}`

📊 Status: *Pending Verification*

Admin payment verify করার পর status update হবে।
""",
            parse_mode="Markdown",
        )

        # ADMIN NOTIFICATION
        try:
            await context.bot.send_message(
                ADMIN_ID,
                f"""
🔔 *New Order Received*

🆔 Order: `#{order_id}`

👤 User: @{user.username or 'N/A'}
🆔 User ID: `{user.id}`

📱 Service: {service}
🔗 Link: {link}
🔢 Quantity: {quantity}

💳 Payment: {payment}
🧾 Transaction ID:
`{transaction_id}`

📊 Status: Pending Verification
""",
                parse_mode="Markdown",
            )
        except Exception:
            pass

        context.user_data.clear()
        return

    await update.message.reply_text(
        "🏠 Main Menu দেখতে /start লিখুন।"
    )


# =========================================================
# PAYMENT CALLBACK
# =========================================================

async def payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    if not data.startswith("pay_"):
        return

    method = data.replace("pay_", "")

    numbers = {
        "bkash": BKASH_NUMBER,
        "nagad": NAGAD_NUMBER,
        "rocket": ROCKET_NUMBER,
    }

    names = {
        "bkash": "bKash",
        "nagad": "Nagad",
        "rocket": "Rocket",
    }

    context.user_data["payment"] = names[method]
    context.user_data["waiting_transaction"] = True

    await query.edit_message_text(
        f"""
💳 *{names[method]} Payment*

📱 Number:
`{numbers[method]}`

Payment করার পর Transaction ID সংগ্রহ করুন।

তারপর এখানে শুধু Transaction ID পাঠান।
""",
        parse_mode="Markdown",
    )


# =========================================================
# GENERAL CALLBACK ROUTER
# =========================================================

async def all_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = update.callback_query.data

    if data.startswith("pay_"):
        await payment_callback(update, context)
    else:
        await callback_handler(update, context)


# =========================================================
# MAIN
# =========================================================

def main():

    if BOT_TOKEN == "YOUR_BOT_TOKEN":
        print("❌ BOT_TOKEN সেট করুন।")
        return

    init_db()

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CallbackQueryHandler(all_callbacks)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler
        )
    )

    print("🤖 RJ Team Bot is running...")

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()