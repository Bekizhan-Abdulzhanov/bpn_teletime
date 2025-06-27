import os
import csv
from datetime import datetime
from telebot.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, InputFile
)
from config import ADMIN_PASSWORD
from storage import save_work_time, is_user_approved, get_all_users
from reports import generate_excel_report_by_months

ADMINS_FILE = 'admins.csv'

# --- Admin utils ---
def is_admin(user_id):
    if not os.path.exists(ADMINS_FILE):
        return False
    with open(ADMINS_FILE, 'r', encoding='utf-8') as file:
        return str(user_id) in [line.strip() for line in file]

def add_admin(user_id):
    with open(ADMINS_FILE, 'a', encoding='utf-8') as file:
        file.write(f"{user_id}\n")

# --- Handlers ---
def register_handlers(bot):

    def show_menu(message):
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            KeyboardButton("🍽 Вышел на обед"),
            KeyboardButton("🍽 Вернулся с обеда"),
            KeyboardButton("🏑 Ушел с работы")
        )
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

    @bot.message_handler(commands=['start'])
    def start_work(message):
        user_id = message.from_user.id
        username = message.from_user.username or f"user_{user_id}"
        if not is_user_approved(user_id):
            return bot.reply_to(message, "❌ Заявка не одобрена. Зарегистрируйтесь через /register.")
        save_work_time(user_id, username, "Пришел на работу")
        bot.reply_to(message, f"👋 Добро пожаловать, {message.from_user.first_name}!")
        show_menu(message)

    @bot.message_handler(commands=['register'])
    def register_user(message):
        user_id = message.from_user.id
        username = message.from_user.username or f"user_{user_id}"
        if is_user_approved(user_id):
            return bot.reply_to(message, "✅ Вы уже зарегистрированы.")
        with open('users.csv', 'a', encoding='utf-8') as file:
            file.write(f"{user_id},{username},1\n")
        bot.reply_to(message, "✅ Вы успешно зарегистрированы!")

    @bot.message_handler(commands=['admin'])
    def ask_admin_password(message):
        msg = bot.reply_to(message, "🔐 Введите пароль админа:")
        bot.register_next_step_handler(msg, check_admin_password)

    def check_admin_password(message):
        user_id = message.from_user.id
        if message.text.strip() == ADMIN_PASSWORD:
            add_admin(user_id)
            bot.reply_to(message, "✅ Теперь вы администратор!")
        else:
            bot.reply_to(message, "❌ Неверный пароль.")

    @bot.message_handler(commands=['admin_menu'])
    def admin_menu(message):
        if not is_admin(message.from_user.id):
            return bot.reply_to(message, "⛔ У вас нет прав админа.")
        markup = InlineKeyboardMarkup()
        for user_id, username in get_all_users().items():
            markup.add(InlineKeyboardButton(f"{username} ({user_id})", callback_data=f"edit_{user_id}"))
        bot.send_message(message.chat.id, "👤 Выберите юзера:", reply_markup=markup)

    @bot.message_handler(func=lambda m: m.text in [
        "🍽 Вышел на обед",
        "🍽 Вернулся с обеда",
        "🏑 Ушел с работы"])
    def handle_work_time(message):
        if not is_user_approved(message.from_user.id):
            return bot.reply_to(message, "❌ Вы не одобрены.")
        actions = {
            "🍽 Вышел на обед": "Вышел на обед",
            "🍽 Вернулся с обеда": "Вернулся с обеда",
            "🏑 Ушел с работы": "Ушел с работы"
        }
        action = actions[message.text]
        save_work_time(message.from_user.id, message.from_user.username, action)
        bot.reply_to(message, f"✅ Отмечено: {action}")

    @bot.message_handler(commands=['send_excel_report'])
    def send_excel_report(message):
        user_id = message.from_user.id
        if not is_user_approved(user_id):
            return bot.reply_to(message, "❌ Вы не одобрены.")
        username = message.from_user.username or f"user_{user_id}"
        file_data = generate_excel_report_by_months(user_id, username)
        if file_data:
            filename = f"Report_{username}_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
            bot.send_document(message.chat.id, InputFile(file_data, filename), caption="📄 Ваш отчет")
        else:
            bot.reply_to(message, "⚠️ Отчет не найден.")

    @bot.message_handler(commands=['1'])
    def manual_menu(message):
        if not is_user_approved(message.from_user.id):
            return bot.reply_to(message, "❌ Вы не зарегистрированы или ваша заявка не одобрена.")
        show_menu(message)

    @bot.message_handler(func=lambda message: message.text in [
        "🍽 Вышел на обед", "🍽 Вернулся с обеда", "🏁 Ушел с работы"])
    def handle_work_time(message):
        if not is_user_approved(message.from_user.id):
            return bot.reply_to(message, "❌ Вы не зарегистрированы или ваша заявка не одобрена.")
        user = message.from_user
        action_text = {
            "🍽 Вышел на обед": "Вышел на обед",
            "🍽 Вернулся с обеда": "Вернулся с обеда",
            "🏁 Ушел с работы": "Ушел с работы"
        }.get(message.text)
        save_work_time(user.id, user.username, action_text)
        bot.reply_to(message, f"✅ Вы отметили: {message.text}")

    @bot.message_handler(commands=['all_reports'])
    def send_all_reports(message):
        if message.from_user.id != ADMIN_ID:
            return bot.reply_to(message, "⛔ У вас нет доступа к этому действию.")
        for user_id, username in get_all_users().items():
            file_data = generate_excel_report_by_months(user_id, username)
            if file_data:
                filename = f"Report_{username}_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
                bot.send_document(message.chat.id, InputFile(file_data, filename), caption=f"📎 Отчет пользователя {username}")
            else:
                bot.send_message(message.chat.id, f"❌ Отчет для пользователя {username} не найден.")
