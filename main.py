import asyncio
import logging
import os
import uuid
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web
import yt_dlp

# --- الإعدادات (تأكد من وضع التوكن الصحيح) ---
API_TOKEN = 'ضع_توكن_بوت_تيك_توك_هنا' 
CHANNEL_ID = '@Ramy_Premium' # آيدي القناة للتحقق من الاشتراك
CHANNEL_LINK = 'https://t.me/Ramy_Premium'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- دالة التحقق من الاشتراك الإجباري ---
async def check_subscription(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        # إذا كان العضو ليس غادراً أو مطروداً فهو مشترك
        if member.status in ['member', 'creator', 'administrator']:
            return True
        return False
    except Exception:
        return False

# --- لوحة أزرار الاشتراك ---
def sub_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="انضم للقناة أولاً 📢", url=CHANNEL_LINK)],
        [InlineKeyboardButton(text="لقد اشتركت، فعل البوت ✅", callback_data="check_sub")]
    ])

# --- دالة تحميل تيك توك ---
def download_tiktok(url):
    unique_filename = f"tiktok_{uuid.uuid4().hex}.mp4"
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': unique_filename,
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        return unique_filename

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    is_sub = await check_subscription(message.from_user.id)
    if not is_sub:
        await message.answer(
            f"مرحباً بك {message.from_user.first_name}! 👋\n\n"
            f"عذراً، يجب عليك الاشتراك في قناة المتجر أولاً لاستخدام البوت والاستفادة من خدماتنا.",
            reply_markup=sub_kb()
        )
    else:
        await message.answer(
            "أهلاً بك مجدداً! البوت مفعل الآن. أرسل رابط تيك توك للتحميل بدون علامة مائية 🎬",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="متجر رامي بريميوم 🛒", url=CHANNEL_LINK)]
            ])
        )

@dp.callback_query(lambda c: c.data == "check_sub")
async def process_callback_check_sub(callback_query: types.CallbackQuery):
    is_sub = await check_subscription(callback_query.from_user.id)
    if is_sub:
        await bot.answer_callback_query(callback_query.id, text="تم تفعيل البوت بنجاح! ✅")
        await bot.send_message(callback_query.from_user.id, "مبروك! أرسل الآن أي رابط تيك توك وسأقوم بتحميله فوراً.")
    else:
        await bot.answer_callback_query(callback_query.id, text="لم تشترك في القناة بعد! ⚠️", show_alert=True)

@dp.message()
async def handle_message(message: types.Message):
    if not message.text or "tiktok.com" not in message.text:
        return

    # التحقق من الاشتراك قبل كل عملية تحميل
    is_sub = await check_subscription(message.from_user.id)
    if not is_sub:
        await message.answer("عذراً، اشتراكك في القناة ضروري لاستمرار الخدمة مجاناً:", reply_markup=sub_kb())
        return

    msg = await message.answer("⏳ جاري التحميل من تيك توك بدون علامة مائية...")
    
    try:
        video_file = await asyncio.to_thread(download_tiktok, message.text)
        video = types.FSInputFile(video_file)
        await message.answer_video(
            video, 
            caption="✅ تم التحميل بواسطة بوت رامي تيك توك!\n🛒 @Ramy_Premium"
        )
        if os.path.exists(video_file):
            os.remove(video_file)
        await msg.delete()
    except Exception as e:
        logging.error(e)
        await msg.edit_text("❌ حدث خطأ! الرابط قد يكون لخاص أو محذوف.")

# --- جزء استقرار Render (المنفذ الوهمي) ---
async def handle(request):
    return web.Response(text="TikTok Bot is Live and Protecting your Channel! 🚀")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    asyncio.create_task(start_web_server())
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
