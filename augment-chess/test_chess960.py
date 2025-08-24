#!/usr/bin/env python3
"""
Comprehensive Chess960 test suite.
Tests all aspects of Chess960 implementation including position generation,
castling mechanics, and edge cases.
"""

import sys
import time
from chess_engine import ChessEngine
from board import ChessBoard
from utils import *

def test_chess960_position_generation():
    """Test Chess960 position generation for all 960 positions."""
    print("Testing Chess960 position generation...")
    
    generated_positions = set()
    
    for pos_id in range(960):
        try:
            board = ChessBoard(chess960=True, position_id=pos_id)
            
            # Get back rank (white pieces on rank 1)
            back_rank = []
            for file in range(8):
                square = coords_to_square(0, file)
                back_rank.append(board.board[square])
            
            position_string = ''.join(str(piece) for piece in back_rank)
            
            # Ensure position is unique
            assert position_string not in generated_positions, f"Duplicate position for ID {pos_id}"
            generated_positions.add(position_string)
            
            # Validate Chess960 constraints
            assert validate_chess960_position(back_rank), f"Invalid Chess960 position for ID {pos_id}"
            
        except Exception as e:
            print(f"✗ Failed for position {pos_id}: {e}")
            return False
    
    print(f"✓ All 960 Chess960 positions generated successfully and are unique")
    return True

def validate_chess960_position(back_rank):
    """Validate that a back rank satisfies Chess960 constraints."""
    # Check that we have exactly the right pieces
    piece_counts = {ROOK: 0, KNIGHT: 0, BISHOP: 0, QUEEN: 0, KING: 0}
    for piece in back_rank:
        if piece in piece_counts:
            piece_counts[piece] += 1
    
    if piece_counts != {ROOK: 2, KNIGHT: 2, BISHOP: 2, QUEEN: 1, KING: 1}:
        return False
    
    # Check bishops on opposite colored squares
    bishop_positions = [i for i, piece in enumerate(back_rank) if piece == BISHOP]
    if len(bishop_positions) != 2:
        return False
    
    # Check if bishops are on opposite colored squares
    bishop1_color = bishop_positions[0] % 2
    bishop2_color = bishop_positions[1] % 2
    if bishop1_color == bishop2_color:
        return False
    
    # Check king between rooks
    king_pos = back_rank.index(KING)
    rook_positions = [i for i, piece in enumerate(back_rank) if piece == ROOK]
    if len(rook_positions) != 2:
        return False
    
    if not (min(rook_positions) < king_pos < max(rook_positions)):
        return False
    
    return True

def test_chess960_castling_scenarios():
    """Test castling in various Chess960 positions."""
    print("Testing Chess960 castling scenarios...")
    
    # Test specific positions with different king/rook placements
    test_positions = [0, 158, 356, 518, 959]  # Sample positions
    
    for pos_id in test_positions:
        try:
            engine = ChessEngine(chess960=True, position_id=pos_id)
            
            # Test that castling moves are generated when appropriate
            legal_moves = engine.get_legal_moves()
            castling_moves = [move for move in legal_moves if move.is_castling]
            
            # In starting position, both castling moves should be available
            # (unless king or rooks are in unusual positions that prevent it)
            print(f"Position {pos_id}: {len(castling_moves)} castling moves available")
            
            # Test making castling moves
            for move in castling_moves:
                engine_copy = ChessEngine(chess960=True, position_id=pos_id)
                success = engine_copy.make_move(str(move))
                assert success, f"Failed to make castling move {move} in position {pos_id}"
                
                # Verify king and rook ended up in correct squares
                king_square = engine_copy.board.find_king(WHITE)
                king_file = square_to_coords(king_square)[1]
                
                if move.to_square == coords_to_square(0, 6):  # Kingside
                    assert king_file == 6, f"King not on g-file after kingside castling in position {pos_id}"
                    # Check rook on f-file
                    rook_square = coords_to_square(0, 5)
                    assert engine_copy.board.board[rook_square] == ROOK, f"Rook not on f-file after kingside castling"
                elif move.to_square == coords_to_square(0, 2):  # Queenside
                    assert king_file == 2, f"King not on c-file after queenside castling in position {pos_id}"
                    # Check rook on d-file
                    rook_square = coords_to_square(0, 3)
                    assert engine_copy.board.board[rook_square] == ROOK, f"Rook not on d-file after queenside castling"
                
        except Exception as e:
            print(f"✗ Castling test failed for position {pos_id}: {e}")
            return False
    
    print("✓ Chess960 castling tests passed")
    return True

def test_chess960_edge_cases():
    """Test Chess960 edge cases and boundary conditions."""
    print("Testing Chess960 edge cases...")
    
    # Test invalid position IDs
    try:
        ChessBoard(chess960=True, position_id=-1)
        assert False, "Should have raised ValueError for negative position ID"
    except ValueError:
        pass
    
    try:
        ChessBoard(chess960=True, position_id=960)
        assert False, "Should have raised ValueError for position ID >= 960"
    except ValueError:
        pass
    
    # Test extreme positions
    extreme_positions = [0, 959]  # First and last positions
    
    for pos_id in extreme_positions:
        try:
            engine = ChessEngine(chess960=True, position_id=pos_id)
            
            # Should be able to generate legal moves
            legal_moves = engine.get_legal_moves()
            assert len(legal_moves) > 0, f"No legal moves in position {pos_id}"
            
            # Should be able to evaluate position
            eval_score = engine.evaluate_position()
            assert isinstance(eval_score, (int, float)), f"Invalid evaluation for position {pos_id}"
            
        except Exception as e:
            print(f"✗ Edge case test failed for position {pos_id}: {e}")
            return False
    
    print("✓ Chess960 edge case tests passed")
    return True

def test_chess960_vs_standard_compatibility():
    """Test that Chess960 implementation doesn't break standard chess."""
    print("Testing Chess960 vs standard chess compatibility...")
    
    try:
        # Standard chess engine
        standard_engine = ChessEngine(chess960=False)
        
        # Chess960 engine with standard starting position (position 518)
        chess960_engine = ChessEngine(chess960=True, position_id=518)
        
        # Both should have same number of legal moves in starting position
        standard_moves = len(standard_engine.get_legal_moves())
        chess960_moves = len(chess960_engine.get_legal_moves())
        
        assert standard_moves == chess960_moves == 20, f"Move count mismatch: standard={standard_moves}, chess960={chess960_moves}"
        
        # Test a few moves
        test_moves = ["e2e4", "d2d4", "g1f3", "b1c3"]
        
        for move in test_moves:
            standard_success = standard_engine.make_move(move)
            chess960_success = chess960_engine.make_move(move)
            
            assert standard_success == chess960_success, f"Move {move} success mismatch"
            
            if standard_success:
                # Undo the move for next test
                standard_engine.undo_move()
                chess960_engine.undo_move()
        
        print("✓ Chess960 vs standard compatibility tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Compatibility test failed: {e}")
        return False

def test_chess960_performance():
    """Test Chess960 performance benchmarks."""
    print("Testing Chess960 performance...")
    
    try:
        # Test position generation speed
        start_time = time.time()
        for pos_id in range(100):  # Test first 100 positions
            ChessBoard(chess960=True, position_id=pos_id)
        generation_time = time.time() - start_time
        
        avg_time_per_position = generation_time / 100 * 1000  # Convert to ms
        print(f"Average Chess960 position generation time: {avg_time_per_position:.2f}ms")
        
        assert avg_time_per_position < 100, f"Position generation too slow: {avg_time_per_position}ms"
        
        # Test move generation speed in Chess960
        engine = ChessEngine(chess960=True, position_id=500)
        
        start_time = time.time()
        for _ in range(100):
            engine.get_legal_moves()
        move_gen_time = time.time() - start_time
        
        avg_move_gen_time = move_gen_time / 100 * 1000
        print(f"Average Chess960 move generation time: {avg_move_gen_time:.2f}ms")
        
        assert avg_move_gen_time < 50, f"Move generation too slow: {avg_move_gen_time}ms"
        
        print("✓ Chess960 performance tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Performance test failed: {e}")
        return False

def run_all_chess960_tests():
    """Run all Chess960 tests."""
    print("=" * 60)
    print("COMPREHENSIVE CHESS960 TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_chess960_position_generation,
        test_chess960_castling_scenarios,
        test_chess960_edge_cases,
        test_chess960_vs_standard_compatibility,
        test_chess960_performance
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print(f"\n{test.__name__.replace('_', ' ').title()}:")
        print("-" * 40)
        
        try:
            if test():
                passed += 1
            else:
                print(f"✗ {test.__name__} FAILED")
        except Exception as e:
            print(f"✗ {test.__name__} FAILED with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"CHESS960 TEST RESULTS: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("🎉 ALL CHESS960 TESTS PASSED! 🎉")
        return True
    else:
        print("❌ SOME CHESS960 TESTS FAILED")
        return False

if __name__ == "__main__":
    success = run_all_chess960_tests()
    sys.exit(0 if success else 1)
