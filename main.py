import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import config
from db.database import db
from bot.handlers import start_router, routes_router, my_routes_router
from services.monitor import TicketMonitor
from services.telegram_caller import caller_instance
from utils.telegram_logger import setup_logger

logger = setup_logger(__name__)


async def main():
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables!")
        return
    
    # Initialize database
    logger.info("Initializing database...")
    try:
        await db.init_db()
    except Exception as e:
        logger.error(f"Failed to initialize database. Please check your DATABASE_URL in .env file.")
        logger.error(f"Error: {e}")
        return
    
    # Check if database pool is ready
    if db.pool is None:
        logger.error("Database pool is not initialized. Cannot continue.")
        return
    
    logger.info("Initializing Pyrogram caller...")
    await caller_instance.initialize()
    
    logger.info("Creating bot instance...")
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher(storage=MemoryStorage())
    
    dp.include_router(start_router)
    dp.include_router(routes_router)
    dp.include_router(my_routes_router)
    
    logger.info("Starting ticket monitor...")
    monitor = TicketMonitor(bot)
    monitor_task = asyncio.create_task(monitor.start())
    
    try:
        logger.info("Bot started successfully!")
        await dp.start_polling(bot)
    finally:
        logger.info("Shutting down...")
        await monitor.stop()
        await monitor_task
        await caller_instance.close()
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
