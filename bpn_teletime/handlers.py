import os
import csv
from io import BytesIO
from datetime import datetime
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InputFile,
)
from storage import save_work_time, is_user_approved, get_all_users
from reports import generate_excel_report_by_months
from config import ADMIN_ID


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
    def start_work(message):
        user_id = message.from_user.id
        if not is_user_approved(user_id):
            bot.reply_to(message, "❌ Заявка не одобрена.")
            return
        save_work_time(user_id, message.from_user.username, "Пришел на работу")
        bot.reply_to(message, f"👋 Добро пожаловать, {message.from_user.first_name}!\n📌 Отметка о начале рабочего дня сохранена.")
        show_menu(message)

    @bot.message_handler(commands=['send_excel_report'])
    def send_excel_report(message):
        user_id = message.from_user.id
        if not is_user_approved(user_id):
            bot.reply_to(message, "❌ Вы не зарегистрированы или ваша заявка не одобрена.")
            return

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
            bot.reply_to(message, "⚠️ Отчёт не найден или не удалось сформировать.")

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

    @bot.message_handler(commands=['admin_menu'])
    def admin_menu(message):
        if message.from_user.id != ADMIN_ID:
            return bot.reply_to(message, "⛔ У вас нет прав администратора.")
        markup = InlineKeyboardMarkup()
        for user_id, username in get_all_users().items():
            markup.add(InlineKeyboardButton(f"{username} ({user_id})", callback_data=f"edit_{user_id}"))
        bot.send_message(message.chat.id, "👤 Выберите пользователя для редактирования:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_"))
    def select_user(call):
        user_id = call.data.split("_")[1]
        dates = set()
        with open('work_time.csv', 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader, None)
            for row in reader:
                if row[0] == user_id:
                    date = row[3].split()[0]
                    dates.add(date)
        markup = InlineKeyboardMarkup()
        for date in sorted(dates):
            markup.add(InlineKeyboardButton(date, callback_data=f"date_{user_id}_{date}"))
        bot.edit_message_text("📅 Выберите дату:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("date_"))
    def select_date(call):
        _, user_id, date = call.data.split("_")
        actions = ["Пришел на работу", "Вышел на обед", "Вернулся с обеда", "Ушел с работы"]
        markup = InlineKeyboardMarkup()
        for action in actions:
            markup.add(InlineKeyboardButton(action, callback_data=f"change_{user_id}_{date}_{action}"))
        bot.edit_message_text(f"✏️ Выберите действие для редактирования ({date}):", call.message.chat.id, call.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("change_"))
    def change_time_prompt(call):
        _, user_id, date, action = call.data.split("_", 3)
        msg = bot.send_message(call.message.chat.id, f"Введите новое время для **{action}** ({date}) в формате ЧЧ:ММ:")
        bot.register_next_step_handler(msg, lambda m: change_time(m, user_id, date, action))

    def change_time(message, user_id, date, action):
        new_time = message.text.strip()
        if len(new_time) != 5 or ':' not in new_time:
            return bot.send_message(message.chat.id, "⚠️ Неверный формат. Введите в формате ЧЧ:ММ")
        updated = False
        rows = []
        with open('work_time.csv', 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            header = next(reader)
            for row in reader:
                if row[0] == user_id and row[2] == action and row[3].startswith(date):
                    row[3] = f"{date} {new_time}:00"
                    updated = True
                rows.append(row)
        if updated:
            with open('work_time.csv', 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(header)
                writer.writerows(rows)
            bot.send_message(message.chat.id, f"✅ Время для '{action}' обновлено на {new_time}")
        else:
            bot.send_message(message.chat.id, "❌ Не удалось найти запись для обновления.")

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

