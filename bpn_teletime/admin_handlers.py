# admin_handlers.py
import io
import csv
from datetime import datetime
from zipfile import ZipFile, ZIP_DEFLATED
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from zoneinfo import ZoneInfo

from config import ADMIN_IDS, TIMEZONE, AUTO_APPROVED_USERS, EMPLOYEE_USERS
from storage import get_all_users, get_user_dates, update_work_time_entry
from reports import generate_excel_report_by_months

TS_ZONE = ZoneInfo(TIMEZONE)

# Контекст для многошагового меню редактирования
CTX: dict[int, dict] = {}

def _deny_admin(bot: TeleBot, message, why: str = ""):
    uid = message.from_user.id if hasattr(message, "from_user") else None
    print(f"[ADMIN_DENY] uid={uid} not in ADMIN_IDS={ADMIN_IDS}. {why}")
    if hasattr(message, "id"):
        bot.reply_to(message, "⛔ Только администраторам.")
    else:
        bot.answer_callback_query(message.id, "⛔ Только администраторам.")

def _all_targets() -> dict[int, str]:
    """
    Объединённый список пользователей для отчётов:
      - approved из users.csv
      - AUTO_APPROVED_USERS
      - EMPLOYEE_USERS
    """
    targets: dict[int, str] = {}

    # approved из users.csv
    for uid_str, uname in get_all_users().items():
        try:
            targets[int(uid_str)] = uname or f"user_{uid_str}"
        except ValueError:
            continue

    # full-auto
    for uid, name in AUTO_APPROVED_USERS.items():
        targets[int(uid)] = name

    # сотрудники (обед-авто)
    for uid, name in EMPLOYEE_USERS.items():
        targets[int(uid)] = name

    return targets


def register_admin_handlers(bot: TeleBot):
    # --- главное меню ---
    @bot.message_handler(commands=['admin', 'menu', 'edit_time'])
    def admin_menu(message):
        if message.from_user.id not in ADMIN_IDS:
            return _deny_admin(bot, message, "admin_menu")

        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🕒 Изменить время сотрудника", callback_data="et_start"),
            InlineKeyboardButton("📊 Отправить отчёты всем (в чат)", callback_data="send_all_reports_chat"),
            InlineKeyboardButton("📦 Все отчёты ZIP (мне)", callback_data="send_all_reports_zip"),
        )
        bot.send_message(message.chat.id, "🔧 Меню администратора:", reply_markup=markup)

    # --- сбор всех отчётов и отправка в текущий чат (по одному файлу) ---
    @bot.callback_query_handler(func=lambda c: c.data == 'send_all_reports_chat')
    def handle_send_reports_chat(call):
        if call.from_user.id not in ADMIN_IDS:
            return _deny_admin(bot, call, "send_all_reports_chat")
        bot.answer_callback_query(call.id)

        targets = _all_targets()
        if not targets:
            return bot.send_message(call.message.chat.id, "👥 Нет пользователей для отчётов.")

        sent = 0
        for uid, uname in targets.items():
            buf = generate_excel_report_by_months(uid, uname)
            if buf:
                filename = f"Report_{uname}_{datetime.now(TS_ZONE):%Y-%m-%d}.xlsx"
                try:
                    bot.send_document(call.message.chat.id, InputFile(buf, filename),
                                      caption=f"Отчёт {uname}")
                    sent += 1
                except Exception as e:
                    print(f"[ERROR] send_document chat failed: uid={uid}, name={uname}, err={e}")
            else:
                bot.send_message(call.message.chat.id, f"⚠️ Нет данных для {uname}")

        bot.send_message(call.message.chat.id, f"✅ Отправлено отчётов: {sent}/{len(targets)}")

    # --- сбор всех отчётов и отправка одним ZIP админу (инициатору) ---
    @bot.callback_query_handler(func=lambda c: c.data == 'send_all_reports_zip')
    def handle_send_reports_zip(call):
        if call.from_user.id not in ADMIN_IDS:
            return _deny_admin(bot, call, "send_all_reports_zip")
        bot.answer_callback_query(call.id)

        _send_zip_to_user(bot, call.from_user.id)

    # Дублируем функционал ZIP ещё и отдельной командой — удобно
    @bot.message_handler(commands=['all_reports_zip'])
    def send_all_reports_zip_cmd(message):
        if message.from_user.id not in ADMIN_IDS:
            return _deny_admin(bot, message, "all_reports_zip")
        _send_zip_to_user(bot, message.from_user.id)

    # Отправить все отчёты как отдельные файлы админу (инициатору)
    @bot.message_handler(commands=['all_reports_to_me'])
    def send_all_reports_to_me(message):
        if message.from_user.id not in ADMIN_IDS:
            return _deny_admin(bot, message, "all_reports_to_me")

        targets = _all_targets()
        if not targets:
            return bot.send_message(message.chat.id, "👥 Нет пользователей для отчётов.")

        sent = 0
        for uid, uname in targets.items():
            buf = generate_excel_report_by_months(uid, uname)
            if buf:
                filename = f"Report_{uname}_{datetime.now(TS_ZONE):%Y-%m-%d}.xlsx"
                try:
                    bot.send_document(message.chat.id, InputFile(buf, filename), caption=f"Отчёт {uname}")
                    sent += 1
                except Exception as e:
                    print(f"[ERROR] send_document to_me failed: uid={uid}, name={uname}, err={e}")
            else:
                bot.send_message(message.chat.id, f"⚠️ Нет данных для {uname}")

        bot.send_message(message.chat.id, f"✅ Отправлено отчётов: {sent}/{len(targets)}")

    # --- ZIP-сборка (вспомогательная) ---
    def _send_zip_to_user(bot: TeleBot, target_admin_id: int):
        targets = _all_targets()
        if not targets:
            return bot.send_message(target_admin_id, "👥 Нет пользователей для отчётов.")

        # Собираем ZIP в памяти
        zip_mem = io.BytesIO()
        with ZipFile(zip_mem, mode="w", compression=ZIP_DEFLATED) as zf:
            added = 0
            for uid, uname in targets.items():
                buf = generate_excel_report_by_months(uid, uname)
                if not buf:
                    continue
                # имя файла внутри архива
                inner_name = f"Report_{uname}_{datetime.now(TS_ZONE):%Y-%m-%d}.xlsx"
                try:
                    zf.writestr(inner_name, buf.getvalue())
                    added += 1
                except Exception as e:
                    print(f"[ERROR] zip add failed: uid={uid}, name={uname}, err={e}")

        if zip_mem.tell() == 0:
            return bot.send_message(target_admin_id, "⚠️ Нет отчётов для архива.")

        zip_mem.seek(0)
        zip_name = f"Reports_{datetime.now(TS_ZONE):%Y-%m-%d}.zip"
        try:
            bot.send_document(target_admin_id, InputFile(zip_mem, zip_name), caption="📦 Все отчёты (ZIP)")
        except Exception as e:
            print(f"[ERROR] send ZIP failed: err={e}")
            bot.send_message(target_admin_id, "⚠️ Не удалось отправить ZIP.")

    # ----------------- Редактирование отметок (как было) -----------------

    @bot.callback_query_handler(func=lambda c: c.data == 'et_start')
    def cb_start_edit(call):
        if call.from_user.id not in ADMIN_IDS:
            return _deny_admin(bot, call, why="cb_start_edit")
        bot.answer_callback_query(call.id)

        users = _all_targets()
        if not users:
            return bot.send_message(call.message.chat.id, "👥 Нет доступных пользователей.")
        CTX[call.message.chat.id] = {}
        markup = InlineKeyboardMarkup(row_width=1)
        for uid, uname in users.items():
            markup.add(InlineKeyboardButton(f"{uname} ({uid})", callback_data=f"et_user:{uid}"))
        bot.edit_message_text("1️⃣ Выберите сотрудника:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda c: c.data.startswith('et_user:'))
    def cb_pick_user(call):
        if call.from_user.id not in ADMIN_IDS:
            return _deny_admin(bot, call, why="cb_pick_user")
        bot.answer_callback_query(call.id)

        chat_id = call.message.chat.id
        uid = call.data.split(':', 1)[1]
        CTX[chat_id] = CTX.get(chat_id, {})
        CTX[chat_id]['user_id'] = uid

        dates = get_user_dates(uid)
        if not dates:
            return bot.send_message(chat_id, "❌ Нет записей для этого пользователя.")
        markup = InlineKeyboardMarkup(row_width=2)
        for d in dates:
            markup.add(InlineKeyboardButton(d, callback_data=f"et_date:{d}"))
        bot.edit_message_text("2️⃣ Выберите дату:", chat_id, call.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda c: c.data.startswith('et_date:'))
    def cb_pick_date(call):
        if call.from_user.id not in ADMIN_IDS:
            return _deny_admin(bot, call, why="cb_pick_date")
        bot.answer_callback_query(call.id)

        chat_id = call.message.chat.id
        date_str = call.data.split(':', 1)[1]
        CTX[chat_id] = CTX.get(chat_id, {})
        CTX[chat_id]['date'] = date_str

        actions = ["Пришел на работу", "Вышел на обед", "Вернулся с обеда", "Ушел с работы"]
        markup = InlineKeyboardMarkup(row_width=1)
        for act in actions:
            code = act.replace(" ", "_")
            markup.add(InlineKeyboardButton(act, callback_data=f"et_act:{code}"))
        bot.edit_message_text("3️⃣ Выберите тип отметки:", chat_id, call.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda c: c.data.startswith('et_act:'))
    def cb_pick_action(call):
        if call.from_user.id not in ADMIN_IDS:
            return _deny_admin(bot, call, why="cb_pick_action")
        bot.answer_callback_query(call.id)

        chat_id = call.message.chat.id
        code = call.data.split(':', 1)[1]
        CTX[chat_id] = CTX.get(chat_id, {})
        CTX[chat_id]['action'] = code.replace("_", " ")
        bot.edit_message_text(
            "4️⃣ Введите новое время в формате `HH:MM:SS` (например `08:30:00`):",
            chat_id, call.message.message_id,
            parse_mode='Markdown'
        )

    @bot.message_handler(func=lambda m: m.chat.id in CTX and 'action' in CTX[m.chat.id] and 'done' not in CTX[m.chat.id])
    def cb_input_time(message):
        if message.from_user.id not in ADMIN_IDS:
            return _deny_admin(bot, message, why="cb_input_time")
        chat_id = message.chat.id
        ctx = CTX[chat_id]
        time_str = message.text.strip()

        try:
            datetime.strptime(time_str, "%H:%M:%S")
        except ValueError:
            return bot.reply_to(message, "❌ Неверный формат. Используйте `HH:MM:SS`.", parse_mode='Markdown')

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
        CTX.pop(chat_id, None)

