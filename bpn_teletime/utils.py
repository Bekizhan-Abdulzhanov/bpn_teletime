from datetime import datetime
import pytz
from config import TIMEZONE

kyrgyz_tz = pytz.timezone(TIMEZONE)

def now():
    return datetime.now(kyrgyz_tz)

def format_now():
    return now().strftime("%Y-%m-%d %H:%M:%S")