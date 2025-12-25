from config import BOT_TOKENS, LOGGER_CHAT_ID
import logging
from logging.handlers import RotatingFileHandler
import aiohttp
import asyncio

class AsyncTelegramHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.bot_token = BOT_TOKENS[0]
        self.chat_id = LOGGER_CHAT_ID
        self.url = f'https://api.telegram.org/bot{self.bot_token}/sendMessage'

    async def _send_message(self, message):
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(self.url, data={
                    'chat_id': self.chat_id,
                    'text': f'📢 {message}'
                })
        except Exception as e:
            print(f"Ошибка при отправке лога в Telegram: {e}")

    def emit(self, record):
        log_entry = self.format(record)
        asyncio.create_task(self._send_message(log_entry))


def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Устанавливаем минимальный уровень логирования

    # Форматтер для логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Обработчик для записи в файл (с ротацией)
    file_handler = RotatingFileHandler(
        'app.log',
        maxBytes=1024*1024*1,  # 1 MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)  # Записываем DEBUG и выше в файл

    # Обработчик для вывода в консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)  # В консоль только INFO и выше

    # Добавляем обработчики к логгеру
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    telegram_handler = AsyncTelegramHandler()
    telegram_handler.setFormatter(formatter)
    logger.addHandler(telegram_handler)

    return logger





