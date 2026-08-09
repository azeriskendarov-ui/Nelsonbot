import os
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

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

# YouTube IP engelini aşan Cobalt API sunucuları
API_INSTANCES = [
    "https://api.cobalt.tools/api/json",
    "https://cobalt-api.kwippy.org/api/json",
    "https://cobalt.qil.dev/api/json"
]

def get_audio_url(youtube_url):
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    payload = {
        "url": youtube_url,
        "downloadMode": "audio",
        "audioFormat": "mp3"
    }
    
    for instance in API_INSTANCES:
        try:
            res = requests.post(instance, json=payload, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if data.get("status") in ["tunnel", "redirect", "stream"]:
                    return data.get("url")
        except Exception:
            continue
    return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if "youtube.com" in text or "youtu.be" in text:
        msg = await update.message.reply_text("🎵 Müzik indiriliyor, lütfen bekleyin...")
        
        audio_download_url = get_audio_url(text)
        
        if not audio_download_url:
            await msg.edit_text("❌ Sunucu yoğunluğu nedeniyle müzik alınamadı. Lütfen birkaç saniye sonra tekrar deneyin.")
            return

        try:
            audio_data = requests.get(audio_download_url, timeout=30).content
            with open("song.mp3", "wb") as f:
                f.write(audio_data)
                
            with open("song.mp3", "rb") as audio:
                await update.message.reply_audio(audio)
                
            os.remove("song.mp3")
            await msg.delete()
        except Exception as e:
            await msg.edit_text(f"❌ İndirme hatası: {e}")

def main():
    threading.Thread(target=run_dummy_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
