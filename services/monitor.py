import asyncio
import logging
import random
from datetime import datetime
from aiogram import Bot
from uz_api.client import UZApiClient
from services.db_service import RouteService, MonitoringService
from services.telegram_caller import caller_instance
from config import config
from utils.telegram_logger import setup_logger

logger = setup_logger(__name__)


class TicketMonitor:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.uz_client = UZApiClient()
        self.is_running = False
    
    async def start(self):
        self.is_running = True
        logger.info("Ticket monitoring started")
        
        while self.is_running:
            try:
                await self.check_all_routes()
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            await asyncio.sleep(config.MONITORING_INTERVAL_SECONDS)
    
    async def stop(self):
        self.is_running = False
        logger.info("Ticket monitoring stopped")
    
    async def check_all_routes(self):
        routes = await RouteService.get_all_active_routes()
        logger.info(f"Checking {len(routes)} active routes")
        
        for idx, route in enumerate(routes):
            try:
                await self.check_route(route)
                
                # Add delay between routes to avoid rate limiting
                if idx < len(routes) - 1:  # Don't delay after last route
                    delay = random.uniform(2, 5)  # Random delay 2-5 seconds
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                logger.error(f"Error checking route {route.id}: {e}")
    
    async def check_route(self, route):
        result = await self.uz_client.check_tickets_availability(
            station_from_id=route['station_from_id'],
            station_to_id=route['station_to_id'],
            dates=route['dates'],
            wagon_classes=route['wagon_classes']
        )
        print(result)
        
        await MonitoringService.update_monitoring(
            route_id=route['id'],
            last_result=result,
            found_tickets=result["has_tickets"]
        )
        
        if result["has_tickets"]:
            logger.info(f"Found tickets for route {route['id']}")
            await self.notify_user(route, result)
    
    async def notify_user(self, route, result):
        try:
            telegram_id = route.get('telegram_id')
            username = route.get('username')
            
            dates_str = ", ".join(result["dates_with_tickets"][:5])
            if len(result["dates_with_tickets"]) > 5:
                dates_str += f" ... (+{len(result['dates_with_tickets'])-5})"
            
            message = (
                f"<b>🎉 Знайдено квитки!</b>\n\n"
                f"🚉 Маршрут: <b>{route['station_from_name']} → {route['station_to_name']}</b>\n"
                f"📅 Дати: <b>{dates_str}</b>\n\n"
                f"<blockquote>Деталі:\n"
            )
            
            for date, tickets in list(result["details"].items())[:3]:
                message += f"\n📆 {date}:\n"
                for ticket in tickets[:2]:
                    depart_time = datetime.fromtimestamp(ticket['depart_at']).strftime('%H:%M')
                    arrive_time = datetime.fromtimestamp(ticket['arrive_at']).strftime('%H:%M')
                    message += (
                        f"  \n🚂 Поїзд {ticket['train_number']}\n"
                        f"  ⏰ {depart_time} → {arrive_time}\n"
                        f"  🎫 {ticket['wagon_name']}: {ticket['free_seats']} місць, {ticket['price']/100:.0f} грн\n"
                    )
            
            message += "</blockquote>\n"
            message += f"\n💬 Здійснюється дзвінок..."
            
            await self.bot.send_message(
                chat_id=telegram_id,
                text=message
            )
            
            # Attempt to make voice call using username (preferred) or telegram_id
            if caller_instance.is_initialized:
                await caller_instance.make_group_call(
                    user_ids=[telegram_id],
                    usernames=[username] if username else []
                )
            else:
                # If caller not initialized, send reminder message
                await self.bot.send_message(
                    chat_id=telegram_id,
                    text=f"⚠️ Щоб отримувати голосові дзвінки, напишіть сервісному аккаунту {config.NOTIFICATION_ACCOUNT}"
                )
            
            logger.info(f"Sent notification to user {telegram_id} for route {route['id']}")
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
