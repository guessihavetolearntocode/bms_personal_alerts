# main.py  (single-run version for GitHub Actions)
import os, json, requests
from datetime import datetime
from twilio.rest import Client as TwilioClient

# Config
MOVIES_FILE = "movies.json"
STATE_FILE = "called_state.json"

# Load env
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM")
TO_PHONE = os.getenv("TO_PHONE")

# Utilities: load/save state
def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# Notifications
def send_telegram(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram not configured, skipping")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
        print("Telegram status:", resp.status_code)
    except Exception as e:
        print("Telegram error:", e)

def make_call():
    if not (TWILIO_SID and TWILIO_TOKEN and TWILIO_FROM and TO_PHONE):
        print("Twilio not configured, skipping call")
        return
    try:
        client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)
        call = client.calls.create(to=TO_PHONE, from_=TWILIO_FROM, url="http://demo.twilio.com/docs/voice.xml")
        print("Twilio call SID:", getattr(call, "sid", "<no-sid>"))
    except Exception as e:
        print("Twilio error:", e)

# Check page simple function
def theatre_live(url, theatre):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if r.status_code != 200:
            print(f"Failed to fetch {url}: {r.status_code}")
            return False
        return theatre.lower() in r.text.lower()
    except Exception as e:
        print("Request error for", url, e)
        return False

def main_once():
    print("Starting single-run check:", datetime.utcnow().isoformat())
    state = load_state()           # existing alerted keys
    movies = json.load(open(MOVIES_FILE, "r"))

    any_alerts = False

    for item in movies:
        movie = item.get("movie")
        url = item.get("url")
        theatres = item.get("theatres", [])

        for theatre in theatres:
            key = f"{movie}||{theatre}"
            live = theatre_live(url, theatre)
            print(f"Checked: {movie} @ {theatre} -> {'LIVE' if live else 'not live'}")

            if live:
                if key in state:
                    print("Already alerted:", key)
                    continue
                # send notifications
                msg = f"🎟 TICKETS LIVE!\nMovie: {movie}\nTheatre: {theatre}\n{url}"
                send_telegram(msg)
                make_call()
                # mark alerted with timestamp
                state[key] = datetime.utcnow().isoformat()
                any_alerts = True

    # Save state even if nothing changed (ensures cache updated)
    save_state(state)
    print("Done. Alerts sent:", any_alerts)

if __name__ == "__main__":
    main_once()
