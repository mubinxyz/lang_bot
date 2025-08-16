import os
import tempfile
from telegram import Update
from telegram.ext import ContextTypes
from deep_translator import GoogleTranslator
from docx import Document
import PyPDF2

# Handles documents sent with the target language in the caption.
# Usage: attach file and set caption to target language code (e.g., "en", "ckb", "fa").
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    # Ensure there's a document
    if not message or not message.document:
        await message.reply_text("⚠️ Please attach a file with the target language as caption (e.g., `en`).")
        return

    # Require caption to contain target language
    if not message.caption or not message.caption.strip():
        await message.reply_text("⚠️ Please set the target language as the file caption (e.g., `en`).")
        return

    target_lang = message.caption.strip().lower()

    # Download file to a temporary path
    file_obj = await message.document.get_file()
    tmp = tempfile.NamedTemporaryFile(delete=False)
    try:
        await file_obj.download_to_drive(tmp.name)
        file_path = tmp.name
        file_name = message.document.file_name or "file"

        # Extract text depending on extension
        text = ""
        fname = file_name.lower()
        if fname.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        elif fname.endswith(".docx"):
            doc = Document(file_path)
            text = "\n".join(p.text for p in doc.paragraphs)
        elif fname.endswith(".pdf"):
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                pages = []
                for pg in reader.pages:
                    page_text = pg.extract_text()
                    if page_text:
                        pages.append(page_text)
                text = "\n".join(pages)
        else:
            await message.reply_text("⚠️ Unsupported file type. Use `.txt`, `.docx`, or `.pdf`.")
            return

        if not text.strip():
            await message.reply_text("⚠️ No extractable text found in the file.")
            return

        # Translate (slice to avoid huge requests). If you want full-file translation, remove the slice
        # or split into chunks and translate in pieces.
        to_translate = text[:4000]
        try:
            translated = GoogleTranslator(source="auto", target=target_lang).translate(to_translate)
        except Exception as e:
            await message.reply_text(f"⚠️ Translation failed: {e}")
            return

        # Send translation as message or as file if too long
        if len(translated) > 3500:
            out_path = tempfile.mktemp(suffix=".txt")
            try:
                with open(out_path, "w", encoding="utf-8") as out_f:
                    out_f.write(translated)
                # open file in binary mode for sending
                with open(out_path, "rb") as payload:
                    await message.reply_document(payload, filename=f"translated_{target_lang}.txt")
            finally:
                if os.path.exists(out_path):
                    os.remove(out_path)
        else:
            await message.reply_text(f"🌐 Translation ({target_lang}):\n{translated}")

    finally:
        # cleanup temp download
        try:
            tmp.close()
        except Exception:
            pass
        if os.path.exists(tmp.name):
            try:
                os.remove(tmp.name)
            except Exception:
                pass
