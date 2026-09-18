import os
import sqlite3
import logging
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================================================
# SETTINGS
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")

ADMIN_ID = 123890
ADMIN_USERNAME = "RJteam1"

BKASH_NUMBER = os.getenv("BKASH_NUMBER", "01XXXXXXXXX")
NAGAD_NUMBER = os.getenv("NAGAD_NUMBER", "01XXXXXXXXX")
ROCKET_NUMBER = os.getenv("ROCKET_NUMBER", "01XXXXXXXXX")

SUPPORT = "@RJteam1"

DB = "rjteam.db"

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


# =========================================================
# DATABASE
# =========================================================

def connect():
    return sqlite3.connect(DB)


def init_db():
    con = connect()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        joined TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        service TEXT,
        link TEXT,
        quantity INTEGER,
        payment TEXT,
        transaction_id TEXT,
        status TEXT,
        created TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        platform TEXT,
        price REAL DEFAULT 0,
        active INTEGER DEFAULT 1
    )
    """)

    cur.execute("SELECT COUNT(*) FROM services")
    count = cur.fetchone()[0]

    if count == 0:
        services = [
            ("YouTube Promotion", "YouTube", 0),
            ("YouTube Advertising", "YouTube", 0),
            ("YouTube Channel Promotion", "YouTube", 0),

            ("Facebook Page Promotion", "Facebook", 0),
            ("Facebook Post Promotion", "Facebook", 0),
            ("Facebook Video Promotion", "Facebook", 0),

            ("Instagram Profile Promotion", "Instagram", 0),
            ("Instagram Post Promotion", "Instagram", 0),
            ("Instagram Reel Promotion", "Instagram", 0),

            ("TikTok Profile Promotion", "TikTok", 0),
            ("TikTok Video Promotion", "TikTok", 0),
        ]

        cur.executemany("""
        INSERT INTO services(name, platform, price)
        VALUES (?, ?, ?)
        """, services)

    con.commit()
    con.close()


def save_user(user):
    con = connect()
    cur = con.cursor()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cur.execute("""
    INSERT INTO users
    (user_id, username, first_name, joined)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(user_id) DO UPDATE SET
        username=excluded.username,
        first_name=excluded.first_name
    """, (
        user.id,
        user.username or "",
        user.first_name or "",
        now,
    ))

    con.commit()
    con.close()


def get_services(platform=None):
    con = connect()
    cur = con.cursor()

    if platform:
        cur.execute("""
        SELECT id, name, price
        FROM services
        WHERE platform=? AND active=1
        ORDER BY id
        """, (platform,))
    else:
        cur.execute("""
        SELECT id, name, platform, price, active
        FROM services
        ORDER BY id
        """)

    rows = cur.fetchall()
    con.close()
    return rows


def get_service(service_id):
    con = connect()
    cur = con.cursor()

    cur.execute("""
    SELECT id, name, platform, price, active
    FROM services
    WHERE id=?
    """, (service_id,))

    row = cur.fetchone()
    con.close()
    return row


def create_order(user, service, link, quantity, payment, transaction):
    con = connect()
    cur = con.cursor()

    cur.execute("""
    INSERT INTO orders
    (user_id, username, service, link, quantity,
     payment, transaction_id, status, created)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user.id,
        user.username or "",
        service,
        link,
        quantity,
        payment,
        transaction,
        "Pending Verification",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    ))

    order_id = cur.lastrowid

    con.commit()
    con.close()

    return order_id


def get_order(order_id):
    con = connect()
    cur = con.cursor()

    cur.execute("""
    SELECT *
    FROM orders
    WHERE id=?
    """, (order_id,))

    row = cur.fetchone()
    con.close()

    return row


def user_orders(user_id):
    con = connect()
    cur = con.cursor()

    cur.execute("""
    SELECT id, service, quantity, status, created
    FROM orders
    WHERE user_id=?
    ORDER BY id DESC
    LIMIT 20
    """, (user_id,))

    rows = cur.fetchall()
    con.close()

    return rows


def pending_orders():
    con = connect()
    cur = con.cursor()

    cur.execute("""
    SELECT *
    FROM orders
    WHERE status='Pending Verification'
    ORDER BY id DESC
    """)

    rows = cur.fetchall()
    con.close()

    return rows


def set_status(order_id, status):
    con = connect()
    cur = con.cursor()

    cur.execute("""
    UPDATE orders
    SET status=?
    WHERE id=?
    """, (status, order_id))

    con.commit()
    con.close()


def total_users():
    con = connect()
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    result = cur.fetchone()[0]

    con.close()
    return result


def total_orders():
    con = connect()
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) FROM orders")
    result = cur.fetchone()[0]

    con.close()
    return result


def all_users():
    con = connect()
    cur = con.cursor()

    cur.execute("SELECT user_id FROM users")

    rows = cur.fetchall()
    con.close()

    return [x[0] for x in rows]


def change_price(service_id, price):
    con = connect()
    cur = con.cursor()

    cur.execute("""
    UPDATE services
    SET price=?
    WHERE id=?
    """, (price, service_id))

    con.commit()
    con.close()


def toggle_service(service_id):
    con = connect()
    cur = con.cursor()

    cur.execute("""
    UPDATE services
    SET active =
        CASE active
        WHEN 1 THEN 0
        ELSE 1
        END
    WHERE id=?
    """, (service_id,))

    con.commit()
    con.close()


# =========================================================
# ADMIN
# =========================================================

def is_admin(user_id, username=None):
    return (
        user_id == ADMIN_ID
        or (
            username
            and username.lower().lstrip("@")
            == ADMIN_USERNAME.lower().lstrip("@")
        )
    )


# =========================================================
# HOME
# =========================================================

def home_keyboard(user_id, username=None):

    keyboard = [
        [
            InlineKeyboardButton(
                "📱 Services",
                callback_data="services"
            ),
            InlineKeyboardButton(
                "🛒 Order",
                callback_data="services"
            ),
        ],
        [
            InlineKeyboardButton(
                "📦 My Orders",
                callback_data="myorders"
            ),
            InlineKeyboardButton(
                "🔎 Status",
                callback_data="status"
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

    if is_admin(user_id, username):
        keyboard.append([
            InlineKeyboardButton(
                "👑 Admin Panel",
                callback_data="admin"
            )
        ])

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    save_user(update.effective_user)
    context.user_data.clear()

    await update.message.reply_text(
        f"""
👋 Welcome {update.effective_user.first_name}!

🤖 *RJ Team Social Media Service*

📱 YouTube
📘 Facebook
📸 Instagram
🎵 TikTok

🛒 Promotion & Advertising Service

👇 নিচের Menu থেকে নির্বাচন করুন।
""",
        reply_markup=home_keyboard(
            update.effective_user.id,
            update.effective_user.username
        ),
        parse_mode="Markdown",
    )


# =========================================================
# CALLBACK ROUTER
# =========================================================

async def callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    username = query.from_user.username
    data = query.data

    # -----------------------------------------------------
    # HOME
    # -----------------------------------------------------

    if data == "home":

        await query.edit_message_text(
            "🏠 *RJ Team Main Menu*",
            reply_markup=home_keyboard(
                user_id,
                username
            ),
            parse_mode="Markdown",
        )
        return

    # -----------------------------------------------------
    # SERVICES
    # -----------------------------------------------------

    if data == "services":

        keyboard = [
            [
                InlineKeyboardButton(
                    "▶️ YouTube",
                    callback_data="platform_YouTube"
                )
            ],
            [
                InlineKeyboardButton(
                    "📘 Facebook",
                    callback_data="platform_Facebook"
                )
            ],
            [
                InlineKeyboardButton(
                    "📸 Instagram",
                    callback_data="platform_Instagram"
                )
            ],
            [
                InlineKeyboardButton(
                    "🎵 TikTok",
                    callback_data="platform_TikTok"
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
        return

    # -----------------------------------------------------
    # PLATFORM
    # -----------------------------------------------------

    if data.startswith("platform_"):

        platform = data.replace("platform_", "")

        services = get_services(platform)

        keyboard = []

        for sid, name, price in services:

            price_text = (
                f"৳{price:g}"
                if price > 0
                else "Price not set"
            )

            keyboard.append([
                InlineKeyboardButton(
                    f"{name} — {price_text}",
                    callback_data=f"selectservice_{sid}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                "🔙 Back",
                callback_data="services"
            )
        ])

        await query.edit_message_text(
            f"📱 *{platform} Services*\n\n"
            "আপনার প্রয়োজনীয় service নির্বাচন করুন:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return

    # -----------------------------------------------------
    # SELECT SERVICE
    # -----------------------------------------------------

    if data.startswith("selectservice_"):

        sid = int(data.split("_")[1])
        service = get_service(sid)

        if not service or service[4] != 1:

            await query.answer(
                "❌ Service বন্ধ আছে।",
                show_alert=True
            )
            return

        context.user_data.clear()

        context.user_data["service_id"] = sid
        context.user_data["service"] = service[1]
        context.user_data["price"] = service[3]
        context.user_data["step"] = "link"

        price_text = (
            f"৳{service[3]:g}"
            if service[3] > 0
            else "Admin-এর সাথে Price নিশ্চিত করুন"
        )

        await query.edit_message_text(
            f"""
🛒 *New Order*

📱 Service: *{service[1]}*
💰 Price: {price_text}

🔗 এখন আপনার content/profile-এর link পাঠান।
""",
            parse_mode="Markdown",
        )
        return

    # -----------------------------------------------------
    # PAYMENT
    # -----------------------------------------------------

    if data == "payment":

        await query.edit_message_text(
            f"""
💳 *Payment Methods*

🟣 bKash
`{BKASH_NUMBER}`

🟢 Nagad
`{NAGAD_NUMBER}`

🔵 Rocket
`{ROCKET_NUMBER}`

Payment করার পর Transaction ID সংরক্ষণ করুন।
""",
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
        return

    # -----------------------------------------------------
    # SUPPORT
    # -----------------------------------------------------

    if data == "support":

        await query.edit_message_text(
            f"""
🛠️ *Support*

যেকোনো সমস্যায় যোগাযোগ করুন:

👤 {SUPPORT}
""",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "👨‍💼 Contact Support",
                        url="https://t.me/RJteam1"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 Back",
                        callback_data="home"
                    )
                ],
            ]),
            parse_mode="Markdown",
        )
        return

    # -----------------------------------------------------
    # MY ORDERS
    # -----------------------------------------------------

    if data == "myorders":

        rows = user_orders(user_id)

        if not rows:

            text = "📦 আপনার কোনো order নেই।"

        else:

            text = "📦 *Your Orders*\n\n"

            for row in rows:

                oid, service, qty, status, created = row

                text += (
                    f"🆔 `#{oid}`\n"
                    f"📱 {service}\n"
                    f"🔢 Quantity: {qty}\n"
                    f"📊 {status}\n"
                    f"🕐 {created}\n"
                    f"━━━━━━━━━━━━\n"
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
        return

    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    if data == "status":

        context.user_data.clear()
        context.user_data["step"] = "status"

        await query.edit_message_text(
            "🔎 আপনার Order ID পাঠান।\n\n"
            "উদাহরণ: `25`",
            parse_mode="Markdown",
        )
        return

    # =====================================================
    # ADMIN PANEL
    # =====================================================

    if data == "admin":

        if not is_admin(user_id, username):
            return

        keyboard = [
            [
                InlineKeyboardButton(
                    "📦 Pending Orders",
                    callback_data="admin_pending"
                )
            ],
            [
                InlineKeyboardButton(
                    "📊 Statistics",
                    callback_data="admin_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    "🛍️ Manage Services",
                    callback_data="admin_services"
                )
            ],
            [
                InlineKeyboardButton(
                    "📢 Broadcast",
                    callback_data="admin_broadcast"
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
👑 *RJ TEAM ADMIN PANEL*

নিচের Menu থেকে Bot control করুন।
""",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return

    # =====================================================
    # ADMIN STATS
    # =====================================================

    if data == "admin_stats":

        if not is_admin(user_id, username):
            return

        await query.edit_message_text(
            f"""
📊 *Bot Statistics*

👥 Total Users: {total_users()}
📦 Total Orders: {total_orders()}
⏳ Pending Orders: {len(pending_orders())}
""",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Admin Panel",
                        callback_data="admin"
                    )
                ]
            ]),
            parse_mode="Markdown",
        )
        return

    # =====================================================
    # ADMIN PENDING
    # =====================================================

    if data == "admin_pending":

        if not is_admin(user_id, username):
            return

        rows = pending_orders()

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

        await query.edit_message_text(
            "📦 Pending orders নিচে দেখানো হচ্ছে..."
        )

        for row in rows[:10]:

            (
                oid,
                customer_id,
                customer_username,
                service,
                link,
                quantity,
                payment,
                transaction,
                status,
                created,
            ) = row

            keyboard = [
                [
                    InlineKeyboardButton(
                        "✅ Approve",
                        callback_data=f"approve_{oid}"
                    ),
                    InlineKeyboardButton(
                        "❌ Reject",
                        callback_data=f"reject_{oid}"
                    ),
                ]
            ]

            await query.message.reply_text(
                f"""
📦 *Order #{oid}*

👤 @{customer_username or 'N/A'}
🆔 `{customer_id}`

📱 {service}
🔗 {link}
🔢 Quantity: {quantity}

💳 {payment}
🧾 `{transaction}`

📊 {status}
🕐 {created}
""",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )

        return

    # =====================================================
    # APPROVE
    # =====================================================

    if data.startswith("approve_"):

        if not is_admin(user_id, username):
            return

        oid = int(data.split("_")[1])
        order = get_order(oid)

        if not order:
            return

        set_status(oid, "Approved")

        try:

            await context.bot.send_message(
                order[1],
                f"""
✅ *Order Approved*

🆔 Order: `#{oid}`
📱 Service: {order[3]}

📊 Status: *Approved*
""",
                parse_mode="Markdown",
            )

        except Exception:
            pass

        await query.edit_message_text(
            f"✅ Order #{oid} Approved."
        )
        return

    # =====================================================
    # REJECT
    # =====================================================

    if data.startswith("reject_"):

        if not is_admin(user_id, username):
            return

        oid = int(data.split("_")[1])
        order = get_order(oid)

        if not order:
            return

        set_status(oid, "Rejected")

        try:

            await context.bot.send_message(
                order[1],
                f"""
❌ *Order Rejected*

🆔 Order: `#{oid}`

Support: {SUPPORT}
""",
                parse_mode="Markdown",
            )

        except Exception:
            pass

        await query.edit_message_text(
            f"❌ Order #{oid} Rejected."
        )
        return

    # =====================================================
    # ADMIN SERVICES
    # =====================================================

    if data == "admin_services":

        if not is_admin(user_id, username):
            return

        rows = get_services()

        keyboard = []

        for sid, name, platform, price, active in rows:

            state = "🟢" if active else "🔴"

            keyboard.append([
                InlineKeyboardButton(
                    f"{state} {name} — ৳{price:g}",
                    callback_data=f"manage_{sid}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                "🔙 Admin Panel",
                callback_data="admin"
            )
        ])

        await query.edit_message_text(
            "🛍️ *Manage Services*\n\n"
            "Service নির্বাচন করুন:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return

    # =====================================================
    # MANAGE SERVICE
    # =====================================================

    if data.startswith("manage_"):

        if not is_admin(user_id, username):
            return

        sid = int(data.split("_")[1])
        service = get_service(sid)

        if not service:
            return

        state = (
            "🟢 Active"
            if service[4]
            else "🔴 Disabled"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "💰 Change Price",
                    callback_data=f"price_{sid}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔄 Enable / Disable",
                    callback_data=f"toggle_{sid}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Services",
                    callback_data="admin_services"
                )
            ],
        ]

        await query.edit_message_text(
            f"""
🛍️ *Service Management*

📱 {service[1]}
🌐 Platform: {service[2]}
💰 Price: ৳{service[3]:g}
📊 {state}
""",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return

    # =====================================================
    # PRICE
    # =====================================================

    if data.startswith("price_"):

        if not is_admin(user_id, username):
            return

        sid = int(data.split("_")[1])

        context.user_data.clear()
        context.user_data["step"] = "price"
        context.user_data["price_service"] = sid

        await query.edit_message_text(
            "💰 নতুন Price লিখুন।\n\n"
            "উদাহরণ: `150`",
            parse_mode="Markdown",
        )
        return

    # =====================================================
    # TOGGLE
    # =====================================================

    if data.startswith("toggle_"):

        if not is_admin(user_id, username):
            return

        sid = int(data.split("_")[1])

        toggle_service(sid)

        service = get_service(sid)

        await query.edit_message_text(
            f"""
🛍️ *{service[1]}*

📊 Service status পরিবর্তন হয়েছে।
""",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Services",
                        callback_data="admin_services"
                    )
                ]
            ]),
            parse_mode="Markdown",
        )
        return

    # =====================================================
    # BROADCAST
    # =====================================================

    if data == "admin_broadcast":

        if not is_admin(user_id, username):
            return

        context.user_data.clear()
        context.user_data["step"] = "broadcast"

        await query.edit_message_text(
            """
📢 *Broadcast*

যে message সবাইকে পাঠাতে চান,
এখন সেটি পাঠান।
""",
            parse_mode="Markdown",
        )
        return


# =========================================================
# TEXT HANDLER
# =========================================================

async def text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user
    text = update.message.text.strip()

    save_user(user)

    step = context.user_data.get("step")

    # -----------------------------------------------------
    # BROADCAST
    # -----------------------------------------------------

    if step == "broadcast" and is_admin(
        user.id,
        user.username
    ):

        users = all_users()
        sent = 0

        for uid in users:

            try:

                await context.bot.send_message(
                    uid,
                    f"📢 *RJ Team Announcement*\n\n{text}",
                    parse_mode="Markdown",
                )

                sent += 1

            except Exception:
                pass

        context.user_data.clear()

        await update.message.reply_text(
            f"""
✅ Broadcast সম্পন্ন হয়েছে।

👥 Sent: {sent}
"""
        )
        return

    # -----------------------------------------------------
    # CHANGE PRICE
    # -----------------------------------------------------

    if step == "price" and is_admin(
        user.id,
        user.username
    ):

        try:

            price = float(text)

            if price < 0:
                raise ValueError

        except ValueError:

            await update.message.reply_text(
                "❌ সঠিক Price দিন।\n"
                "উদাহরণ: `150`",
                parse_mode="Markdown",
            )
            return

        sid = context.user_data.get("price_service")

        change_price(sid, price)

        context.user_data.clear()

        await update.message.reply_text(
            f"✅ Price ৳{price:g} করা হয়েছে।"
        )
        return

    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    if step == "status":

        if not text.isdigit():

            await update.message.reply_text(
                "❌ সঠিক Order ID দিন।"
            )
            return

        oid = int(text)
        order = get_order(oid)

        if not order:

            await update.message.reply_text(
                "❌ Order পাওয়া যায়নি।"
            )
            return

        if (
            order[1] != user.id
            and not is_admin(
                user.id,
                user.username
            )
        ):

            await update.message.reply_text(
                "❌ এই Order আপনার নয়।"
            )
            return

        context.user_data.clear()

        await update.message.reply_text(
            f"""
🔎 *Order Status*

🆔 Order: `#{order[0]}`
📱 Service: {order[3]}
🔗 Link: {order[4]}
🔢 Quantity: {order[5]}

💳 Payment: {order[6]}
🧾 Transaction: `{order[7]}`

📊 Status: *{order[8]}*
🕐 {order[9]}
""",
            parse_mode="Markdown",
        )
        return

    # -----------------------------------------------------
    # LINK
    # -----------------------------------------------------

    if step == "link":

        context.user_data["link"] = text
        context.user_data["step"] = "quantity"

        await update.message.reply_text(
            "🔢 এখন Quantity লিখুন।\n\n"
            "উদাহরণ: `100`",
            parse_mode="Markdown",
        )
        return

    # -----------------------------------------------------
    # QUANTITY
    # -----------------------------------------------------

    if step == "quantity":

        if not text.isdigit() or int(text) <= 0:

            await update.message.reply_text(
                "❌ Quantity হিসেবে সঠিক সংখ্যা দিন।"
            )
            return

        context.user_data["quantity"] = int(text)
        context.user_data["step"] = "payment"

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
            "💳 Payment Method নির্বাচন করুন:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    # -----------------------------------------------------
    # TRANSACTION
    # -----------------------------------------------------

    if step == "transaction":

        transaction = text

        service = context.user_data.get("service")
        link = context.user_data.get("link")
        quantity = context.user_data.get("quantity")
        payment = context.user_data.get("payment")

        if not all([
            service,
            link,
            quantity,
            payment
        ]):

            context.user_data.clear()

            await update.message.reply_text(
                "❌ Order session শেষ হয়ে গেছে। "
                "/start দিয়ে আবার চেষ্টা করুন।"
            )
            return

        oid = create_order(
            user,
            service,
            link,
            quantity,
            payment,
            transaction,
        )

        await update.message.reply_text(
            f"""
✅ *Order Submitted*

🆔 Order ID: `#{oid}`

📱 Service: {service}
🔢 Quantity: {quantity}
💳 Payment: {payment}

🧾 Transaction ID:
`{transaction}`

📊 Status: *Pending Verification*
""",
            parse_mode="Markdown",
        )

        # ADMIN NOTIFICATION
        try:

            await context.bot.send_message(
                ADMIN_ID,
                f"""
🔔 *New Order*

🆔 Order: `#{oid}`

👤 @{user.username or 'N/A'}
🆔 User ID: `{user.id}`

📱 {service}
🔗 {link}
🔢 Quantity: {quantity}

💳 {payment}
🧾 `{transaction}`

📊 Pending Verification
""",
                parse_mode="Markdown",
            )

        except Exception as e:
            logging.error(
                "Admin notification error: %s",
                e
            )

        context.user_data.clear()
        return

    await update.message.reply_text(
        "🏠 Main Menu দেখতে /start লিখুন।"
    )


# =========================================================
# PAYMENT HANDLER
# =========================================================

async def payment_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    method = query.data.replace("pay_", "")

    names = {
        "bkash": "bKash",
        "nagad": "Nagad",
        "rocket": "Rocket",
    }

    numbers = {
        "bkash": BKASH_NUMBER,
        "nagad": NAGAD_NUMBER,
        "rocket": ROCKET_NUMBER,
    }

    context.user_data["payment"] = names[method]
    context.user_data["step"] = "transaction"

    await query.edit_message_text(
        f"""
💳 *{names[method]} Payment*

📱 Number:
`{numbers[method]}`

Payment করার পর Transaction ID পাঠান।
""",
        parse_mode="Markdown",
    )


# =========================================================
# CALLBACK MASTER
# =========================================================

async def master_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    data = update.callback_query.data

    if data.startswith("pay_"):
        await payment_handler(update, context)
    else:
        await callback_router(update, context)


# =========================================================
# MAIN
# =========================================================

def main():

    if BOT_TOKEN == "YOUR_BOT_TOKEN":

        print(
            "❌ BOT_TOKEN সেট করা হয়নি। "
            "GitHub Secret-এ BOT_TOKEN দিন।"
        )

        return

    init_db()

    app = Application.builder().token(
        BOT_TOKEN
    ).build()

    # Only /start command
    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CallbackQueryHandler(master_callback)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler
        )
    )

    print("🤖 RJ Team Bot Running...")

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()