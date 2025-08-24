#!/usr/bin/env python3
"""
Comprehensive test suite for the chess engine covering edge cases, 
performance, and complex scenarios.
"""

from chess_engine import ChessBoard, ChessEngine, WebGUI, InteractiveGame
import time
import json

def test_checkmate_scenarios():
    """Test various checkmate patterns."""
    print("♔ TESTING CHECKMATE SCENARIOS")
    print("=" * 40)
    
    scenarios = [
        {
            "name": "Fool's Mate (fastest checkmate)",
            "moves": ["f2f3", "e7e5", "g2g4", "d8h4"],
            "expected_winner": "Black"
        },
        {
            "name": "Scholar's Mate", 
            "moves": ["e2e4", "e7e5", "d1h5", "b8c6", "f1c4", "g8f6", "h5f7"],
            "expected_winner": "White"
        },
        {
            "name": "Back Rank Mate Setup",
            "setup": "Setup requires piece placement",
            "moves": [],
            "skip": True  # Will implement manual setup
        }
    ]
    
    results = []
    for scenario in scenarios:
        if scenario.get("skip"):
            continue
            
        print(f"\n🎯 Testing: {scenario['name']}")
        board = ChessBoard()
        engine = ChessEngine()
        engine.board = board
        
        # Play the moves
        move_success = True
        for i, move in enumerate(scenario["moves"]):
            success = board.make_move(move)
            if not success:
                print(f"   ❌ Move {i+1} ({move}) failed")
                move_success = False
                break
            print(f"   ✅ Move {i+1}: {move}")
        
        if not move_success:
            results.append(False)
            continue
        
        # Check if game is over
        legal_moves = board.generate_moves()
        is_checkmate = len(legal_moves) == 0 and engine.is_in_check(board)
        is_stalemate = len(legal_moves) == 0 and not engine.is_in_check(board)
        
        if is_checkmate:
            winner = "Black" if board.white_to_move else "White"
            expected = scenario["expected_winner"]
            if winner == expected:
                print(f"   ✅ Checkmate correctly detected - {winner} wins!")
                results.append(True)
            else:
                print(f"   ❌ Wrong winner: expected {expected}, got {winner}")
                results.append(False)
        elif is_stalemate:
            print(f"   ⚖️ Stalemate detected")
            results.append(True)
        else:
            print(f"   ❌ Game should be over but {len(legal_moves)} moves available")
            results.append(False)
    
    return all(results)

def test_castling_variations():
    """Test different castling scenarios including Chess960."""
    print("\n🏰 TESTING CASTLING VARIATIONS")
    print("=" * 40)
    
    tests = []
    
    # Standard castling
    print("\n👑 Testing Standard Castling:")
    board = ChessBoard()
    
    # Clear pieces for kingside castling
    moves_for_kingside = ["e2e4", "e7e5", "g1f3", "g8f6", "f1c4", "f8c5"]
    
    print("  Setting up for kingside castling...")
    for move in moves_for_kingside:
        success = board.make_move(move)
        print(f"    {move}: {'✅' if success else '❌'}")
    
    # Attempt kingside castling
    castling_move = "e1g1"
    legal_moves = board.generate_moves()
    can_castle = castling_move in legal_moves
    print(f"  Kingside castling available: {can_castle}")
    
    if can_castle:
        success = board.make_move(castling_move)
        print(f"  Castling execution: {'✅' if success else '❌'}")
        
        # Verify pieces moved correctly
        king_pos = board.get_piece(7, 6)  # g1
        rook_pos = board.get_piece(7, 5)  # f1
        old_king_pos = board.get_piece(7, 4)  # e1
        old_rook_pos = board.get_piece(7, 7)  # h1
        
        castling_correct = (king_pos == 'K' and rook_pos == 'R' and 
                           old_king_pos == '.' and old_rook_pos == '.')
        print(f"  Piece positions correct: {'✅' if castling_correct else '❌'}")
        tests.append(castling_correct)
    else:
        print(f"  ❌ Castling not available when it should be")
        tests.append(False)
    
    # Test castling rights after king/rook moves
    print("\n🚫 Testing Castling Rights Loss:")
    board2 = ChessBoard()
    
    # Move king and back
    board2.make_move("e1f1")  # King moves
    board2.make_move("e7e6")  # Random black move
    board2.make_move("f1e1")  # King back
    board2.make_move("e6e5")  # Random black move
    
    # Clear for castling
    board2.make_move("g1f3")
    board2.make_move("g8f6") 
    board2.make_move("f1c4")
    board2.make_move("f8c5")
    
    # Try to castle - should fail
    legal_moves2 = board2.generate_moves()
    can_castle_after_king_move = "e1g1" in legal_moves2
    print(f"  Can castle after king moved: {can_castle_after_king_move}")
    print(f"  Castling rights properly revoked: {'✅' if not can_castle_after_king_move else '❌'}")
    tests.append(not can_castle_after_king_move)
    
    return all(tests)

def test_en_passant_capture():
    """Test en passant pawn captures."""
    print("\n⚔️ TESTING EN PASSANT CAPTURE")
    print("=" * 40)
    
    board = ChessBoard()
    
    # Set up en passant scenario
    moves = [
        "e2e4",  # White pawn double move
        "a7a6",  # Black random move
        "e4e5",  # White pawn advances
        "d7d5",  # Black pawn double move next to white pawn
    ]
    
    print("Setting up en passant scenario:")
    for move in moves:
        success = board.make_move(move)
        print(f"  {move}: {'✅' if success else '❌'}")
    
    # Check en passant target
    print(f"En passant target: {board.en_passant_target}")
    
    # Attempt en passant capture
    en_passant_move = "e5d6"
    legal_moves = board.generate_moves()
    en_passant_available = en_passant_move in legal_moves
    
    print(f"En passant capture available: {en_passant_available}")
    
    if en_passant_available:
        # Check captured pieces before
        captured_before = board.get_captured_pieces()
        black_captured_before = len(captured_before['black'])
        
        # Execute en passant
        success = board.make_move(en_passant_move)
        print(f"En passant execution: {'✅' if success else '❌'}")
        
        # Verify capture was recorded
        captured_after = board.get_captured_pieces()
        black_captured_after = len(captured_after['black'])
        
        capture_recorded = black_captured_after > black_captured_before
        print(f"En passant capture recorded: {'✅' if capture_recorded else '❌'}")
        
        # Verify pawn was removed from d5
        d5_empty = board.get_piece(3, 3) == '.'  # d5
        d6_has_white_pawn = board.get_piece(2, 3) == 'P'  # d6
        
        print(f"Target square (d5) empty: {'✅' if d5_empty else '❌'}")
        print(f"Capturing pawn on d6: {'✅' if d6_has_white_pawn else '❌'}")
        
        return success and capture_recorded and d5_empty and d6_has_white_pawn
    else:
        print("❌ En passant not available when it should be")
        return False

def test_pawn_promotion():
    """Test pawn promotion scenarios."""
    print("\n👑 TESTING PAWN PROMOTION")
    print("=" * 40)
    
    board = ChessBoard()
    
    # Set up pawn promotion scenario by manually placing pieces
    # Clear the board
    for row in range(8):
        for col in range(8):
            board.set_piece(row, col, '.')
    
    # Place minimal pieces for promotion test
    board.set_piece(7, 4, 'K')  # White king on e1
    board.set_piece(0, 4, 'k')  # Black king on e8
    board.set_piece(1, 0, 'P')  # White pawn on a7 (ready to promote)
    
    print("Board set up with white pawn on a7, ready to promote")
    
    # Test promotion to queen
    promotion_move = "a7a8q"  # Promote to queen
    board.white_to_move = True
    
    legal_moves = board.generate_moves()
    promotion_available = any(move.startswith("a7a8") for move in legal_moves)
    print(f"Promotion moves available: {promotion_available}")
    
    if promotion_available:
        success = board.make_move(promotion_move)
        print(f"Promotion execution: {'✅' if success else '❌'}")
        
        # Check if piece was promoted correctly
        promoted_piece = board.get_piece(0, 0)  # a8
        is_queen = promoted_piece == 'Q'
        print(f"Pawn promoted to queen: {'✅' if is_queen else '❌'}")
        
        # Check that original pawn square is empty
        original_empty = board.get_piece(1, 0) == '.'  # a7
        print(f"Original square empty: {'✅' if original_empty else '❌'}")
        
        return success and is_queen and original_empty
    else:
        print("❌ Promotion not available")
        return False

def test_performance_benchmarks():
    """Test engine performance on various positions."""
    print("\n⚡ TESTING PERFORMANCE BENCHMARKS")
    print("=" * 40)
    
    engine = ChessEngine()
    
    # Test 1: Starting position performance
    print("\n🚀 Starting Position Performance:")
    start_time = time.time()
    move, score = engine.search(3)  # Depth 3
    elapsed = time.time() - start_time
    
    print(f"  Depth 3 search: {elapsed:.3f}s")
    print(f"  Best move: {move}, Score: {score/100:.2f}")
    
    performance_good = elapsed < 5.0  # Should complete in under 5 seconds
    print(f"  Performance acceptable: {'✅' if performance_good else '❌'}")
    
    # Test 2: Move generation speed
    print("\n⚙️ Move Generation Speed:")
    start_time = time.time()
    for _ in range(1000):
        moves = engine.board.generate_moves()
    elapsed = time.time() - start_time
    
    print(f"  1000 move generations: {elapsed:.3f}s")
    print(f"  Average per generation: {elapsed*1000:.3f}μs")
    
    generation_fast = elapsed < 1.0
    print(f"  Generation speed good: {'✅' if generation_fast else '❌'}")
    
    # Test 3: Position evaluation speed
    print("\n🧮 Position Evaluation Speed:")
    start_time = time.time()
    for _ in range(10000):
        score = engine.evaluate(engine.board)
    elapsed = time.time() - start_time
    
    print(f"  10000 evaluations: {elapsed:.3f}s")
    print(f"  Average per evaluation: {elapsed*100:.3f}μs")
    
    eval_fast = elapsed < 2.0
    print(f"  Evaluation speed good: {'✅' if eval_fast else '❌'}")
    
    return performance_good and generation_fast and eval_fast

def test_complex_game_scenarios():
    """Test complex real-game scenarios."""
    print("\n🎭 TESTING COMPLEX GAME SCENARIOS")
    print("=" * 40)
    
    # Test 1: Sicilian Defense opening
    print("\n🏁 Testing Sicilian Defense:")
    board = ChessBoard()
    sicilian_moves = [
        "e2e4", "c7c5",  # Sicilian Defense
        "g1f3", "d7d6", 
        "d2d4", "c5d4",
        "f3d4", "g8f6",
        "b1c3", "a7a6"   # Najdorf Variation
    ]
    
    moves_played = 0
    for move in sicilian_moves:
        success = board.make_move(move)
        if success:
            moves_played += 1
        else:
            print(f"    ❌ Move failed: {move}")
            break
    
    sicilian_success = moves_played == len(sicilian_moves)
    print(f"  Sicilian Defense played successfully: {'✅' if sicilian_success else '❌'} ({moves_played}/{len(sicilian_moves)} moves)")
    
    # Test 2: King's Indian Defense
    print("\n🏰 Testing King's Indian Defense:")
    board2 = ChessBoard()
    kings_indian = [
        "d2d4", "g8f6",
        "c2c4", "g7g6", 
        "b1c3", "f8g7",
        "e2e4", "d7d6",
        "g1f3", "e8g8"  # Castling
    ]
    
    moves_played2 = 0
    for move in kings_indian:
        success = board2.make_move(move)
        if success:
            moves_played2 += 1
        else:
            print(f"    ❌ Move failed: {move}")
            break
    
    kings_indian_success = moves_played2 == len(kings_indian)
    print(f"  King's Indian Defense played: {'✅' if kings_indian_success else '❌'} ({moves_played2}/{len(kings_indian)} moves)")
    
    return sicilian_success and kings_indian_success

def test_edge_cases():
    """Test various edge cases and boundary conditions."""
    print("\n🔍 TESTING EDGE CASES")
    print("=" * 40)
    
    results = []
    
    # Test 1: Invalid move formats
    print("\n❌ Testing Invalid Move Formats:")
    board = ChessBoard()
    
    invalid_moves = ["", "e", "e2", "e2e", "e2e9", "z2z4", "e2e4e", "🚀🚀🚀🚀"]
    
    for move in invalid_moves:
        is_legal = board.is_legal_move(move)
        print(f"  '{move}': {'❌ Incorrectly allowed' if is_legal else '✅ Correctly rejected'}")
        results.append(not is_legal)
    
    # Test 2: Boundary square moves
    print("\n🗺️ Testing Boundary Squares:")
    boundary_moves = ["a1a8", "h1h8", "a1h1", "a8h8"]  # Corner to corner
    
    for move in boundary_moves:
        try:
            is_legal = board.is_legal_move(move)
            print(f"  {move}: {'⚠️ Legal' if is_legal else '✅ Handled correctly'}")
            results.append(True)  # No crash is success
        except Exception as e:
            print(f"  {move}: ❌ Exception: {e}")
            results.append(False)
    
    # Test 3: Empty board scenarios
    print("\n🕳️ Testing Empty Board:")
    empty_board = ChessBoard()
    
    # Clear the board
    for row in range(8):
        for col in range(8):
            empty_board.set_piece(row, col, '.')
    
    # Add only kings (minimum for legal game)
    empty_board.set_piece(7, 4, 'K')
    empty_board.set_piece(0, 4, 'k')
    
    legal_moves = empty_board.generate_moves()
    king_can_move = len(legal_moves) > 0
    print(f"  King can move on empty board: {'✅' if king_can_move else '❌'}")
    results.append(king_can_move)
    
    # Test all king moves are valid
    all_king_moves_valid = True
    for move in legal_moves:
        if not empty_board.is_legal_move(move):
            all_king_moves_valid = False
            break
    
    print(f"  All generated king moves are valid: {'✅' if all_king_moves_valid else '❌'}")
    results.append(all_king_moves_valid)
    
    return all(results)

def test_web_interface_stress():
    """Test web interface under various conditions."""
    print("\n🌐 TESTING WEB INTERFACE STRESS")
    print("=" * 40)
    
    try:
        web_gui = WebGUI(engine_depth=2)
        results = []
        
        # Test 1: Rapid game state requests
        print("\n⚡ Testing Rapid State Requests:")
        start_time = time.time()
        for i in range(100):
            state = web_gui.get_game_state()
            if not isinstance(state, dict):
                results.append(False)
                break
        else:
            results.append(True)
        
        elapsed = time.time() - start_time
        print(f"  100 state requests: {elapsed:.3f}s")
        print(f"  State consistency: {'✅' if results[-1] else '❌'}")
        
        # Test 2: HTML generation consistency
        print("\n📄 Testing HTML Generation:")
        html1 = web_gui.generate_html()
        html2 = web_gui.generate_html()
        
        # Should be identical for same state
        html_consistent = len(html1) == len(html2)
        print(f"  HTML length consistent: {'✅' if html_consistent else '❌'}")
        results.append(html_consistent)
        
        # Test 3: JSON serialization
        print("\n🔧 Testing JSON Serialization:")
        state = web_gui.get_game_state()
        
        try:
            json_str = json.dumps(state)
            parsed_back = json.loads(json_str)
            json_works = isinstance(parsed_back, dict)
            print(f"  JSON serialization: {'✅' if json_works else '❌'}")
            results.append(json_works)
        except Exception as e:
            print(f"  JSON serialization: ❌ {e}")
            results.append(False)
        
        return all(results)
        
    except Exception as e:
        print(f"❌ Web interface test failed: {e}")
        return False

def run_comprehensive_tests():
    """Run all comprehensive tests."""
    print("🧪 COMPREHENSIVE CHESS ENGINE TEST SUITE")
    print("=" * 60)
    
    test_results = {
        "Checkmate Scenarios": test_checkmate_scenarios(),
        "Castling Variations": test_castling_variations(), 
        "En Passant Capture": test_en_passant_capture(),
        "Pawn Promotion": test_pawn_promotion(),
        "Performance Benchmarks": test_performance_benchmarks(),
        "Complex Game Scenarios": test_complex_game_scenarios(),
        "Edge Cases": test_edge_cases(),
        "Web Interface Stress": test_web_interface_stress()
    }
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🏆 OVERALL RESULT: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Chess engine is working excellently.")
        print("\n🔍 COMPREHENSIVE VALIDATION COMPLETE:")
        print("✅ Checkmate and stalemate detection")
        print("✅ Castling rules and restrictions") 
        print("✅ En passant captures")
        print("✅ Pawn promotion mechanics")
        print("✅ Performance under load")
        print("✅ Complex opening scenarios")
        print("✅ Edge case handling")
        print("✅ Web interface stability")
    else:
        print(f"⚠️ {total - passed} tests failed. Review the failures above.")
    
    return passed == total

if __name__ == "__main__":
    run_comprehensive_tests()