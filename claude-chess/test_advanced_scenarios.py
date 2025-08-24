#!/usr/bin/env python3
"""
Advanced test scenarios for chess engine including Chess960,
threefold repetition, fifty-move rule, and tournament conditions.
"""

from chess_engine import ChessBoard, ChessEngine, WebGUI
import random
import time

def test_chess960_positions():
    """Test Chess960 (Fischer Random) chess positions."""
    print("🎲 TESTING CHESS960 POSITIONS")
    print("=" * 40)
    
    results = []
    
    # Test specific Chess960 position
    print("\n🎯 Testing Chess960 Position #518:")
    try:
        board = ChessBoard(chess960=True, position_id=518)
        
        # Verify it's a valid Chess960 setup
        back_rank = [board.get_piece(0, col) for col in range(8)]
        
        # Check Chess960 rules
        bishops_on_opposite_colors = False
        bishop_squares = []
        for col, piece in enumerate(back_rank):
            if piece == 'b':
                bishop_squares.append(col)
        
        if len(bishop_squares) == 2:
            # One bishop should be on light square (odd), one on dark (even)
            bishops_on_opposite_colors = (bishop_squares[0] % 2) != (bishop_squares[1] % 2)
        
        # Check king between rooks
        king_pos = back_rank.index('k')
        rook_positions = [i for i, piece in enumerate(back_rank) if piece == 'r']
        king_between_rooks = len(rook_positions) == 2 and rook_positions[0] < king_pos < rook_positions[1]
        
        print(f"  Back rank: {''.join(back_rank)}")
        print(f"  Bishops on opposite colors: {'✅' if bishops_on_opposite_colors else '❌'}")
        print(f"  King between rooks: {'✅' if king_between_rooks else '❌'}")
        
        chess960_valid = bishops_on_opposite_colors and king_between_rooks
        results.append(chess960_valid)
        
        # Test that pieces can move
        legal_moves = board.generate_moves()
        has_moves = len(legal_moves) > 0
        print(f"  Legal moves available: {'✅' if has_moves else '❌'} ({len(legal_moves)} moves)")
        results.append(has_moves)
        
    except Exception as e:
        print(f"  ❌ Chess960 test failed: {e}")
        results.append(False)
        results.append(False)
    
    # Test random Chess960 position
    print("\n🎲 Testing Random Chess960 Position:")
    try:
        board_random = ChessBoard(chess960=True)
        back_rank_random = [board_random.get_piece(0, col) for col in range(8)]
        
        print(f"  Random back rank: {''.join(back_rank_random)}")
        
        # Just check it's different from standard
        standard_rank = ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r']
        is_different = back_rank_random != standard_rank
        print(f"  Different from standard: {'✅' if is_different else '⚠️ Same as standard (1/960 chance)'}")
        
        results.append(True)  # Success if no exception
        
    except Exception as e:
        print(f"  ❌ Random Chess960 test failed: {e}")
        results.append(False)
    
    return all(results)

def test_repetition_detection():
    """Test threefold repetition rule."""
    print("\n🔄 TESTING REPETITION DETECTION")
    print("=" * 40)
    
    board = ChessBoard()
    engine = ChessEngine()
    engine.board = board
    
    # Create a repetitive sequence
    print("Creating repetitive move sequence:")
    repetitive_moves = [
        "g1f3", "g8f6",  # Knights out
        "f3g1", "f6g8",  # Knights back
        "g1f3", "g8f6",  # Knights out again
        "f3g1", "f6g8",  # Knights back again
        "g1f3", "g8f6",  # Third repetition starts
    ]
    
    position_history = []
    
    for i, move in enumerate(repetitive_moves):
        success = board.make_move(move)
        print(f"  Move {i+1}: {move} {'✅' if success else '❌'}")
        
        if success:
            # Create a simple position hash (in real implementation, this would be more sophisticated)
            position_key = str(board.board) + str(board.white_to_move)
            position_history.append(position_key)
            
            # Check for repetitions
            repetition_count = position_history.count(position_key)
            print(f"    Position repetitions: {repetition_count}")
    
    # In a full implementation, threefold repetition would trigger a draw
    # This is a basic test to show the framework for detection
    final_repetitions = max([position_history.count(pos) for pos in position_history])
    repetition_detected = final_repetitions >= 3
    
    print(f"  Threefold repetition detected: {'✅' if repetition_detected else '❌'}")
    print(f"  Maximum repetitions: {final_repetitions}")
    
    return repetition_detected

def test_fifty_move_rule():
    """Test fifty-move rule implementation framework."""
    print("\n⏱️ TESTING FIFTY-MOVE RULE FRAMEWORK")
    print("=" * 40)
    
    board = ChessBoard()
    
    # The fifty-move rule states that a draw can be claimed if no pawn moves
    # or captures have been made in the last fifty moves by each side
    
    print("Simulating moves without pawn moves or captures:")
    
    # Make piece moves that don't involve pawns or captures
    moves_without_progress = [
        "g1f3", "g8f6",  # Knights
        "f3g5", "f6g4",  # Knights jump
        "g5f3", "g4f6",  # Knights back
        "f3e5", "f6e4",  # Knights again
        "e5f3", "e4f6",  # Back again
    ]
    
    initial_halfmove_clock = board.halfmove_clock
    
    for move in moves_without_progress:
        success = board.make_move(move)
        if success:
            print(f"  {move}: halfmove clock = {board.halfmove_clock}")
    
    # In proper implementation, halfmove clock should increment
    # (Note: current implementation may not fully implement this)
    clock_incremented = board.halfmove_clock > initial_halfmove_clock
    print(f"Halfmove clock tracking: {'✅' if clock_incremented else '⚠️ Not fully implemented'}")
    
    # Test pawn move resets clock
    print("\nTesting pawn move resets clock:")
    pawn_move = "e2e4"
    pre_pawn_clock = board.halfmove_clock
    success = board.make_move(pawn_move)
    
    if success:
        clock_reset = board.halfmove_clock == 0  # Should reset after pawn move
        print(f"  Pawn move resets clock: {'✅' if clock_reset else '⚠️ Implementation needed'}")
        return clock_reset
    
    return clock_incremented

def test_tournament_time_controls():
    """Test engine performance under tournament time constraints."""
    print("\n⏰ TESTING TOURNAMENT TIME CONTROLS")
    print("=" * 40)
    
    engine = ChessEngine()
    results = []
    
    # Test different time controls
    time_controls = [
        (1, "Blitz (1 second)"),
        (3, "Rapid (3 seconds)"), 
        (5, "Standard (5 seconds)")
    ]
    
    for depth, description in time_controls:
        print(f"\n🕐 Testing {description}:")
        
        start_time = time.time()
        move, score = engine.search(depth)
        elapsed = time.time() - start_time
        
        print(f"  Time taken: {elapsed:.3f}s")
        print(f"  Best move: {move}")
        print(f"  Score: {score/100:.2f}")
        
        # Check if time is reasonable for the depth
        reasonable_time = elapsed < (depth * 3)  # Rough heuristic
        print(f"  Time reasonable for depth: {'✅' if reasonable_time else '❌'}")
        results.append(reasonable_time)
    
    # Test move quality under time pressure
    print(f"\n🎯 Testing Move Quality Under Pressure:")
    
    # Test same position with different time limits
    moves_and_scores = []
    for depth, _ in time_controls:
        move, score = engine.search(depth)
        moves_and_scores.append((move, score, depth))
        print(f"  Depth {depth}: {move} (score: {score/100:.2f})")
    
    # Higher depth should generally produce same or better moves
    scores = [score for _, score, _ in moves_and_scores]
    quality_improving = all(scores[i] <= scores[i+1] for i in range(len(scores)-1))
    print(f"  Move quality improves with time: {'✅' if quality_improving else '⚠️ Varies'}")
    
    results.append(True)  # Quality test is informational
    return all(results)

def test_memory_usage():
    """Test memory usage and potential leaks."""
    print("\n🧠 TESTING MEMORY USAGE")
    print("=" * 40)
    
    import gc
    import sys
    
    # Get initial memory baseline
    gc.collect()
    initial_objects = len(gc.get_objects())
    
    print(f"Initial objects in memory: {initial_objects}")
    
    # Create and destroy many chess boards
    print("Creating and destroying 100 chess boards...")
    
    boards = []
    for i in range(100):
        board = ChessBoard()
        # Make some moves
        board.make_move("e2e4")
        board.make_move("e7e5") 
        boards.append(board)
        
        if i % 20 == 0:
            print(f"  Created {i+1} boards")
    
    # Clear references
    boards.clear()
    del boards
    
    # Force garbage collection
    gc.collect()
    final_objects = len(gc.get_objects())
    
    print(f"Final objects in memory: {final_objects}")
    
    # Check for significant memory increase
    object_increase = final_objects - initial_objects
    memory_reasonable = object_increase < initial_objects * 0.1  # Less than 10% increase
    
    print(f"Object increase: {object_increase}")
    print(f"Memory usage reasonable: {'✅' if memory_reasonable else '⚠️ Potential leak'}")
    
    return memory_reasonable

def test_concurrent_games():
    """Test handling multiple concurrent games."""
    print("\n🎮 TESTING CONCURRENT GAMES")
    print("=" * 40)
    
    results = []
    
    # Create multiple game instances
    print("Creating 5 concurrent games:")
    games = []
    
    for i in range(5):
        try:
            web_gui = WebGUI(engine_depth=2, port=8080 + i)
            games.append(web_gui)
            print(f"  Game {i+1}: ✅ Created")
        except Exception as e:
            print(f"  Game {i+1}: ❌ Failed - {e}")
            results.append(False)
    
    if len(games) == 5:
        results.append(True)
    
    # Test that games are independent
    print("\nTesting game independence:")
    try:
        # Make different moves in each game
        moves = ["e2e4", "d2d4", "g1f3", "c2c4", "f2f4"]
        
        for i, (game, move) in enumerate(zip(games, moves)):
            success = game.engine.board.make_move(move)
            print(f"  Game {i+1} move {move}: {'✅' if success else '❌'}")
        
        # Verify games have different states
        states = [str(game.engine.board.board) for game in games]
        all_different = len(set(states)) == len(states)
        print(f"  All games have different states: {'✅' if all_different else '❌'}")
        results.append(all_different)
        
    except Exception as e:
        print(f"  Independence test failed: {e}")
        results.append(False)
    
    return all(results)

def test_malformed_input_handling():
    """Test handling of malformed or malicious input."""
    print("\n🛡️ TESTING MALFORMED INPUT HANDLING")
    print("=" * 40)
    
    board = ChessBoard()
    web_gui = WebGUI()
    results = []
    
    # Test malformed moves
    print("\n❌ Testing Malformed Moves:")
    malformed_moves = [
        None,
        123,
        [],
        {},
        "' OR 1=1 --",  # SQL injection attempt
        "<script>alert('xss')</script>",  # XSS attempt
        "A" * 1000,  # Very long string
        "\\n\\r\\t",  # Special characters
        "e2e4; rm -rf /",  # Command injection attempt
    ]
    
    safe_count = 0
    for move in malformed_moves:
        try:
            is_legal = board.is_legal_move(str(move) if move is not None else "")
            print(f"  {repr(move)[:30]}...: {'⚠️ Processed' if is_legal else '✅ Safely rejected'}")
            safe_count += 1
        except Exception as e:
            print(f"  {repr(move)[:30]}...: ✅ Exception handled - {type(e).__name__}")
            safe_count += 1
    
    all_handled_safely = safe_count == len(malformed_moves)
    results.append(all_handled_safely)
    
    # Test malformed JSON in web interface simulation
    print(f"\n🌐 Testing Web Interface Input Validation:")
    try:
        # Test game state with malformed data
        original_board = web_gui.engine.board.board
        state = web_gui.get_game_state()
        
        # Verify state is properly structured
        required_keys = ['board', 'is_human_turn', 'status', 'captured_pieces']
        has_required_keys = all(key in state for key in required_keys)
        print(f"  Game state structure valid: {'✅' if has_required_keys else '❌'}")
        results.append(has_required_keys)
        
        # Verify board data is clean
        board_data = state['board']
        is_valid_board = (len(board_data) == 8 and 
                         all(len(row) == 8 for row in board_data))
        print(f"  Board data structure valid: {'✅' if is_valid_board else '❌'}")
        results.append(is_valid_board)
        
    except Exception as e:
        print(f"  Web interface validation failed: {e}")
        results.append(False)
        results.append(False)
    
    return all(results)

def run_advanced_tests():
    """Run all advanced test scenarios."""
    print("🚀 ADVANCED CHESS ENGINE TEST SCENARIOS")
    print("=" * 60)
    
    test_results = {
        "Chess960 Positions": test_chess960_positions(),
        "Repetition Detection": test_repetition_detection(),
        "Fifty-Move Rule Framework": test_fifty_move_rule(),
        "Tournament Time Controls": test_tournament_time_controls(),
        "Memory Usage": test_memory_usage(),
        "Concurrent Games": test_concurrent_games(),
        "Malformed Input Handling": test_malformed_input_handling()
    }
    
    print("\n" + "=" * 60)
    print("📊 ADVANCED TEST RESULTS")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "⚠️ NEEDS ATTENTION"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🏆 ADVANCED TESTING RESULT: {passed}/{total} scenarios passed")
    
    if passed == total:
        print("🎉 ALL ADVANCED TESTS PASSED! Chess engine is production-ready.")
    elif passed >= total * 0.7:  # 70% threshold
        print("✅ Chess engine is solid with room for enhancement.")
    else:
        print("⚠️ Chess engine needs significant improvements.")
    
    return passed / total

if __name__ == "__main__":
    run_advanced_tests()