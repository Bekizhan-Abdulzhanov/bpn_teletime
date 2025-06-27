import os
import csv
from datetime import datetime
from io import BytesIO
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

TRUSTED_USERS = [ADMIN_ID]  # автоматически одобренные пользователи

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
        user_id = str(message.from_user.id)
        username = message.from_user.username or f"user_{user_id}"
        name = message.from_user.first_name

        # Автоматическое одобрение, если это админ или доверенный
        is_admin = int(user_id) == ADMIN_ID
        approved = 1 if is_admin or int(user_id) in TRUSTED_USERS else 0

        already_registered = False
        if os.path.exists('users.csv'):
            with open('users.csv', 'r', encoding='utf-8') as file:
                for line in file:
                    if line.startswith(user_id + ","):
                        already_registered = True
                        break

        if not already_registered:
            with open('users.csv', 'a', encoding='utf-8') as file:
                file.write(f"{user_id},{username},{approved}\n")

        if approved:
            bot.reply_to(message, "✅ Вы зарегистрированы и одобрены.")
            save_work_time(user_id, username, "Пришел на работу")
            show_menu(message)
        else:
            bot.reply_to(message, "📝 Ваша заявка отправлена. Ожидайте одобрения.")

            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{user_id}"),
                InlineKeyboardButton("🚫 Отклонить", callback_data=f"reject_{user_id}")
            )

            bot.send_message(
                ADMIN_ID,
                f"🔔 Новая заявка:\n👤 @{username} ({user_id})\nИмя: {name}",
                reply_markup=markup
            )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
    def approve_user(call):
        user_id = call.data.split("_")[1]
        updated = False
        rows = []

        with open('users.csv', 'r', encoding='utf-8') as file:
            for row in file:
                parts = row.strip().split(',')
                if parts[0] == user_id:
                    parts[2] = '1'
                    updated = True
                rows.append(','.join(parts))

        if updated:
            with open('users.csv', 'w', encoding='utf-8') as file:
                file.write('\n'.join(rows) + '\n')
            bot.edit_message_text(
                f"✅ Пользователь {user_id} одобрен.",
                call.message.chat.id,
                call.message.message_id
            )
            try:
                bot.send_message(user_id, "✅ Ваша заявка одобрена. Вы можете пользоваться ботом.")
            except:
                pass
        else:
            bot.answer_callback_query(call.id, "❌ Пользователь не найден.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
    def reject_user(call):
        user_id = call.data.split("_")[1]
        rows = []

        with open('users.csv', 'r', encoding='utf-8') as file:
            for row in file:
                if not row.startswith(user_id + ","):
                    rows.append(row.strip())

        with open('users.csv', 'w', encoding='utf-8') as file:
            file.write('\n'.join(rows) + '\n')

        bot.edit_message_text(
            f"🚫 Пользователь {user_id} отклонён и удалён из списка.",
            call.message.chat.id,
            call.message.message_id
        )

        try:
            bot.send_message(user_id, "🚫 Ваша заявка была отклонена.")
        except:
            pass

    @bot.message_handler(commands=['send_excel_report'])
    def send_excel_report(message):
        user_id = message.from_user.id
        if not is_user_approved(user_id):
            return bot.reply_to(message, "❌ Вы не зарегистрированы или ваша заявка не одобрена.")

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
