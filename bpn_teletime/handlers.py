import os
import csv
from datetime import datetime
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InputFile,
)
from config import ADMIN_IDS
from storage import (
    save_work_time,
    is_user_approved,
    get_all_users,
    approve_user_by_id,
    reject_user_by_id,
    get_pending_users,
    enable_auto_mode,
    disable_auto_mode,
    is_auto_enabled
)
from reports import generate_excel_report_by_months
from .config import WORKTIME_FILE


AUTO_APPROVED_USERS = {
    378268765: "ErlanNasiev",
    557174721: "BekizhanAbdulzhanov",
}

ALLOWED_AUTO_USERS = AUTO_APPROVED_USERS

def is_admin(user_id):
    return user_id in ADMIN_IDS

def show_menu(bot, message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton("🍽 Вышел на обед"),
        KeyboardButton("🍽 Вернулся с обеда"),
        KeyboardButton("🏁 Ушел с работы"),
    )
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

def register_handlers(bot):
    @bot.message_handler(commands=["start"])
    def start_command(message):
        user_id = message.from_user.id
        username = message.from_user.username or f"user_{user_id}"

        if is_user_approved(user_id) or user_id in AUTO_APPROVED_USERS:
            save_work_time(user_id, username, "Пришел на работу")
            bot.send_message(message.chat.id, "👋 Добро пожаловать! Отметка прихода сохранена.")
            show_menu(bot, message)
        else:
            bot.send_message(message.chat.id, "❌ Вы не одобрены. Сначала зарегистрируйтесь через /register.")

    @bot.message_handler(commands=["register"])
    def register_user(message):
        user_id = message.from_user.id
        username = message.from_user.username or f"user_{user_id}"

        if user_id in AUTO_APPROVED_USERS:
            return bot.send_message(message.chat.id, "✅ Вы уже авторизованы как привилегированный пользователь.")

        if os.path.exists("users.csv"):
            with open("users.csv", "r", encoding="utf-8") as f:
                for row in csv.reader(f):
                    if row and row[0] == str(user_id):
                        return bot.send_message(message.chat.id, "✅ Вы уже зарегистрированы или ожидаете одобрения.")

        with open("users.csv", "a", encoding="utf-8") as f:
            f.write(f"{user_id},{username},0\n")

        bot.send_message(message.chat.id, "📅 Заявка отправлена. Ожидайте одобрения администратора.")

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{user_id}")
        )
        for admin_id in ADMIN_IDS:
            try:
                bot.send_message(admin_id, f"📩 Новый пользователь: @{username} (ID: {user_id})", reply_markup=markup)
            except Exception as e:
                print(f"[WARN] Не удалось отправить сообщение админу {admin_id}: {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
    def handle_approve_user(call):
        if not is_admin(call.from_user.id):
            return bot.answer_callback_query(call.id, "⛔ Только для админов.")

        user_id = int(call.data.replace("approve_", ""))
        approve_user_by_id(user_id)
        bot.send_message(call.message.chat.id, f"✅ Пользователь {user_id} одобрен.")
        try:
            bot.send_message(user_id, "✅ Ваша заявка одобрена! Вы можете пользоваться ботом.")
        except Exception as e:
            print(f"[WARN] Не удалось отправить сообщение пользователю {user_id}: {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
    def handle_reject_user(call):
        if not is_admin(call.from_user.id):
            return bot.answer_callback_query(call.id, "⛔ Только для админов.")

        user_id = int(call.data.replace("reject_", ""))
        reject_user_by_id(user_id)
        bot.send_message(call.message.chat.id, f"🚫 Пользователь {user_id} был отклонён.")
        try:
            bot.send_message(user_id, "🚫 Ваша заявка на регистрацию была отклонена.")
        except Exception as e:
            print(f"[WARN] Не удалось отправить сообщение пользователю {user_id}: {e}")

    @bot.message_handler(commands=["send_excel_report"])
    def send_excel_report(message):
        user_id = message.from_user.id
        if not is_user_approved(user_id) and user_id not in AUTO_APPROVED_USERS:
            return bot.reply_to(message, "❌ Вы не одобрены.")

        username = message.from_user.username or f"user_{user_id}"
        file_data = generate_excel_report_by_months(user_id, username, today_only=True)

        if file_data:
            filename = f"Report_{username}_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
            bot.send_document(message.chat.id, InputFile(file_data, filename), caption="📄 Ваш отчёт о рабочем времени.")
        else:
            bot.reply_to(message, "⚠️ Отчёт не найден.")

    @bot.message_handler(func=lambda msg: msg.text in ["🍽 Вышел на обед", "🍽 Вернулся с обеда", "🏁 Ушел с работы"])
    def handle_actions(message):
        user_id = message.from_user.id
        if not is_user_approved(user_id) and user_id not in AUTO_APPROVED_USERS:
            return bot.reply_to(message, "❌ Вы не одобрены.")

        user = message.from_user
        action = {
            "🍽 Вышел на обед": "Вышел на обед",
            "🍽 Вернулся с обеда": "Вернулся с обеда",
            "🏁 Ушел с работы": "Ушел с работы",
        }[message.text]

        save_work_time(user.id, user.username, action)
        bot.reply_to(message, f"✅ Отмечено: {action}")

    @bot.message_handler(commands=["all_reports"])
    def all_reports(message):
        if not is_admin(message.from_user.id):
            return bot.reply_to(message, "⛔ Только для администраторов.")

        for user_id, username in get_all_users().items():
            file_data = generate_excel_report_by_months(user_id, username)
            if file_data:
                filename = f"Report_{username}_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
                bot.send_document(message.chat.id, InputFile(file_data, filename), caption=f"📎 Отчет {username}")
            else:
                bot.send_message(message.chat.id, f"⚠️ Нет отчета для {username}.")

    @bot.message_handler(commands=["whoami"])
    def whoami(message):
        bot.reply_to(message, f"🪪 Ваш user ID: `{message.from_user.id}`", parse_mode="Markdown")

    @bot.message_handler(commands=["pending"])
    def show_pending_users(message):
        if not is_admin(message.from_user.id):
            return bot.reply_to(message, "⛔ Только для администраторов.")

        pending = get_pending_users()
        if not pending:
            return bot.send_message(message.chat.id, "📭 Нет заявок на одобрение.")

        for user_id, username in pending:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{user_id}"))
            bot.send_message(message.chat.id, f"👤 @{username} (ID: {user_id})", reply_markup=markup)

    @bot.message_handler(commands=["авторежим_вкл"])
    def auto_mode_on(message):
        user_id = message.from_user.id
        if user_id not in ALLOWED_AUTO_USERS:
            return bot.send_message(message.chat.id, "⛔ У вас нет доступа к авто-режиму.")
        enable_auto_mode(user_id)
        bot.send_message(message.chat.id, "✅ Автоматический режим включён. Бот будет отмечать вас сам.")

    @bot.message_handler(commands=["авторежим_выкл"])
    def auto_mode_off(message):
        user_id = message.from_user.id
        if user_id not in ALLOWED_AUTO_USERS:
            return bot.send_message(message.chat.id, "⛔ У вас нет доступа к авто-режиму.")
        disable_auto_mode(user_id)
        bot.send_message(message.chat.id, "🛑 Автоматический режим выключен.")

