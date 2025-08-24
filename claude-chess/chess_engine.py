#!/usr/bin/env python3
"""
Claude Chess Engine - A comprehensive chess engine with multiple interfaces.

This module provides:
- Complete chess game logic with proper move validation
- Multiple game interfaces: CLI, GUI (tkinter), and Web interface
- Chess960 support
- Engine AI with minimax algorithm and alpha-beta pruning
- Comprehensive test suite

Main classes:
- ChessBoard: Core board representation and move logic
- ChessEngine: AI engine with search algorithms
- InteractiveGame: Command-line interface
- GUI: Tkinter-based graphical interface
- WebGUI: Web-based interface

Author: Claude Code Assistant
"""

import sys
import time
import random
import threading
from typing import List, Tuple, Optional, Dict

# Configuration constants
DEFAULT_ENGINE_DEPTH = 4
DEFAULT_WEB_PORT = 8080
DEFAULT_SEARCH_TIMEOUT = 30.0
MAX_SEARCH_DEPTH = 10

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

# Simple web GUI alternative
try:
    import http.server
    import socketserver
    import webbrowser
    import json
    import urllib.parse
    WEB_GUI_AVAILABLE = True
except ImportError:
    WEB_GUI_AVAILABLE = False

PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000,
    'p': -100, 'n': -320, 'b': -330, 'r': -500, 'q': -900, 'k': -20000
}

PIECE_SQUARE_TABLES = {
    'P': [
        0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5,  5, 10, 25, 25, 10,  5,  5,
        0,  0,  0, 20, 20,  0,  0,  0,
        5, -5,-10,  0,  0,-10, -5,  5,
        5, 10, 10,-20,-20, 10, 10,  5,
        0,  0,  0,  0,  0,  0,  0,  0
    ],
    'N': [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50
    ],
    'B': [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20
    ],
    'R': [
        0,  0,  0,  0,  0,  0,  0,  0,
        5, 10, 10, 10, 10, 10, 10,  5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        0,  0,  0,  5,  5,  0,  0,  0
    ],
    'Q': [
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5,  5,  5,  5,  0,-10,
        -5,  0,  5,  5,  5,  5,  0, -5,
        0,  0,  5,  5,  5,  5,  0, -5,
        -10,  5,  5,  5,  5,  5,  0,-10,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20
    ],
    'K': [
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
        20, 20,  0,  0,  0,  0, 20, 20,
        20, 30, 10,  0,  0, 10, 30, 20
    ]
}

class ChessBoard:
    def __init__(self, chess960=False, position_id=None):
        self.chess960 = chess960
        self.king_start_file = {'white': 4, 'black': 4}  # For castling in Chess960
        self.rook_start_files = {'white': {'K': 7, 'Q': 0}, 'black': {'k': 7, 'q': 0}}
        
        if chess960 and position_id is not None:
            self.setup_chess960_position(position_id)
        elif chess960:
            self.setup_random_chess960_position()
        else:
            self.setup_standard_position()
        
        self.white_to_move = True
        self.castling_rights = {'K': True, 'Q': True, 'k': True, 'q': True}
        self.en_passant_target = None
        self.halfmove_clock = 0
        self.fullmove_number = 1
        
        # Track captured pieces
        self.captured_pieces = {'white': [], 'black': []}
        
        # Performance optimization: cache for move generation
        self._move_cache = {}
        self._cache_hits = 0

    def setup_standard_position(self):
        self.board = [
            ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
            ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
            ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        ]
        self.king_start_file = {'white': 4, 'black': 4}
        self.rook_start_files = {'white': {'K': 7, 'Q': 0}, 'black': {'k': 7, 'q': 0}}

    def setup_random_chess960_position(self):
        position_id = random.randint(0, 959)
        self.setup_chess960_position(position_id)

    def setup_chess960_position(self, position_id):
        if not (0 <= position_id <= 959):
            raise ValueError("Chess960 position ID must be between 0 and 959")
        
        # Generate Chess960 starting position from position ID
        back_rank = self.generate_chess960_rank(position_id)
        
        self.board = [
            [piece.lower() for piece in back_rank],  # Black back rank
            ['p'] * 8,                                # Black pawns
            ['.'] * 8,                                # Empty ranks
            ['.'] * 8,
            ['.'] * 8,
            ['.'] * 8,
            ['P'] * 8,                                # White pawns
            back_rank[:]                              # White back rank
        ]
        
        # Find king and rook positions for castling
        self.king_start_file = {
            'white': back_rank.index('K'),
            'black': back_rank.index('K')
        }
        
        # Find rook positions
        rook_positions = [i for i, piece in enumerate(back_rank) if piece == 'R']
        if len(rook_positions) == 2:
            # Queenside rook is the leftmost, kingside is the rightmost
            self.rook_start_files = {
                'white': {'Q': rook_positions[0], 'K': rook_positions[1]},
                'black': {'q': rook_positions[0], 'k': rook_positions[1]}
            }
        else:
            # Fallback (shouldn't happen with valid Chess960)
            self.rook_start_files = {'white': {'K': 7, 'Q': 0}, 'black': {'k': 7, 'q': 0}}

    def generate_chess960_rank(self, position_id):
        # Chess960 position generation algorithm
        # This generates one of the 960 possible starting positions
        
        # Step 1: Place bishops on opposite colored squares
        position = [None] * 8
        
        # Light-squared bishop (squares 1, 3, 5, 7)
        light_squares = [1, 3, 5, 7]
        dark_squares = [0, 2, 4, 6]
        
        # Extract bishop placement from position_id
        n = position_id
        light_bishop_pos = light_squares[n % 4]
        n //= 4
        dark_bishop_pos = dark_squares[n % 4]
        n //= 4
        
        position[light_bishop_pos] = 'B'
        position[dark_bishop_pos] = 'B'
        
        # Step 2: Place queen on one of the remaining squares
        remaining_squares = [i for i in range(8) if position[i] is None]
        queen_pos = remaining_squares[n % 6]
        n //= 6
        position[queen_pos] = 'Q'
        
        # Step 3: Place knights on two of the remaining squares
        remaining_squares = [i for i in range(8) if position[i] is None]
        # There are C(5,2) = 10 ways to place 2 knights on 5 squares
        knight_combinations = []
        for i in range(5):
            for j in range(i + 1, 5):
                knight_combinations.append((i, j))
        
        knight_combo = knight_combinations[n % 10]
        position[remaining_squares[knight_combo[0]]] = 'N'
        position[remaining_squares[knight_combo[1]]] = 'N'
        
        # Step 4: Place rook-king-rook in the remaining squares
        remaining_squares = [i for i in range(8) if position[i] is None]
        position[remaining_squares[0]] = 'R'
        position[remaining_squares[1]] = 'K'
        position[remaining_squares[2]] = 'R'
        
        return position

    def copy(self):
        new_board = ChessBoard()
        new_board.board = [row[:] for row in self.board]
        new_board.white_to_move = self.white_to_move
        new_board.castling_rights = self.castling_rights.copy()
        new_board.en_passant_target = self.en_passant_target
        new_board.halfmove_clock = self.halfmove_clock
        new_board.fullmove_number = self.fullmove_number
        new_board.chess960 = self.chess960
        new_board.king_start_file = self.king_start_file.copy()
        new_board.rook_start_files = {
            'white': self.rook_start_files['white'].copy(),
            'black': self.rook_start_files['black'].copy()
        }
        new_board.captured_pieces = {
            'white': self.captured_pieces['white'].copy(),
            'black': self.captured_pieces['black'].copy()
        }
        return new_board

    def from_fen(self, fen: str):
        parts = fen.split()
        
        # Board position
        rows = parts[0].split('/')
        for i, row in enumerate(rows):
            col = 0
            for char in row:
                if char.isdigit():
                    for _ in range(int(char)):
                        self.board[i][col] = '.'
                        col += 1
                else:
                    self.board[i][col] = char
                    col += 1
        
        # Active color
        self.white_to_move = parts[1] == 'w'
        
        # Castling rights
        castling = parts[2]
        self.castling_rights = {
            'K': 'K' in castling,
            'Q': 'Q' in castling,
            'k': 'k' in castling,
            'q': 'q' in castling
        }
        
        # En passant target
        self.en_passant_target = parts[3] if parts[3] != '-' else None
        
        # Halfmove clock and fullmove number
        self.halfmove_clock = int(parts[4])
        self.fullmove_number = int(parts[5])

    def to_fen(self) -> str:
        # Board position
        fen_rows = []
        for row in self.board:
            fen_row = ""
            empty_count = 0
            for piece in row:
                if piece == '.':
                    empty_count += 1
                else:
                    if empty_count > 0:
                        fen_row += str(empty_count)
                        empty_count = 0
                    fen_row += piece
            if empty_count > 0:
                fen_row += str(empty_count)
            fen_rows.append(fen_row)
        
        position = '/'.join(fen_rows)
        
        # Active color
        active_color = 'w' if self.white_to_move else 'b'
        
        # Castling rights
        castling = ''
        if self.castling_rights['K']:
            castling += 'K'
        if self.castling_rights['Q']:
            castling += 'Q'
        if self.castling_rights['k']:
            castling += 'k'
        if self.castling_rights['q']:
            castling += 'q'
        if not castling:
            castling = '-'
        
        # En passant target
        en_passant = self.en_passant_target if self.en_passant_target else '-'
        
        return f"{position} {active_color} {castling} {en_passant} {self.halfmove_clock} {self.fullmove_number}"

    def get_piece(self, row: int, col: int) -> str:
        if 0 <= row < 8 and 0 <= col < 8:
            return self.board[row][col]
        return None

    def set_piece(self, row: int, col: int, piece: str):
        if 0 <= row < 8 and 0 <= col < 8:
            self.board[row][col] = piece

    def is_white_piece(self, piece: str) -> bool:
        return piece.isupper()

    def is_black_piece(self, piece: str) -> bool:
        return piece.islower()

    def is_empty(self, row: int, col: int) -> bool:
        return self.get_piece(row, col) == '.'

    def is_valid_square(self, row: int, col: int) -> bool:
        return 0 <= row < 8 and 0 <= col < 8

    def get_captured_pieces(self) -> dict:
        """Get all captured pieces organized by color."""
        return {
            'white': self.captured_pieces['white'].copy(),
            'black': self.captured_pieces['black'].copy()
        }

    def generate_moves(self) -> List[str]:
        """Generate all legal moves for the current position."""
        # Create a simple position hash for caching
        position_hash = self._get_position_hash()
        
        if position_hash in self._move_cache:
            self._cache_hits += 1
            return self._move_cache[position_hash].copy()
        
        pseudo_legal_moves = []
        for row in range(8):
            for col in range(8):
                piece = self.get_piece(row, col)
                if piece != '.' and ((self.white_to_move and self.is_white_piece(piece)) or 
                                   (not self.white_to_move and self.is_black_piece(piece))):
                    pseudo_legal_moves.extend(self.generate_piece_moves(row, col, piece))
        
        # Filter out illegal moves that would leave king in check
        legal_moves = []
        for move in pseudo_legal_moves:
            if self.is_legal_move(move):
                legal_moves.append(move)
        
        # Cache the result (limit cache size to prevent memory issues)
        if len(self._move_cache) < 1000:
            self._move_cache[position_hash] = legal_moves.copy()
        
        return legal_moves
    
    def _get_position_hash(self) -> str:
        """Create a simple hash of the current position for caching."""
        board_str = ''.join(''.join(row) for row in self.board)
        return f"{board_str}_{self.white_to_move}_{self.castling_rights}_{self.en_passant_target}"

    def generate_piece_moves(self, row: int, col: int, piece: str) -> List[str]:
        piece_type = piece.lower()
        moves = []
        
        if piece_type == 'p':
            moves.extend(self.generate_pawn_moves(row, col, piece))
        elif piece_type == 'r':
            moves.extend(self.generate_rook_moves(row, col, piece))
        elif piece_type == 'n':
            moves.extend(self.generate_knight_moves(row, col, piece))
        elif piece_type == 'b':
            moves.extend(self.generate_bishop_moves(row, col, piece))
        elif piece_type == 'q':
            moves.extend(self.generate_queen_moves(row, col, piece))
        elif piece_type == 'k':
            moves.extend(self.generate_king_moves(row, col, piece))
        
        return moves

    def generate_pawn_moves(self, row: int, col: int, piece: str) -> List[str]:
        moves = []
        is_white = self.is_white_piece(piece)
        direction = -1 if is_white else 1
        start_row = 6 if is_white else 1
        
        # Forward moves
        new_row = row + direction
        if self.is_valid_square(new_row, col) and self.is_empty(new_row, col):
            if new_row == 0 or new_row == 7:
                # Promotion
                for promote_to in ['q', 'r', 'b', 'n']:
                    if is_white:
                        promote_to = promote_to.upper()
                    moves.append(f"{chr(col + ord('a'))}{8 - row}{chr(col + ord('a'))}{8 - new_row}{promote_to}")
            else:
                moves.append(f"{chr(col + ord('a'))}{8 - row}{chr(col + ord('a'))}{8 - new_row}")
            
            # Double move from starting position
            if row == start_row:
                new_row2 = row + 2 * direction
                if self.is_valid_square(new_row2, col) and self.is_empty(new_row2, col):
                    moves.append(f"{chr(col + ord('a'))}{8 - row}{chr(col + ord('a'))}{8 - new_row2}")
        
        # Captures
        for dc in [-1, 1]:
            new_col = col + dc
            new_row = row + direction
            if self.is_valid_square(new_row, new_col):
                target = self.get_piece(new_row, new_col)
                if target != '.' and ((is_white and self.is_black_piece(target)) or 
                                    (not is_white and self.is_white_piece(target))):
                    if new_row == 0 or new_row == 7:
                        # Capture promotion
                        for promote_to in ['q', 'r', 'b', 'n']:
                            if is_white:
                                promote_to = promote_to.upper()
                            moves.append(f"{chr(col + ord('a'))}{8 - row}{chr(new_col + ord('a'))}{8 - new_row}{promote_to}")
                    else:
                        moves.append(f"{chr(col + ord('a'))}{8 - row}{chr(new_col + ord('a'))}{8 - new_row}")
                
                # En passant
                elif (self.en_passant_target and 
                      f"{chr(new_col + ord('a'))}{8 - new_row}" == self.en_passant_target):
                    moves.append(f"{chr(col + ord('a'))}{8 - row}{chr(new_col + ord('a'))}{8 - new_row}")
        
        return moves

    def generate_rook_moves(self, row: int, col: int, piece: str) -> List[str]:
        moves = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for dr, dc in directions:
            for i in range(1, 8):
                new_row, new_col = row + i * dr, col + i * dc
                if not self.is_valid_square(new_row, new_col):
                    break
                
                target = self.get_piece(new_row, new_col)
                if target == '.':
                    moves.append(f"{chr(col + ord('a'))}{8 - row}{chr(new_col + ord('a'))}{8 - new_row}")
                else:
                    if ((self.is_white_piece(piece) and self.is_black_piece(target)) or
                        (self.is_black_piece(piece) and self.is_white_piece(target))):
                        moves.append(f"{chr(col + ord('a'))}{8 - row}{chr(new_col + ord('a'))}{8 - new_row}")
                    break
        
        return moves

    def generate_knight_moves(self, row: int, col: int, piece: str) -> List[str]:
        moves = []
        knight_moves = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
        
        for dr, dc in knight_moves:
            new_row, new_col = row + dr, col + dc
            if self.is_valid_square(new_row, new_col):
                target = self.get_piece(new_row, new_col)
                if (target == '.' or 
                    (self.is_white_piece(piece) and self.is_black_piece(target)) or
                    (self.is_black_piece(piece) and self.is_white_piece(target))):
                    moves.append(f"{chr(col + ord('a'))}{8 - row}{chr(new_col + ord('a'))}{8 - new_row}")
        
        return moves

    def generate_bishop_moves(self, row: int, col: int, piece: str) -> List[str]:
        moves = []
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        
        for dr, dc in directions:
            for i in range(1, 8):
                new_row, new_col = row + i * dr, col + i * dc
                if not self.is_valid_square(new_row, new_col):
                    break
                
                target = self.get_piece(new_row, new_col)
                if target == '.':
                    moves.append(f"{chr(col + ord('a'))}{8 - row}{chr(new_col + ord('a'))}{8 - new_row}")
                else:
                    if ((self.is_white_piece(piece) and self.is_black_piece(target)) or
                        (self.is_black_piece(piece) and self.is_white_piece(target))):
                        moves.append(f"{chr(col + ord('a'))}{8 - row}{chr(new_col + ord('a'))}{8 - new_row}")
                    break
        
        return moves

    def generate_queen_moves(self, row: int, col: int, piece: str) -> List[str]:
        moves = []
        moves.extend(self.generate_rook_moves(row, col, piece))
        moves.extend(self.generate_bishop_moves(row, col, piece))
        return moves

    def generate_king_moves(self, row: int, col: int, piece: str) -> List[str]:
        moves = []
        king_moves = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        
        for dr, dc in king_moves:
            new_row, new_col = row + dr, col + dc
            if self.is_valid_square(new_row, new_col):
                target = self.get_piece(new_row, new_col)
                if (target == '.' or 
                    (self.is_white_piece(piece) and self.is_black_piece(target)) or
                    (self.is_black_piece(piece) and self.is_white_piece(target))):
                    moves.append(f"{chr(col + ord('a'))}{8 - row}{chr(new_col + ord('a'))}{8 - new_row}")
        
        # Castling (works for both standard and Chess960)
        moves.extend(self.generate_castling_moves(row, col, piece))
        
        return moves

    def generate_castling_moves(self, row: int, col: int, piece: str) -> List[str]:
        moves = []
        
        if self.is_white_piece(piece) and row == 7:
            king_start_col = self.king_start_file['white']
            if col == king_start_col:
                # White kingside castling
                if self.castling_rights['K']:
                    rook_start_col = self.rook_start_files['white']['K']
                    if self.can_castle(row, king_start_col, rook_start_col, 6, 5):  # King to g1, rook to f1
                        moves.append(f"{chr(king_start_col + ord('a'))}{8 - row}g1")
                
                # White queenside castling
                if self.castling_rights['Q']:
                    rook_start_col = self.rook_start_files['white']['Q']
                    if self.can_castle(row, king_start_col, rook_start_col, 2, 3):  # King to c1, rook to d1
                        moves.append(f"{chr(king_start_col + ord('a'))}{8 - row}c1")
        
        elif self.is_black_piece(piece) and row == 0:
            king_start_col = self.king_start_file['black']
            if col == king_start_col:
                # Black kingside castling
                if self.castling_rights['k']:
                    rook_start_col = self.rook_start_files['black']['k']
                    if self.can_castle(row, king_start_col, rook_start_col, 6, 5):  # King to g8, rook to f8
                        moves.append(f"{chr(king_start_col + ord('a'))}{8 - row}g8")
                
                # Black queenside castling
                if self.castling_rights['q']:
                    rook_start_col = self.rook_start_files['black']['q']
                    if self.can_castle(row, king_start_col, rook_start_col, 2, 3):  # King to c8, rook to d8
                        moves.append(f"{chr(king_start_col + ord('a'))}{8 - row}c8")
        
        return moves

    def can_castle(self, row: int, king_col: int, rook_col: int, king_target: int, rook_target: int) -> bool:
        # Check if castling is possible
        by_white = not self.white_to_move  # Opposite color attacks
        
        # Check that rook is still there
        expected_rook = 'R' if row == 7 else 'r'
        if self.get_piece(row, rook_col) != expected_rook:
            return False
        
        # Determine the range of squares that must be empty
        min_col = min(king_col, rook_col, king_target, rook_target)
        max_col = max(king_col, rook_col, king_target, rook_target)
        
        # Check that all squares between king and rook (and target squares) are empty
        # except for the king and rook themselves
        for col in range(min_col, max_col + 1):
            if col != king_col and col != rook_col and not self.is_empty(row, col):
                return False
        
        # Check that king is not in check and doesn't pass through check
        # King must not be attacked on its starting square, any square it passes through, or target square
        squares_to_check = []
        if king_col < king_target:  # Kingside castling
            squares_to_check = [king_col, king_col + 1, king_target]
        else:  # Queenside castling
            squares_to_check = [king_col, king_col - 1, king_target]
        
        for check_col in squares_to_check:
            if self.is_square_attacked(row, check_col, by_white):
                return False
        
        return True

    def is_square_attacked(self, row: int, col: int, by_white: bool) -> bool:
        for r in range(8):
            for c in range(8):
                piece = self.get_piece(r, c)
                if piece != '.' and ((by_white and self.is_white_piece(piece)) or 
                                   (not by_white and self.is_black_piece(piece))):
                    if self.can_piece_attack(r, c, piece, row, col):
                        return True
        return False

    def can_piece_attack(self, from_row: int, from_col: int, piece: str, to_row: int, to_col: int) -> bool:
        piece_type = piece.lower()
        dr, dc = to_row - from_row, to_col - from_col
        
        if piece_type == 'p':
            direction = -1 if self.is_white_piece(piece) else 1
            return dr == direction and abs(dc) == 1
        elif piece_type == 'r':
            return (dr == 0 or dc == 0) and self.is_path_clear(from_row, from_col, to_row, to_col)
        elif piece_type == 'n':
            return (abs(dr) == 2 and abs(dc) == 1) or (abs(dr) == 1 and abs(dc) == 2)
        elif piece_type == 'b':
            return abs(dr) == abs(dc) and self.is_path_clear(from_row, from_col, to_row, to_col)
        elif piece_type == 'q':
            return ((dr == 0 or dc == 0) or abs(dr) == abs(dc)) and self.is_path_clear(from_row, from_col, to_row, to_col)
        elif piece_type == 'k':
            return abs(dr) <= 1 and abs(dc) <= 1
        
        return False

    def is_path_clear(self, from_row: int, from_col: int, to_row: int, to_col: int) -> bool:
        dr = 0 if to_row == from_row else (1 if to_row > from_row else -1)
        dc = 0 if to_col == from_col else (1 if to_col > from_col else -1)
        
        r, c = from_row + dr, from_col + dc
        while r != to_row or c != to_col:
            if not self.is_empty(r, c):
                return False
            r, c = r + dr, c + dc
        
        return True

    def format_move_notation(self, move: str) -> str:
        """Convert internal move notation to proper chess notation."""
        if len(move) < 4:
            return move
            
        from_col = ord(move[0]) - ord('a')
        from_row = 8 - int(move[1])
        to_col = ord(move[2]) - ord('a')
        to_row = 8 - int(move[3])
        
        # Check for castling moves
        piece = self.get_piece(from_row, from_col)
        if piece.lower() == 'k':
            # White castling
            if from_row == 7 and from_col == self.king_start_file['white']:
                if to_col == 6:  # Kingside
                    return "O-O"
                elif to_col == 2:  # Queenside  
                    return "O-O-O"
            # Black castling
            elif from_row == 0 and from_col == self.king_start_file['black']:
                if to_col == 6:  # Kingside
                    return "O-O"
                elif to_col == 2:  # Queenside
                    return "O-O-O"
        
        # For non-castling moves, return original notation
        # Could be enhanced further with piece symbols, captures, etc.
        return move

    def is_legal_move(self, move: str) -> bool:
        """Check if a move is legal (valid piece movement and doesn't leave king in check)."""
        # Input validation
        if not isinstance(move, str) or len(move) < 4:
            return False
        
        try:
            # STEP 1: Check if move is in the list of generated moves (validates piece movement rules)
            from_col = ord(move[0]) - ord('a')
            from_row = 8 - int(move[1])
        except (IndexError, ValueError):
            return False
        
        if not (self.is_valid_square(from_row, from_col)):
            return False
            
        piece = self.get_piece(from_row, from_col)
        if piece == '.' or ((self.white_to_move and not self.is_white_piece(piece)) or 
                           (not self.white_to_move and not self.is_black_piece(piece))):
            return False
        
        # Generate valid moves for this specific piece
        piece_moves = self.generate_piece_moves(from_row, from_col, piece)
        
        # Check if the requested move is among valid piece moves
        if move not in piece_moves:
            return False
        
        # STEP 2: Check if the move leaves the king in check
        # Make a copy of the board and try the move
        board_copy = self.copy()
        
        # Execute the move on the copy (we know it's valid piece movement)
        if board_copy.make_move_unchecked(move):
            # Check if the move leaves the king in check
            # We need to check the king of the player who just moved
            board_copy.white_to_move = not board_copy.white_to_move  # Switch back to check the right king
            king_piece = 'K' if board_copy.white_to_move else 'k'
            
            # Find the king
            for row in range(8):
                for col in range(8):
                    if board_copy.get_piece(row, col) == king_piece:
                        # Check if this king is under attack
                        return not board_copy.is_square_attacked(row, col, not board_copy.white_to_move)
            
            return False  # King not found (shouldn't happen)
        else:
            return False  # Move failed for other reasons

    def make_move_unchecked(self, move: str) -> bool:
        """Execute a move without checking if it's legal (for internal use)."""
        if not isinstance(move, str) or len(move) < 4:
            return False
        
        try:
            from_col = ord(move[0]) - ord('a')
            from_row = 8 - int(move[1])
            to_col = ord(move[2]) - ord('a')
            to_row = 8 - int(move[3])
        except (IndexError, ValueError):
            return False
        
        if not (self.is_valid_square(from_row, from_col) and self.is_valid_square(to_row, to_col)):
            return False
        
        piece = self.get_piece(from_row, from_col)
        if piece == '.':
            return False
        
        # Check if it's the correct player's turn
        if (self.white_to_move and not self.is_white_piece(piece)) or \
           (not self.white_to_move and not self.is_black_piece(piece)):
            return False
        
        # ADDITIONAL SAFETY: Prevent capturing own pieces
        target_piece = self.get_piece(to_row, to_col)
        if target_piece != '.' and ((self.is_white_piece(piece) and self.is_white_piece(target_piece)) or
                                  (self.is_black_piece(piece) and self.is_black_piece(target_piece))):
            return False
        
        # Handle en passant capture
        if piece.lower() == 'p' and self.en_passant_target:
            if f"{move[2]}{move[3]}" == self.en_passant_target:
                # Get the captured pawn before removing it
                if self.white_to_move:
                    captured_pawn = self.get_piece(to_row + 1, to_col)
                    self.set_piece(to_row + 1, to_col, '.')
                else:
                    captured_pawn = self.get_piece(to_row - 1, to_col)
                    self.set_piece(to_row - 1, to_col, '.')
                
                # Track the en passant capture
                if captured_pawn != '.':
                    if self.is_white_piece(captured_pawn):
                        self.captured_pieces['white'].append(captured_pawn)
                    else:
                        self.captured_pieces['black'].append(captured_pawn)
        
        # Handle castling (both standard and Chess960)
        if piece.lower() == 'k' and self.is_castling_move(from_row, from_col, to_row, to_col, piece):
            self.execute_castling(from_row, from_col, to_col, piece)
        
        # Make the move
        captured_piece = self.get_piece(to_row, to_col)
        
        # Track captured pieces
        if captured_piece != '.':
            if self.is_white_piece(captured_piece):
                self.captured_pieces['white'].append(captured_piece)
            else:
                self.captured_pieces['black'].append(captured_piece)
        
        self.set_piece(to_row, to_col, piece)
        self.set_piece(from_row, from_col, '.')
        
        # Handle pawn promotion
        if len(move) == 5 and piece.lower() == 'p':
            promotion_piece = move[4]
            if self.is_black_piece(piece):
                promotion_piece = promotion_piece.lower()
            else:
                promotion_piece = promotion_piece.upper()
            self.set_piece(to_row, to_col, promotion_piece)
        
        # Update castling rights
        if piece == 'K':
            self.castling_rights['K'] = False
            self.castling_rights['Q'] = False
        elif piece == 'k':
            self.castling_rights['k'] = False
            self.castling_rights['q'] = False
        elif piece == 'R':
            if from_row == 7:
                if from_col == self.rook_start_files['white']['Q']:
                    self.castling_rights['Q'] = False
                elif from_col == self.rook_start_files['white']['K']:
                    self.castling_rights['K'] = False
        elif piece == 'r':
            if from_row == 0:
                if from_col == self.rook_start_files['black']['q']:
                    self.castling_rights['q'] = False
                elif from_col == self.rook_start_files['black']['k']:
                    self.castling_rights['k'] = False
        
        # Update en passant target
        if piece.lower() == 'p' and abs(from_row - to_row) == 2:
            self.en_passant_target = f"{chr(from_col + ord('a'))}{8 - (from_row + to_row) // 2}"
        else:
            self.en_passant_target = None
        
        # Update halfmove clock
        if piece.lower() == 'p' or captured_piece != '.':
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1
        
        # Update fullmove number
        if not self.white_to_move:
            self.fullmove_number += 1
        
        # Switch turns
        self.white_to_move = not self.white_to_move
        
        # Clear move cache since position has changed
        self._move_cache.clear()
        
        return True

    def make_move(self, move: str) -> bool:
        """Execute a move if it's legal."""
        # CRITICAL: Check if this move is legal (doesn't leave king in check)
        if not self.is_legal_move(move):
            return False
        
        # If legal, execute the move
        return self.make_move_unchecked(move)

    def is_castling_move(self, from_row: int, from_col: int, to_row: int, to_col: int, piece: str) -> bool:
        # Check if this is a castling move
        if from_row != to_row:
            return False
        
        if self.is_white_piece(piece):
            king_start = self.king_start_file['white']
            return from_col == king_start and (to_col == 2 or to_col == 6)
        else:
            king_start = self.king_start_file['black']
            return from_col == king_start and (to_col == 2 or to_col == 6)

    def execute_castling(self, row: int, from_col: int, to_col: int, piece: str):
        # Execute castling move for both standard and Chess960
        if self.is_white_piece(piece):
            if to_col == 6:  # Kingside castling
                rook_from_col = self.rook_start_files['white']['K']
                rook_to_col = 5
            else:  # Queenside castling (to_col == 2)
                rook_from_col = self.rook_start_files['white']['Q']
                rook_to_col = 3
        else:
            if to_col == 6:  # Kingside castling
                rook_from_col = self.rook_start_files['black']['k']
                rook_to_col = 5
            else:  # Queenside castling (to_col == 2)
                rook_from_col = self.rook_start_files['black']['q']
                rook_to_col = 3
        
        # Move the rook
        rook = self.get_piece(row, rook_from_col)
        self.set_piece(row, rook_from_col, '.')
        self.set_piece(row, rook_to_col, rook)

    def evaluate(self) -> int:
        score = 0
        
        for row in range(8):
            for col in range(8):
                piece = self.get_piece(row, col)
                if piece != '.':
                    # Material value
                    piece_value = PIECE_VALUES.get(piece, 0)
                    
                    # Piece-square table value
                    piece_type = piece.upper()
                    if piece_type in PIECE_SQUARE_TABLES:
                        square_index = row * 8 + col
                        if self.is_black_piece(piece):
                            # Flip the board for black pieces
                            square_index = (7 - row) * 8 + col
                        table_value = PIECE_SQUARE_TABLES[piece_type][square_index]
                        if self.is_black_piece(piece):
                            table_value = -table_value
                    else:
                        table_value = 0
                    
                    score += piece_value + table_value
        
        return score

class ChessEngine:
    def __init__(self, chess960=False):
        self.board = ChessBoard(chess960=chess960)
        self.thinking = False
    
    def evaluate(self, board: ChessBoard) -> int:
        """Evaluate the given board position."""
        return board.evaluate()
        
    def search(self, depth: int) -> Tuple[str, int]:
        def minimax(board: ChessBoard, depth: int, alpha: int, beta: int, maximizing: bool) -> Tuple[Optional[str], int]:
            if depth == 0:
                return None, board.evaluate()
            
            moves = board.generate_moves()
            if not moves:
                # Check for checkmate or stalemate
                if self.is_in_check(board):
                    return None, -20000 if maximizing else 20000
                else:
                    return None, 0  # Stalemate
            
            best_move = None
            if maximizing:
                max_eval = float('-inf')
                for move in moves:
                    board_copy = board.copy()
                    if board_copy.make_move(move):
                        _, eval_score = minimax(board_copy, depth - 1, alpha, beta, False)
                        if eval_score > max_eval:
                            max_eval = eval_score
                            best_move = move
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break
                return best_move, max_eval
            else:
                min_eval = float('inf')
                for move in moves:
                    board_copy = board.copy()
                    if board_copy.make_move(move):
                        _, eval_score = minimax(board_copy, depth - 1, alpha, beta, True)
                        if eval_score < min_eval:
                            min_eval = eval_score
                            best_move = move
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break
                return best_move, min_eval
        
        best_move, score = minimax(self.board, depth, float('-inf'), float('inf'), self.board.white_to_move)
        return best_move or "e2e4", score
    
    def is_in_check(self, board: ChessBoard) -> bool:
        # Find the king
        king_piece = 'K' if board.white_to_move else 'k'
        king_row, king_col = None, None
        
        for row in range(8):
            for col in range(8):
                if board.get_piece(row, col) == king_piece:
                    king_row, king_col = row, col
                    break
            if king_row is not None:
                break
        
        if king_row is None:
            return False
        
        return board.is_square_attacked(king_row, king_col, not board.white_to_move)

class InteractiveGame:
    def __init__(self, chess960=False, position_id=None, human_color='white', engine_depth=4):
        self.engine = ChessEngine(chess960=chess960)
        if chess960 and position_id is not None:
            self.engine.board = ChessBoard(chess960=True, position_id=position_id)
        elif chess960:
            self.engine.board = ChessBoard(chess960=True)
        
        self.human_color = human_color.lower()
        self.engine_depth = engine_depth
        self.game_over = False
        
    def display_board(self):
        print("\n    a   b   c   d   e   f   g   h")
        print("  +---+---+---+---+---+---+---+---+")
        
        for row in range(8):
            # Print the row with pieces, with rank numbers on both sides
            print(f"{8-row} |", end="")
            for col in range(8):
                piece = self.engine.board.get_piece(row, col)
                if piece == '.':
                    piece = ' '
                print(f" {piece} |", end="")
            print(f" {8-row}")
            # Print the horizontal border
            if row < 7:  # Don't print border after last row
                print("  +---+---+---+---+---+---+---+---+")
        
        print("  +---+---+---+---+---+---+---+---+")
        print("    a   b   c   d   e   f   g   h\n")
        
        # Show whose turn it is
        turn = "White" if self.engine.board.white_to_move else "Black"
        print(f"{turn} to move")
        
        # Show if in check
        if self.engine.is_in_check(self.engine.board):
            print("CHECK!")

    def is_human_turn(self):
        if self.human_color == 'white':
            return self.engine.board.white_to_move
        else:
            return not self.engine.board.white_to_move

    def get_human_move(self):
        while True:
            try:
                move_input = input("\nEnter your move (e.g., e2e4, e7e8q for promotion): ").strip().lower()
                
                if move_input in ['quit', 'exit', 'q']:
                    return 'quit'
                
                if move_input == 'help':
                    print("Move format: from_square to_square (e.g., e2e4)")
                    print("For promotion: from_square to_square promotion_piece (e.g., e7e8q)")
                    print("Special commands: quit, help, moves, undo")
                    continue
                
                if move_input == 'moves':
                    legal_moves = self.engine.board.generate_moves()
                    print(f"Legal moves: {' '.join(legal_moves[:20])}")
                    if len(legal_moves) > 20:
                        print(f"... and {len(legal_moves) - 20} more")
                    continue
                
                # Validate move format
                if len(move_input) < 4:
                    print("Invalid move format. Use: e2e4")
                    continue
                
                # Check if move is legal
                legal_moves = self.engine.board.generate_moves()
                if move_input not in legal_moves:
                    print(f"Illegal move: {move_input}")
                    print("Type 'moves' to see legal moves")
                    continue
                
                return move_input
                
            except KeyboardInterrupt:
                print("\nGame interrupted.")
                return 'quit'
            except EOFError:
                print("\nGame ended.")
                return 'quit'

    def make_engine_move(self):
        start_time = time.time()
        
        best_move, score = self.engine.search(self.engine_depth)
        elapsed = time.time() - start_time
        
        formatted_move = self.engine.board.format_move_notation(best_move)
        print(f"🤖 ENGINE PLAYS: {formatted_move}")
        print(f"📊 Evaluation: {score/100:.2f} | Time: {elapsed:.2f}s")
        sys.stdout.flush()
        
        if not self.engine.board.make_move(best_move):
            print("Engine made an illegal move! This is a bug.")
            return False
        
        return True

    def check_game_over(self):
        moves = self.engine.board.generate_moves()
        
        if not moves:
            if self.engine.is_in_check(self.engine.board):
                winner = "Black" if self.engine.board.white_to_move else "White"
                print(f"\nCheckmate! {winner} wins!")
            else:
                print("\nStalemate! Game is a draw.")
            return True
        
        # Check for insufficient material (basic)
        pieces = []
        for row in range(8):
            for col in range(8):
                piece = self.engine.board.get_piece(row, col)
                if piece != '.' and piece.lower() not in ['k']:
                    pieces.append(piece.lower())
        
        # King vs King
        if not pieces:
            print("\nDraw by insufficient material (K vs K)!")
            return True
        
        # King and minor piece vs King
        if len(pieces) == 1 and pieces[0] in ['n', 'b']:
            print("\nDraw by insufficient material!")
            return True
        
        return False

    def play(self):
        print("=== Claude Chess Engine ===")
        print(f"You are playing as {self.human_color.title()}")
        print(f"Engine difficulty: depth {self.engine_depth}")
        print("Type 'help' for commands during the game\n")
        
        self.display_board()
        
        while not self.game_over:
            if self.check_game_over():
                break
            
            # Handle human move
            if self.is_human_turn():
                move = self.get_human_move()
                if move == 'quit':
                    print("Thanks for playing!")
                    break
                
                # Execute human move
                if not self.engine.board.make_move(move):
                    print("Failed to make move. This shouldn't happen.")
                    continue
                
                # IMMEDIATE FEEDBACK: Show human move result
                formatted_move = self.engine.board.format_move_notation(move)
                print("\n" + "="*50)
                print(f"✓ YOUR MOVE: {formatted_move}")
                print("="*50)
                sys.stdout.flush()
                
                self.display_board()
                print(f"\n{self.human_color.title()} has moved. Waiting for engine...")
                sys.stdout.flush()
                
                # Check if game ended after human move
                if self.check_game_over():
                    break
                    
                # FORCE LOOP RESTART - this ensures engine move happens in next iteration
                continue
                
            # Handle engine move (separate iteration)
            if not self.is_human_turn():
                # Engine move
                print("\n" + "-"*50)
                print("🤖 ENGINE IS THINKING...")
                print("-"*50)
                sys.stdout.flush()
                
                if not self.make_engine_move():
                    break
                
                # Show board after engine move
                print("\n" + "="*50)
                print("✓ ENGINE MOVE COMPLETE")
                print("="*50)
                self.display_board()
                
                # FORCE LOOP RESTART - this ensures clean separation
                continue
        
        print("\nGame Over!")

class ChessGUI:
    def __init__(self, chess960=False, position_id=None, human_color='white', engine_depth=4):
        if not GUI_AVAILABLE:
            raise ImportError("tkinter not available. GUI mode requires tkinter.")
        
        self.engine = ChessEngine(chess960=chess960)
        if chess960 and position_id is not None:
            self.engine.board = ChessBoard(chess960=True, position_id=position_id)
        elif chess960:
            self.engine.board = ChessBoard(chess960=True)
        
        self.human_color = human_color.lower()
        self.engine_depth = engine_depth
        self.game_over = False
        
        # GUI state
        self.selected_square = None
        self.highlighted_squares = set()
        self.last_move = None
        self.thinking = False
        
        # Initialize GUI
        self.root = tk.Tk()
        self.root.title("Claude Chess Engine")
        self.root.resizable(False, False)
        
        # Colors
        self.light_color = "#F0D9B5"
        self.dark_color = "#B58863"
        self.highlight_color = "#FFFF00"
        self.move_color = "#90EE90"
        self.selected_color = "#FF6B6B"
        
        # Piece symbols with better contrast and fallbacks
        self.piece_symbols = {
            'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
            'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
        }
        
        # Fallback ASCII symbols for better compatibility
        self.ascii_pieces = {
            'K': 'K', 'Q': 'Q', 'R': 'R', 'B': 'B', 'N': 'N', 'P': 'P',
            'k': 'k', 'q': 'q', 'r': 'r', 'b': 'b', 'n': 'n', 'p': 'p'
        }
        
        self.use_unicode = True  # Default to Unicode for beautiful chess pieces
        
        self.setup_gui()
        self.update_board()
        
        # Start engine turn if human is black
        if not self.is_human_turn():
            self.root.after(500, self.make_engine_move)

    def setup_gui(self):
        # Main frame
        main_frame = tk.Frame(self.root)
        main_frame.pack(padx=10, pady=10)
        
        # Board frame
        board_frame = tk.Frame(main_frame)
        board_frame.pack(side=tk.LEFT)
        
        # Create board squares
        self.squares = []
        for row in range(8):
            square_row = []
            for col in range(8):
                color = self.light_color if (row + col) % 2 == 0 else self.dark_color
                square = tk.Button(
                    board_frame,
                    width=8, height=4,
                    bg=color,
                    font=('Arial', 20),
                    command=lambda r=row, c=col: self.on_square_click(r, c)
                )
                square.grid(row=row, column=col)
                square_row.append(square)
            self.squares.append(square_row)
        
        
        # Control panel
        control_frame = tk.Frame(main_frame)
        control_frame.pack(side=tk.LEFT, padx=(20, 0), fill=tk.Y)
        
        # Status label
        self.status_label = tk.Label(control_frame, text="White to move", font=('Arial', 14, 'bold'))
        self.status_label.pack(pady=10)
        
        # Engine status
        self.engine_label = tk.Label(control_frame, text="", font=('Arial', 12))
        self.engine_label.pack(pady=5)
        
        # Game info
        info_frame = tk.Frame(control_frame)
        info_frame.pack(pady=10, fill=tk.X)
        
        tk.Label(info_frame, text=f"You: {self.human_color.title()}", font=('Arial', 12)).pack()
        tk.Label(info_frame, text=f"Depth: {self.engine_depth}", font=('Arial', 12)).pack()
        
        # Buttons
        button_frame = tk.Frame(control_frame)
        button_frame.pack(pady=20, fill=tk.X)
        
        tk.Button(button_frame, text="New Game", command=self.new_game, width=12).pack(pady=2)
        tk.Button(button_frame, text="Flip Board", command=self.flip_board, width=12).pack(pady=2)
        self.toggle_btn = tk.Button(button_frame, text="Use ASCII", command=self.toggle_pieces, width=12)
        self.toggle_btn.pack(pady=2)
        tk.Button(button_frame, text="Show Moves", command=self.show_legal_moves, width=12).pack(pady=2)
        
        # Move history
        history_frame = tk.Frame(control_frame)
        history_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        tk.Label(history_frame, text="Move History", font=('Arial', 12, 'bold')).pack()
        
        # Scrollable text widget for moves
        text_frame = tk.Frame(history_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.move_history = tk.Text(text_frame, width=20, height=15, state=tk.DISABLED)
        scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.move_history.yview)
        self.move_history.configure(yscrollcommand=scrollbar.set)
        
        self.move_history.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.move_count = 0

    def update_board(self):
        # Clear highlights except selected square
        for row in range(8):
            for col in range(8):
                square = self.squares[row][col]
                color = self.light_color if (row + col) % 2 == 0 else self.dark_color
                
                # Highlight selected square
                if self.selected_square == (row, col):
                    color = self.selected_color
                # Highlight last move
                elif self.last_move and ((row, col) in self.last_move):
                    color = self.move_color
                # Highlight legal moves
                elif (row, col) in self.highlighted_squares:
                    color = self.highlight_color
                
                square.config(bg=color)
                
                # Set piece symbol with coordinates
                piece = self.engine.board.get_piece(row, col)
                
                # Add coordinate labels to specific squares
                coord_text = ""
                if row == 7:  # Bottom row - add file letters
                    coord_text += chr(97 + col)  # a-h
                if col == 0:  # Left column - add rank numbers
                    coord_text += str(8 - row)  # 8-1
                
                if piece == '.':
                    # Show coordinates on empty squares
                    square.config(text=coord_text, fg='#654321', font=('Arial', 8, 'bold'))
                else:
                    if self.use_unicode:
                        symbol = self.piece_symbols.get(piece, piece)
                    else:
                        symbol = self.ascii_pieces.get(piece, piece)
                    
                    # Combine piece with coordinates if present
                    display_text = symbol
                    if coord_text:
                        display_text = f"{symbol}\n{coord_text}"
                    
                    # Set text color based on piece color for better visibility
                    if piece.isupper():  # White pieces
                        text_color = '#FFFFFF'  # White text
                    else:  # Black pieces
                        text_color = '#000000'  # Black text
                    
                    square.config(text=display_text, fg=text_color, 
                                font=('Arial', 16, 'bold'))
        
        # Update status
        turn = "White" if self.engine.board.white_to_move else "Black"
        status = f"{turn} to move"
        
        if self.engine.is_in_check(self.engine.board):
            status += " - CHECK!"
        
        if self.thinking:
            status += " (Engine thinking...)"
        
        self.status_label.config(text=status)

    def on_square_click(self, row, col):
        if self.game_over or self.thinking:
            return
        
        if not self.is_human_turn():
            return
        
        if self.selected_square is None:
            # Select a square if it has a piece of the current player
            piece = self.engine.board.get_piece(row, col)
            if piece != '.' and self.is_player_piece(piece):
                self.selected_square = (row, col)
                self.highlight_legal_moves(row, col)
                self.update_board()
        else:
            # Try to make a move
            from_row, from_col = self.selected_square
            move = self.square_to_move(from_row, from_col, row, col)
            
            if self.is_legal_move(move):
                self.make_human_move(move)
            
            # Clear selection
            self.selected_square = None
            self.highlighted_squares.clear()
            self.update_board()

    def square_to_move(self, from_row, from_col, to_row, to_col):
        from_square = f"{chr(from_col + ord('a'))}{8 - from_row}"
        to_square = f"{chr(to_col + ord('a'))}{8 - to_row}"
        
        # Check for pawn promotion
        piece = self.engine.board.get_piece(from_row, from_col)
        if (piece.lower() == 'p' and 
            ((piece == 'P' and to_row == 0) or (piece == 'p' and to_row == 7))):
            # For simplicity, always promote to queen
            promotion = 'Q' if piece == 'P' else 'q'
            return f"{from_square}{to_square}{promotion}"
        
        return f"{from_square}{to_square}"

    def highlight_legal_moves(self, row, col):
        self.highlighted_squares.clear()
        legal_moves = self.engine.board.generate_moves()
        
        from_square = f"{chr(col + ord('a'))}{8 - row}"
        
        for move in legal_moves:
            if move.startswith(from_square):
                to_col = ord(move[2]) - ord('a')
                to_row = 8 - int(move[3])
                self.highlighted_squares.add((to_row, to_col))

    def is_player_piece(self, piece):
        if self.human_color == 'white':
            return piece.isupper()
        else:
            return piece.islower()

    def is_human_turn(self):
        if self.human_color == 'white':
            return self.engine.board.white_to_move
        else:
            return not self.engine.board.white_to_move

    def is_legal_move(self, move):
        legal_moves = self.engine.board.generate_moves()
        return move in legal_moves

    def make_human_move(self, move):
        formatted_move = self.engine.board.format_move_notation(move)
        if self.engine.board.make_move(move):
            self.add_move_to_history(formatted_move, is_human=True)
            self.last_move = self.move_to_squares(move)
            self.update_board()
            
            if self.check_game_over():
                return
            
            # Schedule engine move
            self.root.after(500, self.make_engine_move)

    def make_engine_move(self):
        if self.game_over or self.is_human_turn():
            return
        
        self.thinking = True
        self.engine_label.config(text=f"Engine thinking (depth {self.engine_depth})...")
        self.update_board()
        
        # Run engine search in a separate thread to keep GUI responsive
        def search_thread():
            start_time = time.time()
            best_move, score = self.engine.search(self.engine_depth)
            elapsed = time.time() - start_time
            
            # Schedule GUI update in main thread
            self.root.after(0, lambda: self.finish_engine_move(best_move, score, elapsed))
        
        thread = threading.Thread(target=search_thread)
        thread.daemon = True
        thread.start()

    def finish_engine_move(self, best_move, score, elapsed):
        self.thinking = False
        formatted_move = self.engine.board.format_move_notation(best_move)
        self.engine_label.config(text=f"Last move: {formatted_move} (eval: {score/100:.2f}, {elapsed:.2f}s)")
        
        if self.engine.board.make_move(best_move):
            self.add_move_to_history(formatted_move, is_human=False)
            self.last_move = self.move_to_squares(best_move)
            self.update_board()
            self.check_game_over()

    def move_to_squares(self, move):
        from_col = ord(move[0]) - ord('a')
        from_row = 8 - int(move[1])
        to_col = ord(move[2]) - ord('a')
        to_row = 8 - int(move[3])
        return [(from_row, from_col), (to_row, to_col)]

    def add_move_to_history(self, move, is_human):
        self.move_count += 1
        player = "You" if is_human else "Engine"
        
        self.move_history.config(state=tk.NORMAL)
        self.move_history.insert(tk.END, f"{self.move_count}. {player}: {move}\n")
        self.move_history.config(state=tk.DISABLED)
        self.move_history.see(tk.END)

    def check_game_over(self):
        moves = self.engine.board.generate_moves()
        
        if not moves:
            if self.engine.is_in_check(self.engine.board):
                winner = "Black" if self.engine.board.white_to_move else "White"
                messagebox.showinfo("Game Over", f"Checkmate! {winner} wins!")
            else:
                messagebox.showinfo("Game Over", "Stalemate! Game is a draw.")
            self.game_over = True
            return True
        
        return False

    def new_game(self):
        response = messagebox.askyesno("New Game", "Start a new game?")
        if response:
            self.engine.board = ChessBoard(chess960=self.engine.board.chess960)
            self.game_over = False
            self.selected_square = None
            self.highlighted_squares.clear()
            self.last_move = None
            self.thinking = False
            self.move_count = 0
            
            # Clear move history
            self.move_history.config(state=tk.NORMAL)
            self.move_history.delete(1.0, tk.END)
            self.move_history.config(state=tk.DISABLED)
            
            self.engine_label.config(text="")
            self.update_board()
            
            # Start engine if human is black
            if not self.is_human_turn():
                self.root.after(500, self.make_engine_move)

    def flip_board(self):
        # Simple implementation: just change human color
        self.human_color = 'black' if self.human_color == 'white' else 'white'
        self.update_board()

    def toggle_pieces(self):
        self.use_unicode = not self.use_unicode
        self.toggle_btn.config(text="Use ASCII" if self.use_unicode else "Use Unicode")
        self.update_board()

    def show_legal_moves(self):
        if self.game_over or not self.is_human_turn():
            return
        
        legal_moves = self.engine.board.generate_moves()
        moves_text = " ".join(legal_moves[:20])
        if len(legal_moves) > 20:
            moves_text += f" ... and {len(legal_moves) - 20} more"
        
        messagebox.showinfo("Legal Moves", f"Available moves:\n{moves_text}")

    def run(self):
        self.root.mainloop()

class WebGUI:
    def __init__(self, chess960=False, position_id=None, human_color='white', engine_depth=DEFAULT_ENGINE_DEPTH, port=DEFAULT_WEB_PORT):
        if not WEB_GUI_AVAILABLE:
            raise ImportError("Web GUI requires http.server, which is not available.")
        
        self.engine = ChessEngine(chess960=chess960)
        if chess960 and position_id is not None:
            self.engine.board = ChessBoard(chess960=True, position_id=position_id)
        elif chess960:
            self.engine.board = ChessBoard(chess960=True)
        
        self.human_color = human_color.lower()
        self.engine_depth = max(1, min(engine_depth, MAX_SEARCH_DEPTH))
        self.port = port
        self.game_over = False
        self.move_history = []

    def generate_html(self):
        # Get board state and game info
        board_state = [[self.engine.board.get_piece(r, c) for c in range(8)] for r in range(8)]
        is_human_turn = self.is_human_turn()
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Claude Chess Engine</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .chess-container {{ display: inline-block; position: relative; }}
        .board {{ display: inline-block; border: 2px solid #333; margin: 20px; }}
        .row {{ display: flex; }}
        .square {{ 
            width: 60px; height: 60px; 
            display: flex; align-items: center; justify-content: center;
            font-size: 40px; cursor: pointer;
            border: 1px solid #999;
            font-weight: bold;
            font-family: Arial, sans-serif;
            text-shadow: 1px 1px 1px rgba(0,0,0,0.5);
            position: relative;
            box-sizing: border-box;
        }}
        .coordinate {{
            position: absolute;
            font-size: 10px;
            font-weight: bold;
            pointer-events: none;
        }}
        .file-coord {{
            bottom: 2px;
            right: 3px;
            color: #654321;
        }}
        .rank-coord {{
            top: 2px;
            left: 3px;
            color: #654321;
        }}
        .piece-symbol {{
            font-size: 40px;
            font-weight: bold;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            height: 100%;
            text-shadow: 1px 1px 1px rgba(0,0,0,0.5);
        }}
        .white-piece {{ color: #FFFFFF; text-shadow: 1px 1px 2px #000000; }}
        .black-piece {{ color: #000000; text-shadow: 1px 1px 2px #FFFFFF; }}
        .light {{ background-color: #F0D9B5; }}
        .dark {{ background-color: #B58863; }}
        .selected {{ background-color: #FF6B6B !important; box-shadow: 0 0 10px #FF6B6B; }}
        .highlight {{ background-color: #FFFF00 !important; }}
        .last-move {{ background-color: #90EE90 !important; }}
        .legal-move {{ 
            background-color: #87CEEB !important; 
            border: 1px solid #4169E1 !important; 
            box-shadow: inset 0 0 0 2px #4169E1, 0 0 8px rgba(65, 105, 225, 0.6) !important;
            animation: legalPulse 2s infinite;
        }}
        @keyframes legalPulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.8; }}
        }}
        .thinking {{ animation: pulse 1s infinite; }}
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.6; }}
            100% {{ opacity: 1; }}
        }}
        .move-animation {{ 
            transform: scale(1.1); 
            transition: transform 0.3s ease;
        }}
        .engine-thinking {{
            background-color: #FFE4B5;
            border: 1px solid #DDD;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            animation: pulse 1s infinite;
        }}
        .move-made {{
            background-color: #98FB98;
            border: 1px solid #90EE90;
            padding: 5px;
            margin: 2px 0;
            border-radius: 3px;
            animation: fadeIn 0.5s;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(-10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .controls {{ 
            display: inline-block; 
            vertical-align: top; 
            margin-left: 20px; 
            width: 300px;
        }}
        .status {{ 
            font-size: 18px; 
            font-weight: bold; 
            margin-bottom: 10px;
            padding: 8px;
            border-radius: 4px;
            background-color: #f0f8ff;
            border: 1px solid #ddd;
        }}
        .status.check {{
            background-color: #ffe4e1 !important;
            border-color: #ff6b6b !important;
            color: #d32f2f !important;
            animation: checkPulse 2s infinite;
        }}
        @keyframes checkPulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.8; }}
        }}
        .move-history {{ 
            height: 200px; 
            overflow-y: auto; 
            border: 1px solid #ccc; 
            padding: 10px;
            background-color: #f9f9f9;
        }}
        button {{ 
            padding: 10px 15px; 
            margin: 5px; 
            font-size: 14px;
            cursor: pointer;
        }}
        .captured-section {{
            margin-top: 10px;
            padding: 10px;
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        .captured-white, .captured-black {{
            margin: 5px 0;
            padding: 5px;
        }}
        .captured-label {{
            font-weight: bold;
            display: inline-block;
            width: 80px;
        }}
        .captured-pieces-display {{
            font-family: Arial, sans-serif;
            font-size: 18px;
            min-height: 20px;
            display: inline-block;
        }}
        .captured-white {{
            background-color: #fff;
            border: 1px solid #ccc;
        }}
        .captured-black {{
            background-color: #333;
            color: #fff;
            border: 1px solid #555;
        }}
        .captured-piece {{
            margin: 0 2px;
            padding: 2px 4px;
            border-radius: 2px;
            display: inline-block;
        }}
        .no-captures {{
            color: #888;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <h1>Claude Chess Engine</h1>
    <div class="chess-container">
        <!-- Chess board -->
        <div class="board" id="board"></div>
    </div>
    <div class="controls">
        <div class="status" id="status">White to move</div>
        <div>You: <span id="player-color">{self.human_color.title()}</span></div>
        <div>Engine Depth: <span id="depth">{self.engine_depth}</span></div>
        <div id="engine-status" style="display: none;" class="engine-thinking">
            🤖 Engine is thinking...
        </div>
        <br>
        <button onclick="newGame()">🆕 New Game</button>
        <button onclick="togglePieces()" id="toggle-btn">🎨 Use ASCII</button>
        <button onclick="showLegalMoves()" id="show-moves-btn">👁️ Show Legal Moves</button>
        <button onclick="undoMove()" id="undo-btn">↩️ Undo Move</button>
        <br><br>
        <div><strong>📝 Move History:</strong></div>
        <div class="move-history" id="move-history"></div>
        <div id="game-info">
            <br>
            <div>⏱️ Last move time: <span id="move-time">-</span></div>
            <div>🧮 Position eval: <span id="position-eval">0.00</span></div>
            <div>🎯 Total moves: <span id="move-count">0</span></div>
        </div>
        
        <div id="captured-pieces">
            <br>
            <div><strong>💀 Captured Pieces:</strong></div>
            <div class="captured-section">
                <div class="captured-white">
                    <span class="captured-label">White lost:</span>
                    <span id="captured-white-pieces" class="captured-pieces-display"></span>
                </div>
                <div class="captured-black">
                    <span class="captured-label">Black lost:</span>
                    <span id="captured-black-pieces" class="captured-pieces-display"></span>
                </div>
            </div>
        </div>
    </div>

    <script>
        const pieceSymbols = {{
            'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
            'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
        }};
        
        const asciiPieces = {{
            'K': 'K', 'Q': 'Q', 'R': 'R', 'B': 'B', 'N': 'N', 'P': 'P',
            'k': 'k', 'q': 'q', 'r': 'r', 'b': 'b', 'n': 'n', 'p': 'p'
        }};
        
        let useUnicode = true;  // Default to Unicode for beautiful chess pieces
        
        let selectedSquare = null;
        let boardState = {json.dumps(board_state)};
        let isHumanTurn = {json.dumps(is_human_turn)};
        let gameOver = {json.dumps(self.game_over)};
        let legalMovesVisible = false;
        let currentLegalMoves = [];
        let lastMoveTime = null;
        let positionEval = 0.00;
        let moveCount = 0;
        
        function createBoard() {{
            const boardDiv = document.getElementById('board');
            boardDiv.innerHTML = '';
            
            for (let row = 0; row < 8; row++) {{
                const rowDiv = document.createElement('div');
                rowDiv.className = 'row';
                
                for (let col = 0; col < 8; col++) {{
                    const square = document.createElement('div');
                    square.className = 'square ' + ((row + col) % 2 === 0 ? 'light' : 'dark');
                    square.onclick = () => onSquareClick(row, col);
                    square.id = `square-${{row}}-${{col}}`;
                    
                    // Add coordinate labels on specific squares
                    if (row === 7) {{  // Bottom row - add file letters
                        const fileLabel = document.createElement('div');
                        fileLabel.className = 'coordinate file-coord';
                        fileLabel.textContent = String.fromCharCode(97 + col); // a-h
                        square.appendChild(fileLabel);
                    }}
                    if (col === 0) {{  // Left column - add rank numbers
                        const rankLabel = document.createElement('div');
                        rankLabel.className = 'coordinate rank-coord';
                        rankLabel.textContent = (8 - row).toString(); // 8-1
                        square.appendChild(rankLabel);
                    }}
                    
                    // Add piece symbol in a separate element to preserve coordinates
                    const piece = boardState[row][col];
                    if (piece !== '.') {{
                        const pieceElement = document.createElement('div');
                        pieceElement.className = 'piece-symbol';
                        const symbol = useUnicode ? (pieceSymbols[piece] || piece) : (asciiPieces[piece] || piece);
                        pieceElement.textContent = symbol;
                        
                        // Add color class for better visibility
                        if (piece === piece.toUpperCase()) {{
                            pieceElement.classList.add('white-piece');
                        }} else {{
                            pieceElement.classList.add('black-piece');
                        }}
                        
                        square.appendChild(pieceElement);
                    }}
                    
                    rowDiv.appendChild(square);
                }}
                boardDiv.appendChild(rowDiv);
            }}
        }}
        
        function onSquareClick(row, col) {{
            if (gameOver || !isHumanTurn) return;
            
            if (selectedSquare === null) {{
                const piece = boardState[row][col];
                if (piece !== '.' && isPlayerPiece(piece)) {{
                    selectedSquare = [row, col];
                    clearHighlights();
                    highlightSquare(row, col, 'selected');
                    
                    // Show possible moves for this piece
                    showPossibleMoves(row, col);
                    
                    // Add animation
                    const square = document.getElementById(`square-${{row}}-${{col}}`);
                    square.classList.add('move-animation');
                    setTimeout(() => square.classList.remove('move-animation'), 300);
                }}
            }} else {{
                const [fromRow, fromCol] = selectedSquare;
                
                // If clicking the same piece, deselect
                if (fromRow === row && fromCol === col) {{
                    selectedSquare = null;
                    clearHighlights();
                    return;
                }}
                
                const move = squareToMove(fromRow, fromCol, row, col);
                makeMove(move);
                
                selectedSquare = null;
                clearHighlights();
            }}
        }}
        
        function isPlayerPiece(piece) {{
            const humanColor = '{self.human_color}';
            return humanColor === 'white' ? piece === piece.toUpperCase() : piece === piece.toLowerCase();
        }}
        
        function squareToMove(fromRow, fromCol, toRow, toCol) {{
            const fromSquare = String.fromCharCode(fromCol + 97) + (8 - fromRow);
            const toSquare = String.fromCharCode(toCol + 97) + (8 - toRow);
            return fromSquare + toSquare;
        }}
        
        function highlightSquare(row, col, className) {{
            const square = document.getElementById(`square-${{row}}-${{col}}`);
            square.classList.add(className);
        }}
        
        function clearHighlights() {{
            document.querySelectorAll('.square').forEach(square => {{
                square.classList.remove('selected', 'highlight', 'last-move', 'legal-move');
            }});
        }}
        
        function showPossibleMoves(fromRow, fromCol) {{
            fetch('/legal_moves')
            .then(response => response.json())
            .then(data => {{
                const fromSquare = String.fromCharCode(fromCol + 97) + (8 - fromRow);
                const pieceMoves = data.moves.filter(move => move.startsWith(fromSquare));
                
                pieceMoves.forEach(move => {{
                    const toCol = move.charCodeAt(2) - 97;
                    const toRow = 8 - parseInt(move[3]);
                    highlightSquare(toRow, toCol, 'legal-move');
                }});
            }});
        }}
        
        function showEngineThinking() {{
            document.getElementById('engine-status').style.display = 'block';
            document.getElementById('status').textContent = '🤖 Engine is thinking...';
        }}
        
        function hideEngineThinking() {{
            document.getElementById('engine-status').style.display = 'none';
        }}
        
        function formatMoveNotation(move) {{
            const fromCol = move.charCodeAt(0) - 97;
            const fromRow = 8 - parseInt(move[1]);
            const toCol = move.charCodeAt(2) - 97;
            const toRow = 8 - parseInt(move[3]);
            
            // Check for castling moves
            const piece = boardState[fromRow][fromCol];
            if (piece === 'K' || piece === 'k') {{
                // White castling
                if (fromRow === 7 && fromCol === 4) {{
                    if (toCol === 6) return "O-O";      // Kingside
                    if (toCol === 2) return "O-O-O";    // Queenside
                }}
                // Black castling
                if (fromRow === 0 && fromCol === 4) {{
                    if (toCol === 6) return "O-O";      // Kingside
                    if (toCol === 2) return "O-O-O";    // Queenside
                }}
            }}
            
            return move.toUpperCase();
        }}
        
        function updateCapturedPieces(capturedPieces) {{
            // Update white captured pieces
            const whitePieces = capturedPieces.white || [];
            const whiteDisplay = document.getElementById('captured-white-pieces');
            if (whitePieces.length > 0) {{
                whiteDisplay.innerHTML = whitePieces.map(piece => {{
                    const symbol = useUnicode ? (pieceSymbols[piece] || piece) : (asciiPieces[piece] || piece);
                    return `<span class="captured-piece white-piece">${{symbol}}</span>`;
                }}).join(' ');
            }} else {{
                whiteDisplay.innerHTML = '<span class="no-captures">None</span>';
            }}
            
            // Update black captured pieces  
            const blackPieces = capturedPieces.black || [];
            const blackDisplay = document.getElementById('captured-black-pieces');
            if (blackPieces.length > 0) {{
                blackDisplay.innerHTML = blackPieces.map(piece => {{
                    const symbol = useUnicode ? (pieceSymbols[piece] || piece) : (asciiPieces[piece] || piece);
                    return `<span class="captured-piece black-piece">${{symbol}}</span>`;
                }}).join(' ');
            }} else {{
                blackDisplay.innerHTML = '<span class="no-captures">None</span>';
            }}
        }}
        
        function makeMove(move) {{
            // STEP 0: Validate move before making any visual changes
            const fromCol = move.charCodeAt(0) - 97;
            const fromRow = 8 - parseInt(move[1]);
            const toCol = move.charCodeAt(2) - 97;
            const toRow = 8 - parseInt(move[3]);
            
            // Check if this is a legal move by fetching current legal moves
            fetch('/legal_moves')
            .then(response => response.json())
            .then(data => {{
                if (!data.moves.includes(move)) {{
                    // Move is not legal - show error and don't make visual change
                    alert(`Illegal move: ${{move}}\\nThat piece cannot move there.`);
                    console.log(`Rejected illegal move: ${{move}}`);
                    console.log(`Legal moves: ${{data.moves.slice(0, 10).join(', ')}}...`);
                    return;
                }}
                
                // Move is legal - proceed with visual update
                executeVisualMove(move);
            }})
            .catch(error => {{
                console.error('Error validating move:', error);
                alert('Error validating move. Please try again.');
            }});
        }}
        
        function executeVisualMove(move) {{
            // STEP 1: Update board with validated human move
            const fromCol = move.charCodeAt(0) - 97;
            const fromRow = 8 - parseInt(move[1]);
            const toCol = move.charCodeAt(2) - 97;
            const toRow = 8 - parseInt(move[3]);
            
            // Store the piece and make the move on the visual board
            const piece = boardState[fromRow][fromCol];
            
            // Handle castling on the visual board
            if ((piece === 'K' || piece === 'k') && Math.abs(toCol - fromCol) === 2) {{
                // This is castling - move both king and rook
                boardState[toRow][toCol] = piece;
                boardState[fromRow][fromCol] = '.';
                
                // Move the rook
                if (toCol === 6) {{ // Kingside
                    const rook = boardState[fromRow][7];
                    boardState[fromRow][5] = rook;
                    boardState[fromRow][7] = '.';
                }} else if (toCol === 2) {{ // Queenside
                    const rook = boardState[fromRow][0];
                    boardState[fromRow][3] = rook;
                    boardState[fromRow][0] = '.';
                }}
            }} else {{
                // Regular move
                boardState[toRow][toCol] = piece;
                boardState[fromRow][fromCol] = '.';
            }}
            
            // Immediately update the display
            createBoard();
            clearHighlights();
            highlightSquare(fromRow, fromCol, 'last-move');
            highlightSquare(toRow, toCol, 'last-move');
            
            // Show immediate feedback in move history with proper notation
            const formattedMove = formatMoveNotation(move);
            const moveDiv = document.createElement('div');
            moveDiv.className = 'move-made';
            moveDiv.textContent = `✅ Your move: ${{formattedMove}}`;
            document.getElementById('move-history').appendChild(moveDiv);
            document.getElementById('move-history').scrollTop = document.getElementById('move-history').scrollHeight;
            
            // Update status (will be properly set when server responds)
            document.getElementById('status').textContent = isHumanTurn ? 'Your turn' : 'Engine thinking...';
            
            // STEP 2: Validate move with server (human move only)
            fetch('/make_human_move', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{move: move}})
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    // Update any additional game state
                    gameOver = data.game_over;
                    isHumanTurn = data.is_human_turn;
                    
                    // Update status including check notification
                    if (data.status) {{
                        const statusElement = document.getElementById('status');
                        statusElement.textContent = data.status;
                        
                        // Add check styling if in check
                        if (data.status.includes('CHECK')) {{
                            statusElement.classList.add('check');
                        }} else {{
                            statusElement.classList.remove('check');
                        }}
                    }}
                    
                    if (data.game_over) {{
                        alert(data.result_message);
                        return;
                    }}
                    
                    // STEP 3: Now get engine move separately
                    showEngineThinking();
                    setTimeout(() => {{
                        fetch('/get_engine_move', {{method: 'POST'}})
                        .then(response => response.json())
                        .then(engineData => {{
                            hideEngineThinking();
                            
                            if (engineData.success) {{
                                // Apply engine move to visual board
                                const engineMove = engineData.move;
                                const eFromCol = engineMove.charCodeAt(0) - 97;
                                const eFromRow = 8 - parseInt(engineMove[1]);
                                const eToCol = engineMove.charCodeAt(2) - 97;
                                const eToRow = 8 - parseInt(engineMove[3]);
                                
                                const enginePiece = boardState[eFromRow][eFromCol];
                                
                                // Handle castling for engine moves
                                if ((enginePiece === 'K' || enginePiece === 'k') && Math.abs(eToCol - eFromCol) === 2) {{
                                    // This is castling - move both king and rook
                                    boardState[eToRow][eToCol] = enginePiece;
                                    boardState[eFromRow][eFromCol] = '.';
                                    
                                    // Move the rook
                                    if (eToCol === 6) {{ // Kingside
                                        const rook = boardState[eFromRow][7];
                                        boardState[eFromRow][5] = rook;
                                        boardState[eFromRow][7] = '.';
                                    }} else if (eToCol === 2) {{ // Queenside
                                        const rook = boardState[eFromRow][0];
                                        boardState[eFromRow][3] = rook;
                                        boardState[eFromRow][0] = '.';
                                    }}
                                }} else {{
                                    // Regular move
                                    boardState[eToRow][eToCol] = enginePiece;
                                    boardState[eFromRow][eFromCol] = '.';
                                }}
                                
                                // Update display with engine move
                                createBoard();
                                clearHighlights();
                                highlightSquare(eFromRow, eFromCol, 'last-move');
                                highlightSquare(eToRow, eToCol, 'last-move');
                                
                                // Add engine move to history with proper notation
                                const formattedEngineMove = formatMoveNotation(engineMove);
                                const engineMoveDiv = document.createElement('div');
                                engineMoveDiv.className = 'move-made';
                                engineMoveDiv.textContent = `🤖 Engine: ${{formattedEngineMove}} (eval: ${{engineData.eval}}, time: ${{engineData.time}}s)`;
                                document.getElementById('move-history').appendChild(engineMoveDiv);
                                document.getElementById('move-history').scrollTop = document.getElementById('move-history').scrollHeight;
                                
                                // Update game state
                                gameOver = engineData.game_over;
                                isHumanTurn = true;
                                const statusElement = document.getElementById('status');
                                const statusText = engineData.status || 'Your turn';
                                statusElement.textContent = statusText;
                                
                                // Add check styling if in check
                                if (statusText.includes('CHECK')) {{
                                    statusElement.classList.add('check');
                                }} else {{
                                    statusElement.classList.remove('check');
                                }}
                                
                                // Update game info
                                document.getElementById('move-time').textContent = engineData.time + 's';
                                document.getElementById('position-eval').textContent = engineData.eval;
                                document.getElementById('move-count').textContent = (parseInt(document.getElementById('move-count').textContent || '0') + 2).toString();
                                
                                if (engineData.game_over) {{
                                    setTimeout(() => alert(engineData.result_message), 300);
                                }}
                            }}
                        }});
                    }}, 500); // Brief delay to show thinking
                    
                }} else {{
                    alert('Illegal move: ' + move);
                    // Revert the visual move
                    boardState[fromRow][fromCol] = piece;
                    boardState[toRow][toCol] = '.';
                    createBoard();
                    moveDiv.remove();
                }}
            }});
        }}
        
        function updateGame(data) {{
            boardState = data.board;
            isHumanTurn = data.is_human_turn;
            gameOver = data.game_over;
            
            // Hide engine thinking indicator
            hideEngineThinking();
            
            // Update status with check styling
            const statusElement = document.getElementById('status');
            statusElement.textContent = data.status;
            
            // Add check styling if in check
            if (data.status && data.status.includes('CHECK')) {{
                statusElement.classList.add('check');
            }} else {{
                statusElement.classList.remove('check');
            }}
            
            // Update game info
            if (data.move_time) {{
                document.getElementById('move-time').textContent = data.move_time + 's';
            }}
            if (data.position_eval !== undefined) {{
                document.getElementById('position-eval').textContent = data.position_eval;
            }}
            if (data.move_count !== undefined) {{
                document.getElementById('move-count').textContent = data.move_count;
            }}
            
            // Update captured pieces display
            if (data.captured_pieces) {{
                updateCapturedPieces(data.captured_pieces);
            }}
            
            if (data.move_history) {{
                const historyDiv = document.getElementById('move-history');
                historyDiv.innerHTML = data.move_history.map((move, i) => {{
                    const moveClass = i === data.move_history.length - 1 ? 'move-made' : '';
                    return `<div class="${{moveClass}}">${{i+1}}. ${{move}}</div>`;
                }}).join('');
                historyDiv.scrollTop = historyDiv.scrollHeight;
            }}
            
            createBoard();
            
            // Highlight last move if available
            if (data.last_move) {{
                const [from, to] = data.last_move;
                highlightSquare(from[0], from[1], 'last-move');
                highlightSquare(to[0], to[1], 'last-move');
            }}
            
            if (data.game_over) {{
                setTimeout(() => alert(data.result_message), 300);
            }}
        }}
        
        function newGame() {{
            fetch('/new_game', {{method: 'POST'}})
            .then(response => response.json())
            .then(data => updateGame(data));
        }}
        
        function togglePieces() {{
            useUnicode = !useUnicode;
            const btn = document.getElementById('toggle-btn');
            btn.textContent = useUnicode ? '🎨 Use ASCII' : '🎨 Use Unicode';
            createBoard();
        }}
        
        function showLegalMoves() {{
            legalMovesVisible = !legalMovesVisible;
            const btn = document.getElementById('show-moves-btn');
            
            if (legalMovesVisible) {{
                fetch('/legal_moves')
                .then(response => {{
                    if (!response.ok) {{
                        throw new Error(`HTTP error! status: ${{response.status}}`);
                    }}
                    return response.json();
                }})
                .then(data => {{
                    console.log('Legal moves received:', data.moves);
                    clearHighlights();
                    
                    // Highlight both source and destination squares
                    data.moves.forEach(move => {{
                        if (move.length >= 4) {{
                            // From square
                            const fromCol = move.charCodeAt(0) - 97;
                            const fromRow = 8 - parseInt(move[1]);
                            // To square  
                            const toCol = move.charCodeAt(2) - 97;
                            const toRow = 8 - parseInt(move[3]);
                            
                            // Only highlight if coordinates are valid
                            if (fromRow >= 0 && fromRow < 8 && fromCol >= 0 && fromCol < 8) {{
                                highlightSquare(fromRow, fromCol, 'legal-move');
                            }}
                            if (toRow >= 0 && toRow < 8 && toCol >= 0 && toCol < 8) {{
                                highlightSquare(toRow, toCol, 'legal-move');
                            }}
                        }}
                    }});
                    
                    btn.textContent = '❌ Hide Legal Moves';
                    console.log(`Highlighted ${{data.moves.length}} legal moves`);
                }})
                .catch(error => {{
                    console.error('Error fetching legal moves:', error);
                    alert('Error loading legal moves: ' + error.message);
                }});
            }} else {{
                clearHighlights();
                btn.textContent = '👁️ Show Legal Moves';
                console.log('Legal moves hidden');
            }}
        }}
        
        function undoMove() {{
            fetch('/undo_move', {{method: 'POST'}})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    updateGame(data);
                }} else {{
                    alert('Cannot undo move');
                }}
            }});
        }}
        
        setInterval(() => {{
            if (!gameOver && !isHumanTurn) {{
                fetch('/get_state')
                .then(response => response.json())
                .then(data => updateGame(data));
            }}
        }}, 1000);
        
        createBoard();
        
        // Initialize captured pieces display
        fetch('/get_state')
        .then(response => response.json())
        .then(data => {{
            if (data.captured_pieces) {{
                updateCapturedPieces(data.captured_pieces);
            }}
        }});
    </script>
</body>
</html>"""

    def is_human_turn(self):
        if self.human_color == 'white':
            return self.engine.board.white_to_move
        else:
            return not self.engine.board.white_to_move

    def get_game_state(self):
        turn = "White" if self.engine.board.white_to_move else "Black"
        status = f"{turn} to move"
        
        if self.engine.is_in_check(self.engine.board):
            status += " - CHECK!"
        
        # Get additional game information
        result_message = ""
        if self.game_over:
            moves = self.engine.board.generate_moves()
            if not moves:
                if self.engine.is_in_check(self.engine.board):
                    winner = "Black" if self.engine.board.white_to_move else "White"
                    result_message = f"Checkmate! {winner} wins!"
                else:
                    result_message = "Stalemate! Game is a draw."
        
        return {
            'board': [[self.engine.board.get_piece(r, c) for c in range(8)] for r in range(8)],
            'is_human_turn': self.is_human_turn(),
            'game_over': self.game_over,
            'status': status,
            'move_history': self.move_history,
            'move_count': len(self.move_history),
            'result_message': result_message,
            'last_move': getattr(self, 'last_move_squares', None),
            'captured_pieces': self.engine.board.get_captured_pieces()
        }

    def run(self):
        class ChessHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, web_gui=None, **kwargs):
                self.web_gui = web_gui
                super().__init__(*args, **kwargs)

            def do_GET(self):
                if self.path == '/':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(self.web_gui.generate_html().encode('utf-8'))
                elif self.path == '/get_state':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps(self.web_gui.get_game_state()).encode('utf-8'))
                elif self.path == '/legal_moves':
                    moves = self.web_gui.engine.board.generate_moves()
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({'moves': moves}).encode('utf-8'))
                else:
                    self.send_error(404)

            def do_POST(self):
                if self.path == '/make_move':
                    import time
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode())
                    
                    move = data['move']
                    success = self.web_gui.engine.board.make_move(move)
                    
                    if success:
                        # Store last move for highlighting
                        from_col = ord(move[0]) - ord('a')
                        from_row = 8 - int(move[1])
                        to_col = ord(move[2]) - ord('a')
                        to_row = 8 - int(move[3])
                        self.web_gui.last_move_squares = [[from_row, from_col], [to_row, to_col]]
                        
                        self.web_gui.move_history.append(f"You: {move}")
                        
                        # Make engine move if it's engine's turn
                        if not self.web_gui.is_human_turn() and not self.web_gui.game_over:
                            start_time = time.time()
                            engine_move, score = self.web_gui.engine.search(self.web_gui.engine_depth)
                            elapsed = time.time() - start_time
                            
                            if self.web_gui.engine.board.make_move(engine_move):
                                # Store engine move for highlighting
                                from_col = ord(engine_move[0]) - ord('a')
                                from_row = 8 - int(engine_move[1])
                                to_col = ord(engine_move[2]) - ord('a')
                                to_row = 8 - int(engine_move[3])
                                self.web_gui.last_move_squares = [[from_row, from_col], [to_row, to_col]]
                                
                                self.web_gui.move_history.append(f"Engine: {engine_move}")
                                
                                # Store timing and evaluation info
                                self.web_gui.last_move_time = f"{elapsed:.2f}"
                                self.web_gui.last_position_eval = f"{score/100:.2f}"
                    
                    response_data = self.web_gui.get_game_state()
                    response_data['success'] = success
                    if hasattr(self.web_gui, 'last_move_time'):
                        response_data['move_time'] = self.web_gui.last_move_time
                    if hasattr(self.web_gui, 'last_position_eval'):
                        response_data['position_eval'] = self.web_gui.last_position_eval
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data).encode('utf-8'))
                
                elif self.path == '/new_game':
                    self.web_gui.engine.board = ChessBoard(chess960=self.web_gui.engine.board.chess960)
                    self.web_gui.game_over = False
                    self.web_gui.move_history = []
                    if hasattr(self.web_gui, 'last_move_squares'):
                        delattr(self.web_gui, 'last_move_squares')
                    
                    response_data = self.web_gui.get_game_state()
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data).encode('utf-8'))
                
                elif self.path == '/make_human_move':
                    # Handle only the human move, no engine response
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode())
                    
                    move = data['move']
                    # Format move before making it (so we can see the original position)
                    formatted_move = self.web_gui.engine.board.format_move_notation(move)
                    success = self.web_gui.engine.board.make_move(move)
                    
                    # Get current game status including check detection
                    game_state = self.web_gui.get_game_state()
                    
                    response_data = {
                        'success': success,
                        'game_over': False,
                        'is_human_turn': False,
                        'result_message': '',
                        'status': game_state['status']
                    }
                    
                    if success:
                        # Store move with proper notation for history  
                        self.web_gui.move_history.append(f"You: {formatted_move}")
                        
                        # Check if game ended after human move
                        moves = self.web_gui.engine.board.generate_moves()
                        if not moves:
                            self.web_gui.game_over = True
                            response_data['game_over'] = True
                            if self.web_gui.engine.is_in_check(self.web_gui.engine.board):
                                response_data['result_message'] = "Checkmate! You win!"
                            else:
                                response_data['result_message'] = "Stalemate! Game is a draw."
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data).encode('utf-8'))
                
                elif self.path == '/get_engine_move':
                    # Handle only the engine move
                    import time
                    
                    if not self.web_gui.game_over:
                        start_time = time.time()
                        engine_move, score = self.web_gui.engine.search(self.web_gui.engine_depth)
                        elapsed = time.time() - start_time
                        
                        # Format move before making it
                        formatted_move = self.web_gui.engine.board.format_move_notation(engine_move)
                        success = self.web_gui.engine.board.make_move(engine_move)
                        
                        # Get current game status including check detection
                        game_state = self.web_gui.get_game_state()
                        
                        response_data = {
                            'success': success,
                            'move': engine_move,
                            'eval': f"{score/100:.2f}",
                            'time': f"{elapsed:.2f}",
                            'game_over': False,
                            'result_message': '',
                            'status': game_state['status']
                        }
                        
                        if success:
                            # Store move with proper notation for history
                            self.web_gui.move_history.append(f"Engine: {formatted_move}")
                            
                            # Check if game ended after engine move
                            moves = self.web_gui.engine.board.generate_moves()
                            if not moves:
                                self.web_gui.game_over = True
                                response_data['game_over'] = True
                                if self.web_gui.engine.is_in_check(self.web_gui.engine.board):
                                    response_data['result_message'] = "Checkmate! Engine wins!"
                                else:
                                    response_data['result_message'] = "Stalemate! Game is a draw."
                    else:
                        response_data = {'success': False}
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data).encode('utf-8'))
                
                elif self.path == '/undo_move':
                    # Simple undo - just go back to previous position
                    # This is a basic implementation, you could store position history for better undo
                    success = False
                    if len(self.web_gui.move_history) >= 2:
                        # Remove last two moves (human + engine)
                        self.web_gui.move_history = self.web_gui.move_history[:-2]
                        
                        # Recreate board from move history
                        self.web_gui.engine.board = ChessBoard(chess960=self.web_gui.engine.board.chess960)
                        for move_entry in self.web_gui.move_history:
                            move = move_entry.split(': ')[1]
                            self.web_gui.engine.board.make_move(move)
                        
                        success = True
                        if hasattr(self.web_gui, 'last_move_squares'):
                            delattr(self.web_gui, 'last_move_squares')
                    
                    response_data = self.web_gui.get_game_state()
                    response_data['success'] = success
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data).encode('utf-8'))

            def log_message(self, format, *args):
                pass  # Suppress server logs

        handler = lambda *args, **kwargs: ChessHandler(*args, web_gui=self, **kwargs)
        
        try:
            with socketserver.TCPServer(("", self.port), handler) as httpd:
                print(f"Chess engine web GUI running at http://localhost:{self.port}")
                print("Press Ctrl+C to stop the server")
                
                # Try to open browser
                try:
                    webbrowser.open(f'http://localhost:{self.port}')
                except:
                    pass
                
                httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down web server...")
        except OSError as e:
            print(f"Error: Port {self.port} might be in use. Try a different port with --port option.")

class UCIEngine:
    def __init__(self):
        self.engine = ChessEngine()
        self.debug = False
        self.chess960 = False
        
    def uci_loop(self):
        while True:
            try:
                command = input().strip()
                if not command:
                    continue
                
                parts = command.split()
                cmd = parts[0].lower()
                
                if cmd == "uci":
                    self.handle_uci()
                elif cmd == "debug":
                    self.handle_debug(parts)
                elif cmd == "isready":
                    self.handle_isready()
                elif cmd == "setoption":
                    self.handle_setoption(parts)
                elif cmd == "register":
                    pass  # Not implemented
                elif cmd == "ucinewgame":
                    self.handle_ucinewgame()
                elif cmd == "position":
                    self.handle_position(parts)
                elif cmd == "go":
                    self.handle_go(parts)
                elif cmd == "stop":
                    self.handle_stop()
                elif cmd == "ponderhit":
                    pass  # Not implemented
                elif cmd == "quit":
                    break
                else:
                    if self.debug:
                        print(f"info string Unknown command: {command}")
                        
            except EOFError:
                break
            except Exception as e:
                if self.debug:
                    print(f"info string Error: {e}")
    
    def handle_uci(self):
        print("id name ClaudeChess 1.0")
        print("id author Claude")
        print("option name Hash type spin default 16 min 1 max 512")
        print("option name Threads type spin default 1 min 1 max 8")
        print("option name UCI_Chess960 type check default false")
        print("uciok")
    
    def handle_debug(self, parts):
        if len(parts) > 1:
            self.debug = parts[1].lower() == "on"
    
    def handle_isready(self):
        print("readyok")
    
    def handle_setoption(self, parts):
        # Parse setoption name <name> [value <value>]
        if len(parts) >= 4 and parts[1].lower() == "name":
            option_name = parts[2]
            if option_name.lower() == "uci_chess960" and len(parts) >= 6 and parts[4].lower() == "value":
                self.chess960 = parts[5].lower() == "true"
                if self.debug:
                    print(f"info string Chess960 mode: {self.chess960}")
        
        if self.debug:
            print(f"info string Setting option: {' '.join(parts[1:])}")
    
    def handle_ucinewgame(self):
        self.engine = ChessEngine(chess960=self.chess960)
        if self.debug:
            print("info string New game started")
    
    def handle_position(self, parts):
        if len(parts) < 2:
            return
        
        if parts[1] == "startpos":
            self.engine.board = ChessBoard(chess960=self.chess960)
            moves_index = 3 if len(parts) > 2 and parts[2] == "moves" else None
        elif parts[1] == "chess960pos" and len(parts) >= 3:
            # Custom command for Chess960 position setup: position chess960pos <position_id> [moves ...]
            try:
                position_id = int(parts[2])
                self.engine.board = ChessBoard(chess960=True, position_id=position_id)
                moves_index = 4 if len(parts) > 3 and parts[3] == "moves" else None
            except ValueError:
                if self.debug:
                    print(f"info string Invalid Chess960 position ID: {parts[2]}")
                return
        elif parts[1] == "fen":
            # Find the moves keyword
            moves_index = None
            fen_parts = []
            for i in range(2, len(parts)):
                if parts[i] == "moves":
                    moves_index = i + 1
                    break
                fen_parts.append(parts[i])
            
            if len(fen_parts) >= 6:
                fen = " ".join(fen_parts)
                self.engine.board.from_fen(fen)
            else:
                if self.debug:
                    print("info string Invalid FEN")
                return
        
        # Apply moves if any
        if moves_index and moves_index < len(parts):
            for move in parts[moves_index:]:
                if not self.engine.board.make_move(move):
                    if self.debug:
                        print(f"info string Invalid move: {move}")
                    break
    
    def handle_go(self, parts):
        # Parse go command options
        depth = 4  # Default depth
        movetime = None
        infinite = False
        
        i = 1
        while i < len(parts):
            if parts[i] == "depth" and i + 1 < len(parts):
                try:
                    depth = int(parts[i + 1])
                    i += 2
                except ValueError:
                    i += 1
            elif parts[i] == "movetime" and i + 1 < len(parts):
                try:
                    movetime = int(parts[i + 1])
                    i += 2
                except ValueError:
                    i += 1
            elif parts[i] == "infinite":
                infinite = True
                i += 1
            else:
                i += 1
        
        # Limit depth to reasonable values
        depth = max(1, min(depth, 8))
        
        self.engine.thinking = True
        start_time = time.time()
        
        try:
            best_move, score = self.engine.search(depth)
            
            # Output thinking information
            elapsed = int((time.time() - start_time) * 1000)
            print(f"info depth {depth} score cp {score} time {elapsed} pv {best_move}")
            print(f"bestmove {best_move}")
            
        except Exception as e:
            if self.debug:
                print(f"info string Search error: {e}")
            # Fallback to a simple move
            moves = self.engine.board.generate_moves()
            if moves:
                print(f"bestmove {moves[0]}")
            else:
                print("bestmove 0000")
        
        self.engine.thinking = False
    
    def handle_stop(self):
        self.engine.thinking = False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Claude Chess Engine')
    parser.add_argument('--interactive', '-i', action='store_true', 
                       help='Start interactive text-based game mode')
    parser.add_argument('--gui', '-g', action='store_true',
                       help='Start tkinter GUI game mode')
    parser.add_argument('--web', '-w', action='store_true',
                       help='Start web-based GUI game mode')
    parser.add_argument('--port', type=int, default=8080,
                       help='Port for web GUI (default: 8080)')
    parser.add_argument('--color', choices=['white', 'black'], default='white',
                       help='Your color in interactive/GUI mode (default: white)')
    parser.add_argument('--depth', type=int, default=4, 
                       help='Engine search depth (default: 4)')
    parser.add_argument('--chess960', action='store_true',
                       help='Enable Chess960 mode')
    parser.add_argument('--position', type=int, metavar='ID',
                       help='Chess960 position ID (0-959)')
    
    args = parser.parse_args()
    
    if args.gui:
        # tkinter GUI game mode
        if not GUI_AVAILABLE:
            print("Error: tkinter GUI mode is not available.")
            print("On macOS, tkinter might not be installed by default.")
            print("Try: brew install python-tk")
            print("Or use --web for web-based GUI or --interactive for text mode.")
            sys.exit(1)
        
        gui = ChessGUI(
            chess960=args.chess960,
            position_id=args.position,
            human_color=args.color,
            engine_depth=args.depth
        )
        gui.run()
    elif args.web:
        # Web GUI game mode
        if not WEB_GUI_AVAILABLE:
            print("Error: Web GUI mode requires http.server module.")
            sys.exit(1)
        
        web_gui = WebGUI(
            chess960=args.chess960,
            position_id=args.position,
            human_color=args.color,
            engine_depth=args.depth,
            port=args.port
        )
        web_gui.run()
    elif args.interactive:
        # Interactive text-based game mode
        game = InteractiveGame(
            chess960=args.chess960,
            position_id=args.position,
            human_color=args.color,
            engine_depth=args.depth
        )
        game.play()
    else:
        # UCI mode
        engine = UCIEngine()
        engine.uci_loop()

if __name__ == "__main__":
    main()
