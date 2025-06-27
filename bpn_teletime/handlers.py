import os
import csv
from datetime import datetime
from io import BytesIO
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InputFile,
)
from storage import save_work_time, is_user_approved, get_all_users, approve_user_by_id
from reports import generate_excel_report_by_months

# Пароль администратора
ADMIN_PASSWORD = "BPN123"

# Файл с ID админов
ADMINS_FILE = "admins.csv"

def is_admin(user_id):
    if not os.path.exists(ADMINS_FILE):
        return False
    with open(ADMINS_FILE, 'r') as f:
        return str(user_id) in f.read().splitlines()

def add_admin(user_id):
    with open(ADMINS_FILE, 'a') as f:
        f.write(f"{user_id}\n")

def register_handlers(bot):

    def show_menu(message):
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            KeyboardButton("🍽 Вышел на обед"),
            KeyboardButton("🍽 Вернулся с обеда"),
            KeyboardButton("🏁 Ушел с работы")
        )
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

    @bot.message_handler(commands=['start'])
    def start_command(message):
        user_id = message.from_user.id
        username = message.from_user.username or f"user_{user_id}"

        if is_user_approved(user_id):
            bot.reply_to(message, "✅ Вы уже зарегистрированы.")
            show_menu(message)
        else:
            with open('users.csv', 'a', encoding='utf-8') as f:
                f.write(f"{user_id},{username},0\n")
            bot.send_message(message.chat.id, "📝 Ваша заявка отправлена. Ожидайте одобрения администратора.")

    @bot.message_handler(commands=['admin'])
    def admin_login(message):
        msg = bot.send_message(message.chat.id, "🔑 Введите пароль администратора:")
        bot.register_next_step_handler(msg, check_admin_password)

    def check_admin_password(message):
        if message.text.strip() == ADMIN_PASSWORD:
            add_admin(message.from_user.id)
            approve_user_by_id(message.from_user.id)
            bot.reply_to(message, "✅ Вы стали администратором и одобрены.")
        else:
            bot.reply_to(message, "❌ Неверный пароль.")

    @bot.message_handler(commands=['send_excel_report'])
    def send_excel_report(message):
        user_id = message.from_user.id
        if not is_user_approved(user_id):
            return bot.reply_to(message, "❌ Вы не одобрены.")

        username = message.from_user.username or f"user_{user_id}"
        file_data = generate_excel_report_by_months(user_id, username)

        if file_data:
            filename = f"Report_{username}_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
            bot.send_document(
                message.chat.id,
                InputFile(file_data, filename),
                caption="📄 Ваш отчёт о рабочем времени."
            )
        else:
            bot.reply_to(message, "⚠️ Отчёт не найден.")

    @bot.message_handler(func=lambda msg: msg.text in [
        "🍽 Вышел на обед", "🍽 Вернулся с обеда", "🏁 Ушел с работы"])
    def work_actions(message):
        if not is_user_approved(message.from_user.id):
            return bot.reply_to(message, "❌ Вы не одобрены.")

        user = message.from_user
        action = {
            "🍽 Вышел на обед": "Вышел на обед",
            "🍽 Вернулся с обеда": "Вернулся с обеда",
            "🏁 Ушел с работы": "Ушел с работы"
        }[message.text]

        save_work_time(user.id, user.username, action)
        bot.reply_to(message, f"✅ Отмечено: {action}")

    @bot.message_handler(commands=['all_reports'])
    def all_reports(message):
        if not is_admin(message.from_user.id):
            return bot.reply_to(message, "⛔ Только для администраторов.")

        for user_id, username in get_all_users().items():
            file_data = generate_excel_report_by_months(user_id, username)
            if file_data:
                filename = f"Report_{username}_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
                bot.send_document(message.chat.id, InputFile(file_data, filename), caption=f"📎 Отчет {username}")
            else:
                bot.send_message(message.chat.id, f"⚠️ Нет отчета для {username}.")
