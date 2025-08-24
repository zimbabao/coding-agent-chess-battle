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

# Import both engines with proper isolation
AUGMENT_AVAILABLE = False
CLAUDE_AVAILABLE = False
AugmentEngine = None
ClaudeBoard = None

# Import Augment engine with proper isolation
try:
    import importlib.util
    augment_path = os.path.join(os.path.dirname(__file__), 'augment-chess', 'chess_engine.py')
    spec = importlib.util.spec_from_file_location("augment_engine_module", augment_path)
    augment_module = importlib.util.module_from_spec(spec)

    # Add augment-chess to path temporarily for imports
    augment_dir = os.path.join(os.path.dirname(__file__), 'augment-chess')
    if augment_dir not in sys.path:
        sys.path.insert(0, augment_dir)

    spec.loader.exec_module(augment_module)
    AugmentEngine = augment_module.ChessEngine
    AUGMENT_AVAILABLE = True

    # Clean up path
    sys.path = [p for p in sys.path if 'augment-chess' not in p]
    print("Successfully imported Augment engine")

except Exception as e:
    print(f"Warning: Could not import Augment engine: {e}")

# Import Claude engine with proper isolation
try:
    import importlib.util
    claude_path = os.path.join(os.path.dirname(__file__), 'claude-chess', 'chess_engine.py')
    spec = importlib.util.spec_from_file_location("claude_engine_module", claude_path)
    claude_module = importlib.util.module_from_spec(spec)

    # Add claude-chess to path temporarily for imports
    claude_dir = os.path.join(os.path.dirname(__file__), 'claude-chess')
    if claude_dir not in sys.path:
        sys.path.insert(0, claude_dir)

    spec.loader.exec_module(claude_module)
    ClaudeBoard = claude_module.ChessBoard
    CLAUDE_AVAILABLE = True

    # Clean up path
    sys.path = [p for p in sys.path if 'claude-chess' not in p]
    print("Successfully imported Claude engine")

except Exception as e:
    print(f"Warning: Could not import Claude engine: {e}")

class HumanPlayer:
    """Simple human player interface"""
    def __init__(self):
        self.white_to_move = True
        self.pending_move = None
        self.captured_pieces = {'white': [], 'black': []}

    def generate_moves(self):
        # Return empty list - human will input move via web interface
        return []

    def make_move(self, move_str: str) -> bool:
        # Simple validation - assume move is valid for now
        # In a real implementation, we'd validate against chess rules
        self.white_to_move = not self.white_to_move
        return True

    def is_in_check(self):
        return False  # Simplified for now

    def get_pending_move(self):
        move = self.pending_move
        self.pending_move = None
        return move

    def set_move(self, move_str: str):
        self.pending_move = move_str

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
        elif self.engine_type == "human":
            # Human player - we'll use a simple board representation
            self.engine = HumanPlayer()
        else:
            raise ValueError(f"Engine type '{self.engine_type}' not available")

    def get_best_move(self, depth: int = 4, time_limit: float = 5.0) -> Tuple[str, float]:
        """Get the best move from the engine"""
        start_time = time.time()

        if self.engine_type == "augment":
            try:
                # Augment engine returns just a Move object
                move = self.engine.get_best_move(depth=depth, time_limit=time_limit)
                if move:
                    # Convert move object to UCI string
                    move_str = str(move)  # Move class has __str__ method that returns UCI format
                else:
                    move_str = None
                elapsed = time.time() - start_time
                return move_str, elapsed
            except Exception as e:
                print(f"Augment engine error: {e}")
                import traceback
                print(f"Augment engine traceback: {traceback.format_exc()}")
                return None, time.time() - start_time

        elif self.engine_type == "claude":
            try:
                # Claude engine: get moves and pick the first one (simple strategy)
                moves = self.engine.generate_moves()  # Fixed: correct method name
                print(f"Claude moves generated: {len(moves) if moves else 0}")
                if moves:
                    print(f"First move type: {type(moves[0])}, value: {repr(moves[0])}")
                    # For now, just take the first legal move
                    # TODO: Add proper search algorithm integration
                    move_str = str(moves[0])  # Ensure it's a string
                else:
                    move_str = None
                elapsed = time.time() - start_time
                return move_str, elapsed
            except Exception as e:
                print(f"Claude engine error: {e}")
                import traceback
                print(f"Claude engine traceback: {traceback.format_exc()}")
                return None, time.time() - start_time

        elif self.engine_type == "human":
            # Wait for human input
            print(f"Waiting for human player move...")
            timeout = time_limit
            while timeout > 0:
                move = self.engine.get_pending_move()
                if move:
                    elapsed = time.time() - start_time
                    return move, elapsed
                time.sleep(0.1)
                timeout -= 0.1

            # Timeout - no move received
            print("Human player timeout")
            return None, time.time() - start_time

        return None, 0.0

    def make_move(self, move_str: str) -> bool:
        """Make a move on the engine's board"""
        try:
            if self.engine_type == "augment":
                return self.engine.make_move(move_str)
            elif self.engine_type == "claude":
                return self.engine.make_move(move_str)
            elif self.engine_type == "human":
                return self.engine.make_move(move_str)
            return False
        except Exception as e:
            print(f"Error making move {move_str} on {self.engine_type}: {e}")
            return False

    def is_game_over(self) -> Tuple[bool, Optional[str]]:
        """Check if the game is over"""
        try:
            if self.engine_type == "augment":
                is_over, result = self.engine.is_game_over()
                if is_over and result:
                    # Improve the result message to clearly show who won
                    if "checkmate" in result.lower():
                        # The player who just moved delivered checkmate, so they won
                        # white_to_move is False when it's white's turn (after black moved)
                        winner = "Black" if self.engine.board.white_to_move else "White"
                        return True, f"{winner} wins by checkmate"
                    elif "stalemate" in result.lower():
                        return True, "Draw by stalemate"
                    else:
                        return True, result
                return is_over, result
            elif self.engine_type == "claude":
                # Use Claude engine's built-in game over detection
                moves = self.engine.generate_moves()
                if not moves:
                    # Check if the current player is in check
                    # We need to create a simple ChessEngine instance to use is_in_check
                    try:
                        # Import ChessEngine from claude module
                        import importlib.util
                        claude_path = os.path.join(os.path.dirname(__file__), 'claude-chess', 'chess_engine.py')
                        spec = importlib.util.spec_from_file_location("claude_engine_module", claude_path)
                        claude_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(claude_module)

                        # Create a temporary engine instance to check for check
                        temp_engine = claude_module.ChessEngine()
                        temp_engine.board = self.engine  # Use our current board state

                        if temp_engine.is_in_check(self.engine):
                            winner = "Black" if self.engine.white_to_move else "White"
                            return True, f"{winner} wins by checkmate"
                        else:
                            return True, "Draw by stalemate"
                    except Exception as e:
                        print(f"Error checking for checkmate in Claude engine: {e}")
                        # Fallback - assume stalemate if no moves and can't determine check
                        return True, "Draw by stalemate"
                return False, None
            elif self.engine_type == "human":
                # For human players, we'll handle game over detection in the web interface
                return False, None
            return False, None
        except Exception as e:
            print(f"Error checking game over for {self.engine_type}: {e}")
            return False, None

    def get_board_state(self) -> str:
        """Get current board state as string for display"""
        if self.engine_type == "augment":
            return str(self.engine.board)
        elif self.engine_type == "claude":
            # Claude board doesn't have display_board, just return a simple representation
            current_player = "white" if self.engine.white_to_move else "black"
            return f"Claude board state (to move: {current_player})"
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

    def __init__(self, port: int = 8003):
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
                    print(f"=== ENGINE MOVE GENERATION ERROR ===", flush=True)
                    print(f"ENGINE ERROR: {current_engine.engine_name} returned no move", flush=True)
                    print(f"This likely indicates the engines are out of sync", flush=True)

                    # Try to get available moves for debugging
                    try:
                        if current_engine.engine_type == "claude":
                            moves = current_engine.engine.generate_moves()
                            print(f"Claude engine reports {len(moves) if moves else 0} available moves", flush=True)
                            if moves:
                                print(f"Sample legal moves: {moves[:5]}", flush=True)
                            else:
                                print("Claude engine sees NO legal moves - may be checkmate/stalemate or invalid state", flush=True)
                        elif current_engine.engine_type == "augment":
                            moves = current_engine.engine.get_legal_moves()
                            print(f"Augment engine reports {len(moves) if moves else 0} available moves", flush=True)
                            if moves:
                                print(f"Sample legal moves: {[str(m) for m in moves[:5]]}", flush=True)
                            else:
                                print("Augment engine sees NO legal moves - may be checkmate/stalemate or invalid state", flush=True)

                        # Check if this is actually game over vs. engine error
                        game_over, result = current_engine.is_game_over()
                        if game_over:
                            print(f"Game is actually over: {result}", flush=True)
                            game.result = result
                        else:
                            print("Game should not be over - this is an engine synchronization error", flush=True)
                            game.result = f"Engine synchronization error: {current_engine.engine_name} could not generate a move (engines out of sync)"

                    except Exception as e:
                        print(f"Could not get moves for debugging: {e}", flush=True)
                        game.result = f"Engine error: {current_engine.engine_name} could not generate a move"

                    game.status = "finished"
                    break

                # Validate the move looks reasonable (reduced debug output)
                if len(move_str) == 5 and move_str[4].upper() in 'QRBN':
                    print(f"Promotion move: {move_str}", flush=True)

                # Clean up the move string to handle promotion properly
                clean_move = move_str
                if len(move_str) == 5 and move_str[4].upper() in 'QRBN':
                    # This is a promotion move - some engines might not expect the promotion piece
                    base_move = move_str[:4]
                    promotion_piece = move_str[4].upper()
                else:
                    base_move = move_str
                    promotion_piece = None

                # Make move on both engines
                current_success = current_engine.make_move(move_str)
                if not current_success:
                    print(f"INVALID MOVE DETECTED:", flush=True)
                    print(f"  Engine: {current_engine.engine_name}", flush=True)
                    print(f"  Move: {move_str}", flush=True)
                    try:
                        print(f"  Move details: from={move_str[:2]}, to={move_str[2:4]}")
                        print(f"  Move type: {type(move_str)}")
                        print(f"  Move length: {len(str(move_str))}")
                    except Exception as e:
                        print(f"  Error parsing move details: {e}")
                        print(f"  Raw move: {repr(move_str)}")

                    game.result = f"Invalid move by {current_engine.engine_name}: {move_str}"
                    game.status = "finished"
                    break

                other_engine = black_engine if current_engine == white_engine else white_engine

                # Try the move with the other engine, with fallback for promotion format differences
                other_success = other_engine.make_move(move_str)

                if not other_success and promotion_piece:
                    # Try various promotion format alternatives
                    alternatives_to_try = []

                    # Get original promotion character from move_str
                    original_promotion_char = move_str[4] if len(move_str) == 5 else promotion_piece

                    # Try opposite case first (most likely to work)
                    if original_promotion_char.isupper():
                        alternatives_to_try.append(base_move + original_promotion_char.lower())
                    else:
                        alternatives_to_try.append(base_move + original_promotion_char.upper())

                    # Try without promotion piece suffix
                    alternatives_to_try.append(base_move)

                    # Try with '=' prefix (some engines use this)
                    alternatives_to_try.append(base_move + '=' + promotion_piece.upper())
                    alternatives_to_try.append(base_move + '=' + promotion_piece.lower())

                    for alternative in alternatives_to_try:
                        print(f"Trying alternative format: {alternative}", flush=True)
                        other_success = other_engine.make_move(alternative)
                        if other_success:
                            print(f"Move accepted with alternative format: {alternative}", flush=True)
                            break
                        else:
                            print(f"Alternative {alternative} also rejected", flush=True)

                if not other_success:
                    print(f"=== CRITICAL ENGINE SYNCHRONIZATION ERROR ===", flush=True)
                    print(f"CRITICAL: Move rejected by other engine: {move_str}", flush=True)
                    print(f"Current engine: {current_engine.engine_name}", flush=True)
                    print(f"Other engine: {other_engine.engine_name}", flush=True)

                    # Try to get legal moves from the rejecting engine for debugging
                    try:
                        if other_engine.engine_type == "claude":
                            other_moves = other_engine.engine.generate_moves()
                            print(f"Claude engine has {len(other_moves) if other_moves else 0} legal moves")
                            if other_moves:
                                print(f"Sample legal moves: {other_moves[:10]}")
                        elif other_engine.engine_type == "augment":
                            other_moves = other_engine.engine.get_legal_moves()
                            print(f"Augment engine has {len(other_moves) if other_moves else 0} legal moves")
                            if other_moves:
                                print(f"Sample legal moves: {[str(m) for m in other_moves[:10]]}")
                    except Exception as e:
                        print(f"Could not get legal moves from other engine: {e}")

                    # Stop the game due to synchronization error - engines are out of sync
                    print(f"STOPPING GAME: Engines are out of sync and cannot continue reliably")
                    game.result = f"Engine synchronization error: {other_engine.engine_name} rejected {move_str} - engines have divergent board states"
                    game.status = "finished"
                    break

                # Switch players first to check if opponent is in checkmate/check
                other_engine = black_engine if current_engine == white_engine else white_engine

                # Check if this move puts opponent in checkmate or check
                move_notation = move_str
                try:
                    game_over, result = other_engine.is_game_over()
                    if game_over and result and "checkmate" in result.lower():
                        move_notation = move_str + "#"  # Checkmate symbol
                    else:
                        # Check if opponent is in check (not checkmate)
                        if other_engine.engine_type == "augment" and hasattr(other_engine.engine, 'board'):
                            if hasattr(other_engine.engine.board, 'is_check') and other_engine.engine.board.is_check():
                                move_notation = move_str + "+"  # Check symbol
                        elif other_engine.engine_type == "claude":
                            # For Claude engine, try to determine if in check
                            try:
                                import importlib.util
                                claude_path = os.path.join(os.path.dirname(__file__), 'claude-chess', 'chess_engine.py')
                                spec = importlib.util.spec_from_file_location("claude_engine_module", claude_path)
                                claude_module = importlib.util.module_from_spec(spec)
                                spec.loader.exec_module(claude_module)
                                temp_engine = claude_module.ChessEngine()
                                temp_engine.board = other_engine.engine
                                if temp_engine.is_in_check(other_engine.engine):
                                    move_notation = move_str + "+"  # Check symbol
                            except:
                                pass  # If check detection fails, just use basic notation
                except:
                    pass  # If check detection fails, just use basic notation

                # Record move with notation
                player = "White" if current_engine == white_engine else "Black"
                game_move = GameMove(
                    move_num=move_num,
                    player=player,
                    move=move_notation,
                    time_taken=time_taken
                )
                game.moves.append(game_move)

                print(f"Move {move_num}: {player} plays {move_notation} (took {time_taken:.2f}s)")

                # Switch to other player
                current_engine = other_engine
                if player == "Black":
                    move_num += 1

                # Update board state
                game.current_position = current_engine.get_board_state()

                # Short delay between moves
                time.sleep(0.5)

        except Exception as e:
            import traceback
            print(f"Error in game: {e}")
            print(f"Full traceback: {traceback.format_exc()}")
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

    def set_human_move(self, game_id: str, move: str):
        """Set a move for a human player"""
        if game_id in self.games:
            game = self.games[game_id]
            # This is a simplified approach - we'd need better tracking in a real implementation
            # For now, just store the move globally and let the game thread pick it up
            if hasattr(self, '_human_moves'):
                self._human_moves[game_id] = move
            else:
                self._human_moves = {game_id: move}

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

                    # Extract additional kwargs, excluding the ones we already have
                    additional_kwargs = {k: v for k, v in data.items()
                                       if k not in ['white_engine', 'black_engine', 'format']}

                    try:
                        game_id = battle.create_game(white_engine, black_engine, game_format, **additional_kwargs)
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

                elif parts[2] == 'human_move':
                    move = data.get('move')
                    game_id = data.get('game_id')

                    if not move or not game_id:
                        self.send_json_response({'error': 'Missing move or game_id'}, status=400)
                        return

                    # Find the human player and set their move
                    game = battle.get_game_state(game_id)
                    if not game:
                        self.send_json_response({'error': 'Game not found'}, status=404)
                        return

                    # Set move for human player (this is a simplified approach)
                    # In a real implementation, you'd need to track which player is human
                    battle.set_human_move(game_id, move)
                    self.send_json_response({'status': 'move_set'})

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
                return """<!DOCTYPE html>
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
            grid-template-columns: auto 350px;
            gap: 20px;
            padding: 20px;
            min-height: 600px;
            justify-content: start;
        }
        .game-area {
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            padding: 0;
            margin: 0;
        }
        .controls {
            background: #fff;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
        }
        .board-container {
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            margin: 0;
            width: fit-content;
        }
        .board-with-labels {
            display: grid;
            grid-template-columns: 30px repeat(8, 50px);
            grid-template-rows: repeat(8, 50px) 30px;
            gap: 1px;
            align-items: center;
            justify-items: center;
        }
        .chess-board {
            display: grid;
            grid-template-columns: repeat(8, 50px);
            grid-template-rows: repeat(8, 50px);
            gap: 0px;
            border: 2px solid #8B4513;
            margin: 0;
        }
        .rank-label {
            grid-column: 1;
            font-weight: bold;
            color: #8B4513;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
        }
        .file-label {
            grid-row: 9;
            font-weight: bold;
            color: #8B4513;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
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
            background-color: #F0D9B5 !important;
        }
        .square.dark {
            background-color: #B58863 !important;
        }
        .square:hover {
            transform: scale(1.05);
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }
        .game-info {
            background: #e3f2fd;
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        .moves-list {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            background: #fafafa;
            margin-top: 20px;
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
        .move-checkmate {
            color: #dc3545;
            font-weight: bold;
        }
        .move-check {
            color: #fd7e14;
            font-weight: bold;
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
        .status.finished-draw {
            background: #fff3cd;
            color: #856404;
            font-size: 16px;
            font-weight: bold;
        }
        .status.finished-win {
            background: #d4edda;
            color: #155724;
            font-size: 16px;
            font-weight: bold;
        }
        .game-result {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            text-align: center;
            font-size: 18px;
            font-weight: bold;
        }
        .result-draw {
            background: #fff3cd;
            color: #856404;
            border: 2px solid #ffc107;
        }
        .result-white-wins {
            background: #d4edda;
            color: #155724;
            border: 2px solid #28a745;
        }
        .result-black-wins {
            background: #f8d7da;
            color: #721c24;
            border: 2px solid #dc3545;
        }
        .engine-info {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 10px;
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
        .engine-status {
            font-size: 12px;
            margin-top: 5px;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
        }
        .engine-white .engine-status {
            background: #e3f2fd;
            color: #1565c0;
        }
        .engine-black .engine-status {
            background: #424242;
            color: #fff;
        }
        .engine-status.thinking {
            background: #fff3cd !important;
            color: #856404 !important;
            animation: pulse 1s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        .captured-pieces {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 10px;
            margin: 5px 0;
            width: fit-content;
        }
        .captured-container {
            display: flex;
            gap: 20px;
            align-items: flex-start;
        }
        .captured-white, .captured-black {
            padding: 8px;
            border-radius: 4px;
            background: white;
            border: 1px solid #ddd;
            min-width: 80px;
            text-align: center;
        }
        .captured-label {
            font-weight: bold;
            font-size: 12px;
            display: block;
            margin-bottom: 5px;
        }
        .captured-list {
            display: flex;
            flex-wrap: wrap;
            gap: 2px;
        }
        .captured-piece {
            font-size: 18px;
            display: inline-block;
        }
        .copy-btn {
            background: #28a745;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
            cursor: pointer;
            margin-top: 10px;
            font-size: 12px;
        }
        .copy-btn:hover {
            background: #218838;
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
                        <h4>⚪ White Engine</h4>
                        <p id="whiteEngine">-</p>
                        <div id="whiteStatus" class="engine-status">Ready</div>
                    </div>
                    <div class="engine-card engine-black">
                        <h4>⚫ Black Engine</h4>
                        <p id="blackEngine">-</p>
                        <div id="blackStatus" class="engine-status">Ready</div>
                    </div>
                </div>

                <div id="chessBoard" class="chess-board">
                    <!-- Board will be generated by JavaScript -->
                </div>

                <div id="capturedPieces" class="captured-pieces">
                    <h4>Captured Pieces</h4>
                    <div class="captured-container">
                        <div class="captured-white">
                            <span class="captured-label">White taken:</span>
                            <div id="capturedWhite" class="captured-list"></div>
                        </div>
                        <div class="captured-black">
                            <span class="captured-label">Black taken:</span>
                            <div id="capturedBlack" class="captured-list"></div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="controls">
                <div id="gameStatus" class="status waiting">
                    Ready to start
                </div>

                <div id="gameResult" class="game-result" style="display: none;">
                    <!-- Game result will be displayed here -->
                </div>

                <div class="form-group">
                    <label>White Player:</label>
                    <select id="whiteEngineSelect">
                        <option value="augment">Augment Engine</option>
                        <option value="claude">Claude Engine</option>
                        <option value="human">Human Player</option>
                    </select>
                </div>

                <div class="form-group">
                    <label>Black Player:</label>
                    <select id="blackEngineSelect">
                        <option value="claude">Claude Engine</option>
                        <option value="augment">Augment Engine</option>
                        <option value="human">Human Player</option>
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

                <button id="createGameBtn">Create New Game</button>
                <button id="startGameBtn" disabled>Start Battle</button>
                <button id="stopGameBtn" disabled>Stop Game</button>
                <button id="refreshBtn">Refresh</button>

                <div id="movesList" class="moves-list">
                    <h4>Move History</h4>
                    <div id="movesContent">No moves yet</div>
                    <button id="copyMovesBtn" class="copy-btn">📋 Copy Moves</button>
                </div>
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

        // Current board state
        let currentBoardPosition = [
            ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
            ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
            ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        ];

        // Captured pieces
        let capturedPieces = {
            white: [], // White pieces captured by black
            black: []  // Black pieces captured by white
        };

        // Initialize chess board display
        function initializeBoard() {
            const board = document.getElementById('chessBoard');
            board.innerHTML = '';

            // Reset to starting position
            currentBoardPosition = [
                ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
                ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
                ['.', '.', '.', '.', '.', '.', '.', '.'],
                ['.', '.', '.', '.', '.', '.', '.', '.'],
                ['.', '.', '.', '.', '.', '.', '.', '.'],
                ['.', '.', '.', '.', '.', '.', '.', '.'],
                ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
                ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
            ];

            // Reset captured pieces
            capturedPieces = {
                white: [],
                black: []
            };

            updateBoardDisplay();
            updateCapturedPieces();
        }

        // Update the visual board display
        function updateBoardDisplay() {
            const board = document.getElementById('chessBoard');
            if (!board) {
                console.error('Chess board element not found!');
                return;
            }

            board.innerHTML = '';

            for (let rank = 0; rank < 8; rank++) {
                for (let file = 0; file < 8; file++) {
                    const square = document.createElement('div');
                    // Fix the alternating pattern - use proper chess board coloring
                    const isLight = (rank + file) % 2 === 0;
                    square.className = `square ${isLight ? 'light' : 'dark'}`;

                    // Explicitly set background color to ensure it works
                    const bgColor = isLight ? '#F0D9B5' : '#B58863';
                    square.style.backgroundColor = bgColor;

                    const piece = currentBoardPosition[rank][file];
                    if (piece !== '.') {
                        square.textContent = pieceUnicode[piece] || piece;
                    }

                    board.appendChild(square);
                }
            }
        }

        // Apply a move to the current board position
        function applyMove(moveStr) {
            // Strip check (+) and checkmate (#) symbols for move parsing
            let cleanMove = moveStr.replace(/[+#]$/, '');

            if (cleanMove.length < 4) return false;

            // Parse move (e.g., "e2e4")
            const fromFile = cleanMove.charAt(0).charCodeAt(0) - 'a'.charCodeAt(0);
            const fromRank = 8 - parseInt(cleanMove.charAt(1));
            const toFile = cleanMove.charAt(2).charCodeAt(0) - 'a'.charCodeAt(0);
            const toRank = 8 - parseInt(cleanMove.charAt(3));

            // Validate coordinates
            if (fromFile < 0 || fromFile > 7 || fromRank < 0 || fromRank > 7 ||
                toFile < 0 || toFile > 7 || toRank < 0 || toRank > 7) {
                return false;
            }

            // Get the piece to move
            const piece = currentBoardPosition[fromRank][fromFile];
            if (piece === '.') return false;

            // Check for capture
            const targetPiece = currentBoardPosition[toRank][toFile];
            if (targetPiece !== '.') {
                // Piece is captured
                if (targetPiece === targetPiece.toLowerCase()) {
                    // Black piece captured by white
                    capturedPieces.black.push(targetPiece);
                } else {
                    // White piece captured by black
                    capturedPieces.white.push(targetPiece);
                }
            }

            // Make the move
            currentBoardPosition[toRank][toFile] = piece;
            currentBoardPosition[fromRank][fromFile] = '.';

            // Handle promotion (simple - just promote to queen)
            if (cleanMove.length === 5) {
                const promotion = cleanMove.charAt(4).toLowerCase();
                if (promotion === 'q') {
                    currentBoardPosition[toRank][toFile] = piece.toLowerCase() === piece ? 'q' : 'Q';
                }
            }

            return true;
        }

        // Update captured pieces display
        function updateCapturedPieces() {
            const capturedWhiteDiv = document.getElementById('capturedWhite');
            const capturedBlackDiv = document.getElementById('capturedBlack');

            capturedWhiteDiv.innerHTML = '';
            capturedBlackDiv.innerHTML = '';

            // Display captured white pieces
            capturedPieces.white.forEach(piece => {
                const span = document.createElement('span');
                span.className = 'captured-piece';
                span.textContent = pieceUnicode[piece] || piece;
                capturedWhiteDiv.appendChild(span);
            });

            // Display captured black pieces
            capturedPieces.black.forEach(piece => {
                const span = document.createElement('span');
                span.className = 'captured-piece';
                span.textContent = pieceUnicode[piece] || piece;
                capturedBlackDiv.appendChild(span);
            });
        }

        // Copy moves to clipboard
        async function copyMovesToClipboard() {
            if (!currentGameId) return;

            try {
                const response = await fetch(`/api/games/${currentGameId}`);
                const game = await response.json();

                if (game.moves) {
                    let moveText = '';
                    for (let i = 0; i < game.moves.length; i += 2) {
                        const moveNum = Math.floor(i / 2) + 1;
                        const whiteMove = game.moves[i];
                        const blackMove = game.moves[i + 1];

                        moveText += `${moveNum}. ${whiteMove.move}`;
                        if (blackMove) {
                            moveText += ` ${blackMove.move}`;
                        }
                        moveText += '\\n';
                    }

                    await navigator.clipboard.writeText(moveText.trim());

                    // Show feedback
                    const btn = document.getElementById('copyMovesBtn');
                    const originalText = btn.textContent;
                    btn.textContent = '✓ Copied!';
                    setTimeout(() => {
                        btn.textContent = originalText;
                    }, 2000);
                }
            } catch (error) {
                console.error('Failed to copy moves:', error);
                alert('Failed to copy moves to clipboard');
            }
        }

        async function createGame() {
            const whiteEngine = document.getElementById('whiteEngineSelect').value;
            const blackEngine = document.getElementById('blackEngineSelect').value;
            const gameFormat = document.getElementById('gameFormat').value;

            if (whiteEngine === blackEngine && whiteEngine !== 'human') {
                alert('Please select different engines for white and black (or use Human Player for both)');
                return;
            }

            try {
                const response = await fetch('/api/create_game', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        white_engine: whiteEngine === 'human' ? 'Human Player' : whiteEngine + ' Engine',
                        black_engine: blackEngine === 'human' ? 'Human Player' : blackEngine + ' Engine',
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
                    const whiteText = whiteEngine === 'human' ? 'Human Player' : whiteEngine + ' Engine';
                    const blackText = blackEngine === 'human' ? 'Human Player' : blackEngine + ' Engine';
                    document.getElementById('whiteEngine').textContent = whiteText;
                    document.getElementById('blackEngine').textContent = blackText;
                    document.getElementById('engineInfo').style.display = 'grid';

                    // Reset board to starting position
                    initializeBoard();

                    // Clear moves list
                    document.getElementById('movesContent').innerHTML = 'No moves yet';
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
                        // Parse and display the result prominently
                        let resultText = '';
                        let resultClass = '';

                        if (game.result.includes('Draw') || game.result.includes('draw')) {
                            resultText = '🤝 DRAW GAME';
                            statusText = `Game finished in a draw: ${game.result}`;
                            statusClass = 'finished-draw';
                            resultClass = 'result-draw';
                        } else if (game.result.includes('White wins') || game.result.includes('white wins')) {
                            const whiteEngineName = game.white_engine || 'White Engine';
                            resultText = `👑 ${whiteEngineName.toUpperCase()} (WHITE) WINS!`;
                            statusText = `⚪ ${whiteEngineName} (White) wins: ${game.result}`;
                            statusClass = 'finished-win';
                            resultClass = 'result-white-wins';
                        } else if (game.result.includes('Black wins') || game.result.includes('black wins')) {
                            const blackEngineName = game.black_engine || 'Black Engine';
                            resultText = `👑 ${blackEngineName.toUpperCase()} (BLACK) WINS!`;
                            statusText = `⚫ ${blackEngineName} (Black) wins: ${game.result}`;
                            statusClass = 'finished-win';
                            resultClass = 'result-black-wins';
                        } else {
                            resultText = `🏁 ${game.result.toUpperCase()}`;
                            statusText = `Finished: ${game.result}`;
                            statusClass = 'finished';
                            resultClass = 'result-draw';
                        }

                        // Show the prominent result display
                        const gameResultDiv = document.getElementById('gameResult');
                        gameResultDiv.textContent = resultText;
                        gameResultDiv.className = `game-result ${resultClass}`;
                        gameResultDiv.style.display = 'block';

                        if (refreshInterval) {
                            clearInterval(refreshInterval);
                            refreshInterval = null;
                        }
                        document.getElementById('stopGameBtn').disabled = true;
                        document.getElementById('createGameBtn').disabled = false;
                        break;
                }

                updateGameStatus(statusText, statusClass);

                // Update moves list and board position
                const movesContent = document.getElementById('movesContent');
                movesContent.innerHTML = '';

                // Reset board to starting position and replay all moves
                initializeBoard();

                game.moves.forEach((move, index) => {
                    const moveDiv = document.createElement('div');
                    let className = `move-item ${move.player.toLowerCase()}`;

                    // Add special styling for checkmate and check moves
                    if (move.move.endsWith('#')) {
                        className += ' move-checkmate';
                    } else if (move.move.endsWith('+')) {
                        className += ' move-check';
                    }

                    moveDiv.className = className;
                    moveDiv.innerHTML = `<span>${move.move_num}. ${move.move}</span><span>${move.player} (${move.time_taken.toFixed(2)}s)</span>`;
                    movesContent.appendChild(moveDiv);

                    // Apply move to visual board
                    applyMove(move.move);
                });

                // Update the visual board after all moves
                updateBoardDisplay();
                updateCapturedPieces();

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

            // Add event listeners for buttons
            document.getElementById('createGameBtn').addEventListener('click', createGame);
            document.getElementById('startGameBtn').addEventListener('click', startGame);
            document.getElementById('stopGameBtn').addEventListener('click', stopGame);
            document.getElementById('refreshBtn').addEventListener('click', refreshGameState);
            document.getElementById('copyMovesBtn').addEventListener('click', copyMovesToClipboard);
        });
    </script>
</body>
</html>"""

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
    battle = EngineBattle(port=8003)
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