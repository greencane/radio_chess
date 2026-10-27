import chess
import chess.pgn
import os
from flask import Flask, redirect, render_template_string, request

app = Flask(__name__)
PGN_FILE = "radio_games.pgn"

# Global state to track the game history
game = chess.pgn.Game()
current_node = game

def load_game():
    global game, current_node
    if os.path.exists(PGN_FILE):
        with open(PGN_FILE) as f:
            loaded_game = chess.pgn.read_game(f)
            if loaded_game:
                game = loaded_game
                current_node = game.end()

load_game()

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
      
      <form action="/reset" method="post" onsubmit="return confirm('Reset board? This will delete the game history.');" style="margin-top: 20px;">
        <button type="submit" style="color: red;">New Game</button>
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
        history=history
    )

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