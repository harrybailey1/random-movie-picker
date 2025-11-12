# Random Letterboxd Movie Picker

A Python GUI application that picks random movies from your Letterboxd watchlist. The app fetches your watchlist, displays movie details including poster, director, genre, and rating, and provides a link to view the movie on Letterboxd.

## Features

- 🎲 Pick random movies from your Letterboxd watchlist
- 🖼️ Display movie posters
- 📋 Show movie details (director, genre, rating)
- 🔗 Direct link to Letterboxd movie page
- 💾 Cache watchlist locally for faster subsequent runs

## Requirements

- Python 3.7+
- Letterboxd account
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

1. **Set Number of Movies**: Choose how many movies to pick (default: 1)
2. **Pick Movie**: Click "🎲 Pick Random Movie"
3. **View Results**: The app will display:
   - Movie title and year
   - Movie poster
   - Director
   - Genre
   - Rating
   - Clickable link to Letterboxd