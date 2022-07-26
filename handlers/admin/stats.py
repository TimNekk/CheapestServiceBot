from datetime import datetime, timedelta

from aiogram import types

from data.config import Commands
from filters import IsAdmin
from loader import dp, db


@dp.message_handler(IsAdmin(), commands=Commands.Admin.stats.command)
async def stats(message: types.Message):
    user = db.get_user(message.chat.id)

    today_users_count = db.get_users_count_by_date(datetime.utcnow() + timedelta(hours=3))
    total_users_count = db.get_users_count()

    text = f"""
📊 <b>Статистика на {datetime.utcnow() + timedelta(hours=3):%d.%m.%Y %H:%M}</b>

<b>Запусков сегодня:</b> {today_users_count}
<b>Запусков за все время:</b> {total_users_count}
"""

    await user.send_message(text)
