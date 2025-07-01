import os
import csv
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from .config import ADMIN_IDS  # заменили с одного ID на список
from .storage import get_all_users
from .reports import generate_excel_report_by_months

def register_admin_handlers(bot: TeleBot):

    # Главное меню админа с выбором пользователей
    @bot.message_handler(commands=['admin_menu'])
    def admin_menu(message):
        if message.from_user.id not in ADMIN_IDS:
            return bot.reply_to(message, "⛔ У вас нет прав администратора.")

        markup = InlineKeyboardMarkup()
        users = get_all_users()
        for uid, username in users.items():
            markup.add(InlineKeyboardButton(f"{username} ({uid})", callback_data=f"edit_{uid}"))

        bot.send_message(message.chat.id, "👥 Выберите пользователя:", reply_markup=markup)

    # Генерация всех отчетов
    @bot.message_handler(commands=['all_reports'])
    def send_all_reports(message):
        if message.from_user.id not in ADMIN_IDS:
            return bot.reply_to(message, "⛔ У вас нет доступа.")

        users = get_all_users()
        for uid, username in users.items():
            path = generate_excel_report_by_months(uid, username)
            if path and os.path.exists(path):
                with open(path, 'rb') as f:
                    bot.send_document(message.chat.id, f, caption=f"📎 Отчет: {username}")
            else:
                bot.send_message(message.chat.id, f"❗ Нет данных для {username}")

    # Команда для отображения своего Telegram ID
    @bot.message_handler(commands=['whoami'])
    def whoami(message):
        bot.reply_to(message, f"🪪 Ваш user ID: `{message.from_user.id}`", parse_mode="Markdown")

