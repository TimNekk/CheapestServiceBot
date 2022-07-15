from aiogram import types
from aiogram.dispatcher.filters import BoundFilter

from loader import db


class IsInDB(BoundFilter):
    key = 'reverse'

    def __init__(self, reverse=False):
        self.reverse = reverse  # Проверять отсутствие в базе

    async def check(self, message: types.Message):
        user = db.get_user(id=message.chat.id)
        return (user and not self.reverse) or (not user and self.reverse)