from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import Message

from data.config import Commands


class IsFeedbackCommand(BoundFilter):
    async def check(self, message: Message) -> bool:
        return message.text in (f"/{Commands.feedback.command}", Commands.feedback.description)
