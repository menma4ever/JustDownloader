import telebot
from telebot import types
import json
import os
from datetime import datetime, timedelta
import time


# Bot tokeningizni kiritishingiz kerak
bot = telebot.TeleBot('7319299432:AAFckpwgsiXqUKQGE7xmNdBYYct4faZg1ow')

# Foydalanuvchi ma'lumotlari fayli yo'li
user_data_file = 'user_data.json'

# Foydalanuvchi ma'lumotlari fayli mavjudligini ta'minlash
if not os.path.exists(user_data_file):
    with open(user_data_file, 'w') as file:
        json.dump({}, file)



# Foydalanuvchi ma'lumotlarini yangilash funktsiyasi
def update_user_data(user_id, user_name, user_username):
    with open(user_data_file, 'r') as file:
        data = json.load(file)
    if user_id in data:
        data[user_id]['name'] = user_name
        data[user_id]['username'] = user_username
        with open(user_data_file, 'w') as file:
            json.dump(data, file)
        return True
    else:
        return False



@bot.message_handler(commands=['status'])
def bot_status(message):
    # User ma'lumotlarini yuklash
    with open('user_data.json', 'r') as user_file:
        user_data = json.load(user_file)
    user_count = len(user_data)

    # Anime ma'lumotlarini yuklash
    with open('hentay_data.json', 'r') as anime_file:
        anime_data = json.load(anime_file)
    anime_count = len(anime_data)
    total_episodes = sum(anime['qismi_soni'] for anime in anime_data)

    # Status xabarini tuzish
    status_message = (
        f"📊 Bot statistikalari:\n\n"
        f"👥 Foydalanuvchilar soni: {user_count}\n"
        f"📚 Animeslar soni: {anime_count}\n"
        f"🎥 Jami qismlar soni: {total_episodes}"
    )
    
    # Xabarni yuborish
    bot.reply_to(message, status_message)



import threading
import time

@bot.message_handler(commands=['reset'])
def reset_premium_time(message):
    if message.from_user.id != admin:
        bot.reply_to(message, "Sizda ushbu komandani ishlatish huquqi yo'q.")
        return
    
    if message.chat.type != 'private':
        bot.reply_to(message, "Ushbu komanda faqat private chatlarda ishlaydi.")
        return
    
    bot.reply_to(message, "Premium muddatlarini tiklash jarayoni boshlandi.")

    with open(user_data_file, 'r') as user_file:
        user_data = json.load(user_file)

    for user_id, user_info in user_data.items():
        if user_info.get('prem', False) and user_info['prem_time'] > 0:
            threading.Thread(target=decrease_prem_time, args=(user_id, user_info['prem_time'], user_data)).start()
    
    bot.reply_to(message, "Barcha premium foydalanuvchilar uchun premium muddatlari davom ettirildi.")

def decrease_prem_time(user_id, prem_time, user_data):
    while prem_time > 0:
        time.sleep(1)
        prem_time -= 1
        
        with open(user_data_file, 'w') as user_file:
            user_data[user_id]['prem_time'] = prem_time
            json.dump(user_data, user_file, indent=4)
    
    user_data[user_id]['prem'] = False
    
    with open(user_data_file, 'w') as user_file:
        json.dump(user_data, user_file, indent=4)
    
    # Foydalanuvchiga prem tugaganini bildirish
    try:
        bot.send_message(user_id, "Premium muddati tugadi. Qayta olish uchun @BlitzB_admin ga murojaat qiling.")
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code == 403:
            bot.send_message(admin[0], f"Foydalanuvchi {user_id} botni blok qilgan. Unga xabar yuborilmadi.")





@bot.message_handler(commands=['add'])
def add_anime(message):
    if message.from_user.id != admin:
        bot.reply_to(message, "Sizda ushbu komandani ishlatish huquqi yo'q.")
        return
    
    if message.chat.type != 'private':
        bot.reply_to(message, "Ushbu komanda faqat private chatlarda ishlaydi.")
        return
    
    bot.reply_to(message, "Anime ID sini kiriting:")
    bot.register_next_step_handler(message, process_anime_id)

def process_anime_id(message):
    anime_id = message.text.strip()
    
    with open('hentay_data.json', 'r') as file:
        anime_data = json.load(file)
    
    anime = next((item for item in anime_data if item["id"] == int(anime_id)), None)
    
    if anime:
        bot.reply_to(message, f"Anime nomi: {anime['nomi']}\nQism qo'shmoqchimisiz? (yes/no)")
        bot.register_next_step_handler(message, process_add_episode, anime)
    else:
        bot.reply_to(message, "Yangi anime qo'shamizmi? (yes/no)")
        bot.register_next_step_handler(message, process_add_new_anime, anime_id)

def process_add_episode(message, anime):
    if message.text.strip().lower() == 'yes':
        bot.reply_to(message, "Linkni kiriting:")
        bot.register_next_step_handler(message, process_episode_link, anime)
    else:
        bot.reply_to(message, "Amal bekor qilindi.")

def process_episode_link(message, anime, anime_data):
    link = message.text.strip()
    last_episode = max(int(key) for key in anime.keys() if key.isdigit())
    new_episode = last_episode + 1
    anime[str(new_episode)] = link
    anime['qismi_soni'] += 1
    
    with open('hentay_data.json', 'w') as file:
        json.dump(anime_data, file, indent=4)
    
    bot.reply_to(message, f"Yangi qism qo'shildi: {new_episode}")

    
    bot.reply_to(message, f"Yangi qism qo'shildi: {new_episode}")

def process_add_new_anime(message, anime_id):
    if message.text.strip().lower() == 'yes':
        bot.reply_to(message, "Anime nomini kiriting:")
        bot.register_next_step_handler(message, process_new_anime_name, anime_id)
    else:
        bot.reply_to(message, "Amal bekor qilindi.")

def process_new_anime_name(message, anime_id):
    anime_name = message.text.strip()
    bot.reply_to(message, "Nechta qism bor?")
    bot.register_next_step_handler(message, process_new_anime_episodes, anime_id, anime_name)

def process_new_anime_episodes(message, anime_id, anime_name):
    episodes = int(message.text.strip())
    bot.reply_to(message, "Qaysi davlat?")
    bot.register_next_step_handler(message, process_new_anime_country, anime_id, anime_name, episodes)

def process_new_anime_country(message, anime_id, anime_name, episodes):
    country = message.text.strip()
    bot.reply_to(message, "Qaysi til?")
    bot.register_next_step_handler(message, process_new_anime_language, anime_id, anime_name, episodes, country)

def process_new_anime_language(message, anime_id, anime_name, episodes, country):
    language = message.text.strip()
    bot.reply_to(message, "Nechanchi yili chiqqan?")
    bot.register_next_step_handler(message, process_new_anime_year, anime_id, anime_name, episodes, country, language)

def process_new_anime_year(message, anime_id, anime_name, episodes, country, language):
    year = int(message.text.strip())
    bot.reply_to(message, "Janri nima?")
    bot.register_next_step_handler(message, process_new_anime_genre, anime_id, anime_name, episodes, country, language, year)

def process_new_anime_genre(message, anime_id, anime_name, episodes, country, language, year):
    genre = message.text.strip()
    bot.reply_to(message, "Pfp uchun file path kiriting:")
    bot.register_next_step_handler(message, process_new_anime_pfp, anime_id, anime_name, episodes, country, language, year, genre)

def process_new_anime_pfp(message, anime_id, anime_name, episodes, country, language, year, genre):
    pfp = message.text.strip()
    bot.reply_to(message, "Linkni kiriting:")
    bot.register_next_step_handler(message, process_new_anime_link, anime_id, anime_name, episodes, country, language, year, genre, pfp)

def process_new_anime_link(message, anime_id, anime_name, episodes, country, language, year, genre, pfp):
    link = message.text.strip()
    new_anime = {
        "id": int(anime_id),
        "nomi": anime_name,
        "qismi": episodes,
        "davlat": country,
        "tili": language,
        "yili": year,
        "janri": genre,
        "qidirishlar_soni": 0,
        "pfp": pfp,
        "qismi_soni": 1,
        "1": link
    }
    
    with open('hentay_data.json', 'r') as file:
        anime_data = json.load(file)
    
    anime_data.append(new_anime)
    
    with open('hentay_data.json', 'w') as file:
        json.dump(anime_data, file, indent=4)
    
    bot.reply_to(message, "Yangi anime qo'shildi.")



@bot.message_handler(commands=['del'])
def delete_anime(message):
    if message.from_user.id != admin:
        bot.reply_to(message, "Sizda ushbu komandani ishlatish huquqi yo'q.")
        return
    
    if message.chat.type != 'private':
        bot.reply_to(message, "Ushbu komanda faqat private chatlarda ishlaydi.")
        return
    
    bot.reply_to(message, "Anime ID sini kiriting:")
    bot.register_next_step_handler(message, process_delete_anime_id)

def process_delete_anime_id(message):
    anime_id = message.text.strip()
    
    with open('hentay_data.json', 'r') as file:
        anime_data = json.load(file)
    
    anime = next((item for item in anime_data if item["id"] == int(anime_id)), None)
    
    if anime:
        anime_info = (
            f"Anime nomi: {anime['nomi']}\n"
            f"Qismlar soni: {anime['qismi_soni']}\n"
            f"Davlat: {anime['davlat']}\n"
            f"Til: {anime['tili']}\n"
            f"Yili: {anime['yili']}\n"
            f"Janri: {anime['janri']}\n"
            f"Qidirishlar soni: {anime['qidirishlar_soni']}\n"
        )
        bot.reply_to(message, f"{anime_info}\nBu animeni o'chirmoqchimisiz? (yes/no)")
        bot.register_next_step_handler(message, confirm_delete_anime, anime_id, anime_data)
    else:
        bot.reply_to(message, "Anime topilmadi.")

def confirm_delete_anime(message, anime_id, anime_data):
    if message.text.strip().lower() == 'yes':
        anime_data = [item for item in anime_data if item["id"] != int(anime_id)]
        
        with open('hentay_data.json', 'w') as file:
            json.dump(anime_data, file, indent=4)
        
        bot.reply_to(message, "Anime o'chirildi.")
    else:
        bot.reply_to(message, "Amal bekor qilindi.")





@bot.message_handler(commands=['bankai'])
def bankai_command(message):
    if message.from_user.id != admin:
        bot.reply_to(message, "Sizda ushbu komandani ishlatish huquqi yo'q.")
        return
    
    if message.chat.type != 'private':
        bot.reply_to(message, "Ushbu komanda faqat private chatlarda ishlaydi.")
        return

    if message.reply_to_message and message.text.strip() != '/bankai':
        bot.reply_to(message, "Iltimos, faqat reply qiling yoki faqat ID kiriting. Ikkisidan birini tanlang.")
        return

    # Agar reply qilingan bo'lsa
    if message.reply_to_message:
        user_id = str(message.reply_to_message.from_user.id)
    else:
        # Agar ID kiritsilgan bo'lsa
        try:
            user_id = message.text.split()[1].strip()
        except IndexError:
            bot.reply_to(message, "Iltimos, foydalanuvchi ID sini kiriting yoki kimdirga reply qiling.")
            return
    
    # user_data.json faylidan foydalanuvchini o'chirish
    with open(user_data_file, 'r') as file:
        user_data = json.load(file)

    if user_id in user_data:
        user_data.pop(user_id)
        with open(user_data_file, 'w') as file:
            json.dump(user_data, file, indent=4)
        bot.reply_to(message, f"Foydalanuvchi ma'lumotlari o'chirildi: {user_id}")
    else:
        bot.reply_to(message, "Foydalanuvchi ma'lumotlar bazasida topilmadi.")










@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)

    # user_data.json faylini ochish
    with open(user_data_file, 'r') as file:
        data = json.load(file)

    if user_id in data:
        user_name = data[user_id]['name']
        welcome_message = f"Hush kelibsiz!!! {user_name} 😊"
    else:
        user_name = message.from_user.first_name
        user_username = message.from_user.username
        save_user_data(user_id, user_name, user_username)
        welcome_message = "Hentay botimizga hush kelibsiz, foydalanish uchun pastdagi tugmalardan foydalaning 😊"
    
    # Kanalga obuna bo'lganligini tekshirish
    channel_id1 = '@Hentay_uz_official'
    channel_id2 = '@Hentay_uz_chat'
    joined_channel1 = check_user_joined_channel(user_id, channel_id1)
    joined_channel2 = check_user_joined_channel(user_id, channel_id2)

    if joined_channel1 and joined_channel2:
        bot.send_message(chat_id, welcome_message)
        
        # Custom reply keyboard
        keyboard = telebot.types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
        button1 = telebot.types.KeyboardButton('🔍 Hentay izlash')
        button2 = telebot.types.KeyboardButton('🔞 Premium ')
        button3 = telebot.types.KeyboardButton("📚 Malumot")
        button4 = telebot.types.KeyboardButton('💵 Reklama va Homiylik')
        keyboard.row(button1)
        keyboard.row(button2, button3, button4)
        
        bot.send_message(chat_id, "Iltimos, pastdagi tugmalardan foydalaning:", reply_markup=keyboard)
    else:
        markup = types.InlineKeyboardMarkup(row_width=2)
        join_button1 = types.InlineKeyboardButton(text="Kanal 1", url=f"https://t.me/{channel_id1[1:]}")
        join_button2 = types.InlineKeyboardButton(text="Kanal 2", url=f"https://t.me/{channel_id2[1:]}")
        link = types.InlineKeyboardButton(text="Instagram", url="https://www.instagram.com/_senpai.1707_/")
        confirm_button = types.InlineKeyboardButton(text="Tasdiqlash", callback_data="confirm_subscription")
        markup.add(join_button1, join_button2)
        markup.add(link)
        markup.add(confirm_button)
        
        bot.send_message(chat_id, "Iltimos, foydalanishdan oldin quyidagi kanallarga obuna bo'ling:", reply_markup=markup)

# Check user subscription status
def check_user_joined_channel(user_id, channel_id):
    try:
        chat_member = bot.get_chat_member(channel_id, user_id)
        if chat_member.status in ['member', 'administrator', 'creator']:
            return True
        else:
            return False
    except:
        return False

# Save user data function
def save_user_data(user_id, user_name, user_username):
    with open(user_data_file, 'r+') as file:
        data = json.load(file)
        if user_id not in data:
            data[user_id] = {
                'name': user_name,
                'username': user_username,
                'joined_at': time.time(),
                'prem': False,
                'prem_time': 0
            }
            file.seek(0)
            json.dump(data, file, indent=4)

@bot.callback_query_handler(func=lambda call: call.data == "confirm_subscription")
def confirm_subscription(call):
    user_id = str(call.from_user.id)
    channel_id1 = '@Hentay_uz_official'
    channel_id2 = '@Hentay_uz_chat'
    
    joined_channel1 = check_user_joined_channel(user_id, channel_id1)
    joined_channel2 = check_user_joined_channel(user_id, channel_id2)
    
    if joined_channel1 and joined_channel2:
        bot.answer_callback_query(call.id, "Obuna tasdiqlandi. Foydalanishni boshlashingiz mumkin.")
        send_welcome(call.message)  # Foydalanuvchi obuna bo'lgach, /start buyrug'ini qayta chaqirish
    else:
        bot.answer_callback_query(call.id, "Obuna hali tasdiqlanmadi. Iltimos, ikkala kanalga obuna bo'ling.")



@bot.message_handler(func=lambda message: message.text == '🔍 Hentay izlash' and message.chat.type == 'private')
def search_anime(message):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)
    
    # Kanalga obuna bo'lganligini tekshirish
    channel_id1 = '@Hentay_uz_official'
    channel_id2 = '@Hentay_uz_chat'
    joined_channel1 = check_user_joined_channel(user_id, channel_id1)
    joined_channel2 = check_user_joined_channel(user_id, channel_id2)
    
    if joined_channel1 and joined_channel2:
        # Faqat Orqaga tugmasi bilan yangi reply keyboard
        keyboard = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        back_button = telebot.types.KeyboardButton('Orqaga')
        keyboard.add(back_button)
        msg = bot.send_message(chat_id, "Anime kodini kiriting:", reply_markup=keyboard)
        
        bot.register_next_step_handler(msg, get_anime_by_id)
    else:
        message_text = (
            "Iltimos, ushbu xizmatdan foydalanish uchun ikkala kanalga ham obuna bo'ling:\n"
            f"Kanal 1: https://t.me/{channel_id1[1:]}\n"
            f"Kanal 2: https://t.me/{channel_id2[1:]}"
        )
        bot.send_message(chat_id, message_text)

# Check user subscription status function
def check_user_joined_channel(user_id, channel_id):
    try:
        chat_member = bot.get_chat_member(channel_id, user_id)
        if chat_member.status in ['member', 'administrator', 'creator']:
            return True
        else:
            return False
    except:
        return False



def get_anime_by_id(message):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)
    
    # Kanalga obuna bo'lganligini tekshirish
    channel_id1 = '@Hentay_uz_official'
    channel_id2 = '@hentay_uz_chat'
    
    joined_channel1 = check_user_joined_channel(user_id, channel_id1)
    joined_channel2 = check_user_joined_channel(user_id, channel_id2)
    
    if joined_channel1 and joined_channel2:
        # Foydalanuvchi "Orqaga" tugmasini bosdi, qaytish
        if message.text == 'Orqaga':
            go_back(message)
            return

        # Raqamlarni tekshirish
        try:
            anime_id = int(message.text)
        except ValueError:
            bot.send_message(chat_id, "Iltimos, faqat raqam kiriting.")
            bot.register_next_step_handler(message, get_anime_by_id)  # Takrorlash uchun qaytadan registratsiya qilish
            return

        with open('hentay_data.json', 'r') as file:
            data = json.load(file)

        anime = next((item for item in data if item["id"] == anime_id), None)

        if anime:
            anime["qidirishlar_soni"] += 1
            with open('hentay_data.json', 'w') as file:
                json.dump(data, file, indent=4)

            anime_info = (
                f"🎬 Nomi: {anime['nomi']}\n"
                f"🎥 Qismi: {anime['qismi_soni']}\n"
                f"🌍 Davlati: {anime['davlat']}\n"
                f"🇺🇿 Tili: {anime['tili']}\n"
                f"📆 Yili: {anime['yili']}\n"
                f"🎞 Janri: {anime['janri']}\n\n"
                f"🔍 Qidirishlar soni: {anime['qidirishlar_soni']}\n\n"
            )

            inline_keyboard = types.InlineKeyboardMarkup()
            download_button = types.InlineKeyboardButton("Yuklab olish", callback_data=f"start_download_{anime_id}_1")
            inline_keyboard.add(download_button)

            pfp = anime['pfp']
            if pfp.startswith('http'):
                bot.send_photo(chat_id, pfp, caption=anime_info, reply_markup=inline_keyboard)
            else:
                bot.send_photo(chat_id, open(pfp, 'rb'), caption=anime_info, reply_markup=inline_keyboard)
        else:
            bot.send_message(chat_id, "Anime topilmadi. Iltimos, qayta urinib ko'ring.")
        
        # Yangi qidiruv uchun qayta registratsiya qilish
        msg = bot.send_message(chat_id, "Yangi anime kodini kiriting yoki Orqaga qayting.")
        msg = bot.send_message(chat_id, "🎬 Relama uchun joy @seevar_06 📩")
        bot.register_next_step_handler(msg, get_anime_by_id)
    else:
        message_text = (
            "Iltimos, ushbu xizmatdan foydalanish uchun uchala kanalga ham obuna bo'ling:\n"
            f"Kanal 1: https://t.me/{channel_id1[1:]}\n"
            f"Kanal 2: https://t.me/{channel_id2[1:]}\n"
        )
        bot.send_message(chat_id, message_text)

# Check user subscription status function
def check_user_joined_channel(user_id, channel_id):
    try:
        chat_member = bot.get_chat_member(channel_id, user_id)
        if chat_member.status in ['member', 'administrator', 'creator']:
            return True
        else:
            return False
    except:
        return False




import requests

@bot.callback_query_handler(func=lambda call: call.data.startswith('start_download_'))
def start_download_anime(call):
    user_id = str(call.from_user.id)
    
    # hentay_data.json faylini ochish
    with open('hentay_data.json', 'r') as file:
        anime_data = json.load(file)

    for anime in anime_data:
        anime_name = anime.get('nomi', 'Anime')
        for qism, qism_path in anime.items():
            if qism.isdigit() and call.data == f"start_download_{anime['id']}_{qism}":
                caption = f"{anime_name}\n\n{qism} qism"
                inline_keyboard = types.InlineKeyboardMarkup(row_width=2)
                prev_qism = int(qism) - 1
                next_qism = int(qism) + 1

                # Oldingi qism tugmasini qo'shish
                if str(prev_qism) in anime:
                    prev_button = types.InlineKeyboardButton("Oldingi", callback_data=f"check_premium_prev_{anime['id']}_{prev_qism}")
                else:
                    prev_button = types.InlineKeyboardButton("Oldingi (yo'q)", callback_data="error_prev_not_found")
                inline_keyboard.add(prev_button)

                # Keyingi qism tugmasini qo'shish
                if str(next_qism) in anime:
                    next_button = types.InlineKeyboardButton("Keyingi", callback_data=f"check_premium_next_{anime['id']}_{next_qism}")
                else:
                    next_button = types.InlineKeyboardButton("Keyingi (yo'q)", callback_data="error_next_not_found")
                inline_keyboard.add(next_button)

                try:
                    # URL manzilni olish va forward qilish
                    if qism_path.startswith('https://t.me/'):
                        chat_info = qism_path.replace('https://t.me/', '').split('/')
                        chat_id = f"@{chat_info[0]}"
                        message_id = int(chat_info[1])
                        
                        # Xabarni forward qilish
                        forwarded_message = bot.forward_message(call.message.chat.id, chat_id, message_id)
                        
                        # Forward qilinganligini yashirish uchun xabar mazmunini qayta yuborish
                        if forwarded_message.video:
                            video_file_id = forwarded_message.video.file_id
                            
                            # Forward qilingan xabarni o'chirib, yangi xabar jo'natish
                            bot.delete_message(call.message.chat.id, forwarded_message.message_id)
                            bot.delete_message(call.message.chat.id, call.message.message_id)
                            bot.send_video(
                                call.message.chat.id, video_file_id, caption=caption, reply_markup=inline_keyboard,
                                supports_streaming=True, protect_content=True
                            )
                        else:
                            bot.send_message(call.message.chat.id, "Forward qilingan xabar video emas.")
                    else:
                        with open(qism_path, 'rb') as media_file:
                            bot.delete_message(call.message.chat.id, call.message.message_id)
                            bot.send_video(
                                call.message.chat.id, media_file, caption=caption, reply_markup=inline_keyboard,
                                supports_streaming=True, protect_content=True
                            )
                except Exception as e:
                    bot.send_message(call.message.chat.id, f"Media yuklab olishda muammo: {e}")
                return

    bot.answer_callback_query(call.id, "Qism topilmadi.")



@bot.callback_query_handler(func=lambda call: call.data.startswith('check_premium_'))
def check_premium(call):
    user_id = str(call.from_user.id)
    
    # user_data.json faylini ochish
    with open(user_data_file, 'r') as user_file:
        user_data = json.load(user_file)
    
    is_premium = user_data.get(user_id, {}).get('prem', False)

    if not is_premium:
        bot.answer_callback_query(call.id, "Premiumingiz mavjud emas.")
        return

    data_parts = call.data.split('_')
    if len(data_parts) == 5:
        action = data_parts[2]
        anime_id = data_parts[3]
        qism = data_parts[4]

        # Qism mavjudligini tekshirish
        with open('hentay_data.json', 'r') as file:
            anime_data = json.load(file)
        
        anime = next((item for item in anime_data if item["id"] == int(anime_id)), None)
        if anime and str(qism) in anime:
            # Keyingi yoki oldingi qismga o'tish
            new_call_data = f"start_download_{anime_id}_{qism}"
            new_call = call
            new_call.data = new_call_data
            start_download_anime(new_call)
        else:
            if action == 'next':
                bot.answer_callback_query(call.id, "Keyingi qism mavjud emas.")
            elif action == 'prev':
                bot.answer_callback_query(call.id, "Oldingi qism mavjud emas.")
    else:
        bot.answer_callback_query(call.id, "Xato yuz berdi.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('error'))
def handle_errors(call):
    error_messages = {
        "error_no_premium": "Premiumingiz mavjud emas.",
        "error_prev_not_found": "Oldingi qism yo'q.",
        "error_next_not_found": "Keyingi qism yo'q."
    }
    bot.answer_callback_query(call.id, error_messages.get(call.data, "Xato yuz berdi."))















@bot.message_handler(func=lambda message: message.text == 'Orqaga' and message.chat.type == 'private')
def go_back(message):
    chat_id = message.chat.id

    # Eski reply keyboardni qayta tiklash
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    button1 = telebot.types.KeyboardButton('🔍 Hentay izlash')
    button2 = telebot.types.KeyboardButton('🔞 Premium ')
    button3 = telebot.types.KeyboardButton("📚 Malumot")
    button4 = telebot.types.KeyboardButton('💵 Reklama va Homiylik')
    keyboard.row(button1)
    keyboard.row(button2, button3, button4)
    
    bot.send_message(chat_id, "Orqaga qaytdingiz.", reply_markup=keyboard)



@bot.message_handler(commands=['restart'])
def restart_user(message):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name
    user_username = message.from_user.username

    if update_user_data(user_id, user_name, user_username):
        bot.send_message(chat_id, "Ma'lumotlaringiz yangilandi 😊")
    else:
        inline_keyboard = telebot.types.InlineKeyboardMarkup()
        private_button = telebot.types.InlineKeyboardButton("Botga O'tish", url=f't.me/{bot.get_me().username}?start')
        inline_keyboard.add(private_button)
        bot.send_message(chat_id, "Siz botda registratsiya qilmagansiz 😊", reply_markup=inline_keyboard)

def update_user_data(user_id, user_name, user_username):
    with open(user_data_file, 'r+') as file:
        data = json.load(file)
        if user_id in data:
            data[user_id]['name'] = user_name
            data[user_id]['username'] = user_username
            file.seek(0)
            json.dump(data, file, indent=4)  # Ma'lumotlarni faylga saqlashda indent parametri bilan
            file.truncate()  # Foylani qisqartirish, ortiqcha qismlarini olib tashlash
            return True
        return False



@bot.message_handler(func=lambda message: message.text == '🔞 Premium' and message.chat.type == 'private')
def send_vip_channel_info(message):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)
    
    # Kanalga obuna bo'lganligini tekshirish
    channel_id1 = '@Hentay_uz_official'
    channel_id2 = '@Hentay_uz_chat'
    joined_channel1 = check_user_joined_channel(user_id, channel_id1)
    joined_channel2 = check_user_joined_channel(user_id, channel_id2)
    
    if joined_channel1 and joined_channel2:
        bot.send_message(chat_id, "🔞 Premium imiz 🔞 \n\nNarxi: 30000 so'm \n🚫 4K Hentai ✅ \n🚫 4k Sex ✅ \n🕔 1 oy uchun \n\ntg: @seevar_06")
    else:
        message_text = (
            "Iltimos, ushbu xizmatdan foydalanish uchun ikkala kanalga ham obuna bo'ling:\n"
            f"Kanal 1: https://t.me/{channel_id1[1:]}\n"
            f"Kanal 2: https://t.me/{channel_id2[1:]}"
        )
        bot.send_message(chat_id, message_text)


@bot.message_handler(func=lambda message: message.text == "📚 Malumot" and message.chat.type == 'private')
def send_qollanma_info(message):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)
    
    # Kanalga obuna bo'lganligini tekshirish
    channel_id1 = '@Hentay_uz_official'
    channel_id2 = '@Hentay_uz_chat'
    joined_channel1 = check_user_joined_channel(user_id, channel_id1)
    joined_channel2 = check_user_joined_channel(user_id, channel_id2)
    
    if joined_channel1 and joined_channel2:
        # Malumotlarni yuborish
        info_message = (
            "*Yangiliklar:*\n"
            "Bizning eng sara va sifatli yangi anime loyihalarimizni Telegram kanalimizda e'lon qilamiz! Har bir anime o'ziga xos va qiziqarli bo'lib, sizni hayratda qoldiradi. 🎉\n\n"
            
            "*ID orqali qidirish:*\n"
            "Mukammal tuzilgan ID tizimimiz orqali yangi jentaklarni tez va oson toping. Bu sizga kerakli ma'lumotlarni tezda topishga yordam beradi. 🔍\n\n"
            
            "*Reklama imkoniyatlari:*\n"
            "Bizning arzon va ishonchli reklama turlarimizdan foydalaning va yangiliklardan xabardor bo'ling! Reklama joylashtirish uchun biz bilan bog'laning va o'z biznesingizni rivojlantiring. 📈\n\n"
            
            "*Qo'shimcha afzalliklar:*\n"
            "- **Yuqori sifat:** Bizning anime loyihalarimiz yuqori sifatli va qiziqarli bo'lib, sizni hayratda qoldiradi.\n"
            "- **Tezkor qidiruv:** ID tizimi orqali kerakli ma'lumotlarni tezda toping.\n"
            "- **Arzon reklama:** Bizning reklama turlarimiz arzon va ishonchli, bu sizga biznesingizni rivojlantirishda yordam beradi.\n"
        )
        bot.send_message(chat_id, info_message, parse_mode='Markdown')
    else:
        message_text = (
            "Iltimos, ushbu xizmatdan foydalanish uchun ikkala kanalga ham obuna bo'ling:\n"
            f"Kanal 1: https://t.me/{channel_id1[1:]}\n"
            f"Kanal 2: https://t.me/{channel_id2[1:]}"
        )
        bot.send_message(chat_id, message_text)
     


@bot.message_handler(func=lambda message: message.text == "💵 Reklama va Homiylik" and message.chat.type == 'private')
def send_homiylik_info(message):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)
    
    # Kanalga obuna bo'lganligini tekshirish
    channel_id1 = '@Hentay_uz_official'
    channel_id2 = '@Hentay_uz_chat'
    joined_channel1 = check_user_joined_channel(user_id, channel_id1)
    joined_channel2 = check_user_joined_channel(user_id, channel_id2)
    
    if joined_channel1 and joined_channel2:
        bot.send_message(chat_id, "💵 Reklama va Homiylik mavjud emas")
    else:
        message_text = (
            "Iltimos, ushbu xizmatdan foydalanish uchun ikkala kanalga ham obuna bo'ling:\n"
            f"Kanal 1: https://t.me/{channel_id1[1:]}\n"
            f"Kanal 2: https://t.me/{channel_id2[1:]}"
        )
        bot.send_message(chat_id, message_text) 



@bot.message_handler(commands=['profile'])
def show_profile(message):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)

    with open(user_data_file, 'r') as file:
        data = json.load(file)

    if user_id in data:
        user_info = data[user_id]
        prem_status = "😊 Mavjud" if user_info['prem'] else "😞 Mavjud emas"
        
        if user_info['prem_time'] > 0:
            premium_end_time = datetime.now() + timedelta(seconds=user_info['prem_time'])
            prem_time_remaining = premium_end_time - datetime.now()
            hours, remainder = divmod(prem_time_remaining.total_seconds(), 3600)
            minutes, _ = divmod(remainder, 60)
            prem_time = f"😃 {int(hours)} soat {int(minutes)} minut"
        else:
            prem_time = "😞 Mavjud emas"

        profile_message = (
            f"Ism: 😊 {user_info['name']} \n"
            f"Username: 😊 @{user_info['username']} \n"
            f"Premium status: {prem_status} \n"
            f"Premium vaqti: {prem_time} \n\n"
            f"/restart - Profilingizni yangilash uchun 🔄"
        )
    else:
        inline_keyboard = telebot.types.InlineKeyboardMarkup()
        private_button = telebot.types.InlineKeyboardButton("Botga O'tish", url=f't.me/{bot.get_me().username}?start')
        inline_keyboard.add(private_button)
        profile_message = "Siz botda registratsiya qilmagansiz 😊"

    bot.reply_to(message, profile_message, reply_markup=inline_keyboard if 'inline_keyboard' in locals() else None)


admin = 7577190183  # Ro'yxatga boshqa adminlar IDlarini qo'shing


import threading
import time

@bot.message_handler(commands=['give'])
def give_premium(message):
    if message.from_user.id != admin:
        bot.reply_to(message, "Sizda ushbu komandani ishlatish huquqi yo'q.")
        return
    
    if not message.reply_to_message:
        bot.reply_to(message, "Ushbu komandani ishlatish uchun foydalanuvchiga reply qiling.")
        return
    
    user_id = str(message.reply_to_message.from_user.id)
    
    with open(user_data_file, 'r') as user_file:
        user_data = json.load(user_file)
    
    if user_id not in user_data:
        bot.reply_to(message, "Ushbu foydalanuvchi ma'lumotlar bazasida topilmadi.")
        return

    if user_data[user_id].get('prem', False):
        bot.reply_to(message, f"{message.reply_to_message.from_user.first_name} allaqachon premium maqomiga ega.")
        return

    user_data[user_id]['prem'] = True
    user_data[user_id]['prem_time'] = 30 * 24 * 60 * 60
    
    with open(user_data_file, 'w') as user_file:
        json.dump(user_data, user_file, indent=4)
    
    bot.reply_to(message, f"{message.reply_to_message.from_user.first_name} premium maqomiga ega bo'ldi.")
    
    # Thread yordamida prem_time ni kamaytirib borish
    def decrease_prem_time(user_id):
        while user_data[user_id]['prem_time'] > 0:
            time.sleep(1)
            user_data[user_id]['prem_time'] -= 1
            
            with open(user_data_file, 'w') as user_file:
                json.dump(user_data, user_file, indent=4)
        
        user_data[user_id]['prem'] = False
        
        with open(user_data_file, 'w') as user_file:
            json.dump(user_data, user_file, indent=4)
        
        # Foydalanuvchiga prem tugaganini bildirish
        try:
            bot.send_message(user_id, "Premium muddati tugadi. Qayta olish uchun @BlitzB_admin ga murojaat qiling.")
        except telebot.apihelper.ApiTelegramException as e:
            if e.error_code == 403:
                bot.send_message(admin, f"Foydalanuvchi {user_id} botni blok qilgan. Unga xabar yuborilmadi.")

    threading.Thread(target=decrease_prem_time, args=(user_id,)).start()


@bot.message_handler(commands=['ban'])
def ban_command(message):
    if message.from_user.id != admin:
        bot.reply_to(message, "Sizda ushbu komandani ishlatish huquqi yo'q.")
        return
    
    if message.chat.type != 'private':
        bot.reply_to(message, "Ushbu komanda faqat private chatlarda ishlaydi.")
        return
    
    bot.reply_to(message, "Botni bloklagan foydalanuvchilarni o'chirishni boshlaymiz.")

    with open(user_data_file, 'r') as user_file:
        user_data = json.load(user_file)
    
    blocked_users = []
    
    for user_id in list(user_data.keys()):
        try:
            bot.send_chat_action(user_id, 'typing')  # Foydalanuvchi botni bloklamaganligini tekshirish
        except telebot.apihelper.ApiTelegramException as e:
            if e.error_code == 403:
                blocked_users.append(user_id)
                user_link = f"https://t.me/{user_id}"
                user_name = user_data[user_id].get('username', 'No username')
                bot.send_message(admin, f"Foydalanuvchi @{user_name} bloklagan: {user_link}")
                del user_data[user_id]
    
    with open(user_data_file, 'w') as user_file:
        json.dump(user_data, user_file, indent=4)
    
    bot.send_message(admin, "Bloklagan foydalanuvchilar o'chirildi.")




is_ad_active = False

@bot.message_handler(commands=['ad'])
def ad_command(message):
    global is_ad_active
    if message.from_user.id != admin:
        bot.reply_to(message, "Sizda ushbu komandani ishlatish huquqi yo'q.")
        return
    
    if message.chat.type != 'private':
        bot.reply_to(message, "Ushbu komanda faqat private chatlarda ishlaydi.")
        return
    
    is_ad_active = True
    bot.reply_to(message, "Reklama matnini, videoni, rasmni yoki gifni yuboring.")

@bot.message_handler(content_types=['text', 'photo', 'video', 'animation'])
def handle_ad_content(message):
    global is_ad_active
    if message.from_user.id != admin:
        return
    
    if message.chat.type != 'private':
        return
    
    if not is_ad_active:
        return
    
    with open(user_data_file, 'r') as user_file:
        user_data = json.load(user_file)
    
    for user_id, user_info in user_data.items():
        try:
            if user_info.get('prem', False):
                bot.send_message(user_id, "Exx sz Premium user ekansz reklama kelgan edi-ya. 😁🎉")
                continue
            
            if message.content_type == 'text':
                bot.send_message(user_id, message.text)
            elif message.content_type == 'photo':
                bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption)
            elif message.content_type == 'video':
                bot.send_video(user_id, message.video.file_id, caption=message.caption)
            elif message.content_type == 'animation':
                bot.send_animation(user_id, message.animation.file_id, caption=message.caption)
        except telebot.apihelper.ApiTelegramException as e:
            if e.error_code == 403:
                bot.send_message(admin, f"Foydalanuvchi {user_id} botni blok qilgan. Unga xabar yuborilmadi.")
            else:
                bot.send_message(admin, f"Foydalanuvchi {user_id} ga reklama yuborishda xatolik yuz berdi: {e}")
    
    is_ad_active = False
    bot.send_message(admin, "Reklama barcha foydalanuvchilarga yuborildi.")










bot.polling()
