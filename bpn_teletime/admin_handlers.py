import csv
from datetime import datetime
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from config import ADMIN_IDS
from storage import get_all_users, update_work_time_entry
from reports import generate_excel_report_by_months

# Временное хранилище для выбора сотрудника при изменении времени
pending_time_update: dict[int, int] = {}

def register_admin_handlers(bot: TeleBot):
    @bot.message_handler(commands=['admin', 'menu'])
    def admin_menu(message):
        if message.from_user.id not in ADMIN_IDS:
            return bot.reply_to(message, "⛔ Только администраторам.")
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🕒 Изменить время сотрудника", callback_data="change_time"),
            InlineKeyboardButton("📊 Отправить отчёты всем", callback_data="send_all_reports"),
        )
        bot.send_message(message.chat.id, "🔧 Меню администратора:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data == 'change_time')
    def handle_change_time(call):
        if call.from_user.id not in ADMIN_IDS:
            return bot.answer_callback_query(call.id, "⛔ Только администраторам.")
        users = get_all_users()
        if not users:
            return bot.answer_callback_query(call.id, "👥 Нет одобренных пользователей.")
        markup = InlineKeyboardMarkup(row_width=1)
        for uid, uname in users.items():
            markup.add(InlineKeyboardButton(f"{uname} ({uid})", callback_data=f"time_user_{uid}"))
        bot.send_message(call.message.chat.id, "Выберите сотрудника:", reply_markup=markup)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('time_user_'))
    def handle_time_user_selection(call):
        if call.from_user.id not in ADMIN_IDS:
            return bot.answer_callback_query(call.id, "⛔ Только администраторам.")
        uid = int(call.data.split('_')[-1])
        pending_time_update[call.message.chat.id] = uid
        bot.send_message(
            call.message.chat.id,
            "В формате:\n"
            "`<действие> YYYY-MM-DD HH:MM:SS`\n\n"
            "Например:\n"
            "`Пришел на работу 2025-07-04 08:30:00`",
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data == 'send_all_reports')
    def handle_send_reports(call):
        if call.from_user.id not in ADMIN_IDS:
            return bot.answer_callback_query(call.id, "⛔ Только администраторам.")
        for uid, uname in get_all_users().items():
            buf = generate_excel_report_by_months(uid, uname)
            if buf:
                filename = f"Report_{uname}_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
                bot.send_document(call.message.chat.id, InputFile(buf, filename),
                                  caption=f"Отчёт {uname}")
        bot.answer_callback_query(call.id, "✅ Отчёты отправлены всем.")

    @bot.message_handler(func=lambda message: message.chat.id in pending_time_update)
    def process_time_change(message):
        chat_id = message.chat.id
        uid = pending_time_update.pop(chat_id)
        text = message.text.strip()
        try:
            # Разбираем действие, дату и время
            # rsplit на две части: до последних двух пробелов
            action, date_str, time_str = text.rsplit(' ', 2)
            # Проверяем корректность даты и времени
            datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
            # Пытаемся обновить запись
            success = update_work_time_entry(str(uid), date_str, action, time_str)
            if success:
                bot.reply_to(
                    message,
                    f"✅ Для пользователя `{uid}` обновлено:\n"
                    f"*{action}* → `{date_str} {time_str}`",
                    parse_mode='Markdown'
                )
            else:
                bot.reply_to(
                    message,
                    "❌ Запись не найдена или не удалось обновить. "
                    "Проверьте, что указали существующее действие и дату."
                )
        except ValueError:
            bot.reply_to(
                message,
                "❌ Неверный формат. Используйте:\n"
                "`<действие> YYYY-MM-DD HH:MM:SS`",
                parse_mode='Markdown'
            )
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка: {e}")



