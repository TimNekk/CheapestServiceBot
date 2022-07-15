from datetime import timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from pypayment import QiwiPayment

from data.config import Qiwi, BOT_TOKEN, VAK_SMS_API_KEY
from utils import VakSMSApi
from utils.db_api.database import Database

bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
db = Database()

vak_sms = VakSMSApi(VAK_SMS_API_KEY)

QiwiPayment.authorize(secret_key=Qiwi.secret_key,
                      theme_code=Qiwi.theme_code,
                      expiration_duration=timedelta(hours=1))
