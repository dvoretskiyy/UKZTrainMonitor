import logging
import json
from typing import List, Optional, Dict, Any
from db.database import db
from utils.telegram_logger import setup_logger

logger = setup_logger(__name__, telegram_logging=True)


class UserService:
    @staticmethod
    async def get_or_create_user(
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> Dict[str, Any]:
        user = await db.fetchone(
            "SELECT * FROM users WHERE telegram_id = $1",
            telegram_id
        )
        
        if not user:
            user = await db.fetchone(
                """
                INSERT INTO users (telegram_id, username, first_name, last_name)
                VALUES ($1, $2, $3, $4)
                RETURNING *
                """,
                telegram_id, username, first_name, last_name
            )
            logger.info(
                f"🆕 New user registered: ID={telegram_id}, "
                f"Username=@{username or 'None'}, "
                f"Name={first_name or ''} {last_name or ''}".strip()
            )
        
        return dict(user) if user else None


class RouteService:
    @staticmethod
    async def create_route(
        user_id: int,
        station_from_id: int,
        station_from_name: str,
        station_to_id: int,
        station_to_name: str,
        dates: List[str],
        wagon_classes: List[str]
    ) -> Dict[str, Any]:
        route = await db.fetchone(
            """
            INSERT INTO routes 
            (user_id, station_from_id, station_from_name, station_to_id, station_to_name, dates, wagon_classes)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
            """,
            user_id, station_from_id, station_from_name, station_to_id, station_to_name,
            json.dumps(dates), json.dumps(wagon_classes)
        )
        
        if route:
            await db.execute(
                "INSERT INTO monitorings (route_id) VALUES ($1)",
                route['id']
            )
            logger.info(f"Created route {route['id']} for user {user_id}")
        
        return dict(route) if route else None
    
    @staticmethod
    async def get_user_routes(telegram_id: int) -> List[Dict[str, Any]]:
        user = await db.fetchone(
            "SELECT id FROM users WHERE telegram_id = $1",
            telegram_id
        )
        
        if not user:
            return []
        
        routes = await db.fetchall(
            "SELECT * FROM routes WHERE user_id = $1 ORDER BY created_at DESC",
            user['id']
        )
        
        result = []
        for route in routes:
            route_dict = dict(route)
            route_dict['dates'] = json.loads(route_dict['dates']) if isinstance(route_dict['dates'], str) else route_dict['dates']
            route_dict['wagon_classes'] = json.loads(route_dict['wagon_classes']) if isinstance(route_dict['wagon_classes'], str) else route_dict['wagon_classes']
            result.append(route_dict)
        
        return result
    
    @staticmethod
    async def get_route_by_id(route_id: int) -> Optional[Dict[str, Any]]:
        route = await db.fetchone(
            "SELECT * FROM routes WHERE id = $1",
            route_id
        )
        
        if route:
            route_dict = dict(route)
            route_dict['dates'] = json.loads(route_dict['dates']) if isinstance(route_dict['dates'], str) else route_dict['dates']
            route_dict['wagon_classes'] = json.loads(route_dict['wagon_classes']) if isinstance(route_dict['wagon_classes'], str) else route_dict['wagon_classes']
            return route_dict
        
        return None
    
    @staticmethod
    async def toggle_route_status(route_id: int) -> bool:
        route = await db.fetchone(
            "SELECT is_active FROM routes WHERE id = $1",
            route_id
        )
        
        if route:
            new_status = not route['is_active']
            await db.execute(
                "UPDATE routes SET is_active = $1, updated_at = NOW() WHERE id = $2",
                new_status, route_id
            )
            logger.info(f"Toggled route {route_id} status to {new_status}")
            return True
        
        return False
    
    @staticmethod
    async def delete_route(route_id: int) -> bool:
        result = await db.execute(
            "DELETE FROM routes WHERE id = $1",
            route_id
        )
        
        if result:
            logger.info(f"Deleted route {route_id}")
            return True
        
        return False
    
    @staticmethod
    async def get_all_active_routes() -> List[Dict[str, Any]]:
        routes = await db.fetchall(
            """
            SELECT r.*, u.telegram_id, u.username 
            FROM routes r 
            JOIN users u ON r.user_id = u.id 
            WHERE r.is_active = TRUE
            """
        )
        
        result = []
        for route in routes:
            route_dict = dict(route)
            route_dict['dates'] = json.loads(route_dict['dates']) if isinstance(route_dict['dates'], str) else route_dict['dates']
            route_dict['wagon_classes'] = json.loads(route_dict['wagon_classes']) if isinstance(route_dict['wagon_classes'], str) else route_dict['wagon_classes']
            result.append(route_dict)
        
        return result


class MonitoringService:
    @staticmethod
    async def update_monitoring(
        route_id: int,
        last_result: dict,
        found_tickets: bool
    ) -> None:
        await db.execute(
            """
            UPDATE monitorings 
            SET last_check = NOW(), 
                last_result = $1, 
                check_count = check_count + 1, 
                found_tickets = $2
            WHERE route_id = $3
            """,
            json.dumps(last_result), found_tickets, route_id
        )
        logger.info(f"Updated monitoring for route {route_id}")
