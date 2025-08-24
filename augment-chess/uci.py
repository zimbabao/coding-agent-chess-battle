# UCI (Universal Chess Interface) Protocol Handler

import sys
from board import ChessBoard
from search import SearchEngine
from utils import parse_uci_move, square_to_algebraic, algebraic_to_square

class UCIEngine:
    def __init__(self):
        self.board = ChessBoard()
        self.search_engine = SearchEngine()
        self.debug = False
        self.name = "PyChess Engine"
        self.author = "Chess Engine Developer"
        
    def send(self, message):
        """Send message to UCI interface."""
        print(message)
        sys.stdout.flush()
    
    def debug_print(self, message):
        """Print debug message if debug mode is enabled."""
        if self.debug:
            self.send(f"info string {message}")
    
    def handle_uci(self):
        """Handle 'uci' command."""
        self.send(f"id name {self.name}")
        self.send(f"id author {self.author}")
        
        # Send options
        self.send("option name Debug type check default false")
        self.send("option name Hash type spin default 64 min 1 max 1024")
        self.send("option name Threads type spin default 1 min 1 max 8")
        
        self.send("uciok")
    
    def handle_debug(self, args):
        """Handle 'debug' command."""
        if args and args[0].lower() == "on":
            self.debug = True
            self.debug_print("Debug mode enabled")
        else:
            self.debug = False
    
    def handle_isready(self):
        """Handle 'isready' command."""
        self.send("readyok")
    
    def handle_setoption(self, args):
        """Handle 'setoption' command."""
        if len(args) >= 4 and args[0] == "name":
            option_name = args[1]
            if len(args) >= 4 and args[2] == "value":
                option_value = args[3]
                
                if option_name.lower() == "debug":
                    self.debug = option_value.lower() == "true"
                elif option_name.lower() == "hash":
                    # Handle hash table size (not implemented in this basic version)
                    pass
                elif option_name.lower() == "threads":
                    # Handle thread count (not implemented in this basic version)
                    pass
    
    def handle_ucinewgame(self):
        """Handle 'ucinewgame' command."""
        self.board = ChessBoard()
        self.search_engine.clear_transposition_table()
        self.debug_print("New game started")
    
    def parse_fen(self, fen):
        """Parse FEN string and set up board position."""
        parts = fen.split()
        if len(parts) < 4:
            return False
        
        # Reset board
        self.board = ChessBoard()
        for i in range(64):
            self.board.board[i] = 0
        
        # Parse piece placement
        piece_placement = parts[0]
        rank = 7
        file = 0
        
        piece_map = {
            'p': (1, 1), 'n': (2, 1), 'b': (3, 1), 'r': (4, 1), 'q': (5, 1), 'k': (6, 1),
            'P': (1, 0), 'N': (2, 0), 'B': (3, 0), 'R': (4, 0), 'Q': (5, 0), 'K': (6, 0)
        }
        
        for char in piece_placement:
            if char == '/':
                rank -= 1
                file = 0
            elif char.isdigit():
                file += int(char)
            elif char in piece_map:
                square = rank * 8 + file
                piece_type, color = piece_map[char]
                self.board.board[square] = piece_type
                self.board.colors[square] = color
                file += 1
        
        # Parse active color
        self.board.to_move = 0 if parts[1] == 'w' else 1
        
        # Parse castling rights
        castling = parts[2]
        self.board.castling_rights = {'K': False, 'Q': False, 'k': False, 'q': False}
        for char in castling:
            if char in self.board.castling_rights:
                self.board.castling_rights[char] = True
        
        # Parse en passant square
        if parts[3] != '-':
            self.board.en_passant_square = algebraic_to_square(parts[3])
        else:
            self.board.en_passant_square = None
        
        # Parse halfmove clock and fullmove number
        if len(parts) >= 5:
            self.board.halfmove_clock = int(parts[4])
        if len(parts) >= 6:
            self.board.fullmove_number = int(parts[5])
        
        return True
    
    def handle_position(self, args):
        """Handle 'position' command."""
        if not args:
            return
        
        if args[0] == "startpos":
            self.board = ChessBoard()
            move_start = 1
            if len(args) > 1 and args[1] == "moves":
                move_start = 2
        elif args[0] == "fen":
            # Find where moves start
            move_start = len(args)
            for i, arg in enumerate(args):
                if arg == "moves":
                    move_start = i + 1
                    break
            
            # Extract FEN string
            fen_parts = args[1:move_start-1] if move_start < len(args) else args[1:]
            fen = " ".join(fen_parts)
            
            if not self.parse_fen(fen):
                self.debug_print("Invalid FEN string")
                return
        else:
            return
        
        # Apply moves
        if move_start < len(args):
            for move_str in args[move_start:]:
                try:
                    move = parse_uci_move(move_str)
                    legal_moves = self.board.generate_legal_moves()
                    
                    # Find matching legal move
                    legal_move = None
                    for legal in legal_moves:
                        if (legal.from_square == move.from_square and 
                            legal.to_square == move.to_square and
                            legal.promotion == move.promotion):
                            legal_move = legal
                            break
                    
                    if legal_move:
                        self.board.make_move(legal_move)
                    else:
                        self.debug_print(f"Illegal move: {move_str}")
                        break
                except Exception as e:
                    self.debug_print(f"Error parsing move {move_str}: {e}")
                    break
    
    def handle_go(self, args):
        """Handle 'go' command."""
        # Parse go parameters
        depth = None
        time_limit = 0
        wtime = 0
        btime = 0
        winc = 0
        binc = 0
        movestogo = 0
        
        i = 0
        while i < len(args):
            if args[i] == "depth" and i + 1 < len(args):
                depth = int(args[i + 1])
                i += 2
            elif args[i] == "movetime" and i + 1 < len(args):
                time_limit = int(args[i + 1]) / 1000.0  # Convert to seconds
                i += 2
            elif args[i] == "wtime" and i + 1 < len(args):
                wtime = int(args[i + 1])
                i += 2
            elif args[i] == "btime" and i + 1 < len(args):
                btime = int(args[i + 1])
                i += 2
            elif args[i] == "winc" and i + 1 < len(args):
                winc = int(args[i + 1])
                i += 2
            elif args[i] == "binc" and i + 1 < len(args):
                binc = int(args[i + 1])
                i += 2
            elif args[i] == "movestogo" and i + 1 < len(args):
                movestogo = int(args[i + 1])
                i += 2
            else:
                i += 1
        
        # Calculate time limit if not specified
        if time_limit == 0:
            if self.board.to_move == 0:  # White
                available_time = wtime
                increment = winc
            else:  # Black
                available_time = btime
                increment = binc
            
            if available_time > 0:
                # Simple time management: use 1/30 of remaining time + increment
                time_limit = (available_time / 30000.0) + (increment / 1000.0)
                time_limit = max(0.1, min(time_limit, available_time / 1000.0 * 0.95))
        
        # Search for best move
        if depth is None:
            depth = 6  # Default depth
        
        best_move = self.search_engine.search_best_move_with_quiescence(
            self.board, depth, time_limit
        )
        
        if best_move:
            self.send(f"bestmove {best_move}")
        else:
            # No legal moves (shouldn't happen in normal play)
            self.send("bestmove 0000")
    
    def handle_stop(self):
        """Handle 'stop' command."""
        # In a more advanced engine, this would stop the search
        pass
    
    def handle_quit(self):
        """Handle 'quit' command."""
        sys.exit(0)
    
    def run(self):
        """Main UCI loop."""
        while True:
            try:
                line = input().strip()
                if not line:
                    continue
                
                parts = line.split()
                command = parts[0].lower()
                args = parts[1:]
                
                if command == "uci":
                    self.handle_uci()
                elif command == "debug":
                    self.handle_debug(args)
                elif command == "isready":
                    self.handle_isready()
                elif command == "setoption":
                    self.handle_setoption(args)
                elif command == "ucinewgame":
                    self.handle_ucinewgame()
                elif command == "position":
                    self.handle_position(args)
                elif command == "go":
                    self.handle_go(args)
                elif command == "stop":
                    self.handle_stop()
                elif command == "quit":
                    self.handle_quit()
                else:
                    self.debug_print(f"Unknown command: {command}")
                    
            except EOFError:
                break
            except Exception as e:
                self.debug_print(f"Error: {e}")

if __name__ == "__main__":
    engine = UCIEngine()
    engine.run()
