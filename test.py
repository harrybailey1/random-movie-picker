from random_movie import fetch_watchlist

# Test the function
watchlist_df = fetch_watchlist("harrybailey1", export_csv=True)
print(f"Found {len(watchlist_df)} movies in watchlist")
print("\nFirst 5 movies:")
print(watchlist_df.head())
print(f"\nColumns: {list(watchlist_df.columns)}")

# Test getting a random sample
random_movie = watchlist_df.sample(1)
print(f"\nRandom movie: {random_movie.iloc[0]['Name']} ({random_movie.iloc[0]['Year']})")
print(f"Letterboxd URI: {random_movie.iloc[0]['Letterboxd URI']}")
print(f"LID: {random_movie.iloc[0]['LID']}")