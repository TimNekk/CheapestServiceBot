from aiogram import types
from aiogram.dispatcher.filters import BoundFilter

from data.config import ADMINS


class IsAdmin(BoundFilter):
    async def check(self, event):
        if isinstance(event, types.Message):
            message = event
        elif isinstance(event, types.CallbackQuery):
            message = event.message
        else:
            raise NotImplementedError("Unknown event")
        return str(message.chat.id) in ADMINS
