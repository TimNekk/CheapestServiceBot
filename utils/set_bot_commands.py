from aiogram import types
from aiogram.types import BotCommandScopeDefault, BotCommandScopeChat

from data.config import Commands, ADMINS


async def set_default_commands(dp):
    default_commands = [
        types.BotCommand(Commands.buy.command, Commands.buy.description),
        types.BotCommand(Commands.guide.command, Commands.guide.description),
        types.BotCommand(Commands.support.command, Commands.support.description),
        types.BotCommand(Commands.feedback.command, Commands.feedback.description)
    ]

    await dp.bot.set_my_commands(commands=default_commands,
                                 scope=BotCommandScopeDefault())

    admin_commands = [
        types.BotCommand(Commands.Admin.settings.command, Commands.Admin.settings.description),
        # types.BotCommand(Commands.Admin.prolong.command, Commands.Admin.prolong.description),
        types.BotCommand(Commands.Admin.send.command, Commands.Admin.send.description),
        types.BotCommand(Commands.Admin.stats.command, Commands.Admin.stats.description),
    ]

    for admin_id in ADMINS:
        await dp.bot.set_my_commands(commands=admin_commands + default_commands,
                                     scope=BotCommandScopeChat(admin_id))
