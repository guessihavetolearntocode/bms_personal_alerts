import os, json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

MOVIES_FILE = "movies.json"

def load_movies():
    try:
        return json.load(open(MOVIES_FILE, "r"))
    except:
        return []

def save_movies(movies):
    with open(MOVIES_FILE, "w") as f:
        json.dump(movies, f, indent=4)

async def add_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # /add_movie MovieName;keyword1,keyword2;theatre1,theatre2;location1,location2
    try:
        text = " ".join(context.args)
        name, keywords, theatres, locations = text.split(";")
        movie = {
            "movie": name.strip(),
            "keywords": [k.strip() for k in keywords.split(",")],
            "theatres": [t.strip() for t in theatres.split(",")],
            "locations": [l.strip() for l in locations.split(",")]
        }
        movies = load_movies()
        movies.append(movie)
        save_movies(movies)
        await update.message.reply_text(f"Movie added: {name}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def remove_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # /remove_movie MovieName
    try:
        name = " ".join(context.args)
        movies = load_movies()
        movies = [m for m in movies if m["movie"].lower() != name.lower()]
        save_movies(movies)
        await update.message.reply_text(f"Movie removed: {name}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def list_movies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    movies = load_movies()
    msg = "\n".join([m["movie"] for m in movies])
    await update.message.reply_text("Movies in watchlist:\n" + msg)

if __name__ == "__main__":
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
    app.add_handler(CommandHandler("add_movie", add_movie))
    app.add_handler(CommandHandler("remove_movie", remove_movie))
    app.add_handler(CommandHandler("list_movies", list_movies))
    app.run_polling()
