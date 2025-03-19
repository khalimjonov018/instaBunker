import logging
import asyncio
import os
import yt_dlp
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile

# Bot tokenini shu yerga kiriting
TOKEN = "7930244847:AAHprORR4-qh7oTEIuTJBKm-0eC3JZ9gRAI"
BOT_USERNAME = "instaBunker_robot"  # O'zingizning bot username-ni kiriting

# Bot va dispatcher obyektlarini yaratamizpip install aiogram
bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("👋 Assalomu alaykum!\n\n"
                         "📥 Instagram videolari va rasmlarini yuklash uchun menga havolani yuboring.")


def download_instagram_media(instagram_url):
    """Instagram video yoki rasmni yuklab olish funksiyasi"""
    try:
        ydl_opts = {
            "outtmpl": "instagram_media.%(ext)s",  # Faqat bitta nom bilan yuklab olish
            "format": "bestvideo+bestaudio/best",  # Eng yaxshi sifat tanlanadi
            "merge_output_format": "mp4",  # Video uchun MP4 format
            "cookies": "cookies.txt",  # Instagram login cookies faylini ishlatamiz
            "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}]
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(instagram_url, download=True)
            file_path = ydl.prepare_filename(info_dict)  # Fayl nomini olish
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB ga o'tkazamiz
            media_type = info_dict.get("ext")  # Foydali: video yoki rasm aniqlash
            return file_path, file_size, media_type
    except Exception as e:
        logging.error(f"Instagram media yuklashda xatolik: {e}", exc_info=True)
        return None, None, None


@dp.message()
async def process_instagram_media(message: Message):
    if not message.text.startswith("https://www.instagram.com"):
        await message.answer("❌ Iltimos, to‘g‘ri Instagram havolasini yuboring!")
        return

    await message.answer("⏳ Media yuklanmoqda, iltimos kuting...")

    media_path, file_size, media_type = download_instagram_media(message.text)
    if media_path:
        if media_type == "mp4":  # Video bo'lsa
            media_file = FSInputFile(media_path)

            caption = (
                "✅ <b>Instagram videosi yuklandi!</b>\n\n"
                f"📦 <b>Hajmi:</b> {file_size:.2f} MB\n"
                f"🔗 <b>Havola:</b> <a href='{message.text}'>Ko‘rish</a>\n\n"
                f"🤖 <b>Bot orqali yuklab olindi:</b> @{BOT_USERNAME}"
            )

            await message.answer_video(video=media_file, caption=caption, parse_mode="HTML")

        else:  # Agar rasm bo'lsa
            media_file = FSInputFile(media_path)
            await message.answer_photo(photo=media_file, caption="✅ Instagram rasmi yuklandi!")

        os.remove(media_path)  # Yuklab olingan faylni o‘chiramiz
    else:
        await message.answer("❌ Media yuklab bo‘lmadi. Havolani tekshirib qayta yuboring!")


async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
