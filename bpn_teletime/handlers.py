import os
import csv
from datetime import datetime
from zoneinfo import ZoneInfo
from telebot import TeleBot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InputFile,
)

from config import (
    ADMIN_IDS,
    TIMEZONE,
    AUTO_APPROVED_USERS,
    EMPLOYEE_USERS,
    ALLOWED_AUTO_USERS,
)
from storage import (
    USERS_FILE,
    save_work_time,
    is_user_approved,
    get_all_users,
    set_user_status,
    deny_user         as reject_user_by_id,
    get_pending_users,
    enable_auto_mode,
    disable_auto_mode,
)
from reports import generate_excel_report_by_months

TS_ZONE = ZoneInfo(TIMEZONE)

TRUSTED_USERS: dict[int, str] = ALLOWED_AUTO_USERS.copy()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def _deny_admin(bot: TeleBot, message, why: str = ""):
    uid = message.from_user.id if hasattr(message, "from_user") else None
    print(f"[ADMIN_DENY] uid={uid} not in ADMIN_IDS={ADMIN_IDS}. {why}")
    return bot.reply_to(message, "⛔ Только для администраторов.")


def show_menu(bot: TeleBot, message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton("🍽 Вышел на обед"),
        KeyboardButton("🍽 Вернулся с обеда"),
        KeyboardButton("🏁 Ушел с работы"),
    )
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)


def register_handlers(bot: TeleBot):
    @bot.message_handler(commands=["start"])
    def start_command(message):
        user_id = message.from_user.id
        username = message.from_user.username or f"user_{user_id}"

        if is_user_approved(user_id) or user_id in TRUSTED_USERS:
            ts = datetime.now(TS_ZONE).strftime("%Y-%m-%d %H:%M:%S")
            save_work_time(user_id, "Пришел на работу", ts)
            bot.send_message(message.chat.id, "👋 Добро пожаловать! Отметка прихода сохранена.")
            show_menu(bot, message)
        else:
            bot.send_message(message.chat.id, "❌ Вы не одобрены. Сначала зарегистрируйтесь через /register.")

    @bot.message_handler(commands=["register"])
    def register_user(message):
        user_id = message.from_user.id
        username = message.from_user.username or f"user_{user_id}"

        if user_id in TRUSTED_USERS:
            return bot.send_message(message.chat.id, "✅ Вы уже авторизованы как доверенный пользователь.")

        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                for row in csv.reader(f):
                    if row and row[0] == str(user_id):
                        return bot.send_message(message.chat.id, "✅ Вы уже зарегистрированы или ожидаете одобрения.")

        with open(USERS_FILE, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([user_id, username, "pending"])

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
        user_id = int(call.data.split("_")[1])
        set_user_status(user_id, "approved")
        bot.send_message(call.message.chat.id, f"✅ Пользователь {user_id} одобрен.")
        try:
            bot.send_message(user_id, "✅ Ваша заявка одобрена! Вы можете пользоваться ботом.")
        except Exception as e:
            print(f"[WARN] Не удалось отправить сообщение пользователю {user_id}: {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
    def handle_reject_user(call):
        if not is_admin(call.from_user.id):
            return bot.answer_callback_query(call.id, "⛔ Только для админов.")
        user_id = int(call.data.split("_")[1])
        reject_user_by_id(user_id)
        set_user_status(user_id, "rejected")
        bot.send_message(call.message.chat.id, f"🚫 Пользователь {user_id} был отклонён.")
        try:
            bot.send_message(user_id, "🚫 Ваша заявка на регистрацию была отклонена.")
        except Exception as e:
            print(f"[WARN] Не удалось отправить сообщение пользователю {user_id}: {e}")

    @bot.message_handler(commands=["t"])
    def send_excel_report(message):
        user_id = message.from_user.id
        if not (is_user_approved(user_id) or user_id in TRUSTED_USERS):
            return bot.reply_to(message, "❌ Вы не одобрены.")
        username = message.from_user.username or f"user_{user_id}"
        buf = generate_excel_report_by_months(user_id, username, today_only=True)
        if buf:
            filename = f"Report_{username}_{datetime.now(TS_ZONE):%Y-%m-%d}.xlsx"
            try:
                bot.send_document(message.chat.id, InputFile(buf, filename), caption="📄 Ваш отчёт на сегодня.")
            except Exception as e:
                print(f"[ERROR] send_document failed (self): uid={user_id}, err={e}")
                bot.reply_to(message, "⚠️ Не удалось отправить файл (проверьте, можно ли боту присылать документы).")
        else:
            bot.reply_to(message, "⚠️ Отчёт не найден.")

    @bot.message_handler(func=lambda m: m.text in ["🍽 Вышел на обед", "🍽 Вернулся с обеда", "🏁 Ушел с работы"])
    def handle_actions(message):
        user_id = message.from_user.id
        if not (is_user_approved(user_id) or user_id in TRUSTED_USERS):
            return bot.reply_to(message, "❌ Вы не одобрены.")
        action_map = {
            "🍽 Вышел на обед": "Вышел на обед",
            "🍽 Вернулся с обеда": "Вернулся с обеда",
            "🏁 Ушел с работы": "Ушел с работы",
        }
        action = action_map[message.text]
        ts = datetime.now(TS_ZONE).strftime("%Y-%m-%d %H:%M:%S")
        save_work_time(user_id, action, ts)
        bot.reply_to(message, f"✅ Отмечено: {action} ({ts})")

    @bot.message_handler(commands=["all_reports"])
    def all_reports(message):
        if not is_admin(message.from_user.id):
            return _deny_admin(bot, message, why="all_reports")
        for uid, uname in get_all_users().items():
            buf = generate_excel_report_by_months(int(uid), uname)
            if buf:
                filename = f"Report_{uname}_{datetime.now(TS_ZONE):%Y-%m-%d}.xlsx"
                try:
                    bot.send_document(message.chat.id, InputFile(buf, filename), caption=f"📎 Отчёт {uname}")
                except Exception as e:
                    print(f"[ERROR] send_document failed (admin->user): uid={uid}, err={e}")
                    bot.send_message(message.chat.id, f"⚠️ Не удалось отправить отчёт {uname} (нет прав на документы?).")
            else:
                bot.send_message(message.chat.id, f"⚠️ Нет отчёта для {uname}.")

    @bot.message_handler(commands=["whoami"])
    def whoami(message):
        bot.reply_to(message, f"🪪 Ваш user ID: `{message.from_user.id}`", parse_mode="Markdown")

    @bot.message_handler(commands=["am_i_admin"])
    def am_i_admin(message):
        uid = message.from_user.id
        is_admin_flag = uid in ADMIN_IDS
        in_auto = uid in AUTO_APPROVED_USERS
        in_emp = uid in EMPLOYEE_USERS
        in_allowed = uid in ALLOWED_AUTO_USERS
        bot.reply_to(
            message,
            (
                "🔎 Диагностика прав:\n"
                f"- ID: <code>{uid}</code>\n"
                f"- ADMIN_IDS: {'✅' if is_admin_flag else '❌'}\n"
                f"- AUTO_APPROVED_USERS: {'✅' if in_auto else '❌'}\n"
                f"- EMPLOYEE_USERS: {'✅' if in_emp else '❌'}\n"
                f"- ALLOWED_AUTO_USERS: {'✅' if in_allowed else '❌'}\n"
            ),
            parse_mode="HTML",
        )

    @bot.message_handler(commands=["pending"])
    def show_pending_users(message):
        if not is_admin(message.from_user.id):
            return _deny_admin(bot, message, why="pending")
        pending = get_pending_users()
        if not pending:
            return bot.send_message(message.chat.id, "📭 Нет заявок на одобрение.")
        for uid, uname in pending.items():
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{uid}"))
            bot.send_message(message.chat.id, f"👤 @{uname} (ID: {uid})", reply_markup=markup)

    
    @bot.message_handler(commands=["авторежим_вкл"])
    def auto_mode_on(message):
        uid = message.from_user.id
        if uid not in TRUSTED_USERS:
            print(f"[AUTO_DENY] uid={uid} not in TRUSTED_USERS")
            return bot.send_message(message.chat.id, "⛔ У вас нет доступа к авто-режиму.")
        enable_auto_mode(uid)
        if uid in EMPLOYEE_USERS:
            bot.send_message(message.chat.id, "✅ Авто-режим включён. Для вас автоматически отмечается только обед (13:00–14:00).")
        else:
            bot.send_message(message.chat.id, "✅ Авто-режим включён. (Сейчас автоматически отмечается обед 13:00–14:00.)")

    @bot.message_handler(commands=["авторежим_выкл"])
    def auto_mode_off(message):
        uid = message.from_user.id
        if uid not in TRUSTED_USERS:
            print(f"[AUTO_DENY] uid={uid} not in TRUSTED_USERS")
            return bot.send_message(message.chat.id, "⛔ У вас нет доступа к авто-режиму.")
        disable_auto_mode(uid)
        bot.send_message(message.chat.id, "🛑 Автомаркер выключен.")
