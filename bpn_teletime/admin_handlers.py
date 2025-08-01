import csv
from datetime import datetime
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from config import ADMIN_IDS
from storage import get_all_users, get_user_dates, update_work_time_entry
from reports import generate_excel_report_by_months

# Контекст для многошагового меню редактирования
CTX: dict[int, dict] = {}

def register_admin_handlers(bot: TeleBot):
    @bot.message_handler(commands=['admin', 'menu', 'edit_time'])
    def admin_menu(message):
        if message.from_user.id not in ADMIN_IDS:
            return bot.reply_to(message, "⛔ Только администраторам.")
        # Шаг 1: выбрать действие
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🕒 Изменить время сотрудника", callback_data="et_start"),
            InlineKeyboardButton("📊 Отправить отчёты всем", callback_data="send_all_reports"),
        )
        bot.send_message(message.chat.id, "🔧 Меню администратора:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda c: c.data == 'et_start')
    def cb_start_edit(call):
        bot.answer_callback_query(call.id)
        # Шаг 2: выбрать сотрудника
        users = get_all_users()
        if not users:
            return bot.send_message(call.message.chat.id, "👥 Нет одобренных пользователей.")
        CTX[call.message.chat.id] = {}
        markup = InlineKeyboardMarkup(row_width=1)
        for uid, uname in users.items():
            markup.add(InlineKeyboardButton(f"{uname} ({uid})", callback_data=f"et_user:{uid}"))
        bot.edit_message_text("1️⃣ Выберите сотрудника:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda c: c.data.startswith('et_user:'))
    def cb_pick_user(call):
        bot.answer_callback_query(call.id)
        chat_id = call.message.chat.id
        uid = call.data.split(':',1)[1]
        CTX[chat_id]['user_id'] = uid
        # Шаг 3: выбрать дату из имеющихся
        dates = get_user_dates(uid)
        if not dates:
            return bot.send_message(chat_id, "❌ Нет записей для этого пользователя.")
        markup = InlineKeyboardMarkup(row_width=2)
        for d in dates:
            markup.add(InlineKeyboardButton(d, callback_data=f"et_date:{d}"))
        bot.edit_message_text("2️⃣ Выберите дату:", chat_id, call.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda c: c.data.startswith('et_date:'))
    def cb_pick_date(call):
        bot.answer_callback_query(call.id)
        chat_id = call.message.chat.id
        date_str = call.data.split(':',1)[1]
        CTX[chat_id]['date'] = date_str
        # Шаг 4: выбрать тип отметки
        actions = ["Пришел на работу", "Вышел на обед", "Вернулся с обеда", "Ушел с работы"]
        markup = InlineKeyboardMarkup(row_width=1)
        for act in actions:
            code = act.replace(" ", "_")
            markup.add(InlineKeyboardButton(act, callback_data=f"et_act:{code}"))
        bot.edit_message_text("3️⃣ Выберите тип отметки:", chat_id, call.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda c: c.data.startswith('et_act:'))
    def cb_pick_action(call):
        bot.answer_callback_query(call.id)
        chat_id = call.message.chat.id
        code = call.data.split(':',1)[1]
        CTX[chat_id]['action'] = code.replace("_", " ")
        # Шаг 5: ввод нового времени
        bot.edit_message_text(
            "4️⃣ Введите новое время в формате `HH:MM:SS` (например `08:30:00`):",
            chat_id, call.message.message_id,
            parse_mode='Markdown'
        )

    @bot.message_handler(func=lambda m: m.chat.id in CTX and 'action' in CTX[m.chat.id] and 'done' not in CTX[m.chat.id])
    def cb_input_time(message):
        chat_id = message.chat.id
        ctx = CTX[chat_id]
        time_str = message.text.strip()
        # Проверка формата
        try:
            datetime.strptime(time_str, "%H:%M:%S")
        except ValueError:
            return bot.reply_to(message, "❌ Неверный формат. Используйте `HH:MM:SS`.", parse_mode='Markdown')
        # Попытка обновить запись
        ok = update_work_time_entry(
            ctx['user_id'],
            ctx['date'],
            ctx['action'],
            time_str
        )
        if ok:
            bot.reply_to(
                message,
                f"✅ Обновлено для `{ctx['user_id']}`:\n"
                f"*{ctx['action']}* → `{ctx['date']} {time_str}`",
                parse_mode='Markdown'
            )
        else:
            bot.reply_to(message, "❌ Не найдено записи для обновления.")
        ctx['done'] = True
        # Очистка контекста
        CTX.pop(chat_id, None)

    @bot.callback_query_handler(func=lambda c: c.data == 'send_all_reports')
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

