import chess
import chess.pgn
import datetime
import os
import re
import shutil
from flask import Flask, redirect, render_template_string, request

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GAMES_DIR = os.path.join(BASE_DIR, "games")
ACTIVE_FILE = os.path.join(GAMES_DIR, "active.txt")
LEGACY_PGN = os.path.join(BASE_DIR, "radio_games.pgn")

# State for the currently open game (each game is one PGN file in GAMES_DIR)
game = chess.pgn.Game()
current_node = game
active_id = None


def game_path(game_id):
    return os.path.join(GAMES_DIR, game_id + ".pgn")


def slugify(text):
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", text).strip("-").lower()
    return slug[:50] or "game"


def valid_id(game_id):
    return bool(game_id) and re.fullmatch(r"[a-z0-9_-]+", game_id) is not None \
        and os.path.exists(game_path(game_id))


def atomic_write(path, text):
    # Write to a temp file then replace, so a power loss can't corrupt the save
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def save_game():
    if active_id:
        atomic_write(game_path(active_id), str(game) + "\n")


def save_active_id():
    atomic_write(ACTIVE_FILE, active_id or "")


def list_games():
    games = []
    for name in sorted(os.listdir(GAMES_DIR)):
        if not name.endswith(".pgn"):
            continue
        gid = name[:-4]
        try:
            with open(game_path(gid)) as f:
                g = chess.pgn.read_game(f)
        except Exception:
            continue
        if g is None:
            continue
        plies = sum(1 for _ in g.mainline_moves())
        games.append({
            "id": gid,
            "title": g.headers.get("Event", gid),
            "opponent": g.headers.get("Black", ""),
            "plies": plies,
            "mtime": os.path.getmtime(game_path(gid)),
        })
    games.sort(key=lambda x: x["mtime"], reverse=True)
    return games


def create_game(title, opponent=""):
    base = slugify(title)
    gid, n = base, 2
    while os.path.exists(game_path(gid)):
        gid = f"{base}-{n}"
        n += 1
    g = chess.pgn.Game()
    g.headers["Event"] = title or "Radio Game"
    g.headers["Site"] = "HAM Radio"
    g.headers["Date"] = datetime.date.today().strftime("%Y.%m.%d")
    g.headers["White"] = "Me"
    g.headers["Black"] = opponent or "?"
    atomic_write(game_path(gid), str(g) + "\n")
    return gid


def open_game(game_id):
    global game, current_node, active_id
    with open(game_path(game_id)) as f:
        loaded = chess.pgn.read_game(f)
    game = loaded or chess.pgn.Game()
    current_node = game.end()
    active_id = game_id
    save_active_id()


def init_games():
    os.makedirs(GAMES_DIR, exist_ok=True)
    # Migrate the old single-game save file
    if os.path.exists(LEGACY_PGN) and not list_games():
        shutil.move(LEGACY_PGN, game_path("legacy-game"))
        with open(game_path("legacy-game")) as f:
            g = chess.pgn.read_game(f)
        if g is not None:
            g.headers["Event"] = "Imported game"
            atomic_write(game_path("legacy-game"), str(g) + "\n")
    saved = ""
    if os.path.exists(ACTIVE_FILE):
        with open(ACTIVE_FILE) as f:
            saved = f.read().strip()
    games = list_games()
    if valid_id(saved):
        open_game(saved)
    elif games:
        open_game(games[0]["id"])
    else:
        open_game(create_game("Game 1"))


init_games()

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>Radio Chess Tracker</title>
  
  <!-- Load jQuery, Chessboard.js (UI), and Chess.js (Logic) via CDN -->
  <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
  <link rel="stylesheet" href="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.css">
  <script src="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/chess.js/0.10.3/chess.min.js"></script>

  <style>
    body { font-family: sans-serif; padding: 20px; background: #f0f0f0; }
    .app-container { 
      display: flex; max-width: 650px; margin: 0 auto; 
      background: white; padding: 20px; border-radius: 8px; 
      box-shadow: 0 2px 4px rgba(0,0,0,0.1); gap: 20px; 
      flex-wrap: wrap; justify-content: center; 
    }
    .board-col { width: 360px; text-align: center; }
    .history-col { 
      width: 200px; background: #fafafa; border: 1px solid #ccc; 
      padding: 10px; border-radius: 4px; height: 440px; 
      overflow-y: auto; font-family: monospace; font-size: 16px; 
    }
    .move-row { padding: 4px; border-bottom: 1px solid #eee; }
    .controls { margin: 15px 0; display: flex; justify-content: center; gap: 10px; }
    button { padding: 8px 12px; cursor: pointer; }
    input[type="text"] { padding: 8px; width: 150px; }
  </style>
</head>
<body>
  <h2 style="text-align: center; margin-top: 0;">Radio Chess Station</h2>
  <h3 style="text-align: center; margin-top: 0;">{{ title }}{% if opponent and opponent != '?' %} vs {{ opponent }}{% endif %}</h3>
  <div class="app-container">
    
    <div class="board-col">
      <!-- Interactive Board Container -->
      <div id="myBoard" style="width: 360px; margin: auto;"></div>
      
      <p><strong>Turn:</strong> {{ 'White' if board.turn else 'Black' }}</p>
      
      <!-- Back / Forward Controls -->
      <div class="controls">
        <form action="/back" method="post" style="margin:0;">
          <button type="submit" {{ 'disabled' if not can_back else '' }}>&lt; Back</button>
        </form>
        <form action="/forward" method="post" style="margin:0;">
          <button type="submit" {{ 'disabled' if not can_forward else '' }}>Forward &gt;</button>
        </form>
      </div>

      <!-- Manual input fallback (still useful for radio) -->
      <form action="/move" method="post">
        <input type="text" name="move" placeholder="e.g. e4, Nf3" autofocus>
        <button type="submit">Manual Enter</button>
      </form>
      
      <hr>
      <form action="/load" method="post" style="margin-bottom: 10px;">
        <select name="game_id" onchange="this.form.submit()">
          {% for g in games %}
            <option value="{{ g.id }}" {{ 'selected' if g.id == active_id else '' }}>
              {{ g.title }}{% if g.opponent and g.opponent != '?' %} vs {{ g.opponent }}{% endif %} ({{ (g.plies + 1) // 2 }} moves)
            </option>
          {% endfor %}
        </select>
        <noscript><button type="submit">Load</button></noscript>
      </form>

      <form action="/new" method="post">
        <input type="text" name="title" placeholder="Game name" style="width:110px;">
        <input type="text" name="opponent" placeholder="Opponent/callsign" style="width:110px;">
        <button type="submit">New Game</button>
      </form>

      <details style="margin-top: 15px; text-align: left;">
        <summary style="cursor: pointer;">Edit game details</summary>
        <form action="/headers" method="post">
          {% for key in header_fields %}
            <div style="margin-top: 6px;">
              <label style="display:inline-block; width:60px;">{{ key }}</label>
              {% if key == 'Result' %}
                <select name="{{ key }}">
                  {% for r in ['*', '1-0', '0-1', '1/2-1/2'] %}
                    <option value="{{ r }}" {{ 'selected' if headers[key] == r else '' }}>{{ r }}</option>
                  {% endfor %}
                </select>
              {% else %}
                <input type="text" name="{{ key }}" value="{{ headers[key] }}" style="width:200px;">
              {% endif %}
            </div>
          {% endfor %}
          <button type="submit" style="margin-top: 8px;">Save Details</button>
        </form>
      </details>

      <form action="/delete" method="post" onsubmit="return confirm('Delete this game permanently?');" style="margin-top: 15px;">
        <button type="submit" style="color: red;">Delete This Game</button>
      </form>

      <!-- Hidden form triggered by drag-and-drop -->
      <form id="hiddenMoveForm" action="/move" method="post" style="display:none;">
        <input type="hidden" id="hiddenMoveInput" name="move">
      </form>
    </div>

    <!-- Move History List -->
    <div class="history-col">
      <h3 style="margin-top:0; font-family:sans-serif; text-align:center;">History</h3>
      {% for row in history %}
        <div class="move-row">{{ row }}</div>
      {% endfor %}
      {% if not history %}
        <div style="color:#999; text-align:center; margin-top:20px;">No moves yet</div>
      {% endif %}
    </div>
  </div>

  <script>
    // Initialize the logic layer with the current FEN from the server
    var game = new Chess('{{ fen }}');
    var board = null;
    
    // Highlight colors
    var whiteSquareGrey = '#a9a9a9';
    var blackSquareGrey = '#696969';

    function removeGreySquares () {
      $('#myBoard .square-55d63').css('background', '');
    }

    function greySquare (square) {
      var $square = $('#myBoard .square-' + square);
      var background = whiteSquareGrey;
      if ($square.hasClass('black-3c85d')) {
        background = blackSquareGrey;
      }
      $square.css('background', background);
    }

    function onDragStart (source, piece) {
      // Do not pick up pieces if the game is over
      if (game.game_over()) return false;

      // Only pick up pieces for the side to move
      if ((game.turn() === 'w' && piece.search(/^b/) !== -1) ||
          (game.turn() === 'b' && piece.search(/^w/) !== -1)) {
        return false;
      }
    }

    function onDrop (source, target) {
      removeGreySquares();

      // See if the move is legal
      var move = game.move({
        from: source,
        to: target,
        promotion: 'q' // Always promote to queen for simplicity
      });

      // If illegal move, snap piece back to original square
      if (move === null) return 'snapback';

      // It's a legal move! Send the standard notation (SAN) to the server
      document.getElementById('hiddenMoveInput').value = move.san;
      document.getElementById('hiddenMoveForm').submit();
    }

    function onMouseoverSquare (square, piece) {
      // Get list of possible moves for this square
      var moves = game.moves({
        square: square,
        verbose: true
      });

      if (moves.length === 0) return;

      // Highlight the square they hovered/clicked
      greySquare(square);

      // Highlight the target squares
      for (var i = 0; i < moves.length; i++) {
        greySquare(moves[i].to);
      }
    }

    function onMouseoutSquare (square, piece) {
      removeGreySquares();
    }

    function onSnapEnd () {
      board.position(game.fen());
    }

    var config = {
      draggable: true,
      position: '{{ fen }}',
      pieceTheme: 'https://chessboardjs.com/img/chesspieces/wikipedia/{piece}.png',
      onDragStart: onDragStart,
      onDrop: onDrop,
      onMouseoutSquare: onMouseoutSquare,
      onMouseoverSquare: onMouseoverSquare,
      onSnapEnd: onSnapEnd
    };
    
    board = Chessboard('myBoard', config);
  </script>
</body>
</html>
"""

def get_history_rows():
    history = []
    temp_board = game.board()
    move_str = ""
    for idx, move in enumerate(game.mainline_moves()):
        san_move = temp_board.san(move)
        if idx % 2 == 0:
            move_str = f"{temp_board.fullmove_number}. {san_move}"
        else:
            move_str += f" {san_move}"
            history.append(move_str)
            move_str = ""
        temp_board.push(move)
        
    if move_str:
        history.append(move_str)
    return history

@app.route("/")
def index():
    board = current_node.board()
    can_back = current_node.parent is not None
    can_forward = len(current_node.variations) > 0
    history = get_history_rows()

    return render_template_string(
        TEMPLATE, 
        fen=board.fen(), 
        board=board,
        can_back=can_back,
        can_forward=can_forward,
        history=history,
        games=list_games(),
        active_id=active_id,
        title=game.headers.get("Event", active_id),
        opponent=game.headers.get("Black", ""),
        header_fields=HEADER_FIELDS,
        headers={k: game.headers.get(k, "") for k in HEADER_FIELDS}
    )

HEADER_FIELDS = ["Event", "Site", "Date", "Round", "White", "Black", "Result"]


@app.route("/headers", methods=["POST"])
def update_headers():
    for key in HEADER_FIELDS:
        if key not in request.form:
            continue
        value = " ".join(request.form[key].split()).replace('"', "'")
        if key == "Result":
            if value not in ("*", "1-0", "0-1", "1/2-1/2"):
                value = "*"
        elif not value:
            value = "?"
        game.headers[key] = value
    save_game()
    return redirect("/")

@app.route("/move", methods=["POST"])
def move():
    global game, current_node
    san = request.form.get("move", "").strip()
    try:
        board = current_node.board()
        parsed_move = board.parse_san(san)
        
        if parsed_move not in [v.move for v in current_node.variations]:
            current_node.variations.clear()
            current_node = current_node.add_variation(parsed_move)
        else:
            current_node = current_node.variation(parsed_move)

        save_game()
    except Exception:
        pass
    return redirect("/")

@app.route("/back", methods=["POST"])
def back():
    global current_node
    if current_node.parent is not None:
        current_node = current_node.parent
    return redirect("/")

@app.route("/forward", methods=["POST"])
def forward():
    global current_node
    if current_node.variations:
        current_node = current_node.variations[0]
    return redirect("/")

@app.route("/new", methods=["POST"])
def new_game():
    title = request.form.get("title", "").strip()
    opponent = request.form.get("opponent", "").strip()
    if not title:
        title = f"Game {len(list_games()) + 1}"
    open_game(create_game(title, opponent))
    return redirect("/")


@app.route("/load", methods=["POST"])
def load():
    game_id = request.form.get("game_id", "")
    if valid_id(game_id):
        open_game(game_id)
    return redirect("/")


@app.route("/delete", methods=["POST"])
def delete():
    if active_id and valid_id(active_id):
        os.remove(game_path(active_id))
    remaining = list_games()
    open_game(remaining[0]["id"] if remaining else create_game("Game 1"))
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)