from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import Message

from data.config import Commands


class IsGuideCommand(BoundFilter):
    async def check(self, message: Message) -> bool:
        return message.text in (f"/{Commands.guide.command}", Commands.guide.description)
