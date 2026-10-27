import chess
import chess.pgn
import chess.svg
import os
from flask import Flask, redirect, render_template_string, request

app = Flask(__name__)
PGN_FILE = "radio_games.pgn"

# Global state to track the game history and our current position in it
game = chess.pgn.Game()
current_node = game

def load_game():
    global game, current_node
    if os.path.exists(PGN_FILE):
        with open(PGN_FILE) as f:
            loaded_game = chess.pgn.read_game(f)
            if loaded_game:
                game = loaded_game
                current_node = game.end() # Jump to the latest move

load_game()

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>Radio Chess Tracker</title>
  <style>
    body { font-family: sans-serif; padding: 20px; background: #f0f0f0; }
    .app-container { 
      display: flex; 
      max-width: 650px; 
      margin: 0 auto; 
      background: white; 
      padding: 20px; 
      border-radius: 8px; 
      box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
      gap: 20px; 
      flex-wrap: wrap; 
      justify-content: center; 
    }
    .board-col { width: 360px; text-align: center; }
    .history-col { 
      width: 200px; 
      background: #fafafa; 
      border: 1px solid #ccc; 
      padding: 10px; 
      border-radius: 4px; 
      height: 440px; 
      overflow-y: auto; 
      font-family: monospace; 
      font-size: 16px; 
    }
    .move-row { padding: 4px; border-bottom: 1px solid #eee; }
    .controls { margin: 15px 0; display: flex; justify-content: center; gap: 10px; }
    button { padding: 8px 12px; cursor: pointer; }
    input[type="text"] { padding: 8px; width: 150px; }
  </style>
</head>
<body>
  <h2 style="text-align: center; margin-top: 0;">Radio Chess Station</h2>
  <div class="app-container">
    
    <div class="board-col">
      <div>{{ svg|safe }}</div>
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

      <form action="/move" method="post">
        <input type="text" name="move" placeholder="e.g. e4, Nf3" autofocus required>
        <button type="submit">Submit Move</button>
      </form>
      
      <form action="/reset" method="post" onsubmit="return confirm('Reset board? This will delete the game history.');" style="margin-top: 20px;">
        <button type="submit" style="color: red;">New Game</button>
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
</body>
</html>
"""

def get_history_rows():
    """Formats the game moves into a list like ['1. e4 e5', '2. Nf3 d6']"""
    history = []
    temp_board = game.board()
    move_str = ""
    for idx, move in enumerate(game.mainline_moves()):
        san_move = temp_board.san(move)
        if idx % 2 == 0:
            # White's move: start a new row
            move_str = f"{temp_board.fullmove_number}. {san_move}"
        else:
            # Black's move: append to the row and save
            move_str += f" {san_move}"
            history.append(move_str)
            move_str = ""
        temp_board.push(move)
        
    # If the game ends on White's move, push the unfinished row
    if move_str:
        history.append(move_str)
    return history

@app.route("/")
def index():
    board = current_node.board()
    
    # Highlight the last move played on the SVG
    lastmove = current_node.move if current_node.parent is not None else None
    
    svg = chess.svg.board(
        board=board, 
        size=360, 
        lastmove=lastmove
    )
    
    # Check if we can go back or forward based on our position in the tree
    can_back = current_node.parent is not None
    can_forward = len(current_node.variations) > 0
    history = get_history_rows()

    return render_template_string(
        TEMPLATE, 
        svg=svg, 
        board=board,
        can_back=can_back,
        can_forward=can_forward,
        history=history
    )

@app.route("/move", methods=["POST"])
def move():
    global game, current_node
    san = request.form.get("move", "").strip()
    try:
        board = current_node.board()
        parsed_move = board.parse_san(san)
        
        # If the user makes a NEW move while looking at the past, 
        # delete the old future moves and start a new branch.
        if parsed_move not in [v.move for v in current_node.variations]:
            current_node.variations.clear()
            current_node = current_node.add_variation(parsed_move)
        else:
            # If they happen to type in the exact move that was already next,
            # just treat it like clicking the Forward button.
            current_node = current_node.variation(parsed_move)

        with open(PGN_FILE, "w") as f:
            f.write(str(game))
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
        # Move forward along the main line
        current_node = current_node.variations[0]
    return redirect("/")

@app.route("/reset", methods=["POST"])
def reset():
    global game, current_node
    game = chess.pgn.Game()
    current_node = game
    if os.path.exists(PGN_FILE):
        os.remove(PGN_FILE)
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)