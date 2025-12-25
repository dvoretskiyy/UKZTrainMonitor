import logging
from typing import List
from pyrogram import Client
from pyrogram.errors import FloodWait, PhoneNumberInvalid, SessionPasswordNeeded
from pyrogram.raw.functions.phone import RequestCall
from pyrogram.raw.types import InputPhoneCall, PhoneCallProtocol
import asyncio
import random
from config import config

logger = logging.getLogger(__name__)


class TelegramCaller:
    def __init__(self):
        self.client = None
        self.is_initialized = False
    
    async def initialize(self):
        if not config.API_ID or not config.API_HASH:
            logger.warning("API_ID or API_HASH not configured. Group calls disabled.")
            return False
        
        try:
            self.client = Client(
                name=config.SESSION_NAME,
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                phone_number=config.PHONE_NUMBER,
                workdir="."
            )
            
            await self.client.start()
            self.is_initialized = True
            logger.info("Pyrogram client initialized successfully")
            return True
            
        except PhoneNumberInvalid:
            logger.error("Invalid phone number")
            return False
        except SessionPasswordNeeded:
            logger.error("2FA password required. Please authorize manually.")
            return False
        except Exception as e:
            logger.error(f"Error initializing Pyrogram client: {e}")
            return False
    
    async def close(self):
        if self.client and self.is_initialized:
            await self.client.stop()
            logger.info("Pyrogram client stopped")
    
    async def make_group_call(self, user_ids: List[int], usernames: List[str] = None) -> bool:
        """
        Initiate voice call to users via Pyrogram
        Note: User must have started conversation with the caller account first
        
        Args:
            user_ids: List of telegram user IDs (fallback)
            usernames: List of usernames (preferred, without @)
        """
        if not self.is_initialized:
            logger.warning("Caller not initialized. Skipping group call.")
            return False
        
        if not usernames:
            usernames = []
        
        try:
            for idx, user_id in enumerate(user_ids):
                try:
                    # Try to use username first if available
                    username = usernames[idx] if idx < len(usernames) and usernames[idx] else None
                    
                    if username:
                        # Use username (remove @ if present)
                        username_clean = username.replace('@', '')
                        logger.info(f"Initiating voice call to @{username_clean}")
                        user = await self.client.get_users(username_clean)
                    else:
                        # Fallback to user_id
                        logger.info(f"Initiating voice call to user {user_id}")
                        user = await self.client.get_users(user_id)
                    
                    # Create call protocol
                    protocol = PhoneCallProtocol(
                        min_layer=65,
                        max_layer=92,
                        udp_p2p=True,
                        udp_reflector=True,
                        library_versions=["2.4.4"]
                    )
                    
                    # Request call via MTProto
                    result = await self.client.invoke(
                        RequestCall(
                            user_id=await self.client.resolve_peer(user.id),
                            random_id=random.randint(1, 2147483647),  # 32-bit int
                            g_a_hash=bytes([0] * 32),  # Placeholder for encryption
                            protocol=protocol,
                            video=False
                        )
                    )
                    
                    logger.info(f"Call initiated successfully to user {user.id} (@{user.username})")
                    
                except FloodWait as e:
                    logger.warning(f"FloodWait for user {user_id}: {e.value} seconds")
                    await asyncio.sleep(e.value)
                except Exception as e:
                    logger.error(f"Error calling user {user_id}: {e}")
                    # Don't send duplicate notification - user already got message via bot
            
            return True
            
        except Exception as e:
            logger.error(f"Error making group call: {e}")
            return False
    
    async def send_call_notification(self, user_id: int, message: str) -> bool:
        if not self.is_initialized:
            logger.warning("Caller not initialized. Skipping notification.")
            return False
        
        try:
            await self.client.send_message(
                chat_id=user_id,
                text=f"📞 {message}"
            )
            logger.info(f"Sent call notification to {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error sending notification to {user_id}: {e}")
            return False


caller_instance = TelegramCaller()
