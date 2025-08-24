# Chess Position Evaluation

from utils import *

# Piece-square tables for positional evaluation
PAWN_TABLE = [
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5,  5, 10, 25, 25, 10,  5,  5,
    0,  0,  0, 20, 20,  0,  0,  0,
    5, -5,-10,  0,  0,-10, -5,  5,
    5, 10, 10,-20,-20, 10, 10,  5,
    0,  0,  0,  0,  0,  0,  0,  0
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]

ROOK_TABLE = [
    0,  0,  0,  0,  0,  0,  0,  0,
    5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    0,  0,  0,  5,  5,  0,  0,  0
]

QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
    -5,  0,  5,  5,  5,  5,  0, -5,
    0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

KING_TABLE_MIDDLEGAME = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    20, 20,  0,  0,  0,  0, 20, 20,
    20, 30, 10,  0,  0, 10, 30, 20
]

KING_TABLE_ENDGAME = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50
]

PIECE_SQUARE_TABLES = {
    PAWN: PAWN_TABLE,
    KNIGHT: KNIGHT_TABLE,
    BISHOP: BISHOP_TABLE,
    ROOK: ROOK_TABLE,
    QUEEN: QUEEN_TABLE,
    KING: KING_TABLE_MIDDLEGAME  # Will switch to endgame table when appropriate
}

def flip_table(table):
    """Flip piece-square table for black pieces."""
    flipped = [0] * 64
    for i in range(64):
        rank = i // 8
        file = i % 8
        flipped_rank = 7 - rank
        flipped_square = flipped_rank * 8 + file
        flipped[i] = table[flipped_square]
    return flipped

def is_endgame(board):
    """Determine if position is in endgame phase."""
    # Simple endgame detection: few pieces remaining
    piece_count = sum(1 for square in range(64) if not board.is_empty(square))
    return piece_count <= 10

def evaluate_material(board):
    """Evaluate material balance."""
    score = 0
    for square in range(64):
        if not board.is_empty(square):
            piece = board.get_piece(square)
            color = board.get_color(square)
            value = PIECE_VALUES[piece]
            if color == WHITE:
                score += value
            else:
                score -= value
    return score

def evaluate_position(board):
    """Evaluate positional factors using piece-square tables."""
    score = 0
    endgame = is_endgame(board)
    
    for square in range(64):
        if not board.is_empty(square):
            piece = board.get_piece(square)
            color = board.get_color(square)
            
            # Get appropriate piece-square table
            if piece == KING and endgame:
                table = KING_TABLE_ENDGAME
            else:
                table = PIECE_SQUARE_TABLES.get(piece, [0] * 64)
            
            # Flip table for black pieces
            if color == BLACK:
                table = flip_table(table)
            
            positional_value = table[square]
            
            if color == WHITE:
                score += positional_value
            else:
                score -= positional_value
    
    return score

def evaluate_mobility(board):
    """Evaluate mobility (number of legal moves)."""
    # Save current state
    original_to_move = board.to_move
    
    # Count moves for white
    board.to_move = WHITE
    white_moves = len(board.generate_legal_moves())
    
    # Count moves for black
    board.to_move = BLACK
    black_moves = len(board.generate_legal_moves())
    
    # Restore original state
    board.to_move = original_to_move
    
    return (white_moves - black_moves) * 10

def evaluate_king_safety(board):
    """Evaluate king safety."""
    score = 0
    
    for color in [WHITE, BLACK]:
        king_square = board.find_king(color)
        if king_square is None:
            continue
        
        king_rank, king_file = square_to_coords(king_square)
        safety_score = 0
        
        # Check pawn shield (for non-endgame)
        if not is_endgame(board):
            pawn_direction = 1 if color == WHITE else -1
            shield_rank = king_rank + pawn_direction
            
            for file_offset in [-1, 0, 1]:
                shield_file = king_file + file_offset
                if is_valid_square(shield_rank, shield_file):
                    shield_square = coords_to_square(shield_rank, shield_file)
                    if (board.get_piece(shield_square) == PAWN and 
                        board.get_color(shield_square) == color):
                        safety_score += 10
        
        # Penalty for exposed king
        attack_count = 0
        for dr in [-1, 0, 1]:
            for df in [-1, 0, 1]:
                if dr == 0 and df == 0:
                    continue
                check_rank, check_file = king_rank + dr, king_file + df
                if is_valid_square(check_rank, check_file):
                    check_square = coords_to_square(check_rank, check_file)
                    if board.is_square_attacked(check_square, opposite_color(color)):
                        attack_count += 1
        
        safety_score -= attack_count * 5
        
        if color == WHITE:
            score += safety_score
        else:
            score -= safety_score
    
    return score

def evaluate_board(board):
    """Main evaluation function."""
    # Check for checkmate/stalemate
    legal_moves = board.generate_legal_moves()
    if not legal_moves:
        if board.is_in_check(board.to_move):
            # Checkmate
            return -20000 if board.to_move == WHITE else 20000
        else:
            # Stalemate
            return 0
    
    score = 0
    
    # Material evaluation
    score += evaluate_material(board)
    
    # Positional evaluation
    score += evaluate_position(board)
    
    # Mobility evaluation
    score += evaluate_mobility(board)
    
    # King safety evaluation
    score += evaluate_king_safety(board)
    
    return score
