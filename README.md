# OLX-apartments-scraper

A simple Python script that monitors OLX listings (e.g. apartments in Wrocław) and sends **newly refreshed offers** directly to a Discord channel via a webhook.

The script uses the public OLX API endpoint, filters offers refreshed *today*, remembers already-seen listings locally, and notifies only about new ones.

---

## Features

* Fetches apartment listings from OLX using their JSON API
* Filters offers refreshed on the current day
* Detects only **new** listings (no duplicates)
* Sends formatted embeds to Discord via webhook
* Configurable polling interval
* Local persistence using `history.json`
* Safe configuration via `.env`

---

## Project structure

```
OLX-apartments-scraper/
├── main.py            # Main application logic
├── requirements.txt   # Python dependencies
├── README.md          # Project documentation
├── .env               # Local configuration (ignored by git)
├── history.json       # Seen offers cache (ignored by git)
├── .gitignore
└── .venv/             # Virtual environment (ignored by git)
```

---

## Requirements

* Python **3.10+**
* Discord webhook URL

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/olx-apartments-scraper.git
cd olx-apartments-scraper
```

### 2. Create virtual environment

```bash
python -m venv .venv
```

Activate it:

**Linux / macOS**

```bash
source .venv/bin/activate
```

**Windows (PowerShell)**

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Configuration

Create a `.env` file in the project root:

```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/XXX/YYY
POLL_SECONDS=60
SEEN_FILE=history.json
```

Optional:

```env
OLX_URL=https://www.olx.pl/api/v1/offers/?...
```

If `OLX_URL` is not provided, a default Wrocław apartments query is used.

---

## Usage

Run the script:

```bash
python main.py
```

On first run, existing offers are stored as history. New or refreshed listings will be sent to Discord automatically.

---

## Notes

* Discord allows **max 10 embeds per message** (handled automatically)
* Only offers refreshed *today* are considered
* `history.json` is reset manually if needed

---

## Disclaimer

This project is for **educational and personal use only**. OLX is a third‑party service and may change or restrict API access at any time.

---

## License

MIT License
