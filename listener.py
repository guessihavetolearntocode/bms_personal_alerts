import os
import json
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

MOVIE_FILE = "movies.json"

def load_movies():
    with open(MOVIE_FILE, "r") as f:
        return json.load(f)

def save_movies(movies):
    with open(MOVIE_FILE, "w") as f:
        json.dump(movies, f, indent=4)

def add_movie(update: Update, context: CallbackContext):
    try:
        args = " ".join(context.args)
        movie_name, keywords, theatres, locations = [x.strip() for x in args.split(";")]
        movies = load_movies()
        movies.append({
            "movie": movie_name,
            "keywords": [k.strip().lower() for k in keywords.split(",")],
            "theatres": [t.strip() for t in theatres.split(",")],
            "locations": [l.strip().lower() for l in locations.split(",")]
        })
        save_movies(movies)
        update.message.reply_text(f"✅ Added movie: {movie_name}")
    except Exception as e:
        update.message.reply_text(f"❌ Failed: {e}")

def remove_movie(update: Update, context: CallbackContext):
    try:
        movie_name = " ".join(context.args).strip().lower()
        movies = load_movies()
        movies = [m for m in movies if m["movie"].lower() != movie_name]
        save_movies(movies)
        update.message.reply_text(f"✅ Removed movie: {movie_name}")
    except Exception as e:
        update.message.reply_text(f"❌ Failed: {e}")

def list_movies(update: Update, context: CallbackContext):
    movies = load_movies()
    msg = "\n".join([m["movie"] for m in movies])
    update.message.reply_text(msg or "No movies in list.")

def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("add_movie", add_movie))
    dp.add_handler(CommandHandler("remove_movie", remove_movie))
    dp.add_handler(CommandHandler("list_movies", list_movies))
    updater.start_polling(timeout=5)  # checks Telegram every 5 seconds
    updater.idle()

if __name__ == "__main__":
    main()
