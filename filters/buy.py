from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import Message

from data.config import Commands


class IsBuyCommand(BoundFilter):
    async def check(self, message: Message) -> bool:
        return message.text in (f"/{Commands.buy.command}", Commands.buy.description)
