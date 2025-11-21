import os, json, requests
from datetime import datetime
from twilio.rest import Client as TwilioClient

# -----------------------------
# Config
# -----------------------------
MOVIES_FILE = "movies.json"
STATE_FILE = "called_state.json"

# Load environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM")
TO_PHONE = os.getenv("TO_PHONE")

# Cinepolis city mapping example
CINEPOLIS_CITY_ID = {
    "bangalore": 17,
    "coimbatore": 39
}

# -----------------------------
# State utils
# -----------------------------
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

# -----------------------------
# Notifications
# -----------------------------
def send_telegram(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram not configured")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
        print("Telegram status:", r.status_code)
    except Exception as e:
        print("Telegram error:", e)

def make_call():
    if not (TWILIO_SID and TWILIO_TOKEN and TWILIO_FROM and TO_PHONE):
        print("Twilio not configured")
        return
    try:
        client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)
        call = client.calls.create(to=TO_PHONE, from_=TWILIO_FROM, url="http://demo.twilio.com/docs/voice.xml")
        print("Twilio call SID:", getattr(call, "sid", "<no-sid>"))
    except Exception as e:
        print("Twilio error:", e)

# -----------------------------
# Cinepolis API scraping
# -----------------------------
def get_cinepolis_nowshowing(city_name):
    city_id = CINEPOLIS_CITY_ID.get(city_name.lower())
    if not city_id:
        print(f"No city id mapping for {city_name}")
        return []
    url = f"https://api_new.cinepolisindia.com/api/movies/now-playing-filtered/?movie_language_id=&movie_genre_id=&city_id={city_id}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            print(f"Cinepolis fetch failed {r.status_code}")
            return []
        data = r.json()
        return data.get("movies", [])
    except Exception as e:
        print("Cinepolis request error:", e)
        return []

# -----------------------------
# Main check function
# -----------------------------
def main_once():
    print("Starting check:", datetime.utcnow().isoformat())
    state = load_state()
    movies_config = json.load(open(MOVIES_FILE, "r"))
    
    for movie_entry in movies_config:
        movie_name = movie_entry["movie"]
        keywords = movie_entry["keywords"]
        theatres_filter = [t.lower() for t in movie_entry["theatres"]]
        locations = movie_entry["locations"]

        for loc in locations:
            cine_movies = get_cinepolis_nowshowing(loc)
            for cine_movie in cine_movies:
                title = cine_movie.get("title", "").lower()
                if any(k.lower() in title for k in keywords):
                    movie_theatres = [t["name"].lower() for t in cine_movie.get("theatres", [])]
                    # Determine theatres to alert
                    if "any" in theatres_filter:
                        relevant_theatres = movie_theatres
                    else:
                        relevant_theatres = [t for t in movie_theatres if t in theatres_filter]

                    for t_name in relevant_theatres:
                        key = f"{movie_name}||{t_name}||{loc}"
                        if key in state:
                            continue
                        msg = f"🎟 TICKETS LIVE!\nMovie: {movie_name}\nTheatre: {t_name}\nLocation: {loc}"
                        send_telegram(msg)
                        make_call()
                        state[key] = datetime.utcnow().isoformat()
    
    save_state(state)
    print("Check completed.")

if __name__ == "__main__":
    main_once()
