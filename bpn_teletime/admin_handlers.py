import os
import csv
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID
from storage import get_all_users
from reports import generate_excel_report_by_months
from telebot import TeleBot

def register_admin_handlers(bot: TeleBot):

    @bot.message_handler(commands=['admin_menu'])
    def admin_menu(message):
        if message.from_user.id != ADMIN_ID:
            return bot.reply_to(message, "\u26d4\ufe0f У вас нет прав администратора.")

        markup = InlineKeyboardMarkup()
        for user_id, username in get_all_users().items():
            markup.add(InlineKeyboardButton(f"{username} ({user_id})", callback_data=f"edit_{user_id}"))

        bot.send_message(message.chat.id, "\ud83d\udc64 Выберите пользователя для редактирования:", reply_markup=markup)

    @bot.message_handler(commands=['all_reports'])
    def send_all_reports(message):
        if message.from_user.id != ADMIN_ID:
            return bot.reply_to(message, "\u26d4\ufe0f У вас нет доступа к этому действию.")

        for user_id, username in get_all_users().items():
            path = generate_excel_report_by_months(user_id)
            if path and os.path.exists(path):
                with open(path, 'rb') as file:
                    bot.send_document(message.chat.id, file, caption=f"\ud83d\udcce Отчет пользователя {username}")
            else:
                bot.send_message(message.chat.id, f"\u274c Отчет для пользователя {username} не найден.")

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

        bot.edit_message_text("\ud83d\udcc5 Выберите дату:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("date_"))
    def select_date(call):
        _, user_id, date = call.data.split("_")
        actions = ["Пришел на работу", "Вышел на обед", "Вернулся с обеда", "Ушел с работы"]

        markup = InlineKeyboardMarkup()
        for action in actions:
            markup.add(InlineKeyboardButton(action, callback_data=f"change_{user_id}_{date}_{action}"))

        bot.edit_message_text(f"\u270f\ufe0f Выберите действие для редактирования ({date}):", call.message.chat.id, call.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("change_"))
    def change_time_prompt(call):
        _, user_id, date, action = call.data.split("_", 3)
        msg = bot.send_message(call.message.chat.id, f"Введите новое время для **{action}** ({date}) в формате ЧЧ:ММ:")
        bot.register_next_step_handler(msg, lambda m: change_time(m, user_id, date, action))

    def change_time(message, user_id, date, action):
        new_time = message.text.strip()
        if len(new_time) != 5 or ':' not in new_time:
            return bot.send_message(message.chat.id, "\u26a0\ufe0f Неверный формат. Введите в формате ЧЧ:ММ")

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
            bot.send_message(message.chat.id, f"\u2705 Время для '{action}' обновлено на {new_time}")
        else:
            bot.send_message(message.chat.id, "\u274c Не удалось найти запись для обновления.")
