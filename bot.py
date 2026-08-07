import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import anthropic

# --- SOZLAMALAR ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "BU_YERGA_BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "BU_YERGA_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Sen Carvon Store — Toshkentdagi smartfon do'koni uchun 
professional SMM va Target AI agentisan.

Quyidagilarni bajara olasan:
1. POST YARATISH — Instagram, Telegram, Facebook uchun
2. REKLAMA MATNI — Facebook/Instagram target uchun
3. STORIES MATNI — Har kungi 5 ta stories
4. HASHTAG — 20 ta samarali hashtag
5. SARLAVHA — 5 ta kreativ sarlavha
6. KAMPANIYA NOMI — TOF/MOF/BOF format
7. HAFTALIK REJA — 7 kunlik kontent
8. TAHLIL — Post statistikasini tahlil
9. DM MATNI — Potensial mijozlarga
10. MUDDATLI TO'LOV — Kreativ matnlar

Doimo O'zbek tilida javob ber.
Emoji ishlat.
Qisqa va aniq bo'l."""

user_history = {}

def get_history(user_id):
    if user_id not in user_history:
        user_history[user_id] = []
    return user_history[user_id]

async def ai_response(user_id: int, message: str) -> str:
    history = get_history(user_id)
    history.append({"role": "user", "content": message})
    if len(history) > 20:
        history = history[-20:]
        user_history[user_id] = history
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=history
        )
        reply = response.content[0].text
        history.append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        logger.error(f"AI xatolik: {e}")
        return "Xatolik yuz berdi. Qayta urining."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📝 Post yozish", callback_data="post"),
         InlineKeyboardButton("🎯 Reklama matni", callback_data="reklama")],
        [InlineKeyboardButton("📸 Stories", callback_data="stories"),
         InlineKeyboardButton("#️⃣ Hashtag", callback_data="hashtag")],
        [InlineKeyboardButton("📅 Haftalik reja", callback_data="reja"),
         InlineKeyboardButton("📊 Tahlil", callback_data="tahlil")],
        [InlineKeyboardButton("💬 DM matni", callback_data="dm"),
         InlineKeyboardButton("💳 Muddatli to'lov", callback_data="muddatli")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Salom! Men Carvon Store SMM Agent!\n\n"
        "Menga buyruq bering yoki quyidan tanlang 👇",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    prompts = {
        "post": "Instagram uchun kreativ post yozib ber. Mahsulot nomini so'ra.",
        "reklama": "Facebook/Instagram target reklama matni yozib ber. Mahsulot va maqsadni so'ra.",
        "stories": "Bugungi 5 ta Instagram stories matni yozib ber. Mavzuni so'ra.",
        "hashtag": "20 ta samarali hashtag yozib ber. Mahsulotni so'ra.",
        "reja": "Haftalik kontent rejasini tuz. Mahsulotlarni so'ra.",
        "tahlil": "Post statistikasini tahlil qilaman. Reach, like, comment, DM sonlarini yubor.",
        "dm": "Potensial mijozlarga DM matni yozaman. Mahsulot va qayerdan topilganini ayt.",
        "muddatli": "Muddatli to'lov uchun kreativ matn yozib ber. Mahsulot va narxni so'ra.",
    }
    msg = prompts.get(query.data, "Nima kerak?")
    reply = await ai_response(user_id, msg)
    await query.message.reply_text(reply)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    await update.message.chat.send_action("typing")
    reply = await ai_response(user_id, text)
    # Uzun xabarlarni bo'laklarga bo'lish
    if len(reply) > 4000:
        parts = [reply[i:i+4000] for i in range(0, len(reply), 4000)]
        for part in parts:
            await update.message.reply_text(part)
    else:
        await update.message.reply_text(reply)

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_history[user_id] = []
    await update.message.reply_text("✅ Suhbat tozalandi!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Carvon Store SMM Agent\n\n"
        "Buyruqlar:\n"
        "/start — Bosh menyu\n"
        "/clear — Suhbatni tozalash\n"
        "/help — Yordam\n\n"
        "Yoki shunchaki yozing:\n"
        "• 'Redmi Note 15 uchun post yoz'\n"
        "• 'Muddatli to'lov reklama matni'\n"
        "• 'Haftalik kontent reja tuz'\n"
        "• 'Bu post statistikasini tahlil qil'"
    )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    logger.info("Bot ishga tushdi!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
