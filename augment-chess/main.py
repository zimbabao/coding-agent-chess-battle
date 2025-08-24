#!/usr/bin/env python3
"""
PyChess Engine - A chess engine with UCI interface

Usage:
    python main.py              # Run in UCI mode
    python main.py --test        # Run tests
    python main.py --interactive # Run in interactive mode
    python main.py --perft N     # Run perft test to depth N
"""

import sys
import argparse
import time
from chess_engine import ChessEngine
from uci import UCIEngine

def run_uci():
    """Run the engine in UCI mode."""
    engine = UCIEngine()
    engine.run()

def run_interactive():
    """Run the engine in interactive mode for testing."""
    engine = ChessEngine()

    print("PyChess Engine - Interactive Mode")
    print("Commands:")
    print("  show          - Show current board")
    print("  move <uci>    - Make a move (e.g., 'move e2e4')")
    print("  undo          - Undo last move")
    print("  legal         - Show legal moves")
    print("  eval          - Evaluate current position")
    print("  best [depth]  - Find best move (optional depth)")
    print("  perft <depth> - Run perft test")
    print("  reset         - Reset to starting position")
    print("  chess960 <id> - Set up Chess960 position (0-959)")
    print("  random960     - Set up random Chess960 position")
    print("  standard      - Switch to standard chess")
    print("  quit          - Exit")
    print()
    
    print(engine.get_board_string())
    
    while True:
        try:
            command = input("chess> ").strip().split()
            if not command:
                continue
            
            cmd = command[0].lower()
            
            if cmd == "quit" or cmd == "exit":
                break
            elif cmd == "show":
                print(engine.get_board_string())
            elif cmd == "move" and len(command) > 1:
                move_str = command[1]
                if engine.make_move(move_str):
                    print(f"Move {move_str} played")
                    print(engine.get_board_string())
                    
                    # Check if game is over
                    game_over, reason = engine.is_game_over()
                    if game_over:
                        print(f"Game over: {reason}")
                else:
                    print(f"Illegal move: {move_str}")
            elif cmd == "undo":
                if engine.undo_move():
                    print("Move undone")
                    print(engine.get_board_string())
                else:
                    print("No move to undo")
            elif cmd == "legal":
                legal_moves = engine.get_legal_moves()
                print(f"Legal moves ({len(legal_moves)}):")
                for i, move in enumerate(legal_moves):
                    print(f"  {move}", end="")
                    if (i + 1) % 8 == 0:
                        print()
                if len(legal_moves) % 8 != 0:
                    print()
            elif cmd == "eval":
                score = engine.evaluate_position()
                print(f"Position evaluation: {score} centipawns")
                if score > 0:
                    print("White is better")
                elif score < 0:
                    print("Black is better")
                else:
                    print("Position is equal")
            elif cmd == "best":
                depth = 6
                if len(command) > 1:
                    try:
                        depth = int(command[1])
                    except ValueError:
                        print("Invalid depth")
                        continue
                
                print(f"Searching for best move (depth {depth})...")
                best_move = engine.get_best_move(depth)
                if best_move:
                    print(f"Best move: {best_move}")
                else:
                    print("No legal moves available")
            elif cmd == "perft" and len(command) > 1:
                try:
                    depth = int(command[1])
                    if depth > 6:
                        print("Warning: depth > 6 may take a long time")
                        confirm = input("Continue? (y/n): ")
                        if confirm.lower() != 'y':
                            continue
                    
                    engine.run_perft_test(depth)
                except ValueError:
                    print("Invalid depth")
            elif cmd == "reset":
                engine.reset_game()
                print("Game reset to starting position")
                print(engine.get_board_string())
            elif cmd == "chess960" and len(command) > 1:
                try:
                    position_id = int(command[1])
                    engine.setup_chess960_position(position_id)
                    print(f"Chess960 position {position_id} set up")
                    print(engine.get_board_string())
                except ValueError as e:
                    print(f"Error: {e}")
            elif cmd == "random960":
                position_id = engine.generate_random_chess960_position()
                print(f"Random Chess960 position {position_id} set up")
                print(engine.get_board_string())
            elif cmd == "standard":
                engine = ChessEngine(chess960=False)
                print("Switched to standard chess")
                print(engine.get_board_string())
            else:
                print("Unknown command. Type 'quit' to exit.")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except EOFError:
            break

def run_tests():
    """Run basic tests."""
    print("Running basic tests...")
    
    engine = ChessEngine()
    
    # Test 1: Initial position
    print("Test 1: Initial position")
    legal_moves = engine.get_legal_moves()
    print(f"Legal moves from starting position: {len(legal_moves)}")
    assert len(legal_moves) == 20, f"Expected 20 legal moves, got {len(legal_moves)}"
    print("✓ Passed")
    
    # Test 2: Make and undo moves
    print("\nTest 2: Make and undo moves")
    initial_eval = engine.evaluate_position()
    engine.make_move("e2e4")
    engine.make_move("e7e5")
    engine.undo_move()
    engine.undo_move()
    final_eval = engine.evaluate_position()
    assert initial_eval == final_eval, "Position not restored after undo"
    print("✓ Passed")
    
    # Test 3: Perft test (depth 3)
    print("\nTest 3: Perft test (depth 3)")
    nodes = engine.perft(3)
    expected_nodes = 8902  # Known perft(3) result for starting position
    print(f"Perft(3) nodes: {nodes}")
    assert nodes == expected_nodes, f"Expected {expected_nodes} nodes, got {nodes}"
    print("✓ Passed")
    
    # Test 4: Best move search
    print("\nTest 4: Best move search")
    best_move = engine.get_best_move(depth=3)
    assert best_move is not None, "No best move found"
    print(f"Best move found: {best_move}")
    print("✓ Passed")
    
    print("\nAll tests passed! ✓")

def main():
    parser = argparse.ArgumentParser(description="PyChess Engine with Chess960 Support")
    parser.add_argument("--test", action="store_true", help="Run tests")
    parser.add_argument("--test-chess960", action="store_true", help="Run Chess960 tests")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--perft", type=int, metavar="N", help="Run perft test to depth N")
    parser.add_argument("--chess960", action="store_true", help="Enable Chess960 mode")
    parser.add_argument("--position", type=int, metavar="ID", help="Chess960 position ID (0-959)")
    parser.add_argument("--web", action="store_true", help="Start web interface")
    parser.add_argument("--port", type=int, default=8080, help="Web server port (default: 8080)")
    
    args = parser.parse_args()
    
    if args.test:
        run_tests()
    elif args.test_chess960:
        import subprocess
        result = subprocess.run([sys.executable, "test_chess960.py"],
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        sys.exit(result.returncode)
    elif args.interactive:
        run_interactive()
    elif args.perft:
        chess960 = args.chess960
        position_id = args.position
        engine = ChessEngine(chess960=chess960, position_id=position_id)
        print(f"Running perft test to depth {args.perft}")
        if chess960:
            print(f"Chess960 mode enabled (Position ID: {engine.position_id})")
        engine.run_perft_test(args.perft)
    elif args.web:
        from web_gui import WebGUI
        chess960 = args.chess960
        position_id = args.position

        if chess960 and position_id is not None:
            if not (0 <= position_id <= 959):
                print("Error: Chess960 position ID must be between 0 and 959")
                sys.exit(1)

        web_gui = WebGUI(port=args.port, chess960=chess960, position_id=position_id)
        try:
            web_gui.start()
            print("Press Ctrl+C to stop the server")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down web server...")
            web_gui.stop()
    else:
        # Default: run in UCI mode
        run_uci()

if __name__ == "__main__":
    main()
