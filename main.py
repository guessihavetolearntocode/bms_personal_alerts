import os, json, requests
from datetime import datetime
from twilio.rest import Client as TwilioClient

MOVIES_FILE = "movies.json"
STATE_FILE = "called_state.json"

# Load env
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM")
TO_PHONE = os.getenv("TO_PHONE")

# Load / Save state
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
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except:
        pass

def make_call():
    if not (TWILIO_SID and TWILIO_TOKEN and TWILIO_FROM and TO_PHONE):
        return
    try:
        client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)
        call = client.calls.create(to=TO_PHONE, from_=TWILIO_FROM,
                                   url="http://demo.twilio.com/docs/voice.xml")
        print("Call SID:", getattr(call, "sid", "<no-sid>"))
    except:
        pass

# Scraper: check PVR / Cinepolis APIs
THEATRE_API_MAPPING = {
    "pvr": "https://api3.pvrcinemas.com/api/v1/booking/content/nowshowing",
    "cinepolis": "https://api_new.cinepolisindia.com/api/movies/now-playing-filtered/?city_id={city_id}"
}

def check_movie(movie):
    keywords = movie["keywords"]
    theatres_filter = movie["theatres"]
    locations_filter = movie["locations"]
    
    found = False
    # --- PVR API ---
    try:
        r = requests.get(THEATRE_API_MAPPING["pvr"])
        if r.status_code == 200:
            data = r.json()
            for m in data.get("data", []):
                title = m.get("title", "").lower()
                if all(k.lower() in title for k in keywords):
                    theatre_name = m.get("name", "")
                    if "any" in theatres_filter or any(t.lower() in theatre_name.lower() for t in theatres_filter):
                        found = True
                        break
    except:
        pass

    # --- Cinepolis API for locations ---
    for loc in locations_filter:
        try:
            city_id = 17 if loc.lower() == "bangalore" else 39 if loc.lower() == "coimbatore" else 17
            r = requests.get(THEATRE_API_MAPPING["cinepolis"].format(city_id=city_id))
            if r.status_code == 200:
                data = r.json()
                for m in data.get("data", []):
                    title = m.get("name", "").lower()
                    if all(k.lower() in title for k in keywords):
                        theatre_name = m.get("theatre_name", "")
                        if "any" in theatres_filter or any(t.lower() in theatre_name.lower() for t in theatres_filter):
                            found = True
                            break
        except:
            pass

    return found

def main():
    state = load_state()
    movies = json.load(open(MOVIES_FILE, "r"))
    alerts_sent = False

    for movie in movies:
        key = movie["movie"]
        if key in state:
            continue  # already called
        if check_movie(movie):
            msg = f"🎟 TICKETS LIVE!\nMovie: {movie['movie']}\nCheck now!"
            send_telegram(msg)
            make_call()
            state[key] = datetime.utcnow().isoformat()
            alerts_sent = True

    save_state(state)
    print("Scraper run complete. Alerts sent:", alerts_sent)

if __name__ == "__main__":
    main()
