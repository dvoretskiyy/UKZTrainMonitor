import os
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()


class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgres://postgres:postgres@localhost/ukz_monitor"
    )
    
    NOTIFICATION_ACCOUNT: str = os.getenv("NOTIFICATION_ACCOUNT", "@UKZ_Notify_Bot")
    
    WAGON_CLASSES: Dict[str, str] = {
        "Л": "Люкс",
        "К": "Купе",
        "П": "Плацкарт",
        "С1": "Сидячий 1 клас",
        "С2": "Сидячий 2 клас",
        "С3": "Сидячий 3 клас"
    }
    
    DEFAULT_ACTIVE_CLASSES: List[str] = ["Л", "К", "П"]
    
    MONITORING_INTERVAL_SECONDS: int = int(os.getenv("MONITORING_INTERVAL", "300"))
    
    MAX_DATES_TO_SHOW: int = 50
    DATES_PER_PAGE: int = 9
    
    MAX_STATIONS_TO_SHOW: int = 10
    
    TIMEZONE: str = "Europe/Kiev"
    
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = "bot.log"
    
    LOGGER_BOT_TOKEN: str = os.getenv("LOGGER_BOT_TOKEN", "")
    LOGGER_CHAT_ID: str = os.getenv("LOGGER_CHAT_ID", "")
    
    API_ID: int = int(os.getenv("API_ID", "0"))
    API_HASH: str = os.getenv("API_HASH", "")
    PHONE_NUMBER: str = os.getenv("PHONE_NUMBER", "")
    SESSION_NAME: str = os.getenv("SESSION_NAME", "caller_session")
    
    # Proxy settings
    PROXY_ENABLED: bool = os.getenv("PROXY_ENABLED", "false").lower() == "true"
    PROXY_TYPE: str = os.getenv("PROXY_TYPE", "http")  # http or socks5
    PROXY_HOST: str = os.getenv("PROXY_HOST", "")
    PROXY_PORT: int = int(os.getenv("PROXY_PORT", "8000"))
    PROXY_USER: str = os.getenv("PROXY_USER", "")
    PROXY_PASS: str = os.getenv("PROXY_PASS", "")


config = Config()
