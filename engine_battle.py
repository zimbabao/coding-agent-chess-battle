#!/usr/bin/env python3
"""
Chess Engine Battle System

A system that allows two different chess engines to play against each other
with a web interface to watch the games live.

Features:
- Engine vs Engine games
- Web interface with live move display
- Game control (start, pause, reset)
- Move history and analysis
- Multiple game formats (standard, Chess960)
"""

import sys
import os
import time
import threading
import json
import http.server
import socketserver
import webbrowser
import urllib.parse
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime

# Add both engine directories to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'augment-chess'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'claude-chess'))

# Import both engines
try:
    from augment_chess.chess_engine import ChessEngine as AugmentEngine
    AUGMENT_AVAILABLE = True
except ImportError:
    try:
        # Try importing from local augment-chess directory
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'augment-chess'))
        from chess_engine import ChessEngine as AugmentEngine
        AUGMENT_AVAILABLE = True
    except ImportError as e:
        print(f"Warning: Could not import Augment engine: {e}")
        AUGMENT_AVAILABLE = False

try:
    from claude_chess.chess_engine import ChessBoard as ClaudeBoard
    CLAUDE_AVAILABLE = True
except ImportError:
    try:
        # Try importing from local claude-chess directory
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'claude-chess'))
        from chess_engine import ChessBoard as ClaudeBoard
        CLAUDE_AVAILABLE = True
    except ImportError as e:
        print(f"Warning: Could not import Claude engine: {e}")
        CLAUDE_AVAILABLE = False

@dataclass
class GameMove:
    """Represents a single move in the game"""
    move_num: int
    player: str
    move: str
    time_taken: float
    evaluation: Optional[float] = None
    
@dataclass
class GameState:
    """Current state of the battle"""
    game_id: str
    white_engine: str
    black_engine: str
    current_position: str  # FEN
    moves: List[GameMove]
    status: str  # 'waiting', 'playing', 'finished'
    result: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None

class EngineWrapper:
    """Wrapper to standardize engine interfaces"""
    
    def __init__(self, engine_type: str, engine_name: str, **kwargs):
        self.engine_type = engine_type
        self.engine_name = engine_name
        self.engine = None
        self._initialize_engine(**kwargs)
    
    def _initialize_engine(self, **kwargs):
        """Initialize the specific engine"""
        if self.engine_type == "augment" and AUGMENT_AVAILABLE:
            chess960 = kwargs.get('chess960', False)
            position_id = kwargs.get('position_id', None)
            self.engine = AugmentEngine(chess960=chess960, position_id=position_id)
        elif self.engine_type == "claude" and CLAUDE_AVAILABLE:
            chess960 = kwargs.get('chess960', False)
            position_id = kwargs.get('position_id', None)
            self.engine = ClaudeBoard(chess960=chess960, position_id=position_id)
        else:
            raise ValueError(f"Engine type '{self.engine_type}' not available")
    
    def get_best_move(self, depth: int = 4, time_limit: float = 5.0) -> Tuple[str, float]:
        """Get the best move from the engine"""
        start_time = time.time()
        
        if self.engine_type == "augment":
            try:
                move, score = self.engine.get_best_move(depth=depth, time_limit=time_limit)
                if move:
                    # Convert move object to UCI string
                    move_str = str(move)  # Move class has __str__ method that returns UCI format
                else:
                    move_str = None
                elapsed = time.time() - start_time
                return move_str, elapsed
            except Exception as e:
                print(f"Augment engine error: {e}")
                return None, time.time() - start_time
                
        elif self.engine_type == "claude":
            try:
                move_str, score = self.engine.search(depth)
                elapsed = time.time() - start_time
                return move_str, elapsed
            except Exception as e:
                print(f"Claude engine error: {e}")
                return None, time.time() - start_time
        
        return None, 0.0
    
    def make_move(self, move_str: str) -> bool:
        """Make a move on the engine's board"""
        if self.engine_type == "augment":
            return self.engine.make_move(move_str)
        elif self.engine_type == "claude":
            return self.engine.make_move(move_str)
        return False
    
    def is_game_over(self) -> Tuple[bool, Optional[str]]:
        """Check if the game is over"""
        if self.engine_type == "augment":
            return self.engine.is_game_over()
        elif self.engine_type == "claude":
            # Implement basic game over detection for Claude engine
            moves = self.engine.generate_moves()
            if not moves:
                if self.engine.is_in_check():
                    color = "White" if self.engine.white_to_move else "Black"
                    winner = "Black" if self.engine.white_to_move else "White"
                    return True, f"{winner} wins by checkmate"
                else:
                    return True, "Draw by stalemate"
            return False, None
        return False, None
    
    def get_board_state(self) -> str:
        """Get current board state as string for display"""
        if self.engine_type == "augment":
            return str(self.engine.board)
        elif self.engine_type == "claude":
            return self.engine.display_board()
        return ""
    
    def reset(self):
        """Reset the engine to starting position"""
        if self.engine_type == "augment":
            self.engine.reset_game()
        elif self.engine_type == "claude":
            # Reinitialize the Claude engine
            kwargs = {}
            if hasattr(self.engine, 'chess960'):
                kwargs['chess960'] = self.engine.chess960
            self._initialize_engine(**kwargs)

class EngineBattle:
    """Main class managing engine battles"""
    
    def __init__(self, port: int = 8001):
        self.port = port
        self.games: Dict[str, GameState] = {}
        self.current_game: Optional[GameState] = None
        self.game_thread: Optional[threading.Thread] = None
        self.stop_game = threading.Event()
        
    def create_game(self, white_engine: str, black_engine: str, 
                   game_format: str = "standard", **kwargs) -> str:
        """Create a new game between two engines"""
        game_id = f"game_{int(time.time())}"
        
        # Initialize engines
        engine_kwargs = {}
        if game_format == "chess960":
            engine_kwargs['chess960'] = True
            if 'position_id' in kwargs:
                engine_kwargs['position_id'] = kwargs['position_id']
        
        game_state = GameState(
            game_id=game_id,
            white_engine=white_engine,
            black_engine=black_engine,
            current_position="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            moves=[],
            status="waiting",
            start_time=datetime.now().isoformat()
        )
        
        self.games[game_id] = game_state
        self.current_game = game_state
        
        return game_id
    
    def start_game(self, game_id: str, depth: int = 4, move_time: float = 5.0):
        """Start a game"""
        if game_id not in self.games:
            raise ValueError(f"Game {game_id} not found")
        
        game = self.games[game_id]
        if game.status != "waiting":
            raise ValueError(f"Game {game_id} is not in waiting state")
        
        game.status = "playing"
        self.stop_game.clear()
        
        # Start game thread
        self.game_thread = threading.Thread(
            target=self._run_game, 
            args=(game, depth, move_time),
            daemon=True
        )
        self.game_thread.start()
    
    def _run_game(self, game: GameState, depth: int, move_time: float):
        """Run the actual game between engines"""
        try:
            # Parse game format from game settings
            game_format = "chess960" if "960" in str(game.white_engine + game.black_engine) else "standard"
            
            # Initialize engines
            white_engine = EngineWrapper(
                engine_type=game.white_engine.split()[0].lower(),
                engine_name=game.white_engine,
                chess960=(game_format == "chess960")
            )
            black_engine = EngineWrapper(
                engine_type=game.black_engine.split()[0].lower(), 
                engine_name=game.black_engine,
                chess960=(game_format == "chess960")
            )
            
            current_engine = white_engine
            move_num = 1
            
            print(f"Starting game: {game.white_engine} vs {game.black_engine}")
            
            while not self.stop_game.is_set():
                # Check if game is over
                game_over, result = current_engine.is_game_over()
                if game_over:
                    game.result = result
                    game.status = "finished"
                    game.end_time = datetime.now().isoformat()
                    print(f"Game finished: {result}")
                    break
                
                # Get move from current engine
                print(f"Move {move_num}, {current_engine.engine_name} thinking...")
                move_str, time_taken = current_engine.get_best_move(depth, move_time)
                
                if not move_str:
                    print("Engine returned no move - game over")
                    game.result = "Engine error"
                    game.status = "finished"
                    break
                
                # Make move on both engines
                if not current_engine.make_move(move_str):
                    print(f"Invalid move from engine: {move_str}")
                    game.result = f"Invalid move by {current_engine.engine_name}"
                    game.status = "finished"
                    break
                
                other_engine = black_engine if current_engine == white_engine else white_engine
                if not other_engine.make_move(move_str):
                    print(f"Move rejected by other engine: {move_str}")
                    # Continue anyway - engines might have different validation
                
                # Record move
                player = "White" if current_engine == white_engine else "Black"
                game_move = GameMove(
                    move_num=move_num,
                    player=player,
                    move=move_str,
                    time_taken=time_taken
                )
                game.moves.append(game_move)
                
                print(f"Move {move_num}: {player} plays {move_str} (took {time_taken:.2f}s)")
                
                # Switch players
                current_engine = black_engine if current_engine == white_engine else white_engine
                if player == "Black":
                    move_num += 1
                
                # Update board state
                game.current_position = current_engine.get_board_state()
                
                # Short delay between moves
                time.sleep(0.5)
                
        except Exception as e:
            print(f"Error in game: {e}")
            game.result = f"Error: {e}"
            game.status = "finished"
            game.end_time = datetime.now().isoformat()
    
    def stop_current_game(self):
        """Stop the current game"""
        self.stop_game.set()
        if self.game_thread:
            self.game_thread.join(timeout=5.0)
    
    def get_game_state(self, game_id: str) -> Optional[Dict]:
        """Get current game state"""
        if game_id in self.games:
            return asdict(self.games[game_id])
        return None
    
    def list_games(self) -> List[Dict]:
        """List all games"""
        return [asdict(game) for game in self.games.values()]

# Web server for the battle interface
class BattleWebServer:
    def __init__(self, battle: EngineBattle):
        self.battle = battle
    
    def create_handler(self):
        battle = self.battle
        
        class BattleHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/':
                    self.send_battle_page()
                elif self.path.startswith('/api/'):
                    self.handle_api_get()
                else:
                    super().do_GET()
            
            def do_POST(self):
                if self.path.startswith('/api/'):
                    self.handle_api_post()
                else:
                    self.send_error(404)
            
            def handle_api_get(self):
                parts = self.path.split('/')
                
                if parts[2] == 'games':
                    if len(parts) == 3:
                        # List all games
                        games = battle.list_games()
                        self.send_json_response(games)
                    elif len(parts) == 4:
                        # Get specific game
                        game_id = parts[3]
                        game = battle.get_game_state(game_id)
                        if game:
                            self.send_json_response(game)
                        else:
                            self.send_error(404, "Game not found")
                else:
                    self.send_error(404)
            
            def handle_api_post(self):
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                parts = self.path.split('/')
                
                if parts[2] == 'create_game':
                    white_engine = data.get('white_engine', 'Augment Engine')
                    black_engine = data.get('black_engine', 'Claude Engine') 
                    game_format = data.get('format', 'standard')
                    
                    try:
                        game_id = battle.create_game(white_engine, black_engine, game_format, **data)
                        self.send_json_response({'game_id': game_id, 'status': 'created'})
                    except Exception as e:
                        self.send_json_response({'error': str(e)}, status=400)
                
                elif parts[2] == 'start_game':
                    game_id = data.get('game_id')
                    depth = data.get('depth', 4)
                    move_time = data.get('move_time', 5.0)
                    
                    try:
                        battle.start_game(game_id, depth, move_time)
                        self.send_json_response({'status': 'started'})
                    except Exception as e:
                        self.send_json_response({'error': str(e)}, status=400)
                
                elif parts[2] == 'stop_game':
                    battle.stop_current_game()
                    self.send_json_response({'status': 'stopped'})
                
                else:
                    self.send_error(404)
            
            def send_json_response(self, data, status=200):
                self.send_response(status)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(data, indent=2).encode())
            
            def send_battle_page(self):
                html_content = self.get_battle_html()
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(html_content.encode())
            
            def get_battle_html(self):
                return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chess Engine Battle</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
        }
        .content {
            display: grid;
            grid-template-columns: 1fr 400px;
            gap: 20px;
            padding: 20px;
            min-height: 600px;
        }
        .game-area {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
        }
        .controls {
            background: #fff;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
        }
        .chess-board {
            display: grid;
            grid-template-columns: repeat(8, 50px);
            grid-template-rows: repeat(8, 50px);
            gap: 1px;
            margin: 20px auto;
            border: 2px solid #8B4513;
            width: fit-content;
        }
        .square {
            width: 50px;
            height: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 32px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.2s;
        }
        .square.light {
            background: #F0D9B5;
        }
        .square.dark {
            background: #B58863;
        }
        .square:hover {
            transform: scale(1.05);
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }
        .game-info {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .moves-list {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            background: #fafafa;
        }
        .move-item {
            padding: 5px 10px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .move-item:last-child {
            border-bottom: none;
        }
        .move-item.white {
            background: #fff;
        }
        .move-item.black {
            background: #f5f5f5;
        }
        button {
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            margin: 5px;
            font-size: 14px;
            transition: background 0.2s;
        }
        button:hover {
            background: #0056b3;
        }
        button:disabled {
            background: #6c757d;
            cursor: not-allowed;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
        }
        select, input {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        .status {
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 15px;
            font-weight: 600;
        }
        .status.waiting {
            background: #fff3cd;
            color: #856404;
        }
        .status.playing {
            background: #d1ecf1;
            color: #0c5460;
        }
        .status.finished {
            background: #d4edda;
            color: #155724;
        }
        .engine-info {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 20px;
        }
        .engine-card {
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .engine-white {
            background: #f8f9fa;
            border: 2px solid #fff;
        }
        .engine-black {
            background: #343a40;
            color: white;
            border: 2px solid #000;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚔️ Chess Engine Battle Arena ⚔️</h1>
            <p>Watch AI chess engines battle it out in real-time</p>
        </div>
        
        <div class="content">
            <div class="game-area">
                <div id="gameInfo" class="game-info">
                    <h3>No active game</h3>
                    <p>Create a new game to start the battle!</p>
                </div>
                
                <div id="engineInfo" class="engine-info" style="display: none;">
                    <div class="engine-card engine-white">
                        <h4>⚪ White</h4>
                        <p id="whiteEngine">-</p>
                    </div>
                    <div class="engine-card engine-black">
                        <h4>⚫ Black</h4>
                        <p id="blackEngine">-</p>
                    </div>
                </div>
                
                <div id="chessBoard" class="chess-board">
                    <!-- Board will be generated by JavaScript -->
                </div>
                
                <div id="movesList" class="moves-list" style="display: none;">
                    <h4>Move History</h4>
                    <div id="movesContent"></div>
                </div>
            </div>
            
            <div class="controls">
                <div id="gameStatus" class="status waiting">
                    Ready to start
                </div>
                
                <div class="form-group">
                    <label>White Engine:</label>
                    <select id="whiteEngineSelect">
                        <option value="augment">Augment Engine</option>
                        <option value="claude">Claude Engine</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Black Engine:</label>
                    <select id="blackEngineSelect">
                        <option value="claude">Claude Engine</option>
                        <option value="augment">Augment Engine</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Game Format:</label>
                    <select id="gameFormat">
                        <option value="standard">Standard Chess</option>
                        <option value="chess960">Chess960 (Fischer Random)</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Search Depth:</label>
                    <input type="number" id="searchDepth" min="1" max="10" value="4">
                </div>
                
                <div class="form-group">
                    <label>Time per Move (seconds):</label>
                    <input type="number" id="moveTime" min="1" max="30" value="5" step="0.5">
                </div>
                
                <button id="createGameBtn" onclick="createGame()">Create New Game</button>
                <button id="startGameBtn" onclick="startGame()" disabled>Start Battle</button>
                <button id="stopGameBtn" onclick="stopGame()" disabled>Stop Game</button>
                <button id="refreshBtn" onclick="refreshGameState()">Refresh</button>
            </div>
        </div>
    </div>

    <script>
        let currentGameId = null;
        let refreshInterval = null;
        
        // Unicode chess pieces
        const pieceUnicode = {
            'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
            'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
        };
        
        // Initialize chess board display
        function initializeBoard() {
            const board = document.getElementById('chessBoard');
            board.innerHTML = '';
            
            // Standard starting position
            const startingPos = [
                ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
                ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
                ['.', '.', '.', '.', '.', '.', '.', '.'],
                ['.', '.', '.', '.', '.', '.', '.', '.'],
                ['.', '.', '.', '.', '.', '.', '.', '.'],
                ['.', '.', '.', '.', '.', '.', '.', '.'],
                ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
                ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
            ];
            
            for (let rank = 0; rank < 8; rank++) {
                for (let file = 0; file < 8; file++) {
                    const square = document.createElement('div');
                    square.className = `square ${(rank + file) % 2 === 0 ? 'light' : 'dark'}`;
                    
                    const piece = startingPos[rank][file];
                    if (piece !== '.') {
                        square.textContent = pieceUnicode[piece] || piece;
                    }
                    
                    board.appendChild(square);
                }
            }
        }
        
        async function createGame() {
            const whiteEngine = document.getElementById('whiteEngineSelect').value;
            const blackEngine = document.getElementById('blackEngineSelect').value;
            const gameFormat = document.getElementById('gameFormat').value;
            
            if (whiteEngine === blackEngine) {
                alert('Please select different engines for white and black');
                return;
            }
            
            try {
                const response = await fetch('/api/create_game', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        white_engine: whiteEngine + ' Engine',
                        black_engine: blackEngine + ' Engine',
                        format: gameFormat
                    })
                });
                
                const result = await response.json();
                
                if (result.error) {
                    alert('Error creating game: ' + result.error);
                } else {
                    currentGameId = result.game_id;
                    document.getElementById('startGameBtn').disabled = false;
                    document.getElementById('createGameBtn').disabled = true;
                    updateGameStatus('Game created! Ready to start.');
                    
                    // Show engine info
                    document.getElementById('whiteEngine').textContent = whiteEngine + ' Engine';
                    document.getElementById('blackEngine').textContent = blackEngine + ' Engine';
                    document.getElementById('engineInfo').style.display = 'grid';
                }
            } catch (error) {
                alert('Error creating game: ' + error.message);
            }
        }
        
        async function startGame() {
            if (!currentGameId) return;
            
            const depth = parseInt(document.getElementById('searchDepth').value);
            const moveTime = parseFloat(document.getElementById('moveTime').value);
            
            try {
                const response = await fetch('/api/start_game', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        game_id: currentGameId,
                        depth: depth,
                        move_time: moveTime
                    })
                });
                
                const result = await response.json();
                
                if (result.error) {
                    alert('Error starting game: ' + result.error);
                } else {
                    document.getElementById('startGameBtn').disabled = true;
                    document.getElementById('stopGameBtn').disabled = false;
                    updateGameStatus('Battle in progress!');
                    
                    // Start auto-refresh
                    refreshInterval = setInterval(refreshGameState, 1000);
                    
                    // Show moves list
                    document.getElementById('movesList').style.display = 'block';
                }
            } catch (error) {
                alert('Error starting game: ' + error.message);
            }
        }
        
        async function stopGame() {
            try {
                await fetch('/api/stop_game', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({})
                });
                
                document.getElementById('stopGameBtn').disabled = true;
                updateGameStatus('Game stopped');
                
                if (refreshInterval) {
                    clearInterval(refreshInterval);
                    refreshInterval = null;
                }
                
            } catch (error) {
                alert('Error stopping game: ' + error.message);
            }
        }
        
        async function refreshGameState() {
            if (!currentGameId) return;
            
            try {
                const response = await fetch(`/api/games/${currentGameId}`);
                const game = await response.json();
                
                if (game.error) {
                    console.error('Error fetching game state:', game.error);
                    return;
                }
                
                // Update status
                let statusText = '';
                let statusClass = game.status;
                
                switch (game.status) {
                    case 'waiting':
                        statusText = 'Waiting to start';
                        break;
                    case 'playing':
                        statusText = `Battle in progress (${game.moves.length} moves)`;
                        break;
                    case 'finished':
                        statusText = `Finished: ${game.result}`;
                        statusClass = 'finished';
                        if (refreshInterval) {
                            clearInterval(refreshInterval);
                            refreshInterval = null;
                        }
                        document.getElementById('stopGameBtn').disabled = true;
                        document.getElementById('createGameBtn').disabled = false;
                        break;
                }
                
                updateGameStatus(statusText, statusClass);
                
                // Update moves list
                const movesContent = document.getElementById('movesContent');
                movesContent.innerHTML = '';
                
                game.moves.forEach((move, index) => {
                    const moveDiv = document.createElement('div');
                    moveDiv.className = `move-item ${move.player.toLowerCase()}`;
                    moveDiv.innerHTML = `
                        <span>${move.move_num}. ${move.move}</span>
                        <span>${move.player} (${move.time_taken.toFixed(2)}s)</span>
                    `;
                    movesContent.appendChild(moveDiv);
                });
                
                // Auto scroll to bottom
                movesContent.scrollTop = movesContent.scrollHeight;
                
            } catch (error) {
                console.error('Error refreshing game state:', error);
            }
        }
        
        function updateGameStatus(text, className = 'waiting') {
            const statusDiv = document.getElementById('gameStatus');
            statusDiv.textContent = text;
            statusDiv.className = `status ${className}`;
        }
        
        // Initialize the page
        document.addEventListener('DOMContentLoaded', function() {
            initializeBoard();
            updateGameStatus('Ready to create a new game');
        });
    </script>
</body>
</html>'''
        
        return BattleHandler

def main():
    """Main function to run the engine battle"""
    print("Chess Engine Battle System")
    print("=" * 40)
    
    # Check engine availability
    print("Checking engine availability...")
    print(f"Augment Engine: {'Available' if AUGMENT_AVAILABLE else 'Not Available'}")
    print(f"Claude Engine: {'Available' if CLAUDE_AVAILABLE else 'Not Available'}")
    
    if not AUGMENT_AVAILABLE and not CLAUDE_AVAILABLE:
        print("No engines available! Please check your installation.")
        return
    
    # Initialize battle system
    battle = EngineBattle(port=8001)
    web_server = BattleWebServer(battle)
    
    # Start web server
    try:
        with socketserver.TCPServer(("", battle.port), web_server.create_handler()) as httpd:
            print(f"\nChess Engine Battle web interface starting on port {battle.port}")
            print(f"Open your browser to: http://localhost:{battle.port}")
            print("\nPress Ctrl+C to stop the server")
            
            # Try to open browser automatically
            try:
                webbrowser.open(f'http://localhost:{battle.port}')
            except:
                pass
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\nShutting down server...")
        battle.stop_current_game()
        print("Server stopped.")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == "__main__":
    main()