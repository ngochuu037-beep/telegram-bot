import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# =========================
# CẤU HÌNH
# =========================

TOKEN = os.getenv("8256418029:AAHWnLrQ_BfKVP9AT1PRaBaCET-RSbEULQU")

GROUP_ID = -1003365347708
GROUP_LINK = "https://t.me/+-_Ylhi8u5PA1Nzhl"

DB_FILE = "bot.db"


# =========================
# DATABASE
# =========================

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            coins INTEGER DEFAULT 0,
            invited_by INTEGER,
            claimed INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def get_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute(
        "SELECT user_id, username, coins, invited_by, claimed "
        "FROM users WHERE user_id = ?",
        (user_id,)
    )

    result = cur.fetchone()
    conn.close()

    return result


def create_user(user_id, username, invited_by=None):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO users
        (user_id, username, coins, invited_by, claimed)
        VALUES (?, ?, 0, ?, 0)
    """, (user_id, username, invited_by))

    conn.commit()
    conn.close()


def add_coins(user_id, amount):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute(
        "UPDATE users SET coins = coins + ? WHERE user_id = ?",
        (amount, user_id)
    )

    conn.commit()
    conn.close()


def set_claimed(user_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute(
        "UPDATE users SET claimed = 1 WHERE user_id = ?",
        (user_id,)
    )

    conn.commit()
    conn.close()


# =========================
# KIỂM TRA JOIN GROUP
# =========================

async def is_member(bot, user_id):
    try:
        member = await bot.get_chat_member(GROUP_ID, user_id)

        return member.status in (
            "member",
            "administrator",
            "creator",
        )

    except Exception:
        return False


# =========================
# /START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    user_id = user.id

    # Lấy mã giới thiệu
    invited_by = None

    if context.args:
        try:
            ref_id = int(context.args[0])

            if ref_id != user_id:
                invited_by = ref_id

        except ValueError:
            pass

    old_user = get_user(user_id)

    # Người dùng mới
    if old_user is None:

        create_user(
            user_id,
            user.username or "",
            invited_by
        )

        # Nếu được người khác giới thiệu
        if invited_by is not None:

            inviter = get_user(invited_by)

            if inviter is not None:
                add_coins(invited_by, 2)

                try:
                    await context.bot.send_message(
                        chat_id=invited_by,
                        text=(
                            "🎉 Có người vừa tham gia bằng link "
                            "giới thiệu của bạn!\n\n"
                            "💰 +2 xu"
                        )
                    )
                except Exception:
                    pass

    keyboard = [
        [
            InlineKeyboardButton(
                "📢 Tham gia Group",
                url=GROUP_LINK
            )
        ],
        [
            InlineKeyboardButton(
                "🔍 Kiểm tra",
                callback_data="check_join"
            )
        ],
        [
            InlineKeyboardButton(
                "👥 Link mời bạn",
                callback_data="ref"
            )
        ],
        [
            InlineKeyboardButton(
                "💰 Số xu",
                callback_data="coins"
            )
        ],
    ]

    await update.message.reply_text(
        "🎁 QUÀ TẶNG MIGUEL FF 🎁\n\n"
        "👥 Mời 1 bạn = +2 xu\n"
        "💰 Đủ 10 xu mới có thể đổi quà!\n\n"
        "⚠️ Bạn cần tham gia group trước.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# NÚT KIỂM TRA JOIN
# =========================

async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    joined = await is_member(
        context.bot,
        user_id
    )

    if joined:

        await query.message.reply_text(
            "✅ Bạn đã tham gia group!\n\n"
            "👥 Mời 1 bạn = +2 xu\n"
            "💰 Đủ 10 xu mới có thể đổi quà."
        )

    else:

        keyboard = [[
            InlineKeyboardButton(
                "📢 Tham gia Group",
                url=GROUP_LINK
            )
        ]]

        await query.message.reply_text(
            "❌ Bạn chưa tham gia group!\n\n"
            "Hãy tham gia group rồi bấm kiểm tra lại.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# =========================
# LINK GIỚI THIỆU
# =========================

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    bot = await context.bot.get_me()

    link = f"https://t.me/{bot.username}?start={user_id}"

    await query.message.reply_text(
        "👥 LINK MỜI BẠN\n\n"
        f"{link}\n\n"
        "🎁 Mời 1 bạn = +2 xu\n"
        "💰 Đủ 10 xu mới được đổi quà."
    )


# =========================
# XEM SỐ XU
# =========================

async def coins(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    user = get_user(user_id)

    if user is None:
        create_user(
            user_id,
            query.from_user.username or ""
        )
        coin = 0
    else:
        coin = user[2]

    await query.message.reply_text(
        "💰 SỐ XU CỦA BẠN\n\n"
        f"🪙 Xu hiện tại: {coin}/10\n\n"
        "👥 Mời 1 bạn = +2 xu"
    )


# =========================
# ĐỔI QUÀ
# =========================

async def doi_qua(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    user = get_user(user_id)

    if user is None:
        create_user(
            user_id,
            update.effective_user.username or ""
        )
        coin = 0
        claimed = 0
    else:
        coin = user[2]
        claimed = user[4]

    if coin < 10:

        await update.message.reply_text(
            "❌ Chưa đủ xu!\n\n"
            f"🪙 Hiện tại: {coin}/10 xu\n"
            "🎁 Cần đủ 10 xu mới có thể đổi quà."
        )

        return

    if claimed:

        await update.message.reply_text(
            "⚠️ Bạn đã đổi quà trước đó rồi."
        )

        return

    # Demo/troll
    set_claimed(user_id)

    await update.message.reply_text(
        "🎉 ĐỔI QUÀ THÀNH CÔNG!\n\n"
        "👤 Acc: ACC_TROLL\n"
        "🔑 Key: MIGUEL-FAKE-001\n\n"
        "😂 Đây chỉ là ACC + KEY DEMO/TROLL."
    )


# =========================
# /HELP
# =========================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📖 HƯỚNG DẪN\n\n"
        "/start - Bắt đầu\n"
        "/doi_qua - Đổi quà\n\n"
        "👥 Mời 1 bạn = +2 xu\n"
        "💰 Đủ 10 xu mới được đổi quà."
    )


# =========================
# CHẠY BOT
# =========================

def main():

    if not TOKEN:
        print("❌ Chưa có BOT_TOKEN!")
        return

    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("doi_qua", doi_qua)
    )

    app.add_handler(
        CommandHandler("help", help_command)
    )

    app.add_handler(
        CallbackQueryHandler(
            check_join,
            pattern="^check_join$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            referral,
            pattern="^ref$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            coins,
            pattern="^coins$"
        )
    )

    print("🤖 Bot đang chạy...")

    app.run_polling()


if __name__ == "__main__":
    main()
