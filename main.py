import logging
import asyncio
import os
import subprocess
import yt_dlp
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile

# Bot tokenini shu yerga kiriting
TOKEN = "7930244847:AAHprORR4-qh7oTEIuTJBKm-0eC3JZ9gRAI"
BOT_USERNAME = "instaBunker_robot"  # O'zingizning bot username-ni kiriting

# Bot va dispatcher obyektlarini yaratamiz
bot = Bot(token=TOKEN)
dp = Dispatcher()


def install_ffmpeg():
    """ffmpeg o‘rnatilganligini tekshirish va kerak bo‘lsa o‘rnatish"""
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("✅ ffmpeg allaqachon o‘rnatilgan.")
    except FileNotFoundError:
        print("⚠️ ffmpeg topilmadi, o‘rnatilmoqda...")
        os.system("apt update && apt install -y ffmpeg")
        print("✅ ffmpeg muvaffaqiyatli o‘rnatildi!")


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("👋 Assalomu alaykum!\n\n"
                         "📥 Instagram videolari va rasmlarini yuklash uchun menga havolani yuboring.")


def download_instagram_media(instagram_url):
    """Instagram video yoki rasmni to'g'ri formatda yuklab olish"""
    try:
        ydl_opts = {
            "outtmpl": "instagram_media.%(ext)s",
            "format": "best[ext=mp4]/best",  # Avval MP4 formatdagi versiyasini olib ko'radi
            "postprocessors": [
                {
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4"  # Majburiy MP4 formatga o'tkazadi
                }
            ],
            "postprocessor_args": [
                "-c:v", "libx264",  # Video kodek
                "-preset", "fast",  # Tez ishlash uchun
                "-movflags", "+faststart"  # Streaming uchun optimallashtiradi (mobil uchun juda muhim)
            ],
            "ffmpeg_location": "/usr/bin/ffmpeg",  # Agar kerak bo‘lsa
            "noplaylist": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(instagram_url, download=True)
            file_path = ydl.prepare_filename(info_dict)
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            media_type = info_dict.get("ext")
            return info_dict, file_path, file_size, media_type
    except Exception as e:
        logging.error(f"Instagram media yuklashda xatolik: {e}", exc_info=True)
        return None, None, None, None



@dp.message()
async def process_instagram_media(message: Message):
    if not message.text.startswith("https://www.instagram.com"):
        await message.answer("❌ Iltimos, to‘g‘ri Instagram havolasini yuboring!")
        return

    await message.answer("⏳ Media yuklanmoqda, iltimos kuting...")

    info_dict, media_path, file_size, media_type = download_instagram_media(message.text)
    if media_path:
        if media_type == "mp4":
            media_file = FSInputFile(media_path)

            # Video davomiyligini olish
            duration = info_dict.get('duration', 'N/A') if media_type == "mp4" else 'N/A'

            caption = (
                "✅ <b>Instagram videosi yuklandi!</b>\n\n"
                f"📦 <b>Hajmi:</b> {file_size:.2f} MB\n"
                f"⏳ <b>Yuklash vaqti:</b> {duration} soniya\n"
                f"🔗 <b>Havola:</b> <a href='{message.text}'>Ko‘rish</a>\n\n"
                "📌 <b>Qo‘shimcha:</b> Agar boshqa video yoki rasm yubormoqchi bo'lsangiz, havolani yuboring!\n\n"
                "🤖 <b>Bot orqali yuklab olindi:</b> {@instaBunker_robot}\n"
                "📣 Boshqa videolarni ko'rish uchun <a href='https://t.me/KinoBunkerNews'>kanalimga</a> tashrif buyuring."
            )

            await message.answer_video(video=media_file, caption=caption, parse_mode="HTML")

        else:
            media_file = FSInputFile(media_path)
            await message.answer_photo(photo=media_file, caption="✅ Instagram rasmi yuklandi!")

        os.remove(media_path)  # Yuklab olingan faylni o‘chiramiz
    else:
        await message.answer("❌ Media yuklab bo‘lmadi. Havolani tekshirib qayta yuboring!")


async def main():
    logging.basicConfig(level=logging.INFO)
    install_ffmpeg()  # ffmpeg o‘rnatilganligini tekshiramiz
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
