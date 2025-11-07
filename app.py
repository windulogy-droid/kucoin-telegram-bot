import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler
from kucoin.client import Market

# ==============================
# Konfigurasi
# ==============================
logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
BASE_URL = os.environ.get("BASE_URL")  # contoh: https://your-app.onrender.com

if not BOT_TOKEN or not BASE_URL:
    raise RuntimeError("❌ Set environment variable BOT_TOKEN dan BASE_URL")

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

# KuCoin Public API
market_client = Market(url="https://api.kucoin.com")

# Dispatcher Telegram
dispatcher = Dispatcher(bot, None, workers=0, use_context=False)

# ==============================
# Handlers
# ==============================

def start(update: Update, context=None):
    text = (
        "👋 Hai! Saya bot KuCoin Public API.\n\n"
        "Perintah yang tersedia:\n"
        "• /price BTC-USDT — harga live\n"
        "• /top — 5 koin volume tertinggi\n"
        "• /info BTC-USDT — info lengkap koin\n"
    )
    update.message.reply_text(text)


def price(update: Update, context=None):
    try:
        msg = update.message.text.split(" ")
        if len(msg) < 2:
            update.message.reply_text("Gunakan format: /price BTC-USDT")
            return
        symbol = msg[1].upper()
        ticker = market_client.get_ticker(symbol)
        price = ticker["price"]
        update.message.reply_text(f"💰 Harga {symbol}: ${price}")
    except Exception as e:
        update.message.reply_text(f"❌ Gagal mengambil harga: {e}")


def top(update: Update, context=None):
    try:
        tickers = market_client.get_all_tickers()["ticker"]
        sorted_tickers = sorted(tickers, key=lambda x: float(x["volValue"]), reverse=True)[:5]
        message = "🔥 Top 5 koin berdasarkan volume:\n\n"
        for t in sorted_tickers:
            message += f"{t['symbol']}: ${t['last']} (vol ${t['volValue'][:10]})\n"
        update.message.reply_text(message)
    except Exception as e:
        update.message.reply_text(f"❌ Gagal mengambil data: {e}")


def info(update: Update, context=None):
    try:
        msg = update.message.text.split(" ")
        if len(msg) < 2:
            update.message.reply_text("Gunakan format: /info BTC-USDT")
            return
        symbol = msg[1].upper()
        ticker = market_client.get_ticker(symbol)
        change = ticker["changeRate"]
        high = ticker["high"]
        low = ticker["low"]
        price = ticker["price"]
        vol = ticker["vol"]
        msg_text = (
            f"📊 Info {symbol}\n\n"
            f"Harga: ${price}\n"
            f"Perubahan: {float(change)*100:.2f}%\n"
            f"Tinggi: ${high}\n"
            f"Rendah: ${low}\n"
            f"Volume: {vol}\n"
        )
        update.message.reply_text(msg_text)
    except Exception as e:
        update.message.reply_text(f"❌ Gagal mengambil data: {e}")


# ==============================
# Daftar Command ke Dispatcher
# ==============================
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("price", price))
dispatcher.add_handler(CommandHandler("top", top))
dispatcher.add_handler(CommandHandler("info", info))


# ==============================
# Webhook
# ==============================
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK"

@app.route("/", methods=["GET"])
def index():
    return "KuCoin Bot Aktif ✅"

if __name__ == "__main__":
    webhook_url = f"{BASE_URL}/{BOT_TOKEN}"
    bot.delete_webhook()
    bot.set_webhook(url=webhook_url)
    print(f"🚀 Webhook diset ke: {webhook_url}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
