from datetime import datetime
import pytz
from config import TIMEZONE

# 🌍 Временная зона Кыргызстана (или указанная в .env/.config)
_kyrgyz_tz = pytz.timezone(TIMEZONE)


def now() -> datetime:
    """
    Возвращает текущее время в заданной временной зоне.
    :return: datetime объект текущего времени
    """
    return datetime.now(_kyrgyz_tz)


def format_now(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Форматированное текущее время.
    :param fmt: строка формата времени (по умолчанию: Y-M-D H:M:S)
    :return: строка с текущим временем
    """
    return now().strftime(fmt)
