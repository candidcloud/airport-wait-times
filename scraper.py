import json
import datetime
import requests
import re
from bs4 import BeautifulSoup
import time


class AirportScraper:
    """
    Base class for all airport scrapers to ensure a consistent structure.
    Every new airport you add should inherit from this class.
    """

    def __init__(self, code):
        self.code = code
        # Standard browser headers to ensure APIs don't block us for missing a User-Agent
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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
            url = "https://api.phx.aero/avn-wait-times/raw?Key=4f85fe2ef5a240d59809b63de94ef536"

            # Fetch the data using standard requests (bypassing heavy web browsers)
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                wait_times = []

                # Loop through the 'current' array in the JSON response
                for item in data.get("current", []):
                    wait_times.append(
                        {
                            "name": item.get("queueName", "Unknown Checkpoint"),
                            # We use 'projectedMaxWaitMinutes' to be conservative with estimates
                            "waitMinutes": item.get("projectedMaxWaitMinutes", 0),
                        }
                    )

                return wait_times
            else:
                print(f"PHX API returned status code: {response.status_code}")
                return []

        except Exception as e:
            print(f"Error scraping PHX: {e}")
            return []


class QsensorScraper(AirportScraper):
    """
    A dynamic scraper that can handle ANY airport tracked by Qsensor.
    Just pass in the airport code, their specific URL slug, and an optional suffix.
    """

    def __init__(self, code, url_slug, suffix="-tsa-wait-times"):
        super().__init__(code)
        # Dynamically build the URL based on the slug and suffix provided
        self.url = f"https://qsensor.co/airports/{url_slug}{suffix}/"

    def scrape(self):
        try:
            import cloudscraper
            from bs4 import BeautifulSoup
            import re

            # Use cloudscraper instead of requests to bypass anti-bot security (like Cloudflare)
            scraper = cloudscraper.create_scraper()
            response = scraper.get(self.url, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                # 1. Strip away ALL HTML tags and replace them with spaces for clean parsing
                page_text = soup.get_text(separator=" ")

                # 2. Remove rogue periods and commas so the regex never trips
                page_text = page_text.replace(".", " ").replace(",", " ")

                wait_times = []

                # 3. Search the now-clean text for the specific data pattern
                pattern = r"((?:Terminal|Security|Fast Track|Gate|Checkpoint|Concourse|Domestic|International|Zone)\s*[A-Za-z0-9\s\-]*?)(?:\s+Queues:\s*\d+)?\s+(\d+)\s*mins?\s*wait"

                for match in re.finditer(pattern, page_text, re.IGNORECASE):
                    # Extract the raw terminal name and the wait time minutes
                    raw_name = match.group(1).strip()
                    minutes = match.group(2).strip()

                    # 4. Clean up the "All Terminals" over-catch caused by greedy regex
                    if "All Terminals" in raw_name:
                        name = "All Terminals"
                    else:
                        name = raw_name

                    # 5. Safety Net: Filter out rogue paragraphs (if a name is too long, it's not a terminal)
                    if len(name) < 40:
                        wait_times.append({"name": name, "waitMinutes": minutes})

                # 6. Remove any accidental duplicates before returning
                unique_times = {v["name"]: v for v in wait_times}.values()
                return list(unique_times)
            else:
                print(f"{self.code} returned status code: {response.status_code}")
                return []

        except Exception as e:
            print(f"Error scraping {self.code}: {e}")
            return []


class ScraperManager:
    """
    Manages the execution of all registered airport scrapers and saves the results.
    """

    def __init__(self):
        self.scrapers = [
            # Custom direct-API scraper
            PHX_Scraper(),
            # Dynamic aggregator scrapers
            QsensorScraper("LAX", "los-angeles-international-airport"),
            QsensorScraper("IAD", "washington-dulles-international-airport"),
            QsensorScraper("IAH", "houston-george-bush-intercontinental-airport"),
            QsensorScraper("LGA", "new-york-laguardia-airport"),
            QsensorScraper("ATL", "hartsfield-jackson-atlanta-international-airport"),
            QsensorScraper("MIA", "miami-international-airport"),
            QsensorScraper("DEN", "denver-international-airport"),
            QsensorScraper("ORD", "chicago-ohare-international-airport"),
            QsensorScraper("CLT", "charlotte-douglas-international-airport"),
            QsensorScraper("BOS", "boston-logan-international-airport"),
            QsensorScraper("AUS", "austin-bergstrom-international-airport"),
            QsensorScraper("MSY", "louis-armstrong-new-orleans-international-airport"),
            QsensorScraper("OSL", "oslo-gardermoen-airport", "-security-wait-times"),
            QsensorScraper("BWI", "baltimore-washington-international-airport"),
            QsensorScraper("RSW", "southwest-florida-international-airport"),
        ]

    def run_all(self):
        import os

        print("Starting Airport Scraper...")

        # 1. Load the existing data so we don't accidentally overwrite good data with empty lists
        existing_data = {}
        if os.path.exists("data.json"):
            try:
                with open("data.json", "r") as f:
                    existing_data = json.load(f)
            except Exception:
                pass

        # 2. Establish the global check time in strict UTC
        current_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

        final_data = {"LAST_UPDATED": current_time}

        # 3. Run each scraper
        for scraper in self.scrapers:
            new_data = scraper.scrape()

            if new_data:
                # SUCCESS: Save the fresh data with a fresh individual timestamp
                final_data[scraper.code] = {
                    "last_updated": current_time,
                    "data": new_data,
                }
                print(f"✅ Fetched fresh data for {scraper.code}")
            else:
                # FAIL: Get the old data from the previous run
                old_entry = existing_data.get(scraper.code)

                # Make sure the old data is actually in our new dictionary format before rescuing it
                if old_entry and isinstance(old_entry, dict) and old_entry.get("data"):
                    final_data[scraper.code] = old_entry
                    print(f"⚠️ Scrape failed for {scraper.code}, rescuing stale data.")
                else:
                    # No old data exists either, record it as truly empty
                    final_data[scraper.code] = {
                        "last_updated": current_time,
                        "data": [],
                    }
                    print(f"⚠️ No data returned or rescued for {scraper.code}")
            time.sleep(0.1)

        # 4. Save the data to a local JSON file
        with open("data.json", "w") as f:
            json.dump(final_data, f, indent=4)

        print("Successfully saved to data.json")


if __name__ == "__main__":
    manager = ScraperManager()
    manager.run_all()
