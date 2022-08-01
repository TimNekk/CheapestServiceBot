from datetime import timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from pypayment import LavaPayment, ChargeCommission

from data.config import Lava, BOT_TOKEN, VAK_SMS_API_KEY, Redis
from utils import VakSMSApi
from utils.db_api.database import Database

bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = RedisStorage2(host=Redis.host, port=Redis.port, password=Redis.password, decode_responses=True) if Redis.use_redis else MemoryStorage()
dp = Dispatcher(bot, storage=storage)
db = Database()

vak_sms = VakSMSApi(VAK_SMS_API_KEY)

LavaPayment.authorize(token=Lava.token,
                      wallet_to=Lava.wallet,
                      expiration_duration=timedelta(hours=1),
                      success_url=f"https://t.me/CheapestServiceBot",
                      charge_commission=ChargeCommission.FROM_CUSTOMER)
