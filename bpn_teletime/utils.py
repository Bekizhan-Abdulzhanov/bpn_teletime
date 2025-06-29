from datetime import datetime
import pytz
from config import TIMEZONE

kyrgyz_tz = pytz.timezone(TIMEZONE)

def now():
    """Текущее время в указанной временной зоне"""
    return datetime.now(kyrgyz_tz)

def format_now():
    """Отформатированное время"""
    return now().strftime("%Y-%m-%d %H:%M:%S")

