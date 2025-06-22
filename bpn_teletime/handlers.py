from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from storage import save_work_time, update_user_status, is_user_approved, get_all_users
from reports import generate_excel_report
from config import ADMIN_ID

import os

from storage import is_user_approved

def register_handlers(bot):
    @bot.message_handler(commands=['start'])
    def start(message):
        print("[DEBUG] /start received from", message.from_user.id)
        if not is_user_approved(message.from_user.id):
            return bot.reply_to(message, "Заявка не одобрена.")
        bot.reply_to(message, "Доброе утро! Хорошей вам рабочего дня.")

    @bot.message_handler(commands=['send_excel_report'])
    def send_excel_report(message):
        user_id = message.from_user.id

        if not is_user_approved(user_id):
            bot.reply_to(message, "Вы не зарегистрированы или ваша заявка не одобрена.")
            return

        report_path = generate_excel_report(user_id)

        if report_path and os.path.exists(report_path):
            with open(report_path, 'rb') as file:
                bot.send_document(message.chat.id, file, caption="Ваш отчёт о рабочем времени.")
        else:
            bot.reply_to(message, "Отчёт не найден. Убедитесь, что у вас есть записанные отметки.")