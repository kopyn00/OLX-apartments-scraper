import os
import time
import json
import requests
from datetime import datetime
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()


def _env(key, default=""):
    return os.getenv(key, default).strip()


def _env_int(key, default):
    try:
        return int(_env(key) or default)
    except ValueError:
        return default


def _env_list(key):
    raw = _env(key)
    return [v.strip() for v in raw.split(",") if v.strip()] if raw else []


DISCORD_ENABLED = _env("DISCORD_ENABLED", "true").lower() == "true"
DISCORD_WEBHOOK_URL = _env("DISCORD_WEBHOOK_URL")
TELEGRAM_ENABLED = _env("TELEGRAM_ENABLED", "true").lower() == "true"
TELEGRAM_BOT_TOKEN = _env("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = _env("TELEGRAM_CHAT_ID")
SEEN_FILE = _env("SEEN_FILE", "history.json")
POLL_SECONDS = _env_int("POLL_SECONDS", 60)

if not DISCORD_WEBHOOK_URL and not TELEGRAM_BOT_TOKEN:
    raise SystemExit("Brak DISCORD_WEBHOOK_URL lub TELEGRAM_BOT_TOKEN w pliku .env")


def build_olx_url():
    city_id = _env("CITY_ID")
    region_id = _env("REGION_ID")
    dist = _env("DIST")

    if not city_id or not region_id:
        raise SystemExit("Brak CITY_ID lub REGION_ID w pliku .env")

    params = {
        "sort_by": _env("SORT_BY", "created_at:desc"),
        "category_id": 15,
        "city_id": city_id,
        "region_id": region_id,
        "limit": _env_int("LIMIT", 40),
    }

    strategy = _env("STRATEGY")
    if dist:
        params["dist"] = dist
    if strategy:
        params["strategy"] = strategy

    price_from = _env("PRICE_FROM")
    price_to = _env("PRICE_TO")
    area_from = _env("AREA_FROM")
    area_to = _env("AREA_TO")

    if price_from:
        params["filter_float_price:from"] = price_from
    if price_to:
        params["filter_float_price:to"] = price_to
    if area_from:
        params["filter_float_m:from"] = area_from
    if area_to:
        params["filter_float_m:to"] = area_to

    for i, room in enumerate(_env_list("ROOMS")):
        params[f"filter_enum_rooms[{i}]"] = room

    for i, bt in enumerate(_env_list("BUILTTYPES")):
        params[f"filter_enum_builttype[{i}]"] = bt

    return "https://www.olx.pl/api/v1/offers/?" + urlencode(params)


OLX_URL = build_olx_url()


def _parse_iso_datetime(dt_str):
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        return None


def _param_label(params, key):
    for p in params:
        if p.get("key") == key:
            return (p.get("value") or {}).get("label", "-")
    return "-"


def extract_today_ads(data):
    today = datetime.now().date()
    results = []

    for offer in data.get("data", []):
        refreshed_str = offer.get("last_refresh_time")
        refreshed_dt = _parse_iso_datetime(refreshed_str)

        if not refreshed_dt:
            continue
        if refreshed_dt.astimezone().date() != today:
            continue

        url = offer.get("url")
        if not url:
            continue

        params = offer.get("params", [])
        location = offer.get("location", {})
        city_name = (location.get("city") or {}).get("name", "-")

        results.append({
            "url": url,
            "title": (offer.get("title") or "").strip(),
            "last_refresh_time": refreshed_str,
            "cena": _param_label(params, "price"),
            "czynsz": _param_label(params, "rent"),
            "powierzchnia": _param_label(params, "m"),
            "pokoje": _param_label(params, "rooms"),
            "typ_budynku": _param_label(params, "builttype"),
            "miasto": city_name,
        })

    return results


def get_offers_from_olx(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            print(f"Blad HTTP {resp.status_code}")
            return []
        return extract_today_ads(resp.json())
    except Exception as e:
        print(f"Wyjatek: {e}")
        return []


def send_ads_to_discord(webhook_url, ads):
    embeds = []
    for ad in ads[:10]:
        embeds.append({
            "title": ad["title"] or "Nowe ogloszenie",
            "url": ad["url"],
            "color": 5814783,
            "fields": [
                {"name": "Cena", "value": ad["cena"], "inline": True},
                {"name": "Czynsz", "value": ad["czynsz"], "inline": True},
                {"name": "Powierzchnia", "value": ad["powierzchnia"], "inline": True},
                {"name": "Pokoje", "value": ad["pokoje"], "inline": True},
                {"name": "Typ budynku", "value": ad["typ_budynku"], "inline": True},
                {"name": "Miasto", "value": ad["miasto"], "inline": True},
                {"name": "Odswiezono", "value": ad["last_refresh_time"], "inline": False},
            ],
        })

    payload = {
        "content": f"🔔 Nowe ogloszenia OLX ({len(ads)})",
        "embeds": embeds,
        "allowed_mentions": {"parse": []},
    }

    try:
        resp = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if resp.status_code in (200, 204):
            print("Wyslano na Discord.")
        else:
            print(f"Blad wysylania: HTTP {resp.status_code}")
    except Exception as e:
        print(f"Wyjatek Discord: {e}")


def send_ads_to_telegram(token, chat_id, ads):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    for ad in ads:
        text = (
            f"🔔 <b>{ad['title'] or 'Nowe ogloszenie'}</b>\n"
            f"<a href=\"{ad['url']}\">{ad['url']}</a>\n\n"
            f"Cena: <b>{ad['cena']}</b>  |  Czynsz: {ad['czynsz']}\n"
            f"Powierzchnia: {ad['powierzchnia']}  |  Pokoje: {ad['pokoje']}\n"
            f"Typ budynku: {ad['typ_budynku']}  |  Miasto: {ad['miasto']}\n"
            f"Odswiezono: {ad['last_refresh_time']}"
        )
        try:
            resp = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)
            if resp.status_code == 200:
                print("Wyslano na Telegram.")
            else:
                print(f"Blad Telegram: HTTP {resp.status_code} — {resp.text}")
        except Exception as e:
            print(f"Wyjatek Telegram: {e}")


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


def save_seen_ads(ads):
    try:
        with open(SEEN_FILE, "w", encoding="utf-8") as f:
            json.dump(ads, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Nie mozna zapisac {SEEN_FILE}: {e}")


def main():
    print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"URL: {OLX_URL}")

    previous_ads = load_seen_ads()
    previous_urls = {a.get("url") for a in previous_ads if a.get("url")}

    def notify(ads):
        if DISCORD_ENABLED and DISCORD_WEBHOOK_URL:
            send_ads_to_discord(DISCORD_WEBHOOK_URL, ads)
        if TELEGRAM_ENABLED and TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            send_ads_to_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ads)

    if not previous_ads:
        current_ads = get_offers_from_olx(OLX_URL)
        if current_ads:
            notify(current_ads)
        save_seen_ads(current_ads)
        previous_ads = current_ads
        previous_urls = {a.get("url") for a in previous_ads if a.get("url")}
        print(f"Zainicjowano pamiec: {len(previous_ads)} ogloszen.")
    else:
        print(f"Wczytano {len(previous_ads)} znanych ogloszen. Oczekiwanie na nowe...")

    while True:
        current_ads = get_offers_from_olx(OLX_URL)
        new_ads = [ad for ad in current_ads if ad.get("url") not in previous_urls]

        if new_ads:
            print(f"Znaleziono {len(new_ads)} nowych ogloszen.")
            notify(new_ads)
            previous_ads.extend(new_ads)
            previous_urls.update(ad["url"] for ad in new_ads)
            save_seen_ads(previous_ads)

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
