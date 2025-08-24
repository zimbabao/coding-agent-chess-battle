# Main Chess Engine Class

from board import ChessBoard
from search import SearchEngine
from evaluation import evaluate_board
from utils import *
import time

class ChessEngine:
    def __init__(self, chess960=False, position_id=None):
        self.chess960 = chess960
        self.position_id = position_id
        self.board = ChessBoard(chess960=chess960, position_id=position_id)
        self.search_engine = SearchEngine()
        self.game_history = []
        self._move_cache = {}  # Performance caching
        
    def reset_game(self):
        """Reset the game to starting position."""
        self.board = ChessBoard(chess960=self.chess960, position_id=self.position_id)
        self.game_history = []
        self.search_engine.clear_transposition_table()
        self._move_cache.clear()
    
    def set_position(self, fen=None):
        """Set board position from FEN string or starting position."""
        if fen is None:
            self.reset_game()
        else:
            # This would need FEN parsing implementation
            # For now, just reset to starting position
            self.reset_game()
    
    def make_move(self, move_str):
        """Make a move given in UCI format."""
        try:
            move = parse_uci_move(move_str)
            legal_moves = self.board.generate_legal_moves()
            
            # Find the matching legal move
            for legal_move in legal_moves:
                if (legal_move.from_square == move.from_square and
                    legal_move.to_square == move.to_square and
                    legal_move.promotion == move.promotion):
                    
                    self.board.make_move(legal_move)
                    self.game_history.append(legal_move)
                    return True
            
            return False  # Illegal move
        except:
            return False
    
    def undo_move(self):
        """Undo the last move."""
        if self.board.undo_move():
            if self.game_history:
                self.game_history.pop()
            return True
        return False
    
    def get_legal_moves(self):
        """Get all legal moves in current position."""
        return self.board.generate_legal_moves()
    
    def is_game_over(self):
        """Check if the game is over."""
        legal_moves = self.board.generate_legal_moves()
        if not legal_moves:
            return True, "checkmate" if self.board.is_in_check(self.board.to_move) else "stalemate"
        
        # Check for insufficient material
        if self.is_insufficient_material():
            return True, "insufficient material"
        
        # Check for 50-move rule
        if self.board.halfmove_clock >= 100:
            return True, "50-move rule"
        
        # Check for threefold repetition (simplified)
        if self.is_threefold_repetition():
            return True, "threefold repetition"
        
        return False, None
    
    def is_insufficient_material(self):
        """Check for insufficient material to checkmate."""
        pieces = {'white': [], 'black': []}
        
        for square in range(64):
            if not self.board.is_empty(square):
                piece = self.board.get_piece(square)
                color = 'white' if self.board.get_color(square) == WHITE else 'black'
                if piece != KING:  # Don't count kings
                    pieces[color].append(piece)
        
        # King vs King
        if not pieces['white'] and not pieces['black']:
            return True
        
        # King and Bishop/Knight vs King
        for color in ['white', 'black']:
            other_color = 'black' if color == 'white' else 'white'
            if (len(pieces[color]) == 1 and not pieces[other_color] and
                pieces[color][0] in [BISHOP, KNIGHT]):
                return True
        
        # King and Bishop vs King and Bishop (same color squares)
        if (len(pieces['white']) == 1 and len(pieces['black']) == 1 and
            pieces['white'][0] == BISHOP and pieces['black'][0] == BISHOP):
            # This is a simplification - would need to check if bishops are on same color squares
            return True
        
        return False
    
    def is_threefold_repetition(self):
        """Check for threefold repetition (simplified)."""
        # This is a very basic implementation
        # A proper implementation would need position hashing
        if len(self.game_history) < 8:
            return False
        
        # Count recent position repetitions (very simplified)
        recent_moves = self.game_history[-8:]
        if len(recent_moves) >= 8:
            # Check if last 4 moves repeat the previous 4 moves
            return (recent_moves[-4:] == recent_moves[-8:-4])
        
        return False
    
    def get_best_move(self, depth=6, time_limit=0):
        """Get the best move using the search engine."""
        return self.search_engine.search_best_move_with_quiescence(
            self.board, depth, time_limit
        )
    
    def evaluate_position(self):
        """Evaluate the current position."""
        return evaluate_board(self.board)

    def evaluate(self, board=None):
        """Evaluate the given board position."""
        if board is None:
            board = self.board
        return evaluate_board(board)

    def is_legal_move(self, move_str):
        """Check if a move string represents a legal move."""
        try:
            move = parse_uci_move(move_str)
            legal_moves = self.board.generate_legal_moves()

            # Find matching legal move
            for legal_move in legal_moves:
                if (legal_move.from_square == move.from_square and
                    legal_move.to_square == move.to_square and
                    legal_move.promotion == move.promotion):
                    return True
            return False
        except Exception:
            return False

    def setup_chess960_position(self, position_id):
        """Set up a specific Chess960 position (0-959)."""
        if not (0 <= position_id <= 959):
            raise ValueError("Chess960 position ID must be between 0 and 959")

        self.chess960 = True
        self.position_id = position_id
        self.board = ChessBoard(chess960=True, position_id=position_id)
        self.game_history = []
        self._move_cache.clear()

    def get_chess960_position_id(self):
        """Get the current Chess960 position ID."""
        return self.position_id if self.chess960 else None

    def is_chess960(self):
        """Check if this is a Chess960 game."""
        return self.chess960

    def generate_random_chess960_position(self):
        """Generate a random Chess960 position."""
        import random
        position_id = random.randint(0, 959)
        self.setup_chess960_position(position_id)
        return position_id
    
    def get_board_string(self):
        """Get a string representation of the board."""
        board_str = ""
        piece_chars = {
            EMPTY: '.',
            PAWN: 'P', KNIGHT: 'N', BISHOP: 'B', 
            ROOK: 'R', QUEEN: 'Q', KING: 'K'
        }
        
        for rank in range(7, -1, -1):  # Start from rank 8
            board_str += f"{rank + 1} "
            for file in range(8):
                square = rank * 8 + file
                piece = self.board.get_piece(square)
                char = piece_chars[piece]
                
                if piece != EMPTY:
                    color = self.board.get_color(square)
                    if color == BLACK:
                        char = char.lower()
                
                board_str += char + " "
            board_str += "\n"
        
        board_str += "  a b c d e f g h\n"
        
        # Add game state info
        to_move = "White" if self.board.to_move == WHITE else "Black"
        board_str += f"\nTo move: {to_move}\n"
        
        # Castling rights
        castling = ""
        for right in ['K', 'Q', 'k', 'q']:
            if self.board.castling_rights[right]:
                castling += right
        if not castling:
            castling = "-"
        board_str += f"Castling: {castling}\n"
        
        # En passant
        ep = "-"
        if self.board.en_passant_square is not None:
            ep = square_to_algebraic(self.board.en_passant_square)
        board_str += f"En passant: {ep}\n"
        
        board_str += f"Halfmove clock: {self.board.halfmove_clock}\n"
        board_str += f"Fullmove number: {self.board.fullmove_number}\n"
        
        return board_str
    
    def perft(self, depth):
        """Performance test - count nodes at given depth."""
        if depth == 0:
            return 1
        
        nodes = 0
        legal_moves = self.board.generate_legal_moves()
        
        for move in legal_moves:
            self.board.make_move(move)
            nodes += self.perft(depth - 1)
            self.board.undo_move()
        
        return nodes
    
    def run_perft_test(self, max_depth=5):
        """Run performance test up to max_depth."""
        print("Running PERFT test...")
        print("Depth | Nodes     | Time (ms)")
        print("------|-----------|----------")
        
        for depth in range(1, max_depth + 1):
            start_time = time.time()
            nodes = self.perft(depth)
            end_time = time.time()
            
            time_ms = int((end_time - start_time) * 1000)
            print(f"{depth:5} | {nodes:9} | {time_ms:8}")
    
    def play_game(self, white_engine=None, black_engine=None, max_moves=100):
        """Play a game between two engines or human players."""
        move_count = 0
        
        while move_count < max_moves:
            print(self.get_board_string())
            
            # Check if game is over
            game_over, reason = self.is_game_over()
            if game_over:
                print(f"Game over: {reason}")
                break
            
            # Get move from appropriate player
            if self.board.to_move == WHITE:
                if white_engine:
                    move = white_engine.get_best_move()
                    if move:
                        print(f"White plays: {move}")
                        self.board.make_move(move)
                    else:
                        print("White has no legal moves")
                        break
                else:
                    # Human player
                    move_str = input("White to move (UCI format): ")
                    if not self.make_move(move_str):
                        print("Illegal move!")
                        continue
            else:
                if black_engine:
                    move = black_engine.get_best_move()
                    if move:
                        print(f"Black plays: {move}")
                        self.board.make_move(move)
                    else:
                        print("Black has no legal moves")
                        break
                else:
                    # Human player
                    move_str = input("Black to move (UCI format): ")
                    if not self.make_move(move_str):
                        print("Illegal move!")
                        continue
            
            move_count += 1
        
        print("Final position:")
        print(self.get_board_string())

if __name__ == "__main__":
    # Simple test
    engine = ChessEngine()
    print("Chess Engine Test")
    print(engine.get_board_string())
    
    # Run a quick perft test
    engine.run_perft_test(4)
