from dataclasses import dataclass

from environs import Env

# Теперь используем вместо библиотеки python-dotenv библиотеку environs
env = Env()
env.read_env()

BOT_TOKEN = env.str("BOT_TOKEN")
DEVELOPER = env.str("DEVELOPER")
ADMINS = env.list("ADMINS")

ADMIN_NICKNAME = env.str("ADMIN_NICKNAME")
FEEDBACK_NICKNAME = env.str("FEEDBACK_NICKNAME")

VAK_SMS_API_KEY = env.str("VAK_SMS_API_KEY")


@dataclass
class Qiwi:
    secret_key: str = env.str("QIWI_SECRET_KEY")
    theme_code: str = env.str("QIWI_THEME_CODE")


@dataclass
class Lava:
    token: str = env.str("LAVA_TOKEN")
    wallet: str = env.str("LAVA_WALLET")


@dataclass
class CommandInfo:
    command: str
    description: str


@dataclass
class Commands:
    buy = CommandInfo("buy", "Купить")
    guide = CommandInfo("guide", "Инструкции по применению")
    support = CommandInfo("support", "Поддержка")
    feedback = CommandInfo("feedback", "Отзывы")

    @dataclass
    class Admin:
        settings = CommandInfo("admin", "Админка")
        send = CommandInfo("send", "Рассылка")
        stats = CommandInfo("stats", "Статистика")


@dataclass
class Subscription:
    id: str = env.str("SUBSCRIPTION_ID")
    url: str = env.str("SUBSCRIPTION_URL")


API_DOCS_URL = "https://vak-sms.com/api/vak/"
ANTI_FLOOD_USERS = []

# with open("flood.txt") as f:
#     ANTI_FLOOD_USERS = list(map(int, f.readlines()))