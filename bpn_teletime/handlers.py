from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from storage import save_work_time, update_user_status, is_user_approved, get_all_users
from reports import generate_excel_report
from config import ADMIN_ID

def register_handlers(bot):

    @bot.message_handler(commands=['start'])
    def start_work(message):
        if not is_user_approved(message.from_user.id):
            return bot.reply_to(message, "Заявка не одобрена.")
        save_work_time(message.from_user.id, message.from_user.username, "Пришел на работу")
        bot.reply_to(message, "Отметка о приходе сохранена.")

    @bot.message_handler(commands=['send_excel_report'])
    def send_report(message):
        path = generate_excel_report(message.from_user.id)
        if path:
            with open(path, 'rb') as file:
                bot.send_document(message.chat.id, file)
        else:
            bot.reply_to(message, "Отчёт не найден.")
