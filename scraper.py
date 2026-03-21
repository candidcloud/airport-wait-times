import json
import datetime
import requests

class AirportScraper:
    """
    Base class for all airport scrapers to ensure a consistent structure.
    Every new airport you add should inherit from this class.
    """
    def __init__(self, code):
        self.code = code
        # Standard browser headers to ensure APIs don't block us for missing a User-Agent
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def scrape(self):
        """Must be overridden by specific airport classes."""
        raise NotImplementedError("Subclasses must implement the scrape method.")

class PHX_Scraper(AirportScraper):
    """
    Phoenix Sky Harbor (PHX) - Direct API Integration
    """
    def __init__(self):
        super().__init__("PHX")

    def scrape(self):
        try:
            # The hidden API endpoint intercepted from the live website
            url = 'https://api.phx.aero/avn-wait-times/raw?Key=4f85fe2ef5a240d59809b63de94ef536'
            
            # Fetch the data using standard requests (bypassing heavy web browsers)
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                wait_times = []
                
                # Loop through the 'current' array in the JSON response
                for item in data.get('current', []):
                    wait_times.append({
                        "name": item.get('queueName', 'Unknown Checkpoint'),
                        # We use 'projectedMaxWaitMinutes' to be conservative with estimates
                        "waitMinutes": item.get('projectedMaxWaitMinutes', 0)
                    })
                
                return wait_times
            else:
                print(f"PHX API returned status code: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error scraping PHX: {e}")
            return []

class ScraperManager:
    """
    Manages the execution of all registered airport scrapers and saves the results.
    """
    def __init__(self):
        # Register active scrapers here. Add more (e.g., ATL_Scraper()) to this list later.
        self.scrapers = [
            PHX_Scraper()
        ]

    def run_all(self):
        print("Starting Airport Scraper...")
        
        # Initialize the final dictionary with an ISO timestamp
        final_data = {
            "LAST_UPDATED": datetime.datetime.now().isoformat()
        }
        
        # Run each scraper and append its data to the dictionary
        for scraper in self.scrapers:
            data = scraper.scrape()
            final_data[scraper.code] = data
            
            if data:
                print(f"✅ Fetched data for {scraper.code}")
            else:
                print(f"⚠️ No data returned for {scraper.code}")

        # Save the aggregated data to a local JSON file for the frontend to read
        with open('data.json', 'w') as f:
            json.dump(final_data, f, indent=4)
            
        print("Successfully saved to data.json")

if __name__ == "__main__":
    manager = ScraperManager()
    manager.run_all()