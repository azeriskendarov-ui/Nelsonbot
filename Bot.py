import os
import re
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

def extract_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

def get_audio_download_link(video_id):
    # Savetube API servisi
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://savetube.me"
    }
    try:
        info_res = requests.get(f"https://api.savetube.me/info?url=https://www.youtube.com/watch?v={video_id}", headers=headers, timeout=10)
        if info_res.status_code == 200:
            data = info_res.json()
            if data.get("status") and "data" in data:
                key = data["data"].get("key")
                title = data["data"].get("title", "Muzik")
                cdn = data["data"].get("cdnUrl") or "https://cdn.savetube.me"
                
                dl_res = requests.post(f"{cdn}/download", json={"key": key, "quality": "128"}, headers=headers, timeout=10)
                if dl_res.status_code == 200:
                    dl_data = dl_res.json()
                    if dl_data.get("status") and "data" in dl_data:
                        return dl_data["data"].get("downloadUrl"), title
    except Exception:
        pass

    # Yedek Cobalt motoru
    try:
        c_res = requests.post(
            "https://co.wuk.sh/api/json",
            json={"url": f"https://www.youtube.com/watch?v={video_id}", "isAudioOnly": True},
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=10
        )
        if c_res.status_code == 200:
            c_data = c_res.json()
            if c_data.get("url"):
                return c_data.get("url"), "Muzik"
    except Exception:
        pass

    return None, None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if "youtube.com" in text or "youtu.be" in text:
        msg = await update.message.reply_text("🎵 Müzik indiriliyor, lütfen bekleyin...")
        
        video_id = extract_video_id(text)
        if not video_id:
            await msg.edit_text("❌ Geçersiz YouTube bağlantısı.")
            return

        audio_url, title = get_audio_download_link(video_id)
        
        if not audio_url:
            await msg.edit_text("❌ İndirme sunucuları yanıt vermedi. Lütfen tekrar deneyin.")
            return

        file_path = "song.mp3"
        try:
            res = requests.get(audio_url, stream=True, timeout=60)
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
