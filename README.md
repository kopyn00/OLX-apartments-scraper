# OLX Apartments Scraper

Monitoruje ogłoszenia na OLX i wysyła nowe oferty na **Discord** i/lub **Telegram**.

Używa publicznego API OLX, śledzi już widziane ogłoszenia lokalnie i powiadamia tylko o nowych.

---

## Funkcje

- Pobiera ogłoszenia przez JSON API OLX
- Wykrywa tylko **nowe** ogłoszenia (bez duplikatów)
- Powiadomienia na **Discord** (embed) i/lub **Telegram**
- Kanały włączane/wyłączane osobno flagami w `.env`
- Wyszukiwanie w promieniu od wybranego miasta (`DIST` + `STRATEGY`)
- Wszystkie filtry (cena, metraż, pokoje, typ budynku) konfigurowane w `.env`
- Lokalny cache w `history.json`

---

## Struktura projektu

```
OLX-apartments-scraper/
├── main.py               # Logika aplikacji
├── requirements.txt      # Zależności
├── .env.example          # Przykładowa konfiguracja (skopiuj do .env)
├── start.sh              # Skrypt uruchomieniowy (Linux / Raspberry Pi)
├── olx-scraper.service   # Plik systemd do autostartu
├── .gitignore
└── README.md
```

---

## Wymagania

- Python 3.10+
- Discord Webhook URL i/lub Telegram Bot Token

---

## Instalacja

```bash
git clone https://github.com/your-username/olx-apartments-scraper.git
cd olx-apartments-scraper
python -m venv .venv
```

Aktywuj środowisko:

```powershell
# Windows
.venv\Scripts\Activate.ps1
```

```bash
# Linux / macOS
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

---

## Konfiguracja

Skopiuj `.env.example` do `.env` i uzupełnij:

```bash
cp .env.example .env
```

### Lokalizacja

| Parametr | Opis |
| --- | --- |
| `CITY_ID` | ID miasta z OLX (znajdziesz w źródle strony szukając `city_id=`) |
| `REGION_ID` | ID regionu (województwa) |
| `DIST` | Promień wyszukiwania w km |
| `STRATEGY` | Ustaw `extended_distance` — wymagane gdy używasz `DIST` |

### Filtry

| Parametr | Przykład | Opis |
| --- | --- | --- |
| `PRICE_FROM` / `PRICE_TO` | `2000` / `3500` | Zakres ceny (PLN) |
| `AREA_FROM` / `AREA_TO` | `40` / `70` | Zakres powierzchni (m²) |
| `ROOMS` | `two,three,four` | Liczba pokoi (`one` `two` `three` `four`) |
| `BUILTTYPES` | `blok,kamienica` | Typ budynku (puste = bez filtra) |

### Powiadomienia

```env
DISCORD_ENABLED=true
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/XXX/YYY

TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=123456789:AAH-xxx
TELEGRAM_CHAT_ID=123456789
```

Swój `TELEGRAM_CHAT_ID` znajdziesz wysyłając `/start` do [@userinfobot](https://t.me/userinfobot).

---

## Uruchomienie

### Windows

```powershell
.venv\Scripts\Activate.ps1
python main.py
```

### Linux / Raspberry Pi

```bash
chmod +x start.sh
./start.sh
```

Skrypt automatycznie tworzy virtualenv i instaluje zależności przy pierwszym uruchomieniu.

### Autostart na Raspberry Pi (systemd)

```bash
sudo cp olx-scraper.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable olx-scraper
sudo systemctl start olx-scraper
```

Jeśli Twój użytkownik nie nazywa się `pi`, zmień `User=` i ścieżki w `olx-scraper.service`.

Logi na żywo:

```bash
journalctl -u olx-scraper -f
```

---

### Ogólne

Przy pierwszym uruchomieniu aktualne ogłoszenia są wysyłane i zapisywane jako punkt startowy. Kolejne uruchomienia wysyłają tylko nowe.

Żeby zresetować historię:

```bash
rm history.json
```

---

## Zastrzeżenie

Projekt do użytku prywatnego i edukacyjnego. OLX może zmienić lub ograniczyć dostęp do API w dowolnym momencie.

---

## Licencja

MIT
