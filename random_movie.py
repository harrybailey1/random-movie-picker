import threading
import requests
import webbrowser
import pandas as pd
import tkinter as tk
import math, io, os, json
from tqdm.auto import tqdm
from bs4 import BeautifulSoup
from datetime import datetime
from PIL import Image, ImageTk
from tkinter import messagebox
from concurrent.futures import ThreadPoolExecutor

# Constants
WATCHLIST_URL = "https://letterboxd.com/{}/watchlist/page/{}/"
DEBUG = True
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive"
}

# Global variables for background metadata (poster,title,etc.) fetching
background_fetch_thread = None
stop_background_flag = threading.Event()
current_background_watchlist_key = None

# Dict mapping (multi-)username keys to their (intersected) watchlists
watchlists = {}

def fetch_page_movies(username, page, session):
    """Fetch and parse movies from a single page"""
    try:
        resolved_url = WATCHLIST_URL.format(username, page)
        if DEBUG:
            print(f"Fetching page {page}: {resolved_url}")
        
        response = session.get(resolved_url, headers=HEADERS)
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
        response = requests.get(first_page_url, headers=HEADERS)
        
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
        # Determine exact number of pages from first page
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

def fetch_multiple_watchlists(usernames, export_csv=False, max_workers=10):
    """
    Fetch and intersect watchlists for multiple usernames.
    Returns a DataFrame with movies common to all users.
    """
    if not usernames:
        return pd.DataFrame()
    
    if len(usernames) == 1:
        return fetch_watchlist(usernames[0], export_csv=export_csv, max_workers=max_workers)
    
    multi_username_key = tuple(sorted(usernames))
    if multi_username_key in watchlists:
        if DEBUG:
            print("Loading intersected watchlist from cache...")
        return watchlists[multi_username_key]
    
    dfs = []
    for user in usernames:
        print(f"Fetching watchlist for user: {user}")
        df = fetch_watchlist(user, export_csv=export_csv, max_workers=max_workers)
        df_clean = df[['Slug', 'Name', 'Year', 'Film ID', 'LID', 'Letterboxd URI']].copy()
        dfs.append(df_clean)
    
    if not dfs:
        return pd.DataFrame()
    
    # Find intersection of all watchlists by Slug
    common_slugs = set(dfs[0]['Slug'])
    for i, df in enumerate(dfs[1:], 1):
        print(f"Intersecting with user {i+1} watchlist...")
        user_slugs = set(df['Slug'])
        common_slugs = common_slugs.intersection(user_slugs)
    
    # Filter the first user's DataFrame to only include common movies
    result = dfs[0][dfs[0]['Slug'].isin(common_slugs)].copy()

    # Save to dict for caching
    watchlists[multi_username_key] = result
    
    print(f"Found {len(result)} common movies across all {len(usernames)} users")
    return result

def fetch_single_metadata(uri, session=None):
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

def poster_url(film_id, slug):
    sep_film_id = ".".join(list(str(film_id)))
    return f"https://a.ltrbxd.com/resized/film-poster/{sep_film_id}/{film_id}-{slug}-0-460-0-690-crop.jpg"

def fetch_metadata_background(df, workers=3):
    """Silently fetch metadata for all movies in the background and add to DataFrame"""
    global stop_background_flag
    
    if df.empty:
        return
    
    # Initialize Metadata column if it doesn't exist
    if 'Metadata' not in df.columns:
        df['Metadata'] = None
    
    # Use a local executor with context manager
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = []
        session = requests.Session()
        
        try:
            for idx, row in df.iterrows():
                # Check if we should stop
                if stop_background_flag.is_set():
                    if DEBUG:
                        print("Background metadata fetch stopped")
                    return
                    
                uri = row.get("Letterboxd URI", "")
                # Skip if we already have metadata for this movie
                if uri and (pd.isna(row.get('Metadata')) or row.get('Metadata') is None):
                    future = executor.submit(fetch_single_metadata, uri, session)
                    futures.append((idx, uri, future))
            
            # Process completed futures and update DataFrame
            fn = tqdm if DEBUG else lambda x: x
            for idx, uri, future in fn(futures):
                # Check if we should stop before processing each result
                if stop_background_flag.is_set():
                    if DEBUG:
                        print("Background metadata fetch stopped during processing")
                    return
                    
                try:
                    metadata = future.result(timeout=30)  # 30 second timeout per movie
                    if metadata:
                        df.at[idx, 'Metadata'] = metadata
                except Exception:
                    continue  # Silently skip failed requests
        finally:
            pass

def start_background_metadata_fetch(df):
    """Start background metadata fetching in a separate thread"""
    global background_fetch_thread, stop_background_flag
    
    # Stop any existing background fetching first
    stop_background_metadata_fetch()
    
    # Clear the stop flag for the new background fetch
    stop_background_flag.clear()
    
    background_fetch_thread = threading.Thread(
        target=fetch_metadata_background, 
        args=(df, 3),
        daemon=True
    )
    background_fetch_thread.start()

def stop_background_metadata_fetch():
    """Stop the background metadata fetching"""
    global background_fetch_thread, stop_background_flag
    
    # Set the stop flag to signal the background thread to stop
    stop_background_flag.set()
    
    # Wait a short time for the thread to notice the stop flag
    if background_fetch_thread and background_fetch_thread.is_alive():
        background_fetch_thread.join(timeout=1.0)  # Wait up to 1 second
    
    # Reset the thread reference
    background_fetch_thread = None

def update_ui_status(message):
    status_label.config(text=message)
    root.update()

# GUI Setup
def on_submit():
    global current_background_watchlist_key
    
    # Clear previous results and show loading status
    result_label.config(text="")
    director_label.config(text="")
    genre_label.config(text="")
    rating_label.config(text="")
    poster_label.config(image="")
    link_label.config(text="")
    submit_btn.config(state='disabled')
    update_ui_status("Loading watchlists...")
    
    try:
        usernames_text = username_entry.get("1.0", "end-1c").strip().replace(",", "\n").split()
        usernames = [u.strip() for u in usernames_text if u.strip()]
        num_samples = 1  # Always pick just one movie
        
        # Create a key to identify this specific watchlist
        if len(usernames) == 1:
            watchlist_key = usernames[0]
            update_ui_status(f"Fetching watchlist for {usernames[0]}...")
            full_watchlist = fetch_watchlist(usernames[0], export_csv=True)
        else:
            watchlist_key = tuple(sorted(usernames))
            update_ui_status(f"Fetching watchlists for {len(usernames)} users...")
            full_watchlist = fetch_multiple_watchlists(usernames, export_csv=True)
        
        if full_watchlist.empty:
            raise Exception("No movies found in the intersection of all users' watchlists.")
        
        # Update status with movie count
        if len(usernames) == 1:
            update_ui_status(f"Found {len(full_watchlist)} movies in watchlist")
        else:
            update_ui_status(f"Found {len(full_watchlist)} movies common to all {len(usernames)} users")
        
        # Only start background metadata fetching if this is a different watchlist
        if current_background_watchlist_key != watchlist_key:
            current_background_watchlist_key = watchlist_key
            start_background_metadata_fetch(full_watchlist)
        
        sample_df = full_watchlist.sample(num_samples)
        sample_row = sample_df.iloc[0]
        sample_index = sample_df.index[0]

        # Display movie title and year
        title = f"{sample_row['Name']} ({sample_row['Year']})"
        uri = sample_row["Letterboxd URI"]
        
        # Try to get metadata from DataFrame first, then force fetch
        meta = None
        if 'Metadata' in sample_row and pd.notna(sample_row['Metadata']) and sample_row['Metadata'] is not None:
            meta = sample_row['Metadata']
        else:
            # Force fetch this specific movie's metadata immediately
            update_ui_status("Fetching movie details...")
            meta = fetch_single_metadata(uri)
            # Store it back in the DataFrame for future use
            if 'Metadata' not in full_watchlist.columns:
                full_watchlist['Metadata'] = None
            full_watchlist.at[sample_index, 'Metadata'] = meta
        
        # Clear status and shrink status box
        status_label.config(text="")

        # Display title
        result_label.config(text=title)
        # Create clickable link
        link_label.config(text="View on Letterboxd", fg=ACCENT_COLOR, cursor="pointinghand")
        link_label.bind("<Button-1>", lambda _: webbrowser.open_new(uri))
        # Display director
        director = meta.get("director", [{}])[0].get("name", "Unknown") if meta.get("director") else "Unknown"
        director_label.config(text=f"Director: {director}")
        # Display genre
        genre = meta.get("genre", ["Unknown"])[0] if meta.get("genre") else "Unknown"
        genre_label.config(text=f"Genre: {genre}")
        # Display rating
        rating = meta.get("aggregateRating", {}).get("ratingValue", "N/A") if meta.get("aggregateRating") else "N/A"
        rating_label.config(text=f"Rating: {rating}")
        # Load and show poster
        img = get_poster_image(meta)
        photo = ImageTk.PhotoImage(img)
        poster_label.config(image=photo)
        poster_label.image = photo  # Save reference to avoid GC
        
    except Exception as e:
        status_label.config(text="")
        print(f"Error: {e}")
        messagebox.showerror("Error", str(e))
    finally:
        # Always re-enable the button
        submit_btn.config(state='normal')

if __name__ == "__main__":
    # Letterboxd color scheme
    BG_COLOR = "#2c3440"  # Dark charcoal
    FG_COLOR = "#9ab"     # Light grey-blue
    ACCENT_COLOR = "#00e054"  # Letterboxd green
    BUTTON_COLOR = "#445566"  # Darker button
    ENTRY_COLOR = "#1a2028"   # Darker input fields
    
    root = tk.Tk()
    root.title("Letterboxd Random Movie Picker")
    root.configure(bg=BG_COLOR)
    root.geometry("420x800")
    root.resizable(True, True)
    root.minsize(380, 600)
    
    # Configure style with better fonts
    base_style = {
        'bg': BG_COLOR,
        'fg': FG_COLOR,
        'relief': 'flat'
    }
    try:
        header_font = ('SF Pro Display', 18, 'bold')  # macOS system font
        body_font = ('SF Pro Text', 11)
        button_font = ('SF Pro Text', 12, 'bold')
    except:
        try:
            header_font = ('Segoe UI', 18, 'bold')  # Windows system font
            body_font = ('Segoe UI', 11)
            button_font = ('Segoe UI', 12, 'bold')
        except:
            header_font = ('Helvetica', 18, 'bold')  # Fallback
            body_font = ('Helvetica', 11)
            button_font = ('Helvetica', 12, 'bold')
    
    default_usernames = "harrybailey1"

    # Configure grid to center content
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)

    # Header
    header_label = tk.Label(root, text="Letterboxd Random Movie Picker", 
                           font=header_font, 
                           bg=BG_COLOR, fg=ACCENT_COLOR)
    header_label.grid(row=0, column=0, columnspan=2, pady=(15, 25), sticky="")

    # Username input
    username_label = tk.Label(root, text="Usernames:", 
                             font=body_font, **base_style)
    username_label.grid(row=1, column=0, sticky="e", padx=(0, 10), pady=(5, 0))
    
    username_entry = tk.Text(root, height=3, width=22, 
                            bg=ENTRY_COLOR, fg=FG_COLOR, 
                            font=body_font,
                            insertbackground=FG_COLOR,
                            relief='flat', bd=3, highlightthickness=1, 
                            highlightcolor=ACCENT_COLOR, highlightbackground="#334155")
    username_entry.grid(row=1, column=1, padx=(0, 0), pady=(5, 0), sticky="w")
    username_entry.insert("1.0", default_usernames)
    
    # Help text
    help_label = tk.Label(root, text="(Enter multiple usernames separated by commas or new lines)", 
                         font=(body_font[0], 9, 'italic'), 
                         bg=BG_COLOR, fg="#667788")
    help_label.grid(row=2, column=0, columnspan=2, pady=(2, 10), sticky="")

    # Submit button
    submit_btn = tk.Button(root, text="🎲 Pick Random Movie", 
                          command=on_submit,
                          bg=ACCENT_COLOR, fg='#000', 
                          font=button_font,
                          relief='flat', bd=0, 
                          padx=25, pady=12,
                          cursor='pointinghand',
                          activebackground="#00b944",  # Darker green when clicked
                          activeforeground='#000')
    submit_btn.grid(row=3, column=0, columnspan=2, pady=25, sticky="")

    # Status/diagnostic label
    status_label = tk.Label(root, text="No results to show", 
                           font=(body_font[0], 11), 
                           bg=BG_COLOR, fg=FG_COLOR,
                           justify="center", wraplength=380)
    status_label.grid(row=4, column=0, columnspan=2, pady=(0, 10), sticky="")

    # Movie info display
    result_label = tk.Label(root, text="", 
                           font=(header_font[0], 15, 'bold'), 
                           bg=BG_COLOR, fg=FG_COLOR, 
                           justify="center", wraplength=380)
    result_label.grid(row=5, column=0, columnspan=2, pady=(0, 10), sticky="")

    director_label = tk.Label(root, text="", 
                             font=body_font, 
                             bg=BG_COLOR, fg="#9ab",
                             justify="center")
    director_label.grid(row=6, column=0, columnspan=2, pady=(0, 4), sticky="")

    genre_label = tk.Label(root, text="", 
                          font=body_font, 
                          bg=BG_COLOR, fg="#9ab",
                          justify="center")
    genre_label = tk.Label(root, text="", 
                          font=body_font, 
                          bg=BG_COLOR, fg="#9ab",
                          justify="center")
    genre_label.grid(row=7, column=0, columnspan=2, pady=(0, 4), sticky="")

    rating_label = tk.Label(root, text="", 
                           font=body_font, 
                           bg=BG_COLOR, fg="#9ab",
                           justify="center")
    rating_label.grid(row=8, column=0, columnspan=2, pady=(0, 12), sticky="")

    # Poster
    poster_label = tk.Label(root, bg=BG_COLOR)
    poster_label.grid(row=9, column=0, columnspan=2, pady=(0, 12), sticky="")

    # Link
    link_label = tk.Label(root, text="", 
                         fg=ACCENT_COLOR, cursor="pointinghand",
                         bg=BG_COLOR, font=(body_font[0], 11, 'underline'))
    link_label.grid(row=10, column=0, columnspan=2, pady=(0, 15), sticky="")

    root.mainloop()