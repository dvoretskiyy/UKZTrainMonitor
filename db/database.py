import asyncpg
import traceback
from contextlib import asynccontextmanager
from typing import Optional
from config import config


class Database:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool: Optional[asyncpg.Pool] = None
    
    async def init_db(self):
        try:
            self.pool = await asyncpg.create_pool(
                dsn=self.dsn,
                min_size=1,
                max_size=10
            )
            print("[DB] Pool created successfully.")
            await self.create_tables()
        except Exception as e:
            print(f"[DB] Failed to initialize database: {e}")
            traceback.print_exc()
            raise
    
    async def create_tables(self):
        async with self.pool.acquire() as conn:
            try:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        telegram_id BIGINT UNIQUE NOT NULL,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        created_at TIMESTAMP DEFAULT NOW(),
                        is_active BOOLEAN DEFAULT TRUE
                    )
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS routes (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        station_from_id INTEGER NOT NULL,
                        station_from_name TEXT NOT NULL,
                        station_to_id INTEGER NOT NULL,
                        station_to_name TEXT NOT NULL,
                        dates JSONB NOT NULL,
                        wagon_classes JSONB NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS monitorings (
                        id SERIAL PRIMARY KEY,
                        route_id INTEGER REFERENCES routes(id) ON DELETE CASCADE,
                        last_check TIMESTAMP,
                        last_result JSONB,
                        check_count INTEGER DEFAULT 0,
                        found_tickets BOOLEAN DEFAULT FALSE,
                        notification_sent BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                
                print("[DB] Tables created successfully.")
            except Exception:
                traceback.print_exc()
    
    @asynccontextmanager
    async def acquire(self):
        async with self.pool.acquire() as conn:
            yield conn
    
    async def fetchone(self, query: str, *args):
        async with self.pool.acquire() as conn:
            try:
                return await conn.fetchrow(query, *args)
            except Exception:
                traceback.print_exc()
                return None
    
    async def fetchall(self, query: str, *args):
        async with self.pool.acquire() as conn:
            try:
                return await conn.fetch(query, *args)
            except Exception:
                traceback.print_exc()
                return []
    
    async def execute(self, query: str, *args):
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(query, *args)
            except Exception:
                traceback.print_exc()
    
    async def fetchval(self, query: str, *args):
        async with self.pool.acquire() as conn:
            try:
                return await conn.fetchval(query, *args)
            except Exception:
                traceback.print_exc()
                return None
    
    async def close(self):
        if self.pool:
            await self.pool.close()
            print("[DB] Pool closed.")


db = Database(config.DATABASE_URL)
