import telebot
from datetime import datetime
import csv
import os
from openpyxl import Workbook
from openpyxl.styles import Font, Border, Side, Alignment
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton,ReplyKeyboardMarkup, KeyboardButton
from apscheduler.schedulers.background import BackgroundScheduler
import time
import pytz
import qrcode

os.environ['TZ'] = 'Asia/Bishkek'

kyrgyzstan_tz = pytz.timezone('Asia/Bishkek')
now = datetime.now(kyrgyzstan_tz)

bot = telebot.TeleBot(os.environ.get('BOT_TOKEN'))

# Генерация общего QR-кода для всех сотрудников
common_qr_url = "https://t.me/BPN_KG_managetime_bot?start=checkin"
qr = qrcode.make(common_qr_url)
qr.save("common_qr_code.png")

# Файлы для хранения данных
WORKTIME_FILE = 'work_time.csv'
EXCEL_REPORT_DIR = 'work_reports'
USERS_FILE = 'users.csv'
ADMIN_ID = 557174721

  # Замените на ID администратора


# Создание папки для отчетов
if not os.path.exists(EXCEL_REPORT_DIR):
    os.makedirs(EXCEL_REPORT_DIR)


# Функция для записи рабочего времени с учетом временной зоны
def save_work_time(user_id, user_name, action): 
    now = datetime.now(kyrgyzstan_tz).strftime("%Y-%m-%d %H:%M:%S")  # Учитываем временную зону
    file_exists = os.path.isfile(WORKTIME_FILE) 

    try: 
        with open(WORKTIME_FILE, mode='a', newline='', encoding='utf-8') as file: 
            writer = csv.writer(file) 
            if not file_exists: 
                writer.writerow(["User ID", "User Name", "Action", "Timestamp"]) 
            writer.writerow([user_id, user_name, action, now]) 
        print(f"[{now}] Записано: {user_name} ({user_id}) - {action}") 
    except Exception as e: 
        print(f"Ошибка при записи времени: {e}") 

# В других местах, где используется время, также заменим на:
now = datetime.now(kyrgyzstan_tz).strftime("%Y-%m-%d %H:%M:%S")

scheduler = BackgroundScheduler()

# Функция для регистрации сотрудников
@bot.message_handler(commands=['register'])
def register(message):
    user = message.from_user
    with open(USERS_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([user.id, user.username, 'pending'])
    bot.send_message(ADMIN_ID, f"Новая заявка на регистрацию от {user.username} ({user.id})",
                     reply_markup=approve_keyboard(user.id))
    bot.reply_to(message, "Ваша заявка отправлена администратору на рассмотрение.")

# Клавиатура для админа
def approve_keyboard(user_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Принять", callback_data=f"approve_{user_id}"))
    markup.add(InlineKeyboardButton("Отклонить", callback_data=f"reject_{user_id}"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def approve_user(call):
    user_id = call.data.split("_")[1]
    update_user_status(user_id, "approved")
    bot.send_message(user_id, "Ваша регистрация одобрена!")
    bot.send_message(ADMIN_ID, f"Пользователь {user_id} одобрен.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
def reject_user(call):
    user_id = call.data.split("_")[1]
    update_user_status(user_id, "rejected")
    bot.send_message(user_id, "Ваша заявка отклонена.")
    bot.send_message(ADMIN_ID, f"Пользователь {user_id} отклонен.")

# Функция для обновления статуса пользователя
def update_user_status(user_id, status):
    users = []
    with open(USERS_FILE, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == user_id:
                row[2] = status
            users.append(row)
    with open(USERS_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(users)

# Проверка доступа
def is_user_approved(user_id):
    with open(USERS_FILE, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == str(user_id) and row[2] == 'approved':
                return True
    return False


# Меню с кнопками
@bot.message_handler(commands=['1'])
def show_menu(message):
    if not is_user_approved(message.from_user.id):
        bot.reply_to(message, "Вы не зарегистрированы или ваша заявка не одобрена.")
        return

    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add(
        KeyboardButton("🍽 Вышел на обед")
    )
    markup.add(
        KeyboardButton("🍽 Вернулся с обеда"),
        KeyboardButton("🏁 Ушел с работы")
    )
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

# Обработчик кнопок
@bot.message_handler(func=lambda message: message.text in [ "🍽 Вышел на обед", "🍽 Вернулся с обеда", "🏁 Ушел с работы"])
def handle_work_time(message):
    if not is_user_approved(message.from_user.id):
        bot.reply_to(message, "Вы не зарегистрированы или ваша заявка не одобрена.")
        return

    user = message.from_user
    actions = {
        "🍽 Вышел на обед": "Вышел на обед",
        "🍽 Вернулся с обеда": "Вернулся с обеда",
        "🏁 Ушел с работы": "Ушел с работы"
    }
    
    action = actions[message.text]
    save_work_time(user.id, user.username, action)
    bot.reply_to(message, f"Вы отметили: {message.text}")


# Команды бота
@bot.message_handler(commands=['start'])
def start_work(message):
    if not is_user_approved(message.from_user.id):
        bot.reply_to(message, "Вы не зарегистрированы или ваша заявка не одобрена.")
        return
    user = message.from_user
    save_work_time(user.id, user.username, "Пришел на работу")
    bot.reply_to(message, f"Доброе утро, {user.first_name}! Вы отметили приход на работу.")

@bot.message_handler(commands=['lunch_out'])
def lunch_out(message):
    if not is_user_approved(message.from_user.id):
        bot.reply_to(message, "Вы не зарегистрированы или ваша заявка не одобрена.")
        return    
    user = message.from_user
    save_work_time(user.id, user.username, "Вышел на обед")
    bot.reply_to(message, "Вы отметили выход на обед.")

@bot.message_handler(commands=['lunch_in'])
def lunch_in(message):
    if not is_user_approved(message.from_user.id):
        bot.reply_to(message, "Вы не зарегистрированы или ваша заявка не одобрена.")
        return    
    user = message.from_user
    save_work_time(user.id, user.username, "Вернулся с обеда")
    bot.reply_to(message, "Вы отметили возвращение с обеда.")

@bot.message_handler(commands=['end'])
def end_work(message):
    if not is_user_approved(message.from_user.id):
        bot.reply_to(message, "Вы не зарегистрированы или ваша заявка не одобрена.")
        return     
    user = message.from_user
    save_work_time(user.id, user.username, "Ушел с работы")
    bot.reply_to(message, f"До свидания, {user.first_name}! Вы отметили уход с работы.")

# Генерация отчета в Excel для администратора
@bot.message_handler(commands=['all_reports'])
def all_reports(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "У вас нет доступа к этому разделу.")
        return
    for user_id in get_all_users():
        report_file = generate_excel_report(user_id)
        if report_file:
            with open(report_file, 'rb') as file:
                bot.send_document(ADMIN_ID, file, caption=f"Отчет сотрудника {user_id}")

@bot.message_handler(commands=['edit_time'])
def edit_time(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "У вас нет прав для редактирования данных.")
        return
    
    markup = InlineKeyboardMarkup()
    
    if not os.path.exists(WORKTIME_FILE):
        bot.reply_to(message, "Файл с рабочим временем пуст или не существует.")
        return
    
    users = {}
    with open(WORKTIME_FILE, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader, None)  # Пропускаем заголовок
        for row in reader:
            if len(row) < 2:
                continue
            user_id, user_name = row[0], row[1]
            users[user_id] = user_name

    for user_id, user_name in users.items():
        markup.add(InlineKeyboardButton(text=user_name, callback_data=f"edit_{user_id}"))

    bot.send_message(message.chat.id, "Выберите сотрудника для редактирования:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_"))
def select_employee(call):
    user_id = call.data.split("_")[1]
    
    markup = InlineKeyboardMarkup()
    
    dates = set()
    with open(WORKTIME_FILE, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader, None)
        for row in reader:
            if len(row) < 4:
                continue
            if row[0] == user_id:
                date = row[3].split()[0]
                dates.add(date)

    for date in sorted(dates):
        markup.add(InlineKeyboardButton(text=date, callback_data=f"date_{user_id}_{date}"))

    bot.send_message(call.message.chat.id, "Выберите дату для редактирования:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("date_"))
def select_date(call):
    _, user_id, date = call.data.split("_")

    markup = InlineKeyboardMarkup()
    actions = ["Пришел на работу", "Вышел на обед", "Вернулся с обеда", "Ушел с работы"]

    for action in actions:
        markup.add(InlineKeyboardButton(text=f"Изменить {action}", callback_data=f"change_{user_id}_{date}_{action}"))

    bot.send_message(call.message.chat.id, "Выберите действие для редактирования:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("change_"))
def change_time(call):
    _, user_id, date, action = call.data.split("_")

    msg = bot.send_message(call.message.chat.id, f"Введите новое время для '{action}' в формате ЧЧ:ММ:")
    bot.register_next_step_handler(msg, lambda message: update_time(message, user_id, date, action))


def update_time(message, user_id, date, action): 
    new_time = message.text.strip()
    try: 
        datetime.strptime(new_time, "%H:%M") 
    except ValueError: 
        bot.send_message(message.chat.id, "Некорректный формат. Введите время в формате ЧЧ:ММ.") 
        return 
    
    updated_rows = [] 
    updated = False 
    
    with open(WORKTIME_FILE, mode='r', encoding='utf-8') as file: 
        reader = csv.reader(file) 
        header = next(reader) 
        for row in reader: 
            if len(row) < 4: 
                continue 
            
            row_date = row[3].split()[0] 
            if row[0] == user_id and row_date == date and row[2] == action: 
                row[3] = f"{date} {new_time}:00" 
                updated = True 
            updated_rows.append(row) 
    
    if updated: 
        with open(WORKTIME_FILE, mode='w', newline='', encoding='utf-8') as file: 
            writer = csv.writer(file) 
            writer.writerow(["User ID", "Имя пользователя", "Действие", "Время"]) 
            writer.writerows(updated_rows) 

        bot.send_message(message.chat.id, f"Время для '{action}' сотрудника {user_id} на {date} обновлено на {new_time}.") 
        generate_excel_report(user_id)  # Добавлено обновление Excel 
    else: 
        bot.send_message(message.chat.id, "Запись не найдена или уже обновлена.")
    
    # После обновления CSV сразу генерируем новый отчет
    generate_excel_report(user_id)


def get_all_users():
    users = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                users[row[0]] = row[1]  # user_id -> user_name
    return users



# Функция для генерации отчета в Excel для каждого сотрудника
def generate_excel_report(user_id):  
    if not os.path.exists(WORKTIME_FILE):  
        return None  
    
    user_data = {}  
    with open(WORKTIME_FILE, mode='r', encoding='utf-8') as file:  
        reader = csv.reader(file)  
        next(reader, None)  
        for row in reader:  
            if len(row) != 4:  
                continue  
            uid, user_name, action, timestamp = row  
            if uid != str(user_id):  
                continue  
            timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")  
            date = timestamp.date()  
            
            if uid not in user_data:  
                user_data[uid] = {'name': user_name, 'log': {}}  
            
            if date not in user_data[uid]['log']:  
                user_data[uid]['log'][date] = {'start': None, 'lunch_out': None, 'lunch_in': None, 'end': None}  
            
            if action == "Пришел на работу":  
                user_data[uid]['log'][date]['start'] = timestamp  
            elif action == "Вышел на обед":  
                user_data[uid]['log'][date]['lunch_out'] = timestamp  
            elif action == "Вернулся с обеда":  
                user_data[uid]['log'][date]['lunch_in'] = timestamp  
            elif action == "Ушел с работы":  
                user_data[uid]['log'][date]['end'] = timestamp  
    
    if str(user_id) not in user_data:  
        return None  
    
    wb = Workbook()  
    ws = wb.active  
    ws.title = "Рабочий отчет"  
    ws.append(["ID пользователя", "Имя пользователя", "Дата", "Начало", "Обед (выход)", "Обед (возврат)", "Конец", "Часы за день"])  
    
    total_hours_month = 0  
    total_hours_all = 0  
    
    for date, times in sorted(user_data[str(user_id)]['log'].items()):  
        start = times['start']  
        lunch_out = times['lunch_out']  
        lunch_in = times['lunch_in']  
        end = times['end']  
        
        total_hours = 0  
        if start and end:  
            total_hours = (end - start).seconds / 3600  
            if lunch_out and lunch_in:  
                total_hours -= (lunch_in - lunch_out).seconds / 3600  
            total_hours_month += total_hours  
            total_hours_all += total_hours  
        
        ws.append([user_id, user_data[str(user_id)]['name'], date.strftime("%Y-%m-%d"),  
                   start.strftime("%H:%M") if start else "",  
                   lunch_out.strftime("%H:%M") if lunch_out else "",  
                   lunch_in.strftime("%H:%M") if lunch_in else "",  
                   end.strftime("%H:%M") if end else "",  
                   round(total_hours, 2)])  
    
    ws.append([])  
    ws.append(["Итого за месяц", round(total_hours_month, 2)])  
    ws.append(["Итого за весь период", round(total_hours_all, 2)])  
    
    thin_border = Border(left=Side(style='thin'),  
                         right=Side(style='thin'),  
                         top=Side(style='thin'),  
                         bottom=Side(style='thin'))  
    
    for col in ws.columns:  
        for cell in col:  
            cell.border = thin_border  
            cell.alignment = Alignment(horizontal="center", vertical="center")  
            if cell.row == 1:  
                cell.font = Font(bold=True)  
    
    report_path = os.path.join(EXCEL_REPORT_DIR, f"report_{user_id}.xlsx")  
    wb.save(report_path)  
    return report_path
    
# Отправка отчета пользователю 
@bot.message_handler(commands=['send_excel_report'])
def send_excel_report(message):
    user_id = message.from_user.id
    report_file = generate_excel_report(user_id)
    
    if report_file and os.path.exists(report_file):
        with open(report_file, 'rb') as file:
            bot.send_document(message.chat.id, file, caption="Ваш личный отчет о рабочем времени.")
    else:
        bot.reply_to(message, "Отчет не найден. Проверьте, есть ли у вас записанные отметки о рабочем времени.")

#87654321: "username2"
AUTO_USERS = {
    378268765: "ErlanNasiev",  

}

# Настроим расписание работы (по реальному времени)
def schedule_auto_records():
    weekdays_1 = [0, 2, 4]  
    weekdays_2 = [1, 3]

    for user_id, username in AUTO_USERS.items():
        # ПН, СР, ПТ - 08:29, 12:00, 13:00, 17:30
        scheduler.add_job(save_work_time, "cron", day_of_week="mon,wed,fri", hour=8, minute=29,
                          args=[user_id, username, "Пришел на работу"])
        scheduler.add_job(save_work_time, "cron", day_of_week="mon,wed,fri", hour=12, minute=0,
                          args=[user_id, username, "Вышел на обед"])
        scheduler.add_job(save_work_time, "cron", day_of_week="mon,wed,fri", hour=13, minute=0,
                          args=[user_id, username, "Вернулся с обеда"])
        scheduler.add_job(save_work_time, "cron", day_of_week="mon,wed,fri", hour=17, minute=30,
                          args=[user_id, username, "Ушел с работы"])

        # ВТ, ЧТ - 08:28, 12:00, 13:00, 17:30
        scheduler.add_job(save_work_time, "cron", day_of_week="tue,thu", hour=8, minute=28,
                          args=[user_id, username, "Пришел на работу"])
        scheduler.add_job(save_work_time, "cron", day_of_week="tue,thu", hour=12, minute=0,
                          args=[user_id, username, "Вышел на обед"])
        scheduler.add_job(save_work_time, "cron", day_of_week="tue,thu", hour=13, minute=0,
                          args=[user_id, username, "Вернулся с обеда"])
        scheduler.add_job(save_work_time, "cron", day_of_week="tue,thu", hour=17, minute=30,
                          args=[user_id, username, "Ушел с работы"])

# Запускаем автоматическое расписание
schedule_auto_records()
scheduler.start()

# Запуск бота
if __name__ == '__main__':
    print("Бот запущен")
    bot.infinity_polling()

print("Автоматическая запись времени включена.")
print('Текущее время:',now)
while True:
    time.sleep(60)
    
