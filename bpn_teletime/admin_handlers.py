import csv
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from config import ADMIN_IDS
from storage import get_all_users, save_work_time
from reports import generate_excel_report_by_months


def register_admin_handlers(bot):
    @bot.message_handler(commands=['admin'])
    def admin_menu(message):
        if message.from_user.id not in ADMIN_IDS:
            return bot.reply_to(message, "⛔ Только для админов.")
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("🕒 Изменить время сотрудника", callback_data="change_time"),
            InlineKeyboardButton("📊 Отправить отчёты всем", callback_data="send_all_reports"),
        )
        bot.send_message(message.chat.id, "🔧 Меню администратора:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data in ['change_time', 'send_all_reports'])
    def handle_admin_actions(call):
        if call.from_user.id not in ADMIN_IDS:
            return bot.answer_callback_query(call.id, "⛔ Только для админов.")
        if call.data == 'change_time':
            bot.send_message(call.message.chat.id,
                "Введите через пробел: user_id действие YYYY-MM-DD HH:MM:SS\n"
                "Например: 12345 Пришел на работу 2025-07-03 08:30:00"
            )
        else:
            for uid, uname in get_all_users().items():
                buf = generate_excel_report_by_months(uid, uname)
                if buf:
                    filename = f"Report_{uname}_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
                    bot.send_document(call.message.chat.id, InputFile(buf, filename), caption=f"📎 Отчёт {uname}")
            bot.answer_callback_query(call.id, "✅ Отчёты отправлены всем.")

    @bot.message_handler(func=lambda m: m.from_user.id in ADMIN_IDS and len(m.text.split()) >= 3)
    def process_time_change(message):
        parts = message.text.split(' ', 2)
        try:
            user_id = int(parts[0])
            action = parts[1]
            ts = parts[2]
            save_work_time(user_id, action, ts)
            bot.reply_to(message, f"✅ Отметка добавлена: {action} для {user_id} в {ts}")
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка парсинга текста. Убедитесь в формате. ({e})")




