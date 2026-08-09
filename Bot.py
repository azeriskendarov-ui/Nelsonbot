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

def get_audio_stream(youtube_url):
    video_id = None
    if "youtu.be/" in youtube_url:
        video_id = youtube_url.split("youtu.be/")[1].split("?")[0].split("&")[0]
    elif "v=" in youtube_url:
        video_id = youtube_url.split("v=")[1].split("&")[0]

    if not video_id:
        return None, None

    instances = [
        f"https://pipedapi.kavin.rocks/streams/{video_id}",
        f"https://api.piped.privacydev.net/streams/{video_id}",
        f"https://pipedapi.mha.fi/streams/{video_id}",
        f"https://invidious.nerdvpn.de/api/v1/videos/{video_id}"
    ]

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    for url in instances:
        try:
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code == 200:
                data = res.json()
                
                if "audioStreams" in data and len(data["audioStreams"]) > 0:
                    for stream in data["audioStreams"]:
                        if stream.get("url"):
                            title = data.get("title", "Muzik")
                            return stream["url"], title

                if "adaptiveFormats" in data:
                    for fmt in data["adaptiveFormats"]:
                        mime = fmt.get("type", "") or fmt.get("mimeType", "")
                        if "audio" in mime and fmt.get("url"):
                            title = data.get("title", "Muzik")
                            return fmt["url"], title
        except Exception:
            continue

    return None, None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if "youtube.com" in text or "youtu.be" in text:
        msg = await update.message.reply_text("🎵 Müzik indiriliyor, lütfen bekleyin...")
        
        audio_url, title = get_audio_stream(text)
        
        if not audio_url:
            await msg.edit_text("❌ Müzik bağlantısı çekilemedi. Lütfen tekrar deneyin.")
            return

        file_path = "song.mp3"
        try:
            res = requests.get(audio_url, stream=True, timeout=30)
            with open(file_path, "wb") as f:
                for chunk in res.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                
            with open(file_path, "rb") as audio:
                await update.message.reply_audio(audio, title=title)
                
            if os.path.exists(file_path):
                os.remove(file_path)
            await msg.delete()
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            await msg.edit_text(f"❌ İndirme hatası: {e}")

def main():
    threading.Thread(target=run_dummy_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
