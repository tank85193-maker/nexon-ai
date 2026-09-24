import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

BASE = os.path.dirname(os.path.abspath(__file__))
TOKEN = os.environ["BOT_TOKEN"]
DB = os.path.join(BASE, "bot.db")

db = sqlite3.connect(DB, check_same_thread=False)
db.execute("""
CREATE TABLE IF NOT EXISTS memory(
    group_id INTEGER,
    trigger TEXT,
    answer TEXT,
    PRIMARY KEY(group_id, trigger)
)
""")
db.commit()

async def is_admin(update):
    try:
        m = await update.effective_chat.get_member(update.effective_user.id)
        return m.status in ("administrator", "creator")
    except:
        return False

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👑 سازنده", callback_data="creator"),
         InlineKeyboardButton("ℹ️ اطلاعات", callback_data="info")],
        [InlineKeyboardButton("🧠 یادگیری", callback_data="learn"),
         InlineKeyboardButton("📚 دستورات", callback_data="commands")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 NEXON AI\n\n🟢 آنلاین و آماده است.",
        reply_markup=menu()
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "creator":
        text = "👑 سازنده\n\n@Mikisportbot"
    elif q.data == "info":
        text = "🤖 NEXON AI\n📦 نسخه: 9.0.0\n🐍 Python\n🟢 آنلاین"
    elif q.data == "learn":
        text = "🧠 یادگیری\n\nمثال:\nیادبگیر سلام\n\nبعد روی پیام ربات Reply کن و جواب را بفرست."
    else:
        text = "📚 دستورات\n\n/learn سلام\nیا\nیادبگیر سلام\n\nحذف سلام"

    try:
        await q.edit_message_text(text, reply_markup=menu())
    except:
        pass

async def learn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ("group", "supergroup"):
        return

    if not await is_admin(update):
        await update.message.reply_text("⛔ فقط ادمین می‌تواند آموزش بدهد.")
        return

    if not context.args:
        await update.message.reply_text("مثال:\n/learn سلام")
        return

    trigger = " ".join(context.args).strip().lower()
    context.chat_data["learning"] = trigger

    await update.message.reply_text(
        f"🧠 «{trigger}»\n\nحالا جواب را روی همین پیام Reply کن.",
        reply_markup=ForceReply(selective=True)
    )

async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat = update.effective_chat
    text = update.message.text.strip()

    if chat.type not in ("group", "supergroup"):
        return

    # یادبگیر سلام
    if text.startswith("یادبگیر "):
        if not await is_admin(update):
            await update.message.reply_text("⛔ فقط ادمین می‌تواند آموزش بدهد.")
            return

        trigger = text[len("یادبگیر "):].strip().lower()

        if not trigger:
            return

        context.chat_data["learning"] = trigger

        await update.message.reply_text(
            f"🧠 «{trigger}»\n\nحالا جواب را روی همین پیام Reply کن.",
            reply_markup=ForceReply(selective=True)
        )
        return

    # ذخیره جواب آموزش
    trigger = context.chat_data.get("learning")

    if trigger:
        reply = update.message.reply_to_message

        if reply and reply.from_user and reply.from_user.is_bot:
            if not await is_admin(update):
                return

            answer = text

            db.execute(
                "INSERT OR REPLACE INTO memory(group_id, trigger, answer) VALUES (?, ?, ?)",
                (chat.id, trigger, answer)
            )
            db.commit()

            context.chat_data.pop("learning", None)

            await update.message.reply_text(
                f"🟢 جواب ذخیره شد.\n\n"
                f"🧠 {trigger}\n"
                f"💬 {answer}"
            )
            return

    # حذف
    if text.startswith("حذف "):
        if not await is_admin(update):
            return

        trigger = text[5:].strip().lower()

        db.execute(
            "DELETE FROM memory WHERE group_id=? AND trigger=?",
            (chat.id, trigger)
        )
        db.commit()

        await update.message.reply_text("🗑️ حذف شد.")
        return

    # پاسخ یادگرفته‌شده
    row = db.execute(
        "SELECT answer FROM memory WHERE group_id=? AND trigger=?",
        (chat.id, text.lower())
    ).fetchone()

    if row:
        await update.message.reply_text(row[0])

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("learn", learn_command))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))

    print("🟢 NEXON AI 9.0 ONLINE")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
