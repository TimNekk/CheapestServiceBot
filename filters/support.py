from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import Message

from data.config import Commands


class IsSupportCommand(BoundFilter):
    async def check(self, message: Message) -> bool:
        return message.text in (f"/{Commands.support.command}", Commands.support.description)
