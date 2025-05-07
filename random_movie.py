import io
import keyring
import os, json
import requests
import webbrowser
import pandas as pd
import tkinter as tk
from bs4 import BeautifulSoup
from PIL import Image, ImageTk
from tkinter import messagebox

LOGIN_URL = "https://letterboxd.com/sign-in/"
LOGIN_FORM = "https://letterboxd.com/user/login.do"
EXPORT_URL_TEMPLATE = "https://letterboxd.com/{}/watchlist/export/"

df = None
if os.path.exists("watchlist.csv"):
    df = pd.read_csv("watchlist.csv")

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive"
}

def fetch_random_movie(username, password, num_samples=1, export_csv=False):
    global df
    if df is None:
        session = requests.Session()

        login_page = session.get(LOGIN_URL, headers=headers)
        soup = BeautifulSoup(login_page.text, "html.parser")
        csrf_input = soup.find("input", {"name": "__csrf"})
        csrf_token = csrf_input["value"] if csrf_input else None

        if not csrf_token:
            raise Exception("CSRF token not found.")

        login_payload = {
            "username": username,
            "password": password,
            "__csrf": csrf_token,
        }
        headers["Referer"] = LOGIN_URL
        login_response = session.post(LOGIN_FORM, data=login_payload, headers=headers)

        if "Invalid username or password" in login_response.text:
            raise Exception("Login failed: Invalid credentials.")

        export_url = EXPORT_URL_TEMPLATE.format(username)
        export_response = session.get(export_url)

        if export_response.status_code != 200 or "text/csv" not in export_response.headers.get("Content-Type", ""):
            raise Exception("Failed to fetch CSV. Are you logged in?")

        df = pd.read_csv(io.StringIO(export_response.text))
    
    if df.empty:
        raise Exception("Watchlist is empty.")

    if export_csv:
        df.to_csv("watchlist.csv", index=False)

    return df.sample(num_samples)

def get_poster_image(metadata, session=None):
    sess = session or requests.Session()
    img_url = metadata["image"]
    img_response = sess.get(img_url)
    img = Image.open(io.BytesIO(img_response.content))
    return img

def get_metadata(uri, session=None):
    sess = session or requests.Session()
    headers = {"User-Agent": "Mozilla/5.0"}

    response = sess.get(uri, headers=headers)
    if response.status_code != 200:
        raise Exception("Could not load movie page")
    # Save the HTML content to a file for debugging
    # with open("movie_page.html", "w", encoding="utf-8") as f:
    #     f.write(response.text)

    soup = BeautifulSoup(response.text, "html.parser")
    json_data = soup.find("script", {"type": "application/ld+json"})
    if not json_data:
        raise Exception("Movie metadata not found in the page")
    
    json_str = json_data.string.replace("/* <![CDATA[ */", "").replace("/* ]]> */", "").strip()
    movie_data = json.loads(json_str)

    return movie_data

# GUI Setup
def on_submit():
    username = username_entry.get().strip()
    password = password_entry.get().strip()
    num_samples = int(samples_entry.get())
    try:
        sample_df = fetch_random_movie(username, password, num_samples=num_samples)
        sample_row = sample_df.iloc[0]

        # Display movie title and year
        title = f"{sample_row['Name']} ({sample_row['Year']})"
        uri = sample_row["Letterboxd URI"]
        result_label.config(text=title)

        # Create clickable link
        link_label.config(text="View on Letterboxd", fg="blue", cursor="hand2")
        link_label.bind("<Button-1>", lambda _: webbrowser.open_new(uri))

        # Load and show poster
        meta = get_metadata(uri)
        img = get_poster_image(meta)
        img = img.resize((150, 225))  # Resize to fit GUI
        photo = ImageTk.PhotoImage(img)
        poster_label.config(image=photo)
        poster_label.image = photo  # Save reference to avoid GC

        # Display director
        director = meta.get("director", [{}])[0].get("name", "Unknown")
        director_label.config(text=f"Director: {director}")

        # Display genre
        genre = meta.get("genre", ["Unknown"])[0]
        genre_label.config(text=f"Genre: {genre}")

        # Display rating
        rating = meta.get("aggregateRating", {}).get("ratingValue", "N/A")
        rating_label.config(text=f"Rating: {rating}")

    except Exception as e:
        messagebox.showerror("Error", str(e))

root = tk.Tk()
root.title("Random Letterboxd Movie Picker")
default_username = "harrybailey1"

tk.Label(root, text="Username:").grid(row=0, column=0, sticky="e")
username_entry = tk.Entry(root)
username_entry.grid(row=0, column=1)
username_entry.insert(0, default_username)

tk.Label(root, text="Password:").grid(row=1, column=0, sticky="e")
password_entry = tk.Entry(root, show="*")
password_entry.grid(row=1, column=1)
password_entry.insert(0, keyring.get_password("letterboxd", default_username))

tk.Label(root, text="Number of movies:").grid(row=2, column=0, sticky="e")
samples_entry = tk.Entry(root)
samples_entry.insert(0, "1")
samples_entry.grid(row=2, column=1)

submit_btn = tk.Button(root, text="🎲 Pick Random Movie", command=on_submit)
submit_btn.grid(row=3, column=0, columnspan=2, pady=10)

result_label = tk.Label(root, text="", font=("Helvetica", 14), fg="darkgreen", justify="left")
result_label.grid(row=4, column=0, columnspan=2, pady=(10, 0))

director_label = tk.Label(root, text="", font=("Helvetica", 14), fg="darkgreen", justify="left")
director_label.grid(row=5, column=0, columnspan=2, pady=(0, 10))

genre_label = tk.Label(root, text="", font=("Helvetica", 14), fg="darkgreen", justify="left")
genre_label.grid(row=6, column=0, columnspan=2, pady=(0, 10))

rating_label = tk.Label(root, text="", font=("Helvetica", 14), fg="darkgreen", justify="left")
rating_label.grid(row=7, column=0, columnspan=2, pady=(0, 10))

poster_label = tk.Label(root)
poster_label.grid(row=8, column=0, columnspan=2)

link_label = tk.Label(root, text="", fg="blue", cursor="hand2")
link_label.grid(row=9, column=0, columnspan=2)

root.mainloop()