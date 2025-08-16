from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from deep_translator import GoogleTranslator
from handlers.file_handler import handle_file 
import os
from dotenv import load_dotenv  

load_dotenv()


BOT_USERNAME = os.getenv("BOT_USERNAME") # replace with your bot's actual username
BOT_TOKEN = os.getenv("BOT_TOKEN")

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! 👋\n\n"
        "📌 *Usage:*\n"
        "- In groups: Reply to a message and mention me (e.g., `@xyzlangbot en`).\n"
        "- In private chat: Send `lang_code your text` (e.g., `fa Hello world`).\n"
        "- To translate a file: attach the file and set the file caption to the target language (e.g., `ckb`).\n\n"
        "🌐 Example: `ckb Hello friend!` → translates to Kurdish Sorani.",
        parse_mode="Markdown"
    )

# Translation handler (text messages)
async def translate_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    try:
        # Case 1: Group usage (reply + mention)
        if message.reply_to_message and f"@{BOT_USERNAME}" in (message.text or ""):
            parts = message.text.strip().split()
            target_lang = parts[1] if len(parts) > 1 else "en"
            text_to_translate = message.reply_to_message.text or ""
        # Case 2: Private usage (lang_code + text)
        elif message.chat and message.chat.type == "private":
            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                await message.reply_text("⚠️ Please provide language code and text.\nExample: `en Hello world`")
                return
            target_lang, text_to_translate = parts[0].lower(), parts[1]
        else:
            return  # ignore other messages

        if not text_to_translate.strip():
            await message.reply_text("⚠️ Nothing to translate.")
            return

        translated_text = GoogleTranslator(source='auto', target=target_lang).translate(text_to_translate)
        await message.reply_text(f"🌐 Translation ({target_lang}):\n{translated_text}")

    except Exception as e:
        await message.reply_text(f"⚠️ Translation failed: {e}")

def main():
    # replace with your real token
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_reply))

    # file handler: documents with caption = target language
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
