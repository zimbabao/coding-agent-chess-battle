#!/usr/bin/env python3
"""
Standalone demonstration of the improved move timing.
Run this directly in a terminal to see the timing in action.
"""

from chess_engine import InteractiveGame

def main():
    print("🎯 CHESS ENGINE - IMPROVED TIMING DEMONSTRATION")
    print("=" * 60)
    print()
    print("This demonstrates the enhanced move timing:")
    print("1. Your move shows immediately with clear borders")
    print("2. Board updates right after your move") 
    print("3. Engine thinking is clearly marked")
    print("4. Engine move shows with evaluation")
    print("5. Final board update")
    print()
    print("To see the timing properly, run this in a terminal:")
    print("python3 demo_timing.py")
    print()
    print("=" * 60)
    
    # Create and start the game
    game = InteractiveGame(engine_depth=3)
    game.play()

if __name__ == "__main__":
    main()