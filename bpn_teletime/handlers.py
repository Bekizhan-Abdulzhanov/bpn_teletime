import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from storage import save_work_time, update_user_status, is_user_approved, get_all_users
from reports import generate_excel_report
from config import ADMIN_ID

def register_handlers(bot):

    @bot.message_handler(commands=['start'])
    def start_work(message):
        user_id = message.from_user.id
        print(f"[DEBUG] Команда /start от user_id={user_id}")

        if not is_user_approved(user_id):
            print("[DEBUG] Пользователь не одобрен.")
            return bot.reply_to(message, "Заявка не одобрена.")

        save_work_time(user_id, message.from_user.username, "Пришел на работу")
        bot.reply_to(message, "Отметка о приходе сохранена.")
        print("[DEBUG] Отметка сохранена")

    @bot.message_handler(commands=['send_excel_report'])
    def send_excel_report(message):
        user_id = message.from_user.id
        print(f"[DEBUG] Команда /send_excel_report от user_id={user_id}")

        if not is_user_approved(user_id):
            print("[DEBUG] Пользователь не одобрен.")
            bot.reply_to(message, "Вы не зарегистрированы или ваша заявка не одобрена.")
            return

        report_path = generate_excel_report(user_id)

        if report_path:
            print(f"[DEBUG] Отчёт создан: {report_path}")
        else:
            print("[ERROR] generate_excel_report вернул None")

        if report_path and os.path.exists(report_path):
            with open(report_path, 'rb') as file:
                bot.send_document(message.chat.id, file, caption="Ваш отчёт о рабочем времени.")
                print("[DEBUG] Файл отправлен")
        else:
            bot.reply_to(message, "Отчёт не найден. Убедитесь, что у вас есть записанные отметки.")
            print("[ERROR] Файл не найден.")
