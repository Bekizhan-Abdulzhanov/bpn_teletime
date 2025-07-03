import os
import csv
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from config import ADMIN_IDS
from storage import (
    USERS_FILE,
    get_pending_users,
    get_all_users,
    set_user_status,
    enable_auto_mode,
    disable_auto_mode,
    is_auto_enabled
)
from reports import generate_excel_report_by_months


def register_admin_handlers(bot: TeleBot):
    @bot.message_handler(commands=['admin', 'admin_menu'])
    def admin_menu(message):
        if message.from_user.id not in ADMIN_IDS:
            return bot.reply_to(message, "⛔ У вас нет прав администратора.")

        markup = InlineKeyboardMarkup(row_width=2)

        # Заявки в ожидании
        pending = get_pending_users()
        if pending:
            for uid, uname in pending.items():
                markup.add(
                    InlineKeyboardButton(f"✅ Одобрить {uname}", callback_data=f"approve_{uid}"),
                    InlineKeyboardButton(f"❌ Отклонить {uname}", callback_data=f"reject_{uid}")
                )
        else:
            markup.add(InlineKeyboardButton("Нет заявок на одобрение", callback_data="noop"))

        # Опции для авто-режима и отчётов
        users = get_all_users()
        for uid, uname in users.items():
            status = "ON" if is_auto_enabled(int(uid)) else "OFF"
            # Кнопки авто-режима
            if is_auto_enabled(int(uid)):
                markup.add(
                    InlineKeyboardButton(f"🛑 Выключить авто {uname} ({uid})", callback_data=f"auto_off_{uid}")
                )
            else:
                markup.add(
                    InlineKeyboardButton(f"▶️ Включить авто {uname} ({uid})", callback_data=f"auto_on_{uid}")
                )
            # Кнопка генерации отчёта
            markup.add(
                InlineKeyboardButton(f"📄 Отчет {uname} ({uid})", callback_data=f"report_{uid}")
            )

        bot.send_message(message.chat.id, "🔧 Меню администратора:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.split('_')[0] in ['approve', 'reject', 'auto', 'report'])
    def handle_admin_actions(call):
        if call.from_user.id not in ADMIN_IDS:
            return bot.answer_callback_query(call.id, "⛔ Только для админов.")

        parts = call.data.split("_")
        action = parts[0]

        if action == 'approve':
            uid = int(parts[1])
            set_user_status(uid, "approved")
            bot.answer_callback_query(call.id, f"✅ Пользователь {uid} одобрен.")
            try:
                bot.send_message(uid, "✅ Ваша заявка одобрена! Вы можете пользоваться ботом.")
            except:
                pass
        elif action == 'reject':
            uid = int(parts[1])
            set_user_status(uid, "rejected")
            bot.answer_callback_query(call.id, f"🚫 Пользователь {uid} отклонён.")
            try:
                bot.send_message(uid, "🚫 Ваша заявка отклонена.")
            except:
                pass
        elif action in ['auto']:
            # parts[1] should be 'on' or 'off'
            sub = parts[1]
            uid = int(parts[2])
            if sub == 'on':
                enable_auto_mode(uid)
                bot.answer_callback_query(call.id, f"✅ Авто-режим включён для {uid}.")
            else:
                disable_auto_mode(uid)
                bot.answer_callback_query(call.id, f"🛑 Авто-режим выключен для {uid}.")
        elif action == 'report':
            uid = int(parts[1])
            users = get_all_users()
            uname = users.get(str(uid), f"user_{uid}")
            buf = generate_excel_report_by_months(uid, uname)
            if buf:
                filename = f"Report_{uname}_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
                bot.send_document(call.message.chat.id, InputFile(buf, filename))
            else:
                bot.answer_callback_query(call.id, f"⚠️ Нет данных для {uid}.")
        else:
            bot.answer_callback_query(call.id, "❓ Неизвестное действие.")



