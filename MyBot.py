import logging
import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8678477203:AAGlPGTzwqUf6dt7UUVbmzRhNxEuNfrc17Y"
DB_FILE = "users.db"

logging.basicConfig(level=logging.INFO)


def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            user_id  INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_user(username: str, user_id: int):
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT OR REPLACE INTO users (username, user_id) VALUES (?, ?)",
        (username.lower(), user_id)
    )
    conn.commit()
    conn.close()


def get_user_id(username: str) -> int | None:
    conn = sqlite3.connect(DB_FILE)
    row = conn.execute(
        "SELECT user_id FROM users WHERE username = ?",
        (username.lower(),)
    ).fetchone()
    conn.close()
    return row[0] if row else None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.username

    if username:
        save_user(username, user.id)
        await update.message.reply_text(
            f"👋 Привет, @{username}!\n\n"
            "Ты зарегистрирован. Теперь другие могут написать тебе анонимно.\n\n"
            "📨 Чтобы написать кому-то:\n"
            "@username текст сообщения\n\n"
            "Например: @friend Привет, это я!"
        )
    else:
        await update.message.reply_text(
            "⚠️ У тебя нет username в Telegram.\n"
            "Установи его в Настройки → Изменить профиль → Имя пользователя."
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip()

    if user.username:
        save_user(user.username, user.id)

    if not text.startswith("@"):
        await update.message.reply_text(
            "ℹ️ Формат отправки:\n@username текст\n\nПример: @friend Как дела?"
        )
        return

    parts = text.split(" ", 1)
    if len(parts) < 2:
        await update.message.reply_text("❌ Укажи текст после @username.")
        return

    target_username = parts[0][1:]
    message_text = parts[1]

    target_id = get_user_id(target_username)
    if not target_id:
        await update.message.reply_text(
            f"❌ @{target_username} не найден.\n"
            "Он должен был запустить бота хотя бы раз."
        )
        return

    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=f"📩 Анонимное сообщение:\n\n{message_text}"
        )
        await update.message.reply_text(f"✅ Сообщение отправлено @{target_username}!")
    except Exception as e:
        await update.message.reply_text(
            "❌ Не удалось доставить. Возможно, пользователь заблокировал бота."
        )
        logging.error(f"Ошибка: {e}")


def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
