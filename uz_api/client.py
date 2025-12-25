import uuid
import logging
import asyncio
import random
from typing import List, Optional, Dict, Any
import cloudscraper
from datetime import datetime, timedelta
from config import config


logger = logging.getLogger(__name__)


class UZApiException(Exception):
    pass


class UZApiClient:
    def __init__(self):
        self.base_url = "https://app.uz.gov.ua/api/"
        self.session_id = str(uuid.uuid4())
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        # Configure proxy if enabled
        self.proxies = None
        if config.PROXY_ENABLED and config.PROXY_HOST:
            proxy_url = f"{config.PROXY_TYPE}://{config.PROXY_USER}:{config.PROXY_PASS}@{config.PROXY_HOST}:{config.PROXY_PORT}"
            self.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            logger.info(f"Proxy enabled: {config.PROXY_TYPE}://{config.PROXY_HOST}:{config.PROXY_PORT}")
    
    def _regenerate_session_id(self):
        """Regenerate session ID when getting 441 error"""
        old_session = self.session_id
        self.session_id = str(uuid.uuid4())
        logger.info(f"Regenerated session ID: {old_session[:8]}... -> {self.session_id[:8]}...")
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "uk,ru-RU;q=0.9,ru;q=0.8,en-US;q=0.7,en;q=0.6",
            "Accept-Encoding": "gzip, deflate, br",
            "Origin": "https://booking.uz.gov.ua",
            "Referer": "https://booking.uz.gov.ua/",
            "X-Client-Locale": "uk",
            "X-Session-Id": self.session_id,
            "X-User-Agent": "UZ/2 Web/1 User/guest",
            "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site"
        }
    
    async def search_stations(self, search_query: str) -> List[Dict[str, Any]]:
        try:
            response = self.scraper.get(
                f"{self.base_url}stations",
                params={"search": search_query},
                headers=self._get_headers(),
                proxies=self.proxies,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Found {len(data)} stations for query: {search_query}")
                return data
            else:
                logger.error(f"Station search failed with status {response.status_code}")
                raise UZApiException(f"API returned status {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error searching stations: {e}")
            raise UZApiException(f"Failed to search stations: {str(e)}")
    
    async def fetch_trains(
        self, 
        station_from_id: int, 
        station_to_id: int, 
        date_str: str, 
        with_transfers: int = 0,
        retry_on_441: bool = True
    ) -> Optional[Dict[str, Any]]:
        try:
            response = self.scraper.get(
                f"{self.base_url}v3/trips", 
                params={
                    "station_from_id": station_from_id,
                    "station_to_id": station_to_id,
                    "with_transfers": with_transfers,
                    "date": date_str
                },
                headers=self._get_headers(),
                proxies=self.proxies,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Fetched trains for {date_str}: {station_from_id} -> {station_to_id}")
                return data
            elif response.status_code == 441 and retry_on_441:
                logger.warning(f"Got 441 error, regenerating session ID and retrying...")
                self._regenerate_session_id()
                # Retry once with new session ID
                return await self.fetch_trains(
                    station_from_id, 
                    station_to_id, 
                    date_str, 
                    with_transfers, 
                    retry_on_441=False
                )
            else:
                logger.error(f"Train fetch failed with status {response.status_code}")
                logger.error(f"Response body: {response.text[:500]}")
                logger.error(f"Request URL: {response.url}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching trains: {e}")
            return None
    
    async def check_tickets_availability(
        self,
        station_from_id: int,
        station_to_id: int,
        dates: List[str],
        wagon_classes: List[str]
    ) -> Dict[str, Any]:
        results = {
            "has_tickets": False,
            "dates_with_tickets": [],
            "details": {}
        }
        
        for idx, date in enumerate(dates):
            trains_data = await self.fetch_trains(
                station_from_id, 
                station_to_id, 
                date
            )
            
            # Add delay between date checks to avoid rate limiting
            if idx < len(dates) - 1:
                await asyncio.sleep(random.uniform(1, 2))
            
            if trains_data and "direct" in trains_data:
                for trip in trains_data["direct"]:
                    if "train" in trip and "wagon_classes" in trip["train"]:
                        for wagon in trip["train"]["wagon_classes"]:
                            wagon_type = wagon.get("id", "")
                            free_seats = wagon.get("free_seats", 0)
                            
                            if wagon_type in wagon_classes and free_seats > 0:
                                results["has_tickets"] = True
                                if date not in results["dates_with_tickets"]:
                                    results["dates_with_tickets"].append(date)
                                
                                if date not in results["details"]:
                                    results["details"][date] = []
                                
                                results["details"][date].append({
                                    "train_number": trip["train"].get("number"),
                                    "depart_at": trip.get("depart_at"),
                                    "arrive_at": trip.get("arrive_at"),
                                    "station_from": trip.get("station_from"),
                                    "station_to": trip.get("station_to"),
                                    "wagon_type": wagon_type,
                                    "wagon_name": wagon.get("name"),
                                    "free_seats": free_seats,
                                    "price": wagon.get("price")
                                })
        
        return results
    
    def generate_dates(self, start_date: str, days: int = 50) -> List[str]:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            dates = []
            for i in range(days):
                date = start + timedelta(days=i)
                dates.append(date.strftime("%Y-%m-%d"))
            return dates
        except Exception as e:
            logger.error(f"Error generating dates: {e}")
            return []
