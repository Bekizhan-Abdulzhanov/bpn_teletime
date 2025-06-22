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

            from telebot.types import ReplyKeyboardMarkup, KeyboardButton

    @bot.message_handler(commands=['1'])
    def show_menu(message):
        if not is_user_approved(message.from_user.id):
            return bot.reply_to(message, "Вы не зарегистрированы или ваша заявка не одобрена.")

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            KeyboardButton("🍽 Вышел на обед"),
            KeyboardButton("🍽 Вернулся с обеда"),
            KeyboardButton("🏁 Ушел с работы")
        )
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

    @bot.message_handler(func=lambda message: message.text in [
        "🍽 Вышел на обед", "🍽 Вернулся с обеда", "🏁 Ушел с работы"
    ])
    def handle_work_time(message):
        if not is_user_approved(message.from_user.id):
            return bot.reply_to(message, "Вы не зарегистрированы или ваша заявка не одобрена.")

        user = message.from_user
        action_text = {
            "🍽 Вышел на обед": "Вышел на обед",
            "🍽 Вернулся с обеда": "Вернулся с обеда",
            "🏁 Ушел с работы": "Ушел с работы"
        }.get(message.text)

        save_work_time(user.id, user.username, action_text)
        bot.reply_to(message, f"✅ Вы отметили: {message.text}")
        print(f"[DEBUG] {user.username} - {action_text}")