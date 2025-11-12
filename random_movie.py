from datetime import datetime
import io
import os, json
import math
import requests
import webbrowser
import pandas as pd
import tkinter as tk
from bs4 import BeautifulSoup
from PIL import Image, ImageTk
from tkinter import messagebox
from concurrent.futures import ThreadPoolExecutor

WATCHLIST_URL = "https://letterboxd.com/{}/watchlist/page/{}/"
DEBUG = True
watchlists = {} # Maps username to their watchlist DataFrame

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive"
}

def fetch_page_movies(username, page, session):
    """Fetch and parse movies from a single page"""
    try:
        resolved_url = WATCHLIST_URL.format(username, page)
        if DEBUG:
            print(f"Fetching page {page}: {resolved_url}")
        
        response = session.get(resolved_url, headers=headers)
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.text, "html.parser")
        movies = soup.find_all("li", attrs={"class": "griditem"})
        
        if not movies:  # No more movies found
            return []
        
        page_movies = []
        # Extract movie information from each griditem
        for movie in movies:
            try:
                react_component = movie.find("div", class_="react-component")
                if react_component:
                    # Extract title and year from data-item-full-display-name
                    full_name = react_component.get("data-item-full-display-name", "")
                    
                    # Parse title and year (format: "Title (Year)")
                    if "(" in full_name and full_name.endswith(")"):
                        title = full_name.rsplit(" (", 1)[0]
                        year = full_name.rsplit(" (", 1)[1][:-1]  # Remove the closing )
                    else:
                        title = full_name
                        year = "Unknown"
                    
                    # Extract other attributes
                    slug = react_component.get("data-item-slug", "")
                    film_id = react_component.get("data-film-id", "")
                    
                    # Parse the postered identifier JSON to get lid
                    postered_identifier = react_component.get("data-postered-identifier", "")
                    lid = ""
                    if postered_identifier:
                        try:
                            identifier_data = json.loads(postered_identifier)
                            lid = identifier_data.get("lid", "")
                        except:
                            lid = ""
                    
                    # Create full Letterboxd URI
                    letterboxd_uri = f"https://boxd.it/{lid}" if lid else ""
                    
                    movie_data = {
                        "Name": title,
                        "Year": year,
                        "Slug": slug,
                        "Film ID": film_id,
                        "LID": lid,
                        "Letterboxd URI": letterboxd_uri,
                    }
                    page_movies.append(movie_data)
                    
            except Exception as e:
                if DEBUG:
                    print(f"Error parsing movie on page {page}: {e}")
                continue
        
        return page_movies
        
    except Exception as e:
        if DEBUG:
            print(f"Error fetching page {page}: {e}")
        return []

def get_total_pages(username):
    """Get the total number of pages by checking data-num-entries on the first page"""
    try:
        first_page_url = WATCHLIST_URL.format(username, 1)
        response = requests.get(first_page_url, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch first page: {response.status_code}")
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find the watchlist content div with data-num-entries
        watchlist_content = soup.find("div", {"class": "js-watchlist-content"})
        if not watchlist_content:
            raise Exception("Could not find watchlist content div")
        
        total_entries = watchlist_content.get("data-num-entries")
        if not total_entries:
            raise Exception("Could not find data-num-entries attribute")
        
        total_entries = int(total_entries)
        
        # Count movies on this first page to determine entries per page
        movies_on_page = len(soup.find_all("li", {"class": "griditem"}))
        if movies_on_page == 0:
            raise Exception("No movies found on first page")
        
        # Calculate total pages needed
        total_pages = math.ceil(total_entries / movies_on_page)
        
        if DEBUG:
            print(f"Found {total_entries} total entries, {movies_on_page} per page = {total_pages} pages")
        return total_pages, total_entries
        
    except Exception as e:
        if DEBUG:
            print(f"Error determining total pages: {e}")
        # Fallback to old method if this fails
        return None, None

def fetch_watchlist(username, export_csv=False, max_workers=10):
    if username not in watchlists:
        # Smart approach: determine exact number of pages from first page
        total_pages, total_entries = get_total_pages(username)
        
        if total_pages is None:
            if DEBUG:
                print("Falling back to sequential fetching...")
            # Fallback to old sequential method if smart detection fails
            return fetch_watchlist_sequential(username, export_csv)
        
        # Fetch all pages concurrently
        all_movies = []
        pages_to_fetch = list(range(1, total_pages + 1))
        
        if DEBUG:
            print(f"Fetching {len(pages_to_fetch)} pages concurrently with {max_workers} workers...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Create a session for each thread to avoid conflicts
            futures = []
            for page in pages_to_fetch:
                thread_session = requests.Session()
                futures.append(executor.submit(fetch_page_movies, username, page, thread_session))
            
            # Collect results as they complete
            for future in futures:
                page_movies = future.result()
                all_movies.extend(page_movies)
        
        # Create DataFrame from collected movie data
        df = pd.DataFrame(all_movies)
        watchlists[username] = df
        if DEBUG:
            print(f"Successfully fetched {len(all_movies)} movies from {len(pages_to_fetch)} pages (expected {total_entries})")
        
        if export_csv and not df.empty:
            os.makedirs("watchlists", exist_ok=True)
            df.to_csv(f"watchlists/{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_watchlist.csv", index=False)

    else:
        if DEBUG:
            print("Loading watchlist from cache...")
        df = watchlists[username]
    
    if df.empty:
        raise Exception("Watchlist is empty.")

    return df

def fetch_watchlist_sequential(username, export_csv=False):
    """Fallback sequential method"""
    session = requests.Session()
    all_movies = []
    
    for page in range(1, 100):
        page_movies = fetch_page_movies(username, page, session)
        if not page_movies:
            break
        all_movies.extend(page_movies)
    
    df = pd.DataFrame(all_movies)
    if export_csv and not df.empty:
        os.makedirs("watchlists", exist_ok=True)
        df.to_csv(f"watchlists/{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_watchlist.csv", index=False)
    
    return df

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

    soup = BeautifulSoup(response.text, "html.parser")
    json_data = soup.find("script", {"type": "application/ld+json"})
    if not json_data:
        if DEBUG:
            print("Movie metadata not found in the page")
        raise Exception("Movie metadata not found in the page")
    
    json_str = json_data.string.replace("/* <![CDATA[ */", "").replace("/* ]]> */", "").strip()
    movie_data = json.loads(json_str)

    return movie_data

def on_submit():
    username = username_entry.get().strip()
    num_samples = int(samples_entry.get())
    try:
        full_watchlist = fetch_watchlist(username, export_csv=True)
        sample_df = full_watchlist.sample(num_samples)
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

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Random Letterboxd Movie Picker")
    default_username = "harrybailey1"

    tk.Label(root, text="Username:").grid(row=0, column=0, sticky="e")
    username_entry = tk.Entry(root)
    username_entry.grid(row=0, column=1)
    username_entry.insert(0, default_username)

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