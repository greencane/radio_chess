# Radio Chess Tracker

A simple Flask web app for keeping track of a chess game played over the radio. Enter each move by dragging pieces on the board or by typing it in standard notation (e.g. `e4`, `Nf3`), and step back and forward through the game as needed.

## Features

- Interactive chessboard with legal-move highlighting
- Manual move entry (SAN) for moves received by voice
- Move history list
- Back / Forward navigation through the game
- Multiple games in parallel: create, switch between, and delete games from the UI
- Each game is saved automatically (atomic write) as `games/<name>.pgn`; the last-open game is reopened on startup, so a Pi reset or restart loses nothing
- An existing `radio_games.pgn` is imported automatically on first run

## Requirements

- Python 3.8+
- Python packages: `flask`, `chess` (python-chess)
- Internet access in the browser (jQuery, chessboard.js, chess.js and piece images are loaded from CDNs)

## Setup

### Windows (PC)

```powershell
cd path\to\radio_chess
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install flask chess
```

If PowerShell blocks the activation script, run once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

In Command Prompt, activate with `venv\Scripts\activate.bat` instead.

### Raspberry Pi (Raspberry Pi OS)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
cd ~/radio_chess
python3 -m venv venv
source venv/bin/activate
pip install flask chess
```

### Leaving the virtual environment

```bash
deactivate
```

## Running

With the virtual environment activated:

```bash
python app.py        # Windows
python3 app.py       # Raspberry Pi
```

Open <http://localhost:5000> in a browser. The server listens on all interfaces (`0.0.0.0:5000`), so other devices on your network can use it at `http://<host-ip>:5000`. On a Raspberry Pi, find its IP with `hostname -I`.

> **Note:** The app has no authentication and runs Flask's development server. Use it only on a trusted local network.

## Usage

1. Make a move by dragging a piece, or type it in the box (e.g. `e4`, `Nf3`, `O-O`) and click **Manual Enter**.
2. Use **< Back** and **Forward >** to review the game. Making a different move from an earlier position replaces the moves after it.
3. Use the dropdown to switch to another game; enter a name and opponent/callsign and click **New Game** to start another. **Delete This Game** permanently removes the open game.

Illegal or unparseable manual moves are silently ignored. Pawn promotions made by dragging always promote to a queen; to promote to another piece, type the move manually (e.g. `e8=N`).

## Files

| File | Purpose |
|------|---------|
| `app.py` | The Flask application and HTML template |
| `games/*.pgn` | One saved PGN per game (created automatically) |
| `games/active.txt` | Which game was open last |
