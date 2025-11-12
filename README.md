# Random Letterboxd Movie Picker

A Python GUI application that picks random movies from your Letterboxd watchlist. The app fetches your watchlist, displays movie details including poster, director, genre, and rating, and provides a link to view the movie on Letterboxd.

## Features

- 🎲 Pick random movies from your Letterboxd watchlist
- 🖼️ Display movie posters
- 📋 Show movie details (director, genre, rating)
- 🔗 Direct link to Letterboxd movie page
- 💾 Cache watchlist locally for faster subsequent runs
- 🔐 Secure password storage using keyring

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
pip install keyring pandas requests beautifulsoup4 Pillow
```

### 3. Set Up Credentials (Optional)

For convenience, you can store your Letterboxd password securely:

```bash
python -c "import keyring; keyring.set_password('letterboxd', 'your_username', 'your_password')"
```

Replace `your_username` and `your_password` with your actual Letterboxd credentials.

## Running the Script

### Method 1: Direct Python Execution

```bash
python random_movie.py
```

### Method 2: Using the Launch Script (macOS/Linux)

Make the launch script executable and run it:

```bash
chmod +x LaunchMoviePicker.command
./LaunchMoviePicker.command
```

Or double-click `LaunchMoviePicker.command` in your file manager.

### Method 3: Using PyInstaller Executables

If you've built the app (see compilation section below), you can run:

- **Standalone executable**: `./dist/random_movie/random_movie`
- **macOS App Bundle**: Double-click `MoviePicker.app`

## How to Use

1. **Enter Credentials**: Input your Letterboxd username and password
2. **Set Number of Movies**: Choose how many movies to pick (default: 1)
3. **Pick Movie**: Click "🎲 Pick Random Movie"
4. **View Results**: The app will display:
   - Movie title and year
   - Movie poster
   - Director
   - Genre
   - Rating
   - Clickable link to Letterboxd

## Compiling into Standalone Applications

The project includes PyInstaller specification files to compile the Python script into standalone executables.

### Prerequisites

Install PyInstaller:

```bash
pip install pyinstaller
```

### Option 1: Single Executable File

Creates a single executable file:

```bash
pyinstaller random_movie.spec
```

This creates:
- `dist/random_movie/` directory with the executable
- Run with: `./dist/random_movie/random_movie`

### Option 2: macOS App Bundle (Recommended for macOS)

Creates a proper macOS application:

```bash
pyinstaller MoviePicker.spec
```

This creates:
- `dist/MoviePicker.app/` - A proper macOS app bundle
- Double-click to run like any other Mac application

### Build Outputs

After compilation, you'll find:
- `build/` - Temporary build files (can be deleted)
- `dist/` - Final executables and app bundles

### Distribution

To share the app:

1. **Single executable**: Share the entire `dist/random_movie/` folder
2. **macOS App**: Share the `MoviePicker.app` bundle

## File Structure

```
random_movie_picker/
├── random_movie.py          # Main Python script
├── requirements.txt         # Python dependencies
├── MoviePicker.spec        # PyInstaller spec for macOS app
├── random_movie.spec       # PyInstaller spec for executable
├── LaunchMoviePicker.command # macOS/Linux launch script
├── watchlist.csv           # Cached watchlist (created automatically)
├── build/                  # Build artifacts (created during compilation)
└── dist/                   # Compiled executables (created during compilation)
```

## Troubleshooting

### Login Issues
- Ensure your Letterboxd username and password are correct
- Check your internet connection
- Letterboxd may have changed their login process - the script may need updates

### Missing Dependencies
- Run `pip install -r requirements.txt` to ensure all packages are installed
- On some systems, you may need to use `pip3` instead of `pip`

### PyInstaller Issues
- Ensure you have the latest version: `pip install --upgrade pyinstaller`
- Try deleting `build/` and `dist/` directories before rebuilding
- For macOS: You might need to install additional tools like Xcode Command Line Tools

### Permission Issues (macOS/Linux)
- Make the launch script executable: `chmod +x LaunchMoviePicker.command`
- For the compiled app, you might need to allow execution in System Preferences > Security

### App Won't Open (macOS)
- Right-click the app and select "Open" to bypass Gatekeeper warnings
- You may need to go to System Preferences > Security & Privacy to allow the app

## Notes

- The app caches your watchlist in `watchlist.csv` for faster subsequent runs
- Delete `watchlist.csv` to force a fresh download of your watchlist
- The app requires an internet connection for the initial watchlist download and to fetch movie posters
- Your credentials are handled securely and are not stored in plain text (when using keyring)

## License

This project is for personal use. Respect Letterboxd's terms of service when using this application.