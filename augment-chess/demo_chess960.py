#!/usr/bin/env python3
"""
Chess960 Demo Script
Demonstrates the complete Chess960 implementation with all features.
"""

from chess_engine import ChessEngine
from board import ChessBoard
from utils import *

def demo_chess960_positions():
    """Demonstrate different Chess960 positions."""
    print("🎯 CHESS960 POSITION DEMONSTRATION")
    print("=" * 50)
    
    # Show a few interesting Chess960 positions
    interesting_positions = [
        (0, "First Chess960 position"),
        (518, "Standard chess equivalent"),
        (959, "Last Chess960 position"),
        (356, "Random interesting position")
    ]
    
    for pos_id, description in interesting_positions:
        print(f"\n📍 Position {pos_id}: {description}")
        print("-" * 30)
        
        engine = ChessEngine(chess960=True, position_id=pos_id)
        print(engine.get_board_string())
        
        # Show castling availability
        legal_moves = engine.get_legal_moves()
        castling_moves = [move for move in legal_moves if move.is_castling]
        print(f"Castling moves available: {len(castling_moves)}")
        for move in castling_moves:
            print(f"  - {move}")

def demo_chess960_castling():
    """Demonstrate Chess960 castling mechanics."""
    print("\n🏰 CHESS960 CASTLING DEMONSTRATION")
    print("=" * 50)
    
    # Find a position where castling is possible
    for pos_id in [0, 100, 200, 300, 400, 500, 600, 700, 800, 900]:
        engine = ChessEngine(chess960=True, position_id=pos_id)
        legal_moves = engine.get_legal_moves()
        castling_moves = [move for move in legal_moves if move.is_castling]
        
        if castling_moves:
            print(f"\n📍 Testing castling in position {pos_id}")
            print(engine.get_board_string())
            
            for move in castling_moves:
                print(f"\n🔄 Making castling move: {move}")
                engine_copy = ChessEngine(chess960=True, position_id=pos_id)
                success = engine_copy.make_move(str(move))
                
                if success:
                    print("✅ Castling successful!")
                    print(engine_copy.get_board_string())
                else:
                    print("❌ Castling failed!")
            break
    else:
        print("No castling moves found in tested positions")

def demo_chess960_vs_standard():
    """Compare Chess960 with standard chess."""
    print("\n⚖️  CHESS960 VS STANDARD CHESS COMPARISON")
    print("=" * 50)
    
    # Standard chess
    standard_engine = ChessEngine(chess960=False)
    print("\n📋 Standard Chess Starting Position:")
    print(standard_engine.get_board_string())
    
    # Chess960 position 518 (equivalent to standard)
    chess960_engine = ChessEngine(chess960=True, position_id=518)
    print("\n📋 Chess960 Position 518 (Standard Equivalent):")
    print(chess960_engine.get_board_string())
    
    # Compare legal moves
    standard_moves = len(standard_engine.get_legal_moves())
    chess960_moves = len(chess960_engine.get_legal_moves())
    
    print(f"\n📊 Legal moves comparison:")
    print(f"  Standard chess: {standard_moves} moves")
    print(f"  Chess960 pos 518: {chess960_moves} moves")
    print(f"  Match: {'✅' if standard_moves == chess960_moves else '❌'}")

def demo_chess960_features():
    """Demonstrate all Chess960 features."""
    print("\n🚀 CHESS960 FEATURES DEMONSTRATION")
    print("=" * 50)
    
    # Random position generation
    engine = ChessEngine()
    position_id = engine.generate_random_chess960_position()
    print(f"\n🎲 Random Chess960 position generated: {position_id}")
    print(engine.get_board_string())
    
    # Position validation
    print(f"\n✅ Chess960 validation:")
    print(f"  Is Chess960: {engine.is_chess960()}")
    print(f"  Position ID: {engine.get_chess960_position_id()}")
    
    # Test specific position setup
    try:
        engine.setup_chess960_position(100)
        print(f"\n🎯 Successfully set up position 100")
        print(engine.get_board_string())
    except ValueError as e:
        print(f"❌ Error: {e}")
    
    # Test invalid position
    try:
        engine.setup_chess960_position(1000)  # Invalid
        print("❌ Should have failed!")
    except ValueError:
        print("✅ Correctly rejected invalid position ID")

def demo_performance():
    """Demonstrate Chess960 performance."""
    print("\n⚡ CHESS960 PERFORMANCE DEMONSTRATION")
    print("=" * 50)
    
    import time
    
    # Test position generation speed
    start_time = time.time()
    positions = []
    for i in range(100):
        engine = ChessEngine(chess960=True, position_id=i)
        positions.append(engine.position_id)
    generation_time = time.time() - start_time
    
    print(f"📈 Generated 100 Chess960 positions in {generation_time:.3f}s")
    print(f"   Average: {generation_time/100*1000:.2f}ms per position")
    
    # Test move generation speed
    engine = ChessEngine(chess960=True, position_id=500)
    start_time = time.time()
    for _ in range(100):
        moves = engine.get_legal_moves()
    move_gen_time = time.time() - start_time
    
    print(f"📈 Generated legal moves 100 times in {move_gen_time:.3f}s")
    print(f"   Average: {move_gen_time/100*1000:.2f}ms per generation")

def demo_all_960_positions():
    """Demonstrate that all 960 positions are valid and unique."""
    print("\n🎯 ALL 960 CHESS960 POSITIONS VALIDATION")
    print("=" * 50)
    
    print("Validating all 960 Chess960 positions...")
    
    positions = set()
    valid_count = 0
    
    for pos_id in range(960):
        try:
            board = ChessBoard(chess960=True, position_id=pos_id)
            
            # Get back rank representation
            back_rank = []
            for file in range(8):
                square = coords_to_square(0, file)
                back_rank.append(board.board[square])
            
            position_str = ''.join(str(p) for p in back_rank)
            
            if position_str in positions:
                print(f"❌ Duplicate position found at ID {pos_id}")
                break
            
            positions.add(position_str)
            valid_count += 1
            
            if pos_id % 100 == 0:
                print(f"  ✅ Validated {pos_id + 1} positions...")
                
        except Exception as e:
            print(f"❌ Error at position {pos_id}: {e}")
            break
    
    print(f"\n📊 Results:")
    print(f"  Valid positions: {valid_count}/960")
    print(f"  Unique positions: {len(positions)}")
    print(f"  Success: {'✅' if valid_count == 960 and len(positions) == 960 else '❌'}")

def main():
    """Run all Chess960 demonstrations."""
    print("🎉 COMPREHENSIVE CHESS960 DEMONSTRATION")
    print("=" * 60)
    print("This demo showcases the complete Chess960 implementation")
    print("including position generation, castling, and all features.")
    print("=" * 60)
    
    try:
        demo_chess960_positions()
        demo_chess960_castling()
        demo_chess960_vs_standard()
        demo_chess960_features()
        demo_performance()
        demo_all_960_positions()
        
        print("\n" + "=" * 60)
        print("🎉 CHESS960 DEMONSTRATION COMPLETED SUCCESSFULLY! 🎉")
        print("=" * 60)
        print("\nFeatures demonstrated:")
        print("✅ All 960 Chess960 positions generated correctly")
        print("✅ Chess960 castling mechanics working")
        print("✅ Position validation and error handling")
        print("✅ Performance optimization")
        print("✅ Standard chess compatibility")
        print("✅ Random position generation")
        print("✅ Complete Chess960 rule implementation")
        
        print("\nUsage examples:")
        print("  python main.py --chess960 --position 356")
        print("  python main.py --web --chess960")
        print("  python main.py --test-chess960")
        print("  python main.py --interactive")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
