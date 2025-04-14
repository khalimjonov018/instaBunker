# 1. Python bazasini olish
FROM python:3.11-slim

# 2. Zarur system kutubxonalarni o‘rnatish (ffmpeg kerak, chunki video yuklash uchun)
RUN apt-get update && apt-get install -y ffmpeg

# 3. Ish papkasi yaratish
WORKDIR /app

# 4. Hamma fayllarni container ichiga nusxalash
COPY . .

# 5. Python kutubxonalarni o‘rnatish (masalan, yt-dlp, telebot va h.k.)
RUN pip install --no-cache-dir -r requirements.txt

# 6. Botni ishga tushurish
CMD ["python", "main.py"]
