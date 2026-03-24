# ✈️ Airport Wait Times PWA

**[🌍 View the Live App Here](https://candidcloud.github.io/airport-wait-times/)**

A Progressive Web App (PWA) that tracks and displays live airport security wait times.

Instead of relying on a traditional paid server or database, this project uses a serverless **Git Scraping** architecture. A Python script runs continuously via GitHub Actions, scrapes the latest data, and commits it directly to a JSON file in this repository. The frontend PWA then fetches that static file, resulting in a completely free, fast, and highly reliable application.

## ✨ Features

* **Live Data:** Security wait times updated automatically every 15 minutes.
* **Progressive Web App:** Installable on iOS and Android home screens.
* **Local Storage:** Automatically remembers your last searched airport.
* **Serverless Backend:** Powered entirely by GitHub Actions and GitHub Pages.

## 📍 Supported Airports

The scraper currently aggregates data for the following airports:

* **ATL** - Hartsfield-Jackson Atlanta
* **AUS** - Austin-Bergstrom
* **BOS** - Boston Logan
* **CLT** - Charlotte Douglas
* **DEN** - Denver International
* **IAD** - Washington Dulles
* **IAH** - George Bush Intercontinental
* **LAX** - Los Angeles International
* **LGA** - LaGuardia
* **MIA** - Miami International
* **MSY** - Louis Armstrong
* **ORD** - Chicago O'Hare
* **OSL** - Oslo Gardermoen
* **PHX** - Phoenix Sky Harbor

## 🏗️ Architecture: How it Works

1. **The Scraper (`scraper.py`):** Uses `requests` and `BeautifulSoup4` to fetch wait times. It hits direct APIs when available (like PHX) and parses aggregator HTML for airports that hide their data.
2. **The Automation (`scrape.yml`):** A GitHub Action runs the Python script on a cron schedule. If the data has changed, the bot amends its previous commit to keep the repository history clean without spamming commits.
3. **The Database (`data.json`):** The single source of truth. It acts as a static JSON API for the frontend.
4. **The Frontend (`index.html`):** A vanilla JavaScript app that fetches the JSON, renders the UI, and utilizes a Service Worker (`sw.js`) to cache assets for offline loading and PWA installation.
