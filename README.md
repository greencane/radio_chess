# Radio Chess Tracker

A Flask web app for recording and reviewing chess games played over the radio. Enter moves by dragging pieces on the interactive board or by typing standard algebraic notation (SAN), such as `e4`, `Nf3`, or `O-O`.

The project also includes a standalone **Android app** (see [Android app](#android-app)) that works fully offline, with no server required.

## Features

- Interactive chessboard with legal-move highlighting and turn-aware piece dragging
- Manual SAN move entry for moves received by voice
- Move history and Back / Forward navigation
- Multiple games: create games, switch between them, and permanently delete the open game
- Editable PGN details: Event, Site, Date, Round, White, Black, and Result
- Automatic PGN saving after moves and detail edits, using a temporary file and atomic replacement
- Reopens the last active game on startup; if that game is unavailable, opens the most recently modified saved game
- Creates a default `Game 1` if there are no saved games
- Migrates `radio_games.pgn` to `games/legacy-game.pgn` when the games folder contains no saved PGN games

## Requirements

- Python 3.8 or later
- Python packages: Flask and python-chess (installed as `flask` and `chess`)
- Internet access in the browser: jQuery, Chessboard.js, Chess.js, and chess piece images are loaded from CDNs

## Setup

### Windows (PC)

```powershell
cd path\to\radio_chess
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install flask chess
```

If PowerShell blocks the activation script, run this once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

In Command Prompt, activate the environment with `venv\Scripts\activate.bat`.

### Raspberry Pi (Raspberry Pi OS)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
cd ~/radio_chess
python3 -m venv venv
source venv/bin/activate
pip install flask chess
```

To leave the virtual environment:

```bash
deactivate
```

## Running

With the virtual environment activated:

```bash
python app.py        # Windows
python3 app.py       # Raspberry Pi
```

Open <http://localhost:5000> in a browser. The server listens on all network interfaces at port 5000, so other devices on the same network can connect at `http://<host-ip>:5000`. On a Raspberry Pi, find its IP address with `hostname -I`.

> **Note:** The app has no authentication and uses Flask's development server. Run it only on a trusted local network.

## Usage

1. Make a move by dragging a piece or enter a SAN move in the text box and select **Manual Enter**.
2. Select **Back** and **Forward** to navigate the saved line. If you enter a different move from an earlier position, the existing continuation from that position is replaced.
3. Use the game dropdown to switch games. Enter a game name and optional opponent/callsign, then select **New Game** to create one.
4. Expand **Edit game details** to update the PGN headers, including the result, then select **Save Details**.
5. Select **Delete This Game** to permanently remove the open game's PGN. The app opens another saved game afterward, or creates a new `Game 1` if none remain.

Illegal or unparseable manual moves are ignored without an on-screen error. Drag-and-drop promotions default to a queen; to promote to another piece, enter the move manually in SAN (for example, `e8=N`).

## Android app

`Radio-Chess_v1.apk` in the repository root is a prebuilt, debug-signed Android build of Radio Chess. It has the same features and layout as the web app, but runs entirely on the phone: no Flask server, no Python, and no internet connection (the chess libraries and piece images are bundled).

### Install

1. Copy `Radio-Chess_v1.apk` to the phone (USB, cloud drive, etc.) and open it, allowing "Install unknown apps" for the file manager if prompted. Alternatively, with USB debugging enabled: `adb install Radio-Chess_v1.apk`.
2. Open **Radio Chess**. Requires Android 8.0 (API 26) or later.

### Usage notes

- Usage is the same as the web app (see [Usage](#usage)): drag pieces or type SAN moves, navigate with Back/Forward, manage multiple games, and edit PGN details.
- Dragging a piece highlights its legal destination squares.
- Games are saved automatically as PGN files in the app's private storage (`games/<game-id>.pgn` and `games/active.txt`), using the same atomic write and reopen-last-game behavior as the desktop app. They are removed if the app is uninstalled; the games are not synced with the PC version.

### How it is built

The Android project is in [`android/`](android). It is a Kotlin app whose single screen is a `WebView` that loads the bundled web UI from `android/app/src/main/assets/` (`index.html`, `app.js`, plus jQuery, Chessboard.js, Chess.js, and piece images in `lib/` and `img/`). `MainActivity.kt` also provides the PGN file storage that the JavaScript calls into. The game logic in `app.js` is a JavaScript port of the Flask routes in `app.py`.

Toolchain: Android Studio (or JDK 17 plus the Android SDK 35), Gradle 8.9 via the included wrapper, Android Gradle Plugin 8.7.3, Kotlin 2.0.21, minSdk 26, targetSdk/compileSdk 35.

To rebuild, set `sdk.dir` in `android/local.properties` to your Android SDK path (or open the `android` folder in Android Studio), then:

```powershell
cd android
.\gradlew.bat assembleDebug
```

The APK is written to `android\app\build\outputs\apk\debug\app-debug.apk`.

Third-party licenses and attribution (including the CC BY-SA chess piece images by Colin M.L. Burnett) are listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

> **Note:** The desktop and Android versions share the PGN format, so a PGN file can be copied between `games/` on the PC and the phone, but the app's private storage is not directly accessible without adb or root. The Android app is not tested against an emulator or physical device in this repository's build environment; the web UI logic was verified in a desktop browser.

## Saved files

| File | Purpose |
|------|---------|
| `app.py` | Flask application and embedded HTML/JavaScript interface |
| `Radio-Chess_v1.apk` | Prebuilt Android version of the app |
| `android/` | Android Studio / Gradle project source for the APK |
| `THIRD_PARTY_NOTICES.md` | Licenses and attribution for bundled libraries and chess piece images |
| `games/<game-id>.pgn` | One PGN file per saved game |
| `games/active.txt` | ID of the game to reopen on startup |
| `radio_games.pgn` | Legacy single-game save file, migrated when there are no saved game PGNs |
