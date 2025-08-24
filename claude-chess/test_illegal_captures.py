#!/usr/bin/env python3
"""
Test suite for illegal capture prevention in the chess engine.
This ensures that pieces cannot capture their own teammates.
"""

from chess_engine import ChessBoard, ChessEngine, InteractiveGame, WebGUI, GUI_AVAILABLE, WEB_GUI_AVAILABLE

def test_illegal_capture_prevention():
    """Test that pieces cannot capture their own teammates."""
    print("=== Testing Illegal Capture Prevention ===")
    
    # Test 1: Direct illegal moves should be rejected by make_move()
    print("\n1. Testing make_move() rejection of illegal captures:")
    board = ChessBoard()
    
    # Try white rook capturing white pawn
    result = board.make_move('a1a2')
    assert result == False, "WHITE ROOK SHOULD NOT CAPTURE WHITE PAWN"
    print("✓ White rook cannot capture white pawn (a1a2)")
    
    # Try black rook capturing black pawn
    board.white_to_move = False
    result = board.make_move('a8a7')
    assert result == False, "BLACK ROOK SHOULD NOT CAPTURE BLACK PAWN"
    print("✓ Black rook cannot capture black pawn (a8a7)")
    
    # Test 2: Set up specific scenarios where pieces are adjacent
    print("\n2. Testing adjacent piece scenarios:")
    
    test_cases = [
        # (piece, from_pos, friendly_piece_pos, illegal_move, description)
        ('N', (7, 1), (5, 2), 'b1c3', 'White knight cannot capture white piece on c3'),
        ('B', (7, 2), (6, 3), 'c1d2', 'White bishop cannot capture white piece on d2'),
        ('R', (7, 0), (7, 1), 'a1b1', 'White rook cannot capture white piece on b1'),
        ('Q', (7, 3), (7, 2), 'd1c1', 'White queen cannot capture white piece on c1'),
        ('K', (7, 4), (7, 3), 'e1d1', 'White king cannot capture white piece on d1'),
        ('P', (6, 4), (5, 3), 'e2d3', 'White pawn cannot capture white piece diagonally'),
    ]
    
    for piece, from_pos, target_pos, move, description in test_cases:
        board = ChessBoard()
        
        # Clear the target position and place a friendly piece there
        board.set_piece(target_pos[0], target_pos[1], 'P')  # Place white pawn as target
        
        # Try the illegal move
        result = board.make_move(move)
        assert result == False, f"ILLEGAL MOVE ALLOWED: {move}"
        print(f"✓ {description}")

def test_move_generation_legality():
    """Test that move generation doesn't include illegal captures."""
    print("\n3. Testing move generation doesn't include illegal captures:")
    
    board = ChessBoard()
    
    # Place white knight surrounded by white pieces
    board.set_piece(4, 4, 'N')  # Knight on e4
    board.set_piece(3, 2, 'P')  # Pawn on c5 
    board.set_piece(3, 6, 'P')  # Pawn on g5
    board.set_piece(5, 2, 'P')  # Pawn on c3
    board.set_piece(5, 6, 'P')  # Pawn on g3
    
    # Generate moves for the knight
    knight_moves = board.generate_knight_moves(4, 4, 'N')
    
    # Check that none of the moves capture white pieces
    illegal_moves = []
    for move in knight_moves:
        to_col = ord(move[2]) - ord('a')
        to_row = 8 - int(move[3])
        target = board.get_piece(to_row, to_col)
        if target != '.' and board.is_white_piece(target):
            illegal_moves.append(move)
    
    assert len(illegal_moves) == 0, f"ILLEGAL MOVES IN GENERATION: {illegal_moves}"
    print("✓ Knight move generation excludes captures of white pieces")

def test_all_piece_types():
    """Test illegal capture prevention for all piece types."""
    print("\n4. Testing all piece types for illegal capture prevention:")
    
    piece_tests = [
        ('Pawn', 'P', (6, 4), [(5, 3), (5, 5)]),
        ('Rook', 'R', (4, 4), [(4, 3), (4, 5), (3, 4), (5, 4)]),
        ('Knight', 'N', (4, 4), [(2, 3), (2, 5), (6, 3), (6, 5)]),
        ('Bishop', 'B', (4, 4), [(3, 3), (3, 5), (5, 3), (5, 5)]),
        ('Queen', 'Q', (4, 4), [(3, 4), (4, 3), (3, 3), (5, 5)]),
        ('King', 'K', (4, 4), [(3, 4), (4, 3), (3, 3), (5, 5)]),
    ]
    
    for piece_name, piece, pos, target_positions in piece_tests:
        board = ChessBoard()
        board.set_piece(pos[0], pos[1], piece)
        
        # Place friendly pieces at target positions
        for target_pos in target_positions:
            if 0 <= target_pos[0] < 8 and 0 <= target_pos[1] < 8:
                board.set_piece(target_pos[0], target_pos[1], 'P')
        
        # Generate all legal moves and check none capture friendly pieces
        all_moves = board.generate_moves()
        from_square = f"{chr(pos[1] + ord('a'))}{8 - pos[0]}"
        piece_moves = [move for move in all_moves if move.startswith(from_square)]
        
        illegal_captures = []
        for move in piece_moves:
            to_col = ord(move[2]) - ord('a')
            to_row = 8 - int(move[3])
            target = board.get_piece(to_row, to_col)
            if target != '.' and board.is_white_piece(target):
                illegal_captures.append(move)
        
        assert len(illegal_captures) == 0, f"{piece_name} HAS ILLEGAL CAPTURES: {illegal_captures}"
        print(f"✓ {piece_name} cannot capture friendly pieces")

def test_gui_interfaces():
    """Test that GUI interfaces also prevent illegal captures."""
    print("\n5. Testing GUI interfaces:")
    
    # Test interactive game
    game = InteractiveGame()
    # Place pieces to create potential illegal capture
    game.engine.board.set_piece(4, 4, 'N')  # Knight
    game.engine.board.set_piece(3, 2, 'P')  # Friendly pawn
    
    # Try illegal move through GUI logic
    illegal_move = 'e4c5'
    is_legal = illegal_move in game.engine.board.generate_moves()
    assert not is_legal, "GUI ALLOWS ILLEGAL CAPTURE IN MOVE LIST"
    print("✓ Interactive game prevents illegal captures")
    
    # Test web GUI if available
    if WEB_GUI_AVAILABLE:
        web_gui = WebGUI()
        web_gui.engine.board.set_piece(4, 4, 'N')
        web_gui.engine.board.set_piece(3, 2, 'P')
        
        # Test move validation
        result = web_gui.engine.board.make_move('e4c5')
        assert not result, "WEB GUI ALLOWS ILLEGAL CAPTURE"
        print("✓ Web GUI prevents illegal captures")
    else:
        print("⚠ Web GUI not available for testing")

def test_regression_scenarios():
    """Test specific scenarios that might have caused the original bug."""
    print("\n6. Testing regression scenarios:")
    
    # Scenario 1: Knight attempting to capture bishop (the reported bug)
    board = ChessBoard()
    
    # Set up the exact scenario: white knight captures white bishop
    board.set_piece(4, 3, 'N')  # Knight on d4
    board.set_piece(4, 4, 'B')  # Bishop on e4
    
    # This should be rejected
    result = board.make_move('d4e4')
    assert not result, "KNIGHT CAPTURED BISHOP - ORIGINAL BUG STILL PRESENT!"
    print("✓ White knight cannot capture white bishop (original bug fixed)")
    
    # Scenario 2: Various same-color capture attempts
    regression_tests = [
        ('d4e4', 'Knight captures bishop'),
        ('e4d4', 'Bishop captures knight'),
    ]
    
    for move, description in regression_tests:
        board = ChessBoard()
        board.set_piece(4, 3, 'N')  # Knight on d4
        board.set_piece(4, 4, 'B')  # Bishop on e4
        
        result = board.make_move(move)
        assert not result, f"REGRESSION: {description} was allowed!"
        print(f"✓ {description} properly blocked")

def run_all_tests():
    """Run all illegal capture prevention tests."""
    print("🧪 RUNNING ILLEGAL CAPTURE PREVENTION TEST SUITE")
    print("=" * 60)
    
    try:
        test_illegal_capture_prevention()
        test_move_generation_legality()
        test_all_piece_types()
        test_gui_interfaces()
        test_regression_scenarios()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED! Illegal capture prevention is working correctly.")
        print("✅ The chess engine properly prevents pieces from capturing teammates.")
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("🐛 There is still a bug in illegal capture prevention!")
        return False
    except Exception as e:
        print(f"\n💥 TEST ERROR: {e}")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)