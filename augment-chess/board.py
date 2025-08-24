# Chess Board Representation and Move Generation

from utils import *
import copy

class ChessBoard:
    def __init__(self, chess960=False, position_id=None):
        self.chess960 = chess960
        self.position_id = position_id

        # Chess960 specific attributes
        self.original_king_file = {'white': 4, 'black': 4}  # Standard position
        self.original_rook_files = {'white': {'kingside': 7, 'queenside': 0},
                                   'black': {'kingside': 7, 'queenside': 0}}

        if chess960:
            if position_id is not None:
                if not (0 <= position_id <= 959):
                    raise ValueError("Chess960 position ID must be between 0 and 959")
                self.setup_chess960_position(position_id)
            else:
                # Generate random Chess960 position
                import random
                self.position_id = random.randint(0, 959)
                self.setup_chess960_position(self.position_id)
        else:
            self.board = INITIAL_BOARD[:]
            self.colors = INITIAL_COLORS[:]

        self.to_move = WHITE
        self.castling_rights = {'K': True, 'Q': True, 'k': True, 'q': True}
        self.en_passant_square = None
        self.halfmove_clock = 0
        self.fullmove_number = 1
        self.move_history = []
    
    def copy(self):
        """Create a deep copy of the board."""
        new_board = ChessBoard()
        new_board.board = self.board[:]
        new_board.colors = self.colors[:]
        new_board.to_move = self.to_move
        new_board.castling_rights = self.castling_rights.copy()
        new_board.en_passant_square = self.en_passant_square
        new_board.halfmove_clock = self.halfmove_clock
        new_board.fullmove_number = self.fullmove_number
        new_board.move_history = self.move_history[:]
        return new_board

    def setup_chess960_position(self, position_id):
        """Set up a specific Chess960 position (0-959)."""
        if not (0 <= position_id <= 959):
            raise ValueError("Chess960 position ID must be between 0 and 959")

        # Generate the specific position using Chess960 algorithm
        back_rank = self._generate_chess960_rank(position_id)

        # Initialize empty board
        self.board = [EMPTY] * 64
        self.colors = [WHITE] * 64  # Dummy colors for empty squares

        # Set up pawns
        for file in range(8):
            self.board[8 + file] = PAWN  # White pawns on rank 2
            self.colors[8 + file] = WHITE
            self.board[48 + file] = PAWN  # Black pawns on rank 7
            self.colors[48 + file] = BLACK

        # Set up back ranks with Chess960 position
        for file, piece in enumerate(back_rank):
            # White pieces on rank 1
            self.board[file] = piece
            self.colors[file] = WHITE
            # Black pieces on rank 8
            self.board[56 + file] = piece
            self.colors[56 + file] = BLACK

        # Track original king and rook positions for castling
        self._update_chess960_castling_info(back_rank)

    def _generate_chess960_rank(self, position_id):
        """Generate Chess960 back rank from position ID using standard algorithm."""
        # Chess960 position generation algorithm
        # Based on the standard Chess960 numbering system

        # Step 1: Place bishops on opposite colored squares
        bishop_positions = [[], []]  # [light_squares, dark_squares]

        # Light squares (b, d, f, h): 1, 3, 5, 7
        light_squares = [1, 3, 5, 7]
        # Dark squares (a, c, e, g): 0, 2, 4, 6
        dark_squares = [0, 2, 4, 6]

        # Extract bishop placement from position_id
        light_bishop_idx = position_id % 4
        dark_bishop_idx = (position_id // 4) % 4

        light_bishop_square = light_squares[light_bishop_idx]
        dark_bishop_square = dark_squares[dark_bishop_idx]

        # Step 2: Place queen on remaining squares
        remaining_squares = [i for i in range(8) if i not in [light_bishop_square, dark_bishop_square]]
        queen_idx = (position_id // 16) % 6
        queen_square = remaining_squares[queen_idx]

        # Step 3: Place knights on remaining squares
        remaining_squares.remove(queen_square)
        knight_placement = (position_id // 96) % 10

        # Generate all possible knight placements (C(5,2) = 10 combinations)
        knight_combinations = []
        for i in range(5):
            for j in range(i + 1, 5):
                knight_combinations.append((i, j))

        knight1_idx, knight2_idx = knight_combinations[knight_placement]
        knight1_square = remaining_squares[knight1_idx]
        knight2_square = remaining_squares[knight2_idx]

        # Step 4: Place rooks and king (king must be between rooks)
        remaining_squares = [sq for sq in remaining_squares if sq not in [knight1_square, knight2_square]]
        remaining_squares.sort()  # Ensure proper order for king between rooks

        # The remaining 3 squares: rook, king, rook (in that order)
        rook1_square = remaining_squares[0]
        king_square = remaining_squares[1]
        rook2_square = remaining_squares[2]

        # Create the back rank
        back_rank = [EMPTY] * 8
        back_rank[light_bishop_square] = BISHOP
        back_rank[dark_bishop_square] = BISHOP
        back_rank[queen_square] = QUEEN
        back_rank[knight1_square] = KNIGHT
        back_rank[knight2_square] = KNIGHT
        back_rank[rook1_square] = ROOK
        back_rank[king_square] = KING
        back_rank[rook2_square] = ROOK

        return back_rank

    def _update_chess960_castling_info(self, back_rank):
        """Update castling information for Chess960 position."""
        # Find king and rook positions
        king_file = back_rank.index(KING)
        rook_files = [i for i, piece in enumerate(back_rank) if piece == ROOK]

        # Store original positions
        self.original_king_file = {'white': king_file, 'black': king_file}

        # Determine which rook is kingside/queenside
        queenside_rook = min(rook_files)
        kingside_rook = max(rook_files)

        self.original_rook_files = {
            'white': {'kingside': kingside_rook, 'queenside': queenside_rook},
            'black': {'kingside': kingside_rook, 'queenside': queenside_rook}
        }
    
    def get_piece(self, square):
        """Get piece type at square."""
        return self.board[square]
    
    def get_color(self, square):
        """Get piece color at square."""
        return self.colors[square]
    
    def is_empty(self, square):
        """Check if square is empty."""
        return self.board[square] == EMPTY
    
    def is_enemy(self, square, color):
        """Check if square contains enemy piece."""
        return not self.is_empty(square) and self.colors[square] != color
    
    def is_friendly(self, square, color):
        """Check if square contains friendly piece."""
        return not self.is_empty(square) and self.colors[square] == color
    
    def find_king(self, color):
        """Find the king of given color."""
        for square in range(64):
            if self.board[square] == KING and self.colors[square] == color:
                return square
        return None
    
    def is_square_attacked(self, square, by_color):
        """Check if square is attacked by pieces of given color."""
        rank, file = square_to_coords(square)
        
        # Check pawn attacks
        pawn_direction = 1 if by_color == WHITE else -1
        for df in [-1, 1]:
            attack_rank = rank - pawn_direction
            attack_file = file + df
            if is_valid_square(attack_rank, attack_file):
                attack_square = coords_to_square(attack_rank, attack_file)
                if (self.board[attack_square] == PAWN and 
                    self.colors[attack_square] == by_color):
                    return True
        
        # Check knight attacks
        for dr, df in KNIGHT_MOVES:
            new_rank, new_file = rank + dr, file + df
            if is_valid_square(new_rank, new_file):
                attack_square = coords_to_square(new_rank, new_file)
                if (self.board[attack_square] == KNIGHT and 
                    self.colors[attack_square] == by_color):
                    return True
        
        # Check sliding piece attacks (bishop, rook, queen)
        for directions, piece_types in [(BISHOP_DIRECTIONS, [BISHOP, QUEEN]), 
                                       (ROOK_DIRECTIONS, [ROOK, QUEEN])]:
            for dr, df in directions:
                for distance in range(1, 8):
                    new_rank = rank + dr * distance
                    new_file = file + df * distance
                    if not is_valid_square(new_rank, new_file):
                        break
                    
                    attack_square = coords_to_square(new_rank, new_file)
                    if not self.is_empty(attack_square):
                        if (self.colors[attack_square] == by_color and 
                            self.board[attack_square] in piece_types):
                            return True
                        break
        
        # Check king attacks
        for dr, df in KING_MOVES:
            new_rank, new_file = rank + dr, file + df
            if is_valid_square(new_rank, new_file):
                attack_square = coords_to_square(new_rank, new_file)
                if (self.board[attack_square] == KING and 
                    self.colors[attack_square] == by_color):
                    return True
        
        return False
    
    def is_in_check(self, color):
        """Check if king of given color is in check."""
        king_square = self.find_king(color)
        if king_square is None:
            return False
        return self.is_square_attacked(king_square, opposite_color(color))
    
    def generate_pawn_moves(self, square, color, moves):
        """Generate pawn moves from given square."""
        rank, file = square_to_coords(square)
        direction = 1 if color == WHITE else -1
        start_rank = 1 if color == WHITE else 6
        promotion_rank = 7 if color == WHITE else 0
        
        # Forward moves
        new_rank = rank + direction
        if is_valid_square(new_rank, file):
            new_square = coords_to_square(new_rank, file)
            if self.is_empty(new_square):
                if new_rank == promotion_rank:
                    # Promotion
                    for piece in [QUEEN, ROOK, BISHOP, KNIGHT]:
                        moves.append(Move(square, new_square, piece))
                else:
                    moves.append(Move(square, new_square))
                
                # Double pawn move
                if rank == start_rank:
                    double_square = coords_to_square(new_rank + direction, file)
                    if self.is_empty(double_square):
                        moves.append(Move(square, double_square))
        
        # Captures
        for df in [-1, 1]:
            if is_valid_square(new_rank, file + df):
                capture_square = coords_to_square(new_rank, file + df)
                if self.is_enemy(capture_square, color):
                    if new_rank == promotion_rank:
                        # Promotion with capture
                        for piece in [QUEEN, ROOK, BISHOP, KNIGHT]:
                            moves.append(Move(square, capture_square, piece))
                    else:
                        moves.append(Move(square, capture_square))
                
                # En passant
                elif (self.en_passant_square == capture_square):
                    moves.append(Move(square, capture_square, is_en_passant=True))
    
    def generate_piece_moves(self, square, piece_type, color, moves):
        """Generate moves for non-pawn pieces."""
        rank, file = square_to_coords(square)
        
        if piece_type == KNIGHT:
            for dr, df in KNIGHT_MOVES:
                new_rank, new_file = rank + dr, file + df
                if is_valid_square(new_rank, new_file):
                    new_square = coords_to_square(new_rank, new_file)
                    if self.is_empty(new_square) or self.is_enemy(new_square, color):
                        moves.append(Move(square, new_square))
        
        elif piece_type == KING:
            for dr, df in KING_MOVES:
                new_rank, new_file = rank + dr, file + df
                if is_valid_square(new_rank, new_file):
                    new_square = coords_to_square(new_rank, new_file)
                    if self.is_empty(new_square) or self.is_enemy(new_square, color):
                        moves.append(Move(square, new_square))
            
            # Castling
            self.generate_castling_moves(square, color, moves)
        
        else:  # Sliding pieces (bishop, rook, queen)
            if piece_type == BISHOP:
                directions = BISHOP_DIRECTIONS
            elif piece_type == ROOK:
                directions = ROOK_DIRECTIONS
            else:  # QUEEN
                directions = QUEEN_DIRECTIONS
            
            for dr, df in directions:
                for distance in range(1, 8):
                    new_rank = rank + dr * distance
                    new_file = file + df * distance
                    if not is_valid_square(new_rank, new_file):
                        break
                    
                    new_square = coords_to_square(new_rank, new_file)
                    if self.is_empty(new_square):
                        moves.append(Move(square, new_square))
                    elif self.is_enemy(new_square, color):
                        moves.append(Move(square, new_square))
                        break
                    else:  # Friendly piece
                        break
    
    def generate_castling_moves(self, king_square, color, moves):
        """Generate castling moves for both standard and Chess960."""
        if self.is_in_check(color):
            return

        rank = 0 if color == WHITE else 7
        color_name = 'white' if color == WHITE else 'black'

        # Get original positions for Chess960
        if self.chess960:
            king_file = self.original_king_file[color_name]
            kingside_rook_file = self.original_rook_files[color_name]['kingside']
            queenside_rook_file = self.original_rook_files[color_name]['queenside']
        else:
            king_file = 4  # Standard position
            kingside_rook_file = 7
            queenside_rook_file = 0

        # Kingside castling
        castle_key = 'K' if color == WHITE else 'k'
        if self.castling_rights[castle_key]:
            if self._can_castle_kingside(color, king_square, rank, king_file, kingside_rook_file):
                target_square = coords_to_square(rank, 6)  # g-file for both standard and Chess960
                moves.append(Move(king_square, target_square, is_castling=True))

        # Queenside castling
        castle_key = 'Q' if color == WHITE else 'q'
        if self.castling_rights[castle_key]:
            if self._can_castle_queenside(color, king_square, rank, king_file, queenside_rook_file):
                target_square = coords_to_square(rank, 2)  # c-file for both standard and Chess960
                moves.append(Move(king_square, target_square, is_castling=True))

    def _can_castle_kingside(self, color, king_square, rank, king_file, rook_file):
        """Check if kingside castling is possible."""
        # Target squares for king and rook
        king_target = 6  # g-file
        rook_target = 5  # f-file

        # Check if rook is still in original position
        rook_square = coords_to_square(rank, rook_file)
        if self.board[rook_square] != ROOK or self.colors[rook_square] != color:
            return False

        # Check squares between king and target (inclusive)
        start_file = min(king_file, king_target)
        end_file = max(king_file, king_target)

        for file in range(start_file, end_file + 1):
            square = coords_to_square(rank, file)
            # Square must be empty (except for king and rook in original positions)
            if square != king_square and square != rook_square and not self.is_empty(square):
                return False
            # King cannot move through check
            if file >= min(king_file, king_target) and file <= max(king_file, king_target):
                if self.is_square_attacked(coords_to_square(rank, file), opposite_color(color)):
                    return False

        # Check squares between rook and target
        start_file = min(rook_file, rook_target)
        end_file = max(rook_file, rook_target)

        for file in range(start_file, end_file + 1):
            square = coords_to_square(rank, file)
            if square != king_square and square != rook_square and not self.is_empty(square):
                return False

        return True

    def _can_castle_queenside(self, color, king_square, rank, king_file, rook_file):
        """Check if queenside castling is possible."""
        # Target squares for king and rook
        king_target = 2  # c-file
        rook_target = 3  # d-file

        # Check if rook is still in original position
        rook_square = coords_to_square(rank, rook_file)
        if self.board[rook_square] != ROOK or self.colors[rook_square] != color:
            return False

        # Check squares between king and target (inclusive)
        start_file = min(king_file, king_target)
        end_file = max(king_file, king_target)

        for file in range(start_file, end_file + 1):
            square = coords_to_square(rank, file)
            # Square must be empty (except for king and rook in original positions)
            if square != king_square and square != rook_square and not self.is_empty(square):
                return False
            # King cannot move through check
            if file >= min(king_file, king_target) and file <= max(king_file, king_target):
                if self.is_square_attacked(coords_to_square(rank, file), opposite_color(color)):
                    return False

        # Check squares between rook and target
        start_file = min(rook_file, rook_target)
        end_file = max(rook_file, rook_target)

        for file in range(start_file, end_file + 1):
            square = coords_to_square(rank, file)
            if square != king_square and square != rook_square and not self.is_empty(square):
                return False

        return True

    def generate_legal_moves(self):
        """Generate all legal moves for the current position."""
        moves = []

        for square in range(64):
            if not self.is_empty(square) and self.colors[square] == self.to_move:
                piece_type = self.board[square]
                if piece_type == PAWN:
                    self.generate_pawn_moves(square, self.to_move, moves)
                else:
                    self.generate_piece_moves(square, piece_type, self.to_move, moves)

        # Filter out moves that leave king in check
        legal_moves = []
        for move in moves:
            board_copy = self.copy()
            board_copy.make_move(move)
            if not board_copy.is_in_check(self.to_move):
                legal_moves.append(move)

        return legal_moves

    def make_move(self, move):
        """Make a move on the board."""
        from_square = move.from_square
        to_square = move.to_square

        # Store move for history
        move_info = {
            'move': move,
            'captured_piece': self.board[to_square],
            'captured_color': self.colors[to_square] if not self.is_empty(to_square) else None,
            'castling_rights': self.castling_rights.copy(),
            'en_passant_square': self.en_passant_square,
            'halfmove_clock': self.halfmove_clock
        }
        self.move_history.append(move_info)

        # Handle en passant capture
        if move.is_en_passant:
            # Remove the captured pawn
            captured_pawn_rank = square_to_coords(from_square)[0]
            captured_pawn_square = coords_to_square(captured_pawn_rank, square_to_coords(to_square)[1])
            self.board[captured_pawn_square] = EMPTY

        # Handle castling
        if move.is_castling:
            king_rank = square_to_coords(from_square)[0]
            color_name = 'white' if self.colors[from_square] == WHITE else 'black'

            if square_to_coords(to_square)[1] == 6:  # Kingside castling
                if self.chess960:
                    rook_from_file = self.original_rook_files[color_name]['kingside']
                    rook_from = coords_to_square(king_rank, rook_from_file)
                else:
                    rook_from = coords_to_square(king_rank, 7)
                rook_to = coords_to_square(king_rank, 5)  # f-file
            else:  # Queenside castling
                if self.chess960:
                    rook_from_file = self.original_rook_files[color_name]['queenside']
                    rook_from = coords_to_square(king_rank, rook_from_file)
                else:
                    rook_from = coords_to_square(king_rank, 0)
                rook_to = coords_to_square(king_rank, 3)  # d-file

            # Move the rook
            self.board[rook_to] = self.board[rook_from]
            self.colors[rook_to] = self.colors[rook_from]
            self.board[rook_from] = EMPTY

        # Move the piece
        moving_piece = self.board[from_square]
        moving_color = self.colors[from_square]

        self.board[to_square] = moving_piece
        self.colors[to_square] = moving_color
        self.board[from_square] = EMPTY

        # Handle promotion
        if move.promotion:
            self.board[to_square] = move.promotion

        # Update castling rights
        if moving_piece == KING:
            if moving_color == WHITE:
                self.castling_rights['K'] = False
                self.castling_rights['Q'] = False
            else:
                self.castling_rights['k'] = False
                self.castling_rights['q'] = False
        elif moving_piece == ROOK:
            # Check if rook moved from original position (Chess960 compatible)
            from_rank, from_file = square_to_coords(from_square)
            color_name = 'white' if moving_color == WHITE else 'black'

            if self.chess960:
                # Check against original rook positions
                if (from_rank == (0 if moving_color == WHITE else 7) and
                    from_file == self.original_rook_files[color_name]['kingside']):
                    if moving_color == WHITE:
                        self.castling_rights['K'] = False
                    else:
                        self.castling_rights['k'] = False
                elif (from_rank == (0 if moving_color == WHITE else 7) and
                      from_file == self.original_rook_files[color_name]['queenside']):
                    if moving_color == WHITE:
                        self.castling_rights['Q'] = False
                    else:
                        self.castling_rights['q'] = False
            else:
                # Standard chess castling rights
                if from_square == 0:  # a1
                    self.castling_rights['Q'] = False
                elif from_square == 7:  # h1
                    self.castling_rights['K'] = False
                elif from_square == 56:  # a8
                    self.castling_rights['q'] = False
                elif from_square == 63:  # h8
                    self.castling_rights['k'] = False

        # Update en passant square
        self.en_passant_square = None
        if moving_piece == PAWN:
            from_rank, from_file = square_to_coords(from_square)
            to_rank, to_file = square_to_coords(to_square)
            if abs(to_rank - from_rank) == 2:  # Double pawn move
                self.en_passant_square = coords_to_square((from_rank + to_rank) // 2, from_file)

        # Update halfmove clock
        if moving_piece == PAWN or not self.is_empty(to_square):
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        # Update move counters
        if self.to_move == BLACK:
            self.fullmove_number += 1
        self.to_move = opposite_color(self.to_move)

    def undo_move(self):
        """Undo the last move."""
        if not self.move_history:
            return False

        move_info = self.move_history.pop()
        move = move_info['move']

        # Restore board state
        self.castling_rights = move_info['castling_rights']
        self.en_passant_square = move_info['en_passant_square']
        self.halfmove_clock = move_info['halfmove_clock']

        # Switch turn back
        self.to_move = opposite_color(self.to_move)
        if self.to_move == BLACK:
            self.fullmove_number -= 1

        from_square = move.from_square
        to_square = move.to_square

        # Move piece back
        moving_piece = self.board[to_square]
        if move.promotion:
            moving_piece = PAWN  # Restore original pawn

        self.board[from_square] = moving_piece
        self.colors[from_square] = self.to_move

        # Restore captured piece
        if move_info['captured_piece'] != EMPTY:
            self.board[to_square] = move_info['captured_piece']
            self.colors[to_square] = move_info['captured_color']
        else:
            self.board[to_square] = EMPTY

        # Handle special moves
        if move.is_en_passant:
            # Restore captured pawn
            captured_pawn_rank = square_to_coords(from_square)[0]
            captured_pawn_square = coords_to_square(captured_pawn_rank, square_to_coords(to_square)[1])
            self.board[captured_pawn_square] = PAWN
            self.colors[captured_pawn_square] = opposite_color(self.to_move)
            self.board[to_square] = EMPTY

        if move.is_castling:
            # Move rook back
            king_rank = square_to_coords(from_square)[0]
            if square_to_coords(to_square)[1] == 6:  # Kingside
                rook_from = coords_to_square(king_rank, 7)
                rook_to = coords_to_square(king_rank, 5)
            else:  # Queenside
                rook_from = coords_to_square(king_rank, 0)
                rook_to = coords_to_square(king_rank, 3)

            self.board[rook_from] = self.board[rook_to]
            self.colors[rook_from] = self.colors[rook_to]
            self.board[rook_to] = EMPTY

        return True
