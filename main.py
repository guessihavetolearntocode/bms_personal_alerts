import os
import json
import requests
from bs4 import BeautifulSoup
from twilio.rest import Client
import telegram

# Load environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM")
TO_PHONE = os.getenv("TO_PHONE")

# Initialize Telegram bot
tg_bot = telegram.Bot(token=TELEGRAM_TOKEN)
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Load movies
with open("movies.json", "r") as f:
    movies = json.load(f)

# Load called_state
if os.path.exists("called_state.json"):
    with open("called_state.json", "r") as f:
        called_state = json.load(f)
else:
    called_state = {}

# Example: PVR Now Showing API
def fetch_pvr_movies(location="bengaluru"):
    url = "https://api3.pvrcinemas.com/api/v1/booking/content/nowshowing"
    resp = requests.get(url)
    if resp.status_code != 200:
        return []
    data = resp.json()
    result = []
    for m in data.get("movies", []):
        result.append({
            "title": m.get("title", "").lower(),
            "theatres": [t.get("name","").lower() for t in m.get("theatreList",[])]
        })
    return result

# Example: Cinepolis API
def fetch_cinepolis_movies(city_id=17):
    url = f"https://api_new.cinepolisindia.com/api/movies/now-playing-filtered/?city_id={city_id}"
    resp = requests.get(url)
    if resp.status_code != 200:
        return []
    data = resp.json()
    result = []
    for m in data.get("movies", []):
        result.append({
            "title": m.get("title","").lower(),
            "theatres": [t.get("name","").lower() for t in m.get("theatreList",[])]
        })
    return result

def send_alert(movie_name):
    if called_state.get(movie_name):
        return  # Already called
    message = f"🎬 {movie_name} is now showing!"
    # Telegram
    tg_bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    # Twilio SMS
    twilio_client.messages.create(
        body=message,
        from_=TWILIO_FROM,
        to=TO_PHONE
    )
    called_state[movie_name] = True
    with open("called_state.json", "w") as f:
        json.dump(called_state, f)

def main():
    # Fetch movies
    pvr_movies = fetch_pvr_movies()
    cine_movies = fetch_cinepolis_movies()
    all_movies = pvr_movies + cine_movies

    for movie in movies:
        keywords = [k.lower() for k in movie["keywords"]]
        desired_theatres = [t.lower() for t in movie["theatres"]]
        desired_locations = [l.lower() for l in movie["locations"]]

        for showing in all_movies:
            title = showing["title"]
            theatres = showing.get("theatres", [])
            if any(k in title for k in keywords):
                if "any" in desired_theatres or any(t in theatres for t in desired_theatres):
                    send_alert(movie["movie"])
                    break  # Only one alert per movie

if __name__ == "__main__":
    main()
