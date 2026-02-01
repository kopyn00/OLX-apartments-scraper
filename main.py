import os
import time
import json
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

# --- konfiguracja z .env (pod importami, jak prosiłeś) ---
load_dotenv()

OLX_URL = os.getenv("OLX_URL", "").strip()
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
SEEN_FILE = os.getenv("SEEN_FILE", "history.json").strip()
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "60"))

if not OLX_URL or not DISCORD_WEBHOOK_URL:
    raise SystemExit("Brak OLX_URL lub DISCORD_WEBHOOK_URL w pliku .env")


def _parse_iso_datetime(dt_str: str):
    """
    OLX zwykle zwraca ISO z 'Z' (UTC). Zamieniamy na +00:00 i parsujemy.
    Zwraca datetime lub None.
    """
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        return None


def extract_today_ads(data: dict):
    """
    Zwraca listę ogłoszeń odświeżonych dzisiaj (wg czasu lokalnego).
    """
    today = datetime.now().date()
    results = []

    for offer in data.get("data", []):
        refreshed_str = offer.get("last_refresh_time")
        refreshed_dt = _parse_iso_datetime(refreshed_str)

        if not refreshed_dt:
            continue

        # Porównujemy po dacie lokalnej (tak jak w Twoim pierwotnym kodzie)
        if refreshed_dt.astimezone().date() != today:
            continue

        url = offer.get("url")
        title = (offer.get("title") or "").strip()
        params = offer.get("params", [])

        cena = "-"
        czynsz = "-"

        for p in params:
            if p.get("name") == "Cena":
                cena = (p.get("value") or {}).get("label", "-")
            elif p.get("name") == "Czynsz (dodatkowo)":
                czynsz = (p.get("value") or {}).get("label", "-")

        if url:
            results.append(
                {
                    "url": url,
                    "title": title,
                    "last_refresh_time": refreshed_str,
                    "cena": cena,
                    "czynsz": czynsz,
                }
            )

    return results


def get_offers_from_olx(url: str):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            print(f"Blad pobierania danych: HTTP {resp.status_code}")
            return []
        return extract_today_ads(resp.json())
    except Exception as e:
        print(f"Wyjatek podczas pobierania danych: {e}")
        return []


def send_ads_to_discord(webhook_url: str, ads: list[dict]):
    """
    Discord: max 10 embedów na wiadomość.
    Bez emoji w polach (wg preferencji).
    """
    embeds = []
    for ad in ads[:10]:
        embed = {
            "title": ad["title"] or "Nowe ogloszenie",
            "url": ad["url"],
            "color": 5814783,
            "fields": [
                {"name": "Cena", "value": ad.get("cena", "-"), "inline": True},
                {"name": "Czynsz", "value": ad.get("czynsz", "-"), "inline": True},
                {"name": "Odswiezone", "value": ad.get("last_refresh_time", "-"), "inline": False},
            ],
        }
        embeds.append(embed)

    payload = {
        "content": f"Nowe ogloszenia OLX: {len(ads)}",
        "embeds": embeds,
        "allowed_mentions": {"parse": []},
    }

    headers = {"Content-Type": "application/json"}
    try:
        resp = requests.post(webhook_url, data=json.dumps(payload), headers=headers, timeout=10)
        if resp.status_code in (200, 204):
            print("Wyslano na Discord.")
        else:
            print(f"Blad wysylania: HTTP {resp.status_code}")
    except Exception as e:
        print(f"Wyjatek podczas wysylania: {e}")


def load_seen_ads():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return []


def save_seen_ads(ads: list[dict]):
    try:
        with open(SEEN_FILE, "w", encoding="utf-8") as f:
            json.dump(ads, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Nie mozna zapisac {SEEN_FILE}: {e}")


def _ads_to_url_set(ads: list[dict]):
    return {a.get("url") for a in ads if a.get("url")}


def main():
    previous_ads = load_seen_ads()
    previous_urls = _ads_to_url_set(previous_ads)

    print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not previous_ads:
        current_ads = get_offers_from_olx(OLX_URL)
        save_seen_ads(current_ads)
        previous_ads = current_ads
        previous_urls = _ads_to_url_set(previous_ads)
        print("Zainicjowano pamiec dzisiejszymi ogloszeniami.")
    else:
        print("Skrypt uruchomiony. Oczekiwanie na nowe ogloszenia...")

    while True:
        current_ads = get_offers_from_olx(OLX_URL)
        new_ads = [ad for ad in current_ads if ad.get("url") and ad["url"] not in previous_urls]

        if new_ads:
            send_ads_to_discord(DISCORD_WEBHOOK_URL, new_ads)
            previous_ads.extend(new_ads)
            previous_urls.update(_ads_to_url_set(new_ads))
            save_seen_ads(previous_ads)

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
