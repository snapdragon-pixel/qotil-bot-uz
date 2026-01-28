# 🎮 Qotil (Among Us Style) Telegram Bot

Ushbu bot Telegram guruhlarida "Qotil" o'yinini o'tkazish uchun mo'ljallangan.

## 🚀 O'rnatish bo'yicha ko'rsatma

### 1. Talablar
- Python 3.8+
- Bot Token (BotFather orqali olingan)

### 2. Kutubxonalarni o'rnatish
```bash
pip install pyTelegramBotAPI flask
```

### 3. Botni ishga tushirish
```bash
python main.py
```

## 🎮 O'yin mexanikasi
1. Botni guruhga qo'shing va unga adminlik bering.
2. `/start_game` buyrug'ini bering.
3. O'yinchilar "Qo'shilish" tugmasini bosadi (8-12 kishi).
4. `/run` buyrug'i bilan o'yinni boshlang.

## 🌙 Tungi faza
- Qotil kimni o'ldirishni tanlaydi.
- Doctor kimni saqlashni tanlaydi.

## ☀️ Kunduzi faza
- O'ldirilgan o'yinchi e'lon qilinadi.
- Hamma muhokama qiladi va ovoz beradi.
- Eng ko'p ovoz olgan o'yinchi haydaladi.

## 💎 Premium va Monetizatsiya
- `/premium` - Premium funksiyalar haqida ma'lumot.
- Botda reklama joylari va turnir rejimlari mavjud.

## 🛠 Texnik qism
- **Backend:** Python + Telebot
- **Database:** SQLite (ma'lumotlarni ishonchli saqlash uchun)
- **Hosting:** 24/7 ishlashi uchun `keep_alive.py` (Flask) qo'shilgan.
