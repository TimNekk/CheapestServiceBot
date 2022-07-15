from loader import dp
from .db import IsInDB
from .admin import IsAdmin
from .buy import IsBuyCommand
from .guide import IsGuideCommand
from .support import IsSupportCommand
from .feedback import IsFeedbackCommand


if __name__ == "filters":
    dp.filters_factory.bind(IsInDB)
    dp.filters_factory.bind(IsAdmin)
    dp.filters_factory.bind(IsBuyCommand)
    dp.filters_factory.bind(IsGuideCommand)
    dp.filters_factory.bind(IsSupportCommand)
    dp.filters_factory.bind(IsFeedbackCommand)
