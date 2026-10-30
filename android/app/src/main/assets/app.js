(function () {
  var HEADER_FIELDS = ["Event", "Site", "Date", "Round", "White", "Black", "Result"];
  var RESULTS = ["*", "1-0", "0-1", "1/2-1/2"];

  // ---- Storage: native app files on Android, localStorage when run in a plain browser ----
  var store;
  if (window.Native) {
    store = {
      list: function () { return JSON.parse(Native.listGames()); },
      save: function (id, text) { return Native.saveGame(id, text); },
      remove: function (id) { return Native.deleteGame(id); },
      getActive: function () { return Native.getActive(); },
      setActive: function (id) { return Native.setActive(id); }
    };
  } else {
    store = {
      list: function () {
        var out = [];
        for (var i = 0; i < localStorage.length; i++) {
          var k = localStorage.key(i);
          if (k.indexOf("rc:game:") === 0) {
            var rec = JSON.parse(localStorage.getItem(k));
            out.push({ id: k.slice(8), mtime: rec.mtime, text: rec.text });
          }
        }
        return out;
      },
      save: function (id, text) {
        localStorage.setItem("rc:game:" + id, JSON.stringify({ mtime: Date.now(), text: text }));
        return true;
      },
      remove: function (id) { localStorage.removeItem("rc:game:" + id); return true; },
      getActive: function () { return localStorage.getItem("rc:active") || ""; },
      setActive: function (id) { localStorage.setItem("rc:active", id); return true; }
    };
  }

  // ---- PGN ----
  function parsePgn(text) {
    var headers = {};
    var re = /^\[(\w+)\s+"((?:[^"\\]|\\.)*)"\]\s*$/gm;
    var m;
    while ((m = re.exec(text)) !== null) {
      headers[m[1]] = m[2].replace(/\\(["\\])/g, "$1");
    }
    var body = text.replace(/^\[.*\]\s*$/gm, "").replace(/^%.*$/gm, "")
      .replace(/\{[^}]*\}/g, " ").replace(/;[^\n]*/g, " ");
    var depth = 0, flat = "";
    for (var i = 0; i < body.length; i++) {
      var c = body[i];
      if (c === "(") depth++;
      else if (c === ")") { if (depth > 0) depth--; }
      else if (depth === 0) flat += c;
    }
    var chess = new Chess();
    var moves = [];
    var tokens = flat.replace(/\$\d+/g, " ").split(/\s+/);
    for (var t = 0; t < tokens.length; t++) {
      var tok = tokens[t].replace(/^\d+\.+/, "");
      if (!tok || RESULTS.indexOf(tok) !== -1) continue;
      var mv = chess.move(tok, { sloppy: true });
      if (!mv) break;
      moves.push(mv.san);
    }
    return { headers: headers, moves: moves };
  }

  function toPgn(headers, moves) {
    var keys = HEADER_FIELDS.concat(Object.keys(headers).filter(function (k) {
      return HEADER_FIELDS.indexOf(k) === -1;
    }));
    var lines = keys.map(function (k) {
      var v = headers[k] === undefined ? (k === "Result" ? "*" : "?") : headers[k];
      return "[" + k + ' "' + String(v).replace(/\\/g, "\\\\").replace(/"/g, '\\"') + '"]';
    });
    var words = [];
    moves.forEach(function (san, i) {
      if (i % 2 === 0) words.push((i / 2 + 1) + ".");
      words.push(san);
    });
    words.push(headers.Result || "*");
    var text = "", line = "";
    words.forEach(function (w) {
      if (line && (line + " " + w).length > 80) { text += line + "\n"; line = w; }
      else line = line ? line + " " + w : w;
    });
    return lines.join("\n") + "\n\n" + text + line + "\n\n";
  }

  // ---- Game state: mainline SAN list plus a pointer to the current position ----
  var activeId = null;
  var headers = {};
  var moves = [];
  var idx = 0;
  var pos = new Chess();
  var board = null;

  function slugify(text) {
    var slug = text.replace(/[^A-Za-z0-9_-]+/g, "-").replace(/^-+|-+$/g, "").toLowerCase();
    return slug.slice(0, 50) || "game";
  }

  function listGames() {
    var games = [];
    store.list().forEach(function (rec) {
      var g = parsePgn(rec.text);
      games.push({
        id: rec.id,
        title: g.headers.Event || rec.id,
        opponent: g.headers.Black || "",
        plies: g.moves.length,
        mtime: rec.mtime
      });
    });
    games.sort(function (a, b) { return b.mtime - a.mtime; });
    return games;
  }

  function saveGame() {
    if (activeId) store.save(activeId, toPgn(headers, moves));
  }

  function createGame(title, opponent) {
    var taken = {};
    store.list().forEach(function (r) { taken[r.id] = true; });
    var base = slugify(title), gid = base, n = 2;
    while (taken[gid]) gid = base + "-" + n++;
    var d = new Date();
    var pad = function (v) { return (v < 10 ? "0" : "") + v; };
    var h = {
      Event: title || "Radio Game",
      Site: "HAM Radio",
      Date: d.getFullYear() + "." + pad(d.getMonth() + 1) + "." + pad(d.getDate()),
      Round: "?",
      White: "Me",
      Black: opponent || "?",
      Result: "*"
    };
    store.save(gid, toPgn(h, []));
    return gid;
  }

  function openGame(id) {
    var rec = store.list().filter(function (r) { return r.id === id; })[0];
    var g = rec ? parsePgn(rec.text) : { headers: {}, moves: [] };
    headers = g.headers;
    moves = g.moves;
    idx = moves.length;
    activeId = id;
    store.setActive(id);
  }

  function initGames() {
    var saved = store.getActive();
    var games = listGames();
    var ids = games.map(function (g) { return g.id; });
    if (saved && ids.indexOf(saved) !== -1) openGame(saved);
    else if (games.length) openGame(games[0].id);
    else openGame(createGame("Game 1"));
  }

  function rebuildPosition() {
    pos = new Chess();
    for (var i = 0; i < idx; i++) pos.move(moves[i], { sloppy: true });
  }

  function applyMove(text) {
    var m = pos.move(text.trim(), { sloppy: true });
    if (!m) return false;
    if (moves[idx] === m.san) {
      idx++;
    } else {
      moves.length = idx;
      moves.push(m.san);
      idx++;
    }
    saveGame();
    render();
    return true;
  }

  // ---- Rendering ----
  function render() {
    rebuildPosition();
    var opp = headers.Black || "";
    var title = (headers.Event || activeId) + (opp && opp !== "?" ? " vs " + opp : "");
    $("#gameTitle").text(title);
    $("#turn").text(pos.turn() === "w" ? "White" : "Black");
    $("#backBtn").prop("disabled", idx === 0);
    $("#forwardBtn").prop("disabled", idx >= moves.length);

    var $hist = $("#history").empty();
    for (var i = 0; i < moves.length; i += 2) {
      var row = (i / 2 + 1) + ". " + moves[i] + (moves[i + 1] ? " " + moves[i + 1] : "");
      $("<div class='move-row'>").text(row).appendTo($hist);
    }
    if (!moves.length) {
      $("<div>").css({ color: "#999", textAlign: "center", marginTop: "20px" })
        .text("No moves yet").appendTo($hist);
    }

    var $sel = $("#gameSelect").empty();
    listGames().forEach(function (g) {
      var label = g.title + (g.opponent && g.opponent !== "?" ? " vs " + g.opponent : "") +
        " (" + Math.floor((g.plies + 1) / 2) + " moves)";
      $("<option>").val(g.id).text(label).prop("selected", g.id === activeId).appendTo($sel);
    });

    var $form = $("#headersForm");
    if (!$form.data("built")) {
      HEADER_FIELDS.forEach(function (key) {
        var $f = $("<div class='field'>").append($("<label>").text(key));
        if (key === "Result") {
          var $s = $("<select>").attr("name", key);
          RESULTS.forEach(function (r) { $("<option>").val(r).text(r).appendTo($s); });
          $f.append($s);
        } else {
          $f.append($("<input type='text'>").attr("name", key));
        }
        $form.append($f);
      });
      $form.append($("<button type='submit' style='margin-top: 8px;'>Save Details</button>"));
      $form.data("built", true);
    }
    HEADER_FIELDS.forEach(function (key) {
      var v = headers[key] === undefined ? "" : headers[key];
      $form.find("[name='" + key + "']").val(v);
    });

    if (board) board.position(pos.fen());
  }

  // ---- Board ----
  var whiteSquareGrey = "#a9a9a9";
  var blackSquareGrey = "#696969";

  function removeGreySquares() { $("#myBoard .square-55d63").css("background", ""); }

  function greySquare(square) {
    var $sq = $("#myBoard .square-" + square);
    $sq.css("background", $sq.hasClass("black-3c85d") ? blackSquareGrey : whiteSquareGrey);
  }

  function onDragStart(source, piece) {
    if (pos.game_over()) return false;
    if ((pos.turn() === "w" && piece.search(/^b/) !== -1) ||
        (pos.turn() === "b" && piece.search(/^w/) !== -1)) {
      return false;
    }
    // Touch has no hover, so show the legal targets when a piece is picked up.
    var legal = pos.moves({ square: source, verbose: true });
    if (legal.length) {
      greySquare(source);
      legal.forEach(function (m) { greySquare(m.to); });
    }
  }

  function onDrop(source, target) {
    removeGreySquares();
    if (source === target) return;
    var probe = new Chess(pos.fen());
    var move = probe.move({ from: source, to: target, promotion: "q" });
    if (move === null) return "snapback";
    applyMove(move.san);
  }

  function onMouseoverSquare(square) {
    var legal = pos.moves({ square: square, verbose: true });
    if (!legal.length) return;
    greySquare(square);
    legal.forEach(function (m) { greySquare(m.to); });
  }

  function onSnapEnd() { board.position(pos.fen()); }

  // ---- Events ----
  function cleanHeader(key, raw) {
    var value = raw.split(/\s+/).filter(Boolean).join(" ").replace(/"/g, "'");
    if (key === "Result") return RESULTS.indexOf(value) !== -1 ? value : "*";
    return value || "?";
  }

  $(function () {
    initGames();

    board = Chessboard("myBoard", {
      draggable: true,
      position: "start",
      pieceTheme: "img/pieces/{piece}.png",
      onDragStart: onDragStart,
      onDrop: onDrop,
      onMouseoutSquare: removeGreySquares,
      onMouseoverSquare: onMouseoverSquare,
      onSnapEnd: onSnapEnd
    });
    render();
    $(window).on("resize", function () { board.resize(); });

    $("#backBtn").on("click", function () {
      if (idx > 0) { idx--; render(); }
    });
    $("#forwardBtn").on("click", function () {
      if (idx < moves.length) { idx++; render(); }
    });

    $("#moveForm").on("submit", function (e) {
      e.preventDefault();
      var text = $("#moveInput").val().trim();
      if (text) applyMove(text);
      $("#moveInput").val("");
    });

    $("#gameSelect").on("change", function () {
      openGame($(this).val());
      render();
    });

    $("#newForm").on("submit", function (e) {
      e.preventDefault();
      var title = $("#newTitle").val().trim();
      var opponent = $("#newOpponent").val().trim();
      if (!title) title = "Game " + (listGames().length + 1);
      openGame(createGame(title, opponent));
      $("#newTitle, #newOpponent").val("");
      render();
    });

    $("#headersForm").on("submit", function (e) {
      e.preventDefault();
      HEADER_FIELDS.forEach(function (key) {
        headers[key] = cleanHeader(key, String($("#headersForm [name='" + key + "']").val()));
      });
      saveGame();
      render();
    });

    $("#deleteBtn").on("click", function () {
      if (!confirm("Delete this game permanently?")) return;
      if (activeId) store.remove(activeId);
      var remaining = listGames();
      openGame(remaining.length ? remaining[0].id : createGame("Game 1"));
      render();
    });
  });
})();
