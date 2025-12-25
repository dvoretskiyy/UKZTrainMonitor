import requests
import cloudscraper 
import uuid


class UKZApiClient:
    def __init__(self):
        self.base_url = "https://app.uz.gov.ua/api/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Origin": "https://booking.uz.gov.ua",
            "Referer": "https://booking.uz.gov.ua/",
            "X-Client-Locale": "uk",
            "X-Session-Id": str(uuid.uuid4()),
            "X-User-Agent": "UZ/2 Web/1 User/guest"
        }
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
    
    async def search_stations(self, search_query):
        response = self.scraper.get(
            f"{self.base_url}stations",
            params={"search": search_query},
            headers=self.headers
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: Status {response.status_code}")
            return None
    
    async def fetch_trains(self, station_from_id, station_to_id, date_str, with_transfers=0):
        response = self.scraper.get(
            f"{self.base_url}v3/trips", 
            params={
                "station_from_id": station_from_id,
                "station_to_id": station_to_id,
                "with_transfers": with_transfers,
                "date": date_str
            },
            headers=self.headers
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: Status {response.status_code}")
            return None


async def main():
    client = UKZApiClient()
    print(await client.search_stations("Шепетівка"))
    print(await client.fetch_trains(2218000, 2218095, "2026-01-04"))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())