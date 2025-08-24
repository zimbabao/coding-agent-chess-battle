# Chess Engine Utilities and Constants

# Piece constants
EMPTY = 0
PAWN = 1
KNIGHT = 2
BISHOP = 3
ROOK = 4
QUEEN = 5
KING = 6

WHITE = 0
BLACK = 1

# Piece values for evaluation
PIECE_VALUES = {
    EMPTY: 0,
    PAWN: 100,
    KNIGHT: 320,
    BISHOP: 330,
    ROOK: 500,
    QUEEN: 900,
    KING: 20000
}

# Square constants (a1 = 0, h8 = 63)
def square_to_coords(square):
    """Convert square index to (rank, file) coordinates."""
    return square // 8, square % 8

def coords_to_square(rank, file):
    """Convert (rank, file) coordinates to square index."""
    return rank * 8 + file

def square_to_algebraic(square):
    """Convert square index to algebraic notation (e.g., 0 -> 'a1')."""
    rank, file = square_to_coords(square)
    return chr(ord('a') + file) + str(rank + 1)

def algebraic_to_square(algebraic):
    """Convert algebraic notation to square index (e.g., 'a1' -> 0)."""
    file = ord(algebraic[0]) - ord('a')
    rank = int(algebraic[1]) - 1
    return coords_to_square(rank, file)

# Direction vectors for piece movement
KNIGHT_MOVES = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
KING_MOVES = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
BISHOP_DIRECTIONS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
ROOK_DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
QUEEN_DIRECTIONS = BISHOP_DIRECTIONS + ROOK_DIRECTIONS

def is_valid_square(rank, file):
    """Check if rank and file are within board bounds."""
    return 0 <= rank < 8 and 0 <= file < 8

def opposite_color(color):
    """Return the opposite color."""
    return 1 - color

# Move representation
class Move:
    def __init__(self, from_square, to_square, promotion=None, is_castling=False, is_en_passant=False):
        self.from_square = from_square
        self.to_square = to_square
        self.promotion = promotion
        self.is_castling = is_castling
        self.is_en_passant = is_en_passant
    
    def __str__(self):
        """Convert move to UCI format."""
        move_str = square_to_algebraic(self.from_square) + square_to_algebraic(self.to_square)
        if self.promotion:
            promotion_chars = {QUEEN: 'q', ROOK: 'r', BISHOP: 'b', KNIGHT: 'n'}
            move_str += promotion_chars[self.promotion]
        return move_str
    
    def __eq__(self, other):
        return (self.from_square == other.from_square and 
                self.to_square == other.to_square and
                self.promotion == other.promotion)
    
    def __hash__(self):
        return hash((self.from_square, self.to_square, self.promotion))

def parse_uci_move(move_str):
    """Parse UCI move string into Move object."""
    from_square = algebraic_to_square(move_str[:2])
    to_square = algebraic_to_square(move_str[2:4])
    
    promotion = None
    if len(move_str) == 5:
        promotion_chars = {'q': QUEEN, 'r': ROOK, 'b': BISHOP, 'n': KNIGHT}
        promotion = promotion_chars[move_str[4]]
    
    return Move(from_square, to_square, promotion)

# Initial board setup
INITIAL_BOARD = [
    # Rank 1 (White pieces)
    ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK,
    # Rank 2 (White pawns)
    PAWN, PAWN, PAWN, PAWN, PAWN, PAWN, PAWN, PAWN,
    # Ranks 3-6 (Empty squares)
    EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY,
    EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY,
    EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY,
    EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY,
    # Rank 7 (Black pawns)
    PAWN, PAWN, PAWN, PAWN, PAWN, PAWN, PAWN, PAWN,
    # Rank 8 (Black pieces)
    ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK
]

INITIAL_COLORS = [
    # Rank 1 (White pieces)
    WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE,
    # Rank 2 (White pawns)
    WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE,
    # Ranks 3-6 (Empty squares)
    WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE,  # Dummy colors for empty squares
    WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE,
    WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE,
    WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE,
    # Rank 7 (Black pawns)
    BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,
    # Rank 8 (Black pieces)
    BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK
]
