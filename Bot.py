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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "youtube.com" in text or "youtu.be" in text:
        msg = await update.message.reply_text("🎵 Müzik indiriliyor, lütfen bekleyin...")
        try:
            api_url = "https://api.cobalt.tools/api/json"
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            payload = {
                "url": text,
                "downloadMode": "audio",
                "audioFormat": "mp3"
            }
            response = requests.post(api_url, json=payload, headers=headers).json()
            
            if response.get("status") in ["stream", "redirect"]:
                audio_url = response.get("url")
                audio_data = requests.get(audio_url).content
                
                with open("song.mp3", "wb") as f:
                    f.write(audio_data)
                    
                with open("song.mp3", "rb") as audio:
                    await update.message.reply_audio(audio)
                    
                os.remove("song.mp3")
                await msg.delete()
            else:
                await msg.edit_text("❌ Müzik indirilemedi, lütfen farklı bir link deneyin.")
        except Exception as e:
            await msg.edit_text(f"❌ Hata oluştu: {e}")

def main():
    threading.Thread(target=run_dummy_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
