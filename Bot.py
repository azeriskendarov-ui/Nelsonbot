import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import yt_dlp

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

TOKEN = "8641919539:AAHfRVMmyLuk2an48eGAbdoVQ6WGcXrEj1M"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "youtube.com" in text or "youtu.be" in text:
        msg = await update.message.reply_text("🎵 Müzik indiriliyor, lütfen bekleyin...")
        ydl_opts = {
            'format': 'm4a/bestaudio/best',
            'outtmpl': 'song.%(ext)s',
            'nocheckcertificate': True,
            'quiet': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios']
                }
            }
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([text])
            for file in os.listdir():
                if file.startswith("song."):
                    with open(file, 'rb') as audio:
                        await update.message.reply_audio(audio)
                    os.remove(file)
                    break
            await msg.delete()
        except Exception as e:
            await update.message.reply_text(f"❌ Hata oluştu: {e}")

def main():
    threading.Thread(target=run_dummy_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
