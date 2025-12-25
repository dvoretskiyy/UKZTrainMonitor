import logging
from logging.handlers import RotatingFileHandler
import aiohttp
import asyncio
from config import config


class AsyncTelegramHandler(logging.Handler):
    def __init__(self, bot_token: str, chat_id: str):
        super().__init__()
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.url = f'https://api.telegram.org/bot{self.bot_token}/sendMessage'

    async def _send_message(self, message):
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(self.url, data={
                    'chat_id': self.chat_id,
                    'text': f'📢 {message}'
                })
        except Exception as e:
            print(f"Error sending log to Telegram: {e}")

    def emit(self, record):
        log_entry = self.format(record)
        try:
            asyncio.create_task(self._send_message(log_entry))
        except RuntimeError:
            pass


def setup_logger(name: str, telegram_logging: bool = False) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler = RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=1024*1024*1,
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, config.LOG_LEVEL))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    if telegram_logging and hasattr(config, 'LOGGER_BOT_TOKEN') and hasattr(config, 'LOGGER_CHAT_ID'):
        if config.LOGGER_BOT_TOKEN and config.LOGGER_CHAT_ID:
            telegram_handler = AsyncTelegramHandler(
                config.LOGGER_BOT_TOKEN,
                config.LOGGER_CHAT_ID
            )
            telegram_handler.setFormatter(formatter)
            telegram_handler.setLevel(logging.INFO)
            logger.addHandler(telegram_handler)

    return logger
