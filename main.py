import logging
import asyncio
import os
import subprocess
import yt_dlp
from yt_dlp import YoutubeDL
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile

# Bot tokenini shu yerga kiriting
TOKEN = "6674407743:AAGCDQkI1TzLK6hnKhRKStCnnHpxqkBxGz0"
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
# ... (oldingi kod o‘zgarishsiz qoladi)

def download_youtube_audio(youtube_url):
    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": "youtube_audio.%(ext)s",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "ffmpeg_location": "/usr/bin/ffmpeg"
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            file_path = ydl.prepare_filename(info).replace(info['ext'], 'mp3')
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            return info, file_path, file_size
    except Exception as e:
        logging.error(f"YouTube audio yuklashda xatolik: {e}", exc_info=True)
        return None, None, None


@dp.message()
async def process_instagram_media(message: Message):
    text = message.text.strip()

    # YouTube havolani aniqlash
    if "youtube.com" in text or "youtu.be" in text:
        await message.answer("🎧 Audio MP3 formatda yuklanmoqda, iltimos kuting...")

        info, audio_path, file_size = download_youtube_audio(text)
        if audio_path:
            caption_text = (
                f"✅ <b>YouTube audio yuklandi!</b>\n\n"
                f"📦 <b>Hajmi:</b> {file_size:.2f} MB\n"
                f"🎵 <b>Sarlavha:</b> {info.get('title')}\n"
                f"🔗 <a href='{text}'>Video havola</a>\n"
                f"🤖 <b>Bot:</b> @{BOT_USERNAME}"
            )

            audio_file = FSInputFile(audio_path)
            await message.answer_audio(audio=audio_file, caption=caption_text, parse_mode="HTML")
            os.remove(audio_path)
        else:
            await message.answer("❌ Audio yuklab bo‘lmadi. Havola noto‘g‘ri bo‘lishi mumkin.")
        return

    # Instagram uchun mavjud kod
    if not text.startswith("https://www.instagram.com"):
        await message.answer("❌ Iltimos, Instagram yoki YouTube havolasini yuboring!")
        return

    await message.answer("⏳ Instagram mediasi yuklanmoqda, iltimos kuting...")

    info_dict, media_path, file_size, media_type = download_instagram_media(text)
    if media_path:
        caption_text = (
            f"✅ <b>Instagram fayli yuklandi!</b>\n\n"
            f"📦 <b>Hajmi:</b> {file_size:.2f} MB\n"
            f"🔗 <a href='{text}'>Ko‘rish</a>\n"
            f"🤖 <b>Bot:</b> @{BOT_USERNAME}"
        )

        media_file = FSInputFile(media_path)

        if media_type == "mp4":
            await message.answer_video(video=media_file, caption=caption_text, parse_mode="HTML")
        elif media_type in ["jpg", "jpeg", "png", "webp"]:
            await message.answer_photo(photo=media_file, caption=caption_text, parse_mode="HTML")
        else:
            await message.answer_document(document=media_file, caption=caption_text, parse_mode="HTML")

        os.remove(media_path)
    else:
        await message.answer("❌ Media yuklab bo‘lmadi. Havola noto‘g‘ri yoki maxfiy akkauntdan bo‘lishi mumkin.")


def download_instagram_media(instagram_url):
    """Instagram video yoki rasmni to'g'ri formatda yuklab olish"""
    try:
        ydl_opts = {
            "outtmpl": "instagram_media.%(ext)s",
            "format": "best[ext=mp4]/best",            # Avval MP4 formatdagi versiyasini olib ko'radi
            "cookiefile": "cookies.txt",  # <<< bu yerda cookies faylingiz
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
        caption_text = (
            f"✅ <b>Instagram fayli yuklandi!</b>\n\n"
            f"📦 <b>Hajmi:</b> {file_size:.2f} MB\n"
            f"🔗 <b>Havola:</b> <a href='{message.text}'>Ko‘rish</a>\n"
            f"🤖 <b>Bot:</b> @{BOT_USERNAME}"
        )

        media_file = FSInputFile(media_path)

        # Media turi bo‘yicha jo‘natamiz
        if media_type == "mp4":
            await message.answer_video(video=media_file, caption=caption_text, parse_mode="HTML")
        elif media_type in ["jpg", "jpeg", "png", "webp"]:
            await message.answer_photo(photo=media_file, caption=caption_text, parse_mode="HTML")
        else:
            await message.answer_document(document=media_file, caption=caption_text, parse_mode="HTML")

        os.remove(media_path)  # Foydalanuvchiga jo‘natilgandan so‘ng o‘chiramiz
    else:
        await message.answer("❌ Media yuklab bo‘lmadi. Ehtimol havola noto‘g‘ri yoki maxfiy akkauntdan!")

async def main():
    logging.basicConfig(level=logging.INFO)
    install_ffmpeg()  # ffmpeg o‘rnatilganligini tekshiramiz
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
