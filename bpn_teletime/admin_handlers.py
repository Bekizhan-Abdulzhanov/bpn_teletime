import os
import csv
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID
from storage import get_all_users
from reports import generate_excel_report_by_months

def register_admin_handlers(bot: TeleBot):

    @bot.message_handler(commands=['admin_menu'])
    def admin_menu(message):
        if message.from_user.id != ADMIN_ID:
            return bot.reply_to(message, "⛔ У вас нет прав администратора.")
        markup = InlineKeyboardMarkup()
        for uid, username in get_all_users().items():
            markup.add(InlineKeyboardButton(f"{username} ({uid})", callback_data=f"edit_{uid}"))
        bot.send_message(message.chat.id, "👥 Выберите пользователя:", reply_markup=markup)

    @bot.message_handler(commands=['all_reports'])
    def send_all_reports(message):
        if message.from_user.id != ADMIN_ID:
            return bot.reply_to(message, "⛔ У вас нет доступа.")
        for uid, username in get_all_users().items():
            path = generate_excel_report_by_months(uid, username)
            if path and os.path.exists(path):
                with open(path, 'rb') as f:
                    bot.send_document(message.chat.id, f, caption=f"📎 Отчет: {username}")
            else:
                bot.send_message(message.chat.id, f"❗ Нет данных для {username}")

    # Реализацию edit/select_date/change_time оставьте, если нужна.
