# Chess Search Algorithms

from evaluation import evaluate_board
from utils import *
import time

class SearchEngine:
    def __init__(self):
        self.nodes_searched = 0
        self.start_time = 0
        self.time_limit = 0
        self.max_depth = 6
        self.transposition_table = {}
    
    def is_time_up(self):
        """Check if search time limit has been exceeded."""
        if self.time_limit <= 0:
            return False
        return time.time() - self.start_time >= self.time_limit
    
    def clear_transposition_table(self):
        """Clear the transposition table."""
        self.transposition_table.clear()
    
    def minimax(self, board, depth, alpha, beta, maximizing_player):
        """Minimax search with alpha-beta pruning."""
        self.nodes_searched += 1
        
        # Check time limit
        if self.is_time_up():
            return evaluate_board(board)
        
        # Base case: maximum depth reached or terminal position
        if depth == 0:
            return evaluate_board(board)
        
        legal_moves = board.generate_legal_moves()
        if not legal_moves:
            return evaluate_board(board)
        
        if maximizing_player:
            max_eval = float('-inf')
            for move in legal_moves:
                board.make_move(move)
                eval_score = self.minimax(board, depth - 1, alpha, beta, False)
                board.undo_move()
                
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                
                if beta <= alpha:
                    break  # Alpha-beta pruning
                
                if self.is_time_up():
                    break
            
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                board.make_move(move)
                eval_score = self.minimax(board, depth - 1, alpha, beta, True)
                board.undo_move()
                
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                
                if beta <= alpha:
                    break  # Alpha-beta pruning
                
                if self.is_time_up():
                    break
            
            return min_eval
    
    def search_best_move(self, board, depth=None, time_limit=0):
        """Search for the best move using iterative deepening."""
        if depth is None:
            depth = self.max_depth
        
        self.nodes_searched = 0
        self.start_time = time.time()
        self.time_limit = time_limit
        
        legal_moves = board.generate_legal_moves()
        if not legal_moves:
            return None
        
        if len(legal_moves) == 1:
            return legal_moves[0]
        
        best_move = legal_moves[0]
        best_score = float('-inf') if board.to_move == WHITE else float('inf')
        
        # Iterative deepening
        for current_depth in range(1, depth + 1):
            if self.is_time_up():
                break
            
            current_best_move = None
            current_best_score = float('-inf') if board.to_move == WHITE else float('inf')
            
            # Move ordering: try the previous best move first
            ordered_moves = legal_moves[:]
            if best_move in ordered_moves:
                ordered_moves.remove(best_move)
                ordered_moves.insert(0, best_move)
            
            for move in ordered_moves:
                if self.is_time_up():
                    break
                
                board.make_move(move)
                
                if board.to_move == BLACK:  # We just made a white move
                    score = self.minimax(board, current_depth - 1, float('-inf'), float('inf'), False)
                    if score > current_best_score:
                        current_best_score = score
                        current_best_move = move
                else:  # We just made a black move
                    score = self.minimax(board, current_depth - 1, float('-inf'), float('inf'), True)
                    if score < current_best_score:
                        current_best_score = score
                        current_best_move = move
                
                board.undo_move()
            
            # Update best move if we completed the depth
            if current_best_move and not self.is_time_up():
                best_move = current_best_move
                best_score = current_best_score
                
                print(f"info depth {current_depth} score cp {int(best_score)} nodes {self.nodes_searched} pv {best_move}")
        
        search_time = time.time() - self.start_time
        print(f"info time {int(search_time * 1000)} nodes {self.nodes_searched}")
        
        return best_move
    
    def quiescence_search(self, board, alpha, beta, depth=0):
        """Quiescence search to avoid horizon effect."""
        self.nodes_searched += 1
        
        if depth > 10 or self.is_time_up():
            return evaluate_board(board)
        
        stand_pat = evaluate_board(board)
        
        if board.to_move == WHITE:
            if stand_pat >= beta:
                return beta
            alpha = max(alpha, stand_pat)
        else:
            if stand_pat <= alpha:
                return alpha
            beta = min(beta, stand_pat)
        
        # Generate only capture moves
        legal_moves = board.generate_legal_moves()
        capture_moves = []
        
        for move in legal_moves:
            if not board.is_empty(move.to_square) or move.is_en_passant:
                capture_moves.append(move)
        
        # Sort captures by MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
        def capture_score(move):
            victim_value = PIECE_VALUES.get(board.get_piece(move.to_square), 0)
            attacker_value = PIECE_VALUES.get(board.get_piece(move.from_square), 0)
            return victim_value - attacker_value
        
        capture_moves.sort(key=capture_score, reverse=True)
        
        for move in capture_moves:
            if self.is_time_up():
                break
            
            board.make_move(move)
            score = self.quiescence_search(board, alpha, beta, depth + 1)
            board.undo_move()
            
            if board.to_move == WHITE:
                if score >= beta:
                    return beta
                alpha = max(alpha, score)
            else:
                if score <= alpha:
                    return alpha
                beta = min(beta, score)
        
        return alpha if board.to_move == WHITE else beta
    
    def minimax_with_quiescence(self, board, depth, alpha, beta, maximizing_player):
        """Minimax with quiescence search."""
        self.nodes_searched += 1
        
        if self.is_time_up():
            return evaluate_board(board)
        
        if depth == 0:
            return self.quiescence_search(board, alpha, beta)
        
        legal_moves = board.generate_legal_moves()
        if not legal_moves:
            return evaluate_board(board)
        
        if maximizing_player:
            max_eval = float('-inf')
            for move in legal_moves:
                board.make_move(move)
                eval_score = self.minimax_with_quiescence(board, depth - 1, alpha, beta, False)
                board.undo_move()
                
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                
                if beta <= alpha:
                    break
                
                if self.is_time_up():
                    break
            
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                board.make_move(move)
                eval_score = self.minimax_with_quiescence(board, depth - 1, alpha, beta, True)
                board.undo_move()
                
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                
                if beta <= alpha:
                    break
                
                if self.is_time_up():
                    break
            
            return min_eval
    
    def search_best_move_with_quiescence(self, board, depth=None, time_limit=0):
        """Search for best move using minimax with quiescence search."""
        if depth is None:
            depth = self.max_depth
        
        self.nodes_searched = 0
        self.start_time = time.time()
        self.time_limit = time_limit
        
        legal_moves = board.generate_legal_moves()
        if not legal_moves:
            return None
        
        if len(legal_moves) == 1:
            return legal_moves[0]
        
        best_move = legal_moves[0]
        
        for current_depth in range(1, depth + 1):
            if self.is_time_up():
                break
            
            current_best_move = None
            current_best_score = float('-inf') if board.to_move == WHITE else float('inf')
            
            for move in legal_moves:
                if self.is_time_up():
                    break
                
                board.make_move(move)
                
                if board.to_move == BLACK:
                    score = self.minimax_with_quiescence(board, current_depth - 1, float('-inf'), float('inf'), False)
                    if score > current_best_score:
                        current_best_score = score
                        current_best_move = move
                else:
                    score = self.minimax_with_quiescence(board, current_depth - 1, float('-inf'), float('inf'), True)
                    if score < current_best_score:
                        current_best_score = score
                        current_best_move = move
                
                board.undo_move()
            
            if current_best_move and not self.is_time_up():
                best_move = current_best_move
                print(f"info depth {current_depth} score cp {int(current_best_score)} nodes {self.nodes_searched} pv {best_move}")
        
        return best_move
