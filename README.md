# Random Letterboxd Movie Picker

A Python GUI application that picks random movies from your Letterboxd watchlist. The app features a sleek dark theme inspired by Letterboxd's design, supports multiple users, and can find movies common to all users' watchlists.

## Features

- 🎲 Pick random movies from single or multiple Letterboxd watchlists
- 🖼️ Display movie posters
- 📋 Show movie details (director, genre, rating)
- 🔗 Direct link to Letterboxd movie page
- 💾 Cache watchlists locally for faster subsequent runs
- 👥 Multi-user support: Find movies that are in everyone's watchlist
- 🌙 Dark Letterboxd theme: Beautiful charcoal design matching Letterboxd's aesthetic
- ⚡ Fast multithreaded fetching: Concurrent page processing for quick loading

## Requirements

- Python 3.7+
- Letterboxd account(s)
- Internet connection

## Installation and Setup

### 1. Clone or Download the Project

Download all the files to a directory on your computer.

### 2. Install Python Dependencies

Open a terminal/command prompt and navigate to the project directory, then run:

```bash
pip install -r requirements.txt
```

Or install packages individually:
```bash
pip install pandas requests beautifulsoup4 Pillow pyinstaller
```

## Running the Script

### Method 1: Direct Python Execution

```bash
python random_movie.py
```

### Method 2: Compile Into Executable Using PyInstaller

You can compile the script into a standalone executable using PyInstaller. Run the following command in the terminal:

```bash
pyinstaller --onefile --windowed --name "MoviePicker" --icon="icon.icns" random_movie.py
```

After compilation, file structure will be:
```
random_movie_picker/
├── random_movie.py           # Main Python script
├── requirements.txt          # Python dependencies
├── MoviePicker.spec          # PyInstaller spec for macOS app
├── random_movie.spec         # PyInstaller spec for executable
├── LaunchMoviePicker.command # macOS/Linux launch script
├── watchlist.csv             # Cached watchlist (created automatically)
├── build/                    # Build artifacts (created during compilation)
└── dist/                     # Compiled executables (created during compilation)
    ├── MoviePicker.app       # macOS application bundle
    └── random_movie          # Standalone executable
```

All executables and app bundles will be located in the `dist/` folder.


## How to Use

### Single User Mode
1. **Enter Username**: Input your Letterboxd username in the text field
2. **Set Number of Movies**: Choose how many movies to pick (default: 1)
3. **Pick Movie**: Click "🎲 Pick Random Movie"

### Multi-User Mode (Find Common Movies)
1. **Enter Multiple Usernames**: In the username field, enter multiple usernames separated by commas or new lines:
   ```
   username1, username2, username3
   ```
   or
   ```
   username1
   username2
   username3
   ```
2. **Pick Movie**: Click "🎲 Pick Random Movie"
3. **View Results**: The app will find movies that are in ALL users' watchlists and pick randomly from those

### Results Display
The app will display:
- Movie title and year
- Movie poster
- Director
- Genre
- Rating
- Clickable link to Letterboxd

## Future Improvements
- Add filtering options (genre, year, rating)
- Allow fetched metadata to be transferred across watchlists for the same movie
- Improve error handling and user feedback
- Add support for picking more than one movie at a time