import telebot
import random
import time
import threading
from telebot import types
from database import db
from keep_alive import keep_alive

TOKEN = '8299180433:AAGF7sOYqXzm4Cx4rgNgYyGKEh61LNmtl-o'
ADMIN_ID = 6566152502

bot = telebot.TeleBot(TOKEN)

# O'yin holati
games = {}
# games = {
#    chat_id: {
#        'status': 'waiting' | 'playing' | 'night' | 'day',
#        'players': {user_id: {'name': name, 'role': role, 'alive': True, 'skin': skin}},
#        'votes': {},
#        'night_actions': {'killer': target_id, 'doctor': target_id},
#        'timer': None
#    }
# }

ROLES = ['QOTIL', 'DOCTOR', 'CREWMATE']

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎮 O'yinni boshlash", "🏆 Reyting")
    markup.add("💎 Premium", "📢 Reklama")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    db.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    text = "👋 Salom! 'Qotil' o'yiniga xush kelibsiz.\n\n"
    text += "🎮 O'yinni boshlash uchun botni guruhga qo'shing va /start_game buyrug'ini bering.\n"
    text += "💎 Premium funksiyalar uchun /premium yozing."
    bot.send_message(message.chat.id, text, reply_markup=get_main_keyboard())

@bot.message_handler(commands=['start_game'])
def start_game_cmd(message):
    if message.chat.type == 'private':
        bot.reply_to(message, "❌ Bu buyruq faqat guruhlarda ishlaydi!")
        return
    
    chat_id = message.chat.id
    if chat_id in games and games[chat_id]['status'] != 'waiting':
        bot.reply_to(message, "⚠️ O'yin allaqachon boshlangan!")
        return

    games[chat_id] = {
        'status': 'waiting',
        'players': {},
        'votes': {},
        'night_actions': {},
        'timer': None
    }
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Qo'shilish ➕", callback_data="join_game"))
    bot.send_message(chat_id, "🎮 O'yin boshlanmoqda! Qo'shilish uchun tugmani bosing (8-12 o'yinchi).", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "join_game")
def join_game(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    user_name = call.from_user.first_name

    if chat_id not in games:
        bot.answer_callback_query(call.id, "O'yin topilmadi.")
        return

    if user_id in games[chat_id]['players']:
        bot.answer_callback_query(call.id, "Siz allaqachon qo'shilgansiz!")
        return

    if len(games[chat_id]['players']) >= 12:
        bot.answer_callback_query(call.id, "Guruh to'lgan!")
        return

    games[chat_id]['players'][user_id] = {'name': user_name, 'role': None, 'alive': True, 'skin': '👤'}
    bot.answer_callback_query(call.id, "Siz o'yinga qo'shildingiz!")
    
    player_count = len(games[chat_id]['players'])
    bot.edit_message_text(f"🎮 O'yin boshlanmoqda! Qo'shilganlar: {player_count}/12\nRo'yxat: " + ", ".join([p['name'] for p in games[chat_id]['players'].values()]), 
                         chat_id, call.message.message_id, 
                         reply_markup=call.message.reply_markup)

    if player_count >= 8:
        # Avtomatik boshlash uchun taymer yoki tugma qo'shish mumkin
        pass

@bot.message_handler(commands=['run'])
def run_game(message):
    chat_id = message.chat.id
    if chat_id not in games or len(games[chat_id]['players']) < 4: # Test uchun 4 ta (aslida 8)
        bot.reply_to(message, "❌ Kamida 8 ta o'yinchi kerak!")
        return

    # Rollarni taqsimlash
    player_ids = list(games[chat_id]['players'].keys())
    random.shuffle(player_ids)
    
    killer_id = player_ids[0]
    doctor_id = player_ids[1]
    
    games[chat_id]['players'][killer_id]['role'] = 'QOTIL'
    games[chat_id]['players'][doctor_id]['role'] = 'DOCTOR'
    
    for pid in player_ids[2:]:
        games[chat_id]['players'][pid]['role'] = 'CREWMATE'
    
    games[chat_id]['status'] = 'playing'
    bot.send_message(chat_id, "🎭 Rollar taqsimlandi! Shaxsiy xabarlaringizni tekshiring.")
    
    for pid, pdata in games[chat_id]['players'].items():
        try:
            bot.send_message(pid, f"Sizning rolingiz: **{pdata['role']}** {pdata['skin']}")
        except:
            bot.send_message(chat_id, f"⚠️ {pdata['name']} botga /start bosmagan, unga rolini ayta olmayman!")

    start_night_phase(chat_id)

def start_night_phase(chat_id):
    games[chat_id]['status'] = 'night'
    games[chat_id]['night_actions'] = {}
    bot.send_message(chat_id, "🌙 TUN TUSHDI. Hamma ko'zini yumadi. Qotil va Doctor o'z ishini qiladi (60 soniya).")
    
    killer_id = next(pid for pid, p in games[chat_id]['players'].items() if p['role'] == 'QOTIL' and p['alive'])
    doctor_id = next((pid for pid, p in games[chat_id]['players'].items() if p['role'] == 'DOCTOR' and p['alive']), None)
    
    # Qotilga tanlash tugmalari
    markup_kill = types.InlineKeyboardMarkup()
    for pid, p in games[chat_id]['players'].items():
        if p['alive'] and p['role'] != 'QOTIL':
            markup_kill.add(types.InlineKeyboardButton(p['name'], callback_data=f"kill_{pid}"))
    bot.send_message(killer_id, "🔪 Kimni o'ldirasan?", reply_markup=markup_kill)
    
    # Doctorga tanlash tugmalari
    if doctor_id:
        markup_save = types.InlineKeyboardMarkup()
        for pid, p in games[chat_id]['players'].items():
            if p['alive']:
                markup_save.add(types.InlineKeyboardButton(p['name'], callback_data=f"save_{pid}"))
        bot.send_message(doctor_id, "🏥 Kimni saqlaysan?", reply_markup=markup_save)
    
    threading.Timer(60, end_night_phase, [chat_id]).start()

@bot.callback_query_handler(func=lambda call: call.data.startswith(('kill_', 'save_')))
def handle_night_actions(call):
    user_id = call.from_user.id
    action, target_id = call.data.split('_')
    target_id = int(target_id)
    
    # Chat ID ni topish (bu yerda biroz murakkablik bor, o'yinchi faqat bitta o'yinda bo'lishi kerak)
    chat_id = None
    for cid, g in games.items():
        if user_id in g['players']:
            chat_id = cid
            break
            
    if not chat_id: return

    if action == 'kill':
        games[chat_id]['night_actions']['killer'] = target_id
        bot.answer_callback_query(call.id, "Nishon belgilandi.")
    elif action == 'save':
        games[chat_id]['night_actions']['doctor'] = target_id
        bot.answer_callback_query(call.id, "O'yinchi himoyaga olindi.")

def end_night_phase(chat_id):
    if games[chat_id]['status'] != 'night': return
    
    actions = games[chat_id]['night_actions']
    killed_id = actions.get('killer')
    saved_id = actions.get('doctor')
    
    bot.send_message(chat_id, "☀️ KUN BO'LDI! Hamma uyg'ondi.")
    
    if killed_id and killed_id != saved_id:
        name = games[chat_id]['players'][killed_id]['name']
        games[chat_id]['players'][killed_id]['alive'] = False
        bot.send_message(chat_id, f"😱 Dahshat! Bugun tunda **{name}** o'ldirildi!")
    else:
        bot.send_message(chat_id, "😇 Xudoga shukur, bugun hech kim o'lmadi.")
    
    if check_game_over(chat_id): return
    
    start_day_phase(chat_id)

def start_day_phase(chat_id):
    games[chat_id]['status'] = 'day'
    games[chat_id]['votes'] = {}
    
    markup = types.InlineKeyboardMarkup()
    for pid, p in games[chat_id]['players'].items():
        if p['alive']:
            markup.add(types.InlineKeyboardButton(p['name'], callback_data=f"vote_{pid}"))
    
    bot.send_message(chat_id, "⚖️ Ovoz berish vaqti! Kim qotil deb o'ylaysiz? (90 soniya)", reply_markup=markup)
    threading.Timer(90, end_day_phase, [chat_id]).start()

@bot.callback_query_handler(func=lambda call: call.data.startswith('vote_'))
def handle_vote(call):
    voter_id = call.from_user.id
    target_id = int(call.data.split('_')[1])
    
    chat_id = call.message.chat.id
    if chat_id not in games or games[chat_id]['status'] != 'day': return
    
    if not games[chat_id]['players'][voter_id]['alive']:
        bot.answer_callback_query(call.id, "O'liklar ovoz bera olmaydi!")
        return
        
    games[chat_id]['votes'][voter_id] = target_id
    bot.answer_callback_query(call.id, "Ovozingiz qabul qilindi.")

def end_day_phase(chat_id):
    if games[chat_id]['status'] != 'day': return
    
    votes = games[chat_id]['votes']
    if not votes:
        bot.send_message(chat_id, "💤 Hech kim ovoz bermadi, hech kim haydalmadi.")
    else:
        # Eng ko'p ovoz olganni topish
        vote_counts = {}
        for v in votes.values():
            vote_counts[v] = vote_counts.get(v, 0) + 1
        
        max_votes = max(vote_counts.values())
        candidates = [k for k, v in vote_counts.items() if v == max_votes]
        
        if len(candidates) > 1:
            bot.send_message(chat_id, "🤝 Ovozlar teng keldi, hech kim haydalmadi.")
        else:
            lynched_id = candidates[0]
            name = games[chat_id]['players'][lynched_id]['name']
            role = games[chat_id]['players'][lynched_id]['role']
            games[chat_id]['players'][lynched_id]['alive'] = False
            bot.send_message(chat_id, f"⚖️ Ko'pchilik qarori bilan **{name}** haydaldi! Uning roli: {role}")
    
    if check_game_over(chat_id): return
    
    start_night_phase(chat_id)

def check_game_over(chat_id):
    players = games[chat_id]['players']
    alive_players = [p for p in players.values() if p['alive']]
    killer_alive = any(p['role'] == 'QOTIL' and p['alive'] for p in players.values())
    
    if not killer_alive:
        bot.send_message(chat_id, "🎉 G'ALABA! Qotil topildi. Crewmate'lar yutdi!")
        del games[chat_id]
        return True
    
    if len(alive_players) <= 2:
        bot.send_message(chat_id, "🔪 G'ALABA! Qotil hamma bilan hisoblashdi. Qotil yutdi!")
        del games[chat_id]
        return True
        
    return False

# Admin buyruqlari
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    bot.reply_to(message, "Salom Admin! Bot ishlamoqda.")

@bot.message_handler(commands=['premium'])
def premium_info(message):
    text = "💎 **PREMIUM OBUNA**\n\n"
    text += "✅ Maxsus rollar (Phantom, Jester)\n"
    text += "✅ Maxsus skinlar (Emoji)\n"
    text += "✅ Reklamasiz o'yin\n\n"
    text += "Narxi: 30,000 so'm/oy\n"
    text += "To'lov uchun: @admin_username"
    bot.send_message(message.chat.id, text)

if __name__ == "__main__":
    keep_alive()
    print("Bot ishga tushdi...")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Xatolik yuz berdi: {e}")
            time.sleep(5)

