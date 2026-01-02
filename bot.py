import telebot
from telebot import types
import json
import os

# Твои данные
TOKEN = '8265143216:AAE6Q-X7qkGiiMwWcrmTS92jM3WADalBRHg'
ADMIN_ID = 6140351301

bot = telebot.TeleBot(TOKEN)

# Файлы базы данных
DB_USERS = "users.txt"
DATA_FILE = "texts.json"

# Инициализация текстов (добавлены новые ключи для рангов)
default_texts = {
    "ruk": "Текст еще не добавлен",
    "rules": "Текст еще не добавлен",
    "vch": "Текст еще не добавлен",
    "biz": "Текст еще не добавлен",
    "rank9": "Норматив для Положенца (9) еще не добавлен",
    "rank8": "Норматив для Смотрящего (8) еще не добавлен",
    "rank7": "Норматив для Братка (7) еще не добавлен"
}

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        button_texts = json.load(f)
else:
    button_texts = default_texts

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(button_texts, f, ensure_ascii=False, indent=4)

def add_user(user_id):
    if not os.path.exists(DB_USERS):
        with open(DB_USERS, "w") as f: pass
    with open(DB_USERS, "r") as f:
        users = f.read().splitlines()
    if str(user_id) not in users:
        with open(DB_USERS, "a") as f:
            f.write(str(user_id) + "\n")

# --- КЛАВИАТУРЫ ---

def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("Руководство ОПГ", callback_data="ruk"),
        types.InlineKeyboardButton("Основные правила", callback_data="rules"),
        types.InlineKeyboardButton("Правила нападений на В/Ч", callback_data="vch"),
        types.InlineKeyboardButton("Правила проведения BizWar", callback_data="biz"),
        types.InlineKeyboardButton("📋 Нормативы", callback_data="norm_menu")
    )
    return markup

def norm_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("Положенец (9)", callback_data="rank9"),
        types.InlineKeyboardButton("Смотрящий (8)", callback_data="rank8"),
        types.InlineKeyboardButton("Браток (7)", callback_data="rank7"),
        types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")
    )
    return markup

# --- КОМАНДЫ ---

@bot.message_handler(commands=['start'])
def start(message):
    add_user(message.chat.id)
    bot.send_message(message.chat.id, "Привет! Выбери нужный раздел:", reply_markup=main_menu())

@bot.message_handler(commands=['add'])
def add_command(message):
    if message.from_user.id != ADMIN_ID: return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("✏️ Ред: Руководство", callback_data="edit_ruk"),
        types.InlineKeyboardButton("✏️ Ред: Правила", callback_data="edit_rules"),
        types.InlineKeyboardButton("✏️ Ред: В/Ч", callback_data="edit_vch"),
        types.InlineKeyboardButton("✏️ Ред: BizWar", callback_data="edit_biz"),
        types.InlineKeyboardButton("✏️ Ред: Положенец (9)", callback_data="edit_rank9"),
        types.InlineKeyboardButton("✏️ Ред: Смотрящий (8)", callback_data="edit_rank8"),
        types.InlineKeyboardButton("✏️ Ред: Браток (7)", callback_data="edit_rank7")
    )
    bot.send_message(message.chat.id, "Какой раздел хочешь изменить?", reply_markup=markup)

@bot.message_handler(commands=['o'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    text_to_send = message.text.replace('/o', '').strip()
    if not text_to_send:
        bot.reply_to(message, "Использование: /o [текст]")
        return
    full_message = f"❗️ *Новое уведомление от Разработчика*\n\n{text_to_send}"
    if os.path.exists(DB_USERS):
        with open(DB_USERS, "r") as f:
            users = f.read().splitlines()
        for user in users:
            try: bot.send_message(user, full_message, parse_mode="Markdown")
            except: continue
        bot.send_message(message.chat.id, "✅ Рассылка завершена.")

# --- ОБРАБОТЧИК КНОПОК ---

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    # Переход в меню нормативов
    if call.data == "norm_menu":
        bot.edit_message_text("Выберите ранг для просмотра нормативов:", 
                              call.message.chat.id, call.message.message_id, 
                              reply_markup=norm_menu())
    
    # Возврат в главное меню
    elif call.data == "back_to_main":
        bot.edit_message_text("Привет! Выбери нужный раздел:", 
                              call.message.chat.id, call.message.message_id, 
                              reply_markup=main_menu())

    # Редактирование (для админа)
    elif call.data.startswith('edit_'):
        key = call.data.replace('edit_', '')
        msg = bot.send_message(call.message.chat.id, f"Отправь новый текст для раздела `{key}`:")
        bot.register_next_step_handler(msg, save_new_text, key)
        bot.answer_callback_query(call.id)

    # Просмотр текста раздела
    elif call.data in button_texts:
        # Определяем, какую клавиатуру вернуть (основную или нормативов)
        back_markup = norm_menu() if "rank" in call.data else main_menu()
        try:
            bot.edit_message_text(button_texts[call.data], 
                                  call.message.chat.id, call.message.message_id, 
                                  reply_markup=back_markup, parse_mode="Markdown")
        except:
            bot.edit_message_text(button_texts[call.data], 
                                  call.message.chat.id, call.message.message_id, 
                                  reply_markup=back_markup)
        bot.answer_callback_query(call.id)

def save_new_text(message, key):
    button_texts[key] = message.text
    save_data()
    bot.send_message(message.chat.id, "✅ Сохранено!")

print("Бот запущен...")
bot.polling(none_stop=True)

