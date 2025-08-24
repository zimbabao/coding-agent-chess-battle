#!/usr/bin/env python3
"""
A truly interactive chess game that forces real-time display
by requiring user input between each phase.
"""

from chess_engine import ChessBoard, ChessEngine
import sys
import time

class TrulyInteractiveGame:
    def __init__(self, engine_depth=3):
        self.board = ChessBoard()
        self.engine = ChessEngine()
        self.engine.board = self.board
        self.engine_depth = engine_depth
        self.human_color = 'white'
        
    def display_board(self):
        print("\n    a   b   c   d   e   f   g   h")
        print("  +---+---+---+---+---+---+---+---+")
        
        for row in range(8):
            print(f"{8-row} |", end="")
            for col in range(8):
                piece = self.board.get_piece(row, col)
                if piece == '.':
                    piece = ' '
                print(f" {piece} |", end="")
            print(f" {8-row}")
            print("  +---+---+---+---+---+---+---+---+")
        
        print("    a   b   c   d   e   f   g   h\n")
        
    def play(self):
        print("🎯 TRULY INTERACTIVE CHESS - IMMEDIATE DISPLAY MODE")
        print("=" * 60)
        print("This version forces real-time display by requiring")
        print("user confirmation between each phase.")
        print("=" * 60)
        
        self.display_board()
        
        while True:
            # PHASE 1: Get human move
            print("📝 PHASE 1: YOUR TURN")
            print("-" * 30)
            
            legal_moves = self.board.generate_moves()
            if not legal_moves:
                if self.engine.is_in_check(self.board):
                    print("🏁 CHECKMATE! You lose.")
                else:
                    print("🤝 STALEMATE!")
                break
                
            while True:
                try:
                    move = input("Enter your move (e.g., e2e4) or 'quit': ").strip().lower()
                    if move == 'quit':
                        return
                    if move in legal_moves:
                        break
                    print(f"Illegal move: {move}. Try again.")
                except (KeyboardInterrupt, EOFError):
                    return
            
            # PHASE 2: Execute human move and show immediately
            print(f"\n✅ EXECUTING YOUR MOVE: {move.upper()}")
            print("=" * 40)
            self.board.make_move(move)
            self.display_board()
            
            print("👆 YOUR MOVE IS NOW COMPLETE AND VISIBLE!")
            print("The board above shows your move applied.")
            input("Press ENTER to let the engine think...")
            
            # PHASE 3: Check if game ended
            legal_moves = self.board.generate_moves()
            if not legal_moves:
                if self.engine.is_in_check(self.board):
                    print("🎉 CHECKMATE! You win!")
                else:
                    print("🤝 STALEMATE!")
                break
            
            # PHASE 4: Engine thinking
            print("\n🤖 PHASE 2: ENGINE'S TURN")
            print("-" * 30)
            print("Engine is now calculating its move...")
            print("(This may take a few seconds)")
            
            start_time = time.time()
            best_move, score = self.engine.search(self.engine_depth)
            elapsed = time.time() - start_time
            
            # PHASE 5: Execute engine move and show
            print(f"\n🤖 ENGINE PLAYS: {best_move.upper()}")
            print(f"📊 Evaluation: {score/100:.2f} | Time: {elapsed:.2f}s")
            print("=" * 40)
            
            self.board.make_move(best_move)
            self.display_board()
            
            print("👆 ENGINE MOVE IS NOW COMPLETE AND VISIBLE!")
            input("Press ENTER to continue to your next turn...")

if __name__ == "__main__":
    game = TrulyInteractiveGame()
    game.play()