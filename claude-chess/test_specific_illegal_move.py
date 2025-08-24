#!/usr/bin/env python3
"""
Test the specific illegal move scenario: e2e4 b8c6 d1h5 e7e5 h5f1
"""

from chess_engine import ChessBoard

def test_specific_scenario():
    """Test the exact move sequence described by the user."""
    print("🎯 TESTING SPECIFIC ILLEGAL MOVE SCENARIO")
    print("=" * 50)
    
    board = ChessBoard()
    
    # Play the exact sequence
    moves = [
        ("e2e4", "White pawn to e4"),
        ("b8c6", "Black knight to c6"),
        ("d1h5", "White queen to h5"),
        ("e7e5", "Black pawn to e5"),
    ]
    
    print("📋 PLAYING MOVE SEQUENCE:")
    for move, description in moves:
        print(f"  {move}: {description}")
        success = board.make_move(move)
        if not success:
            print(f"    ❌ FAILED to make move {move}")
            return False
        else:
            print(f"    ✅ Move made successfully")
    
    # Show board state
    print("\n🏁 BOARD STATE AFTER 4 MOVES:")
    print("Current position should have:")
    print("- White queen on h5")
    print("- White bishop on f1 (original position)")
    print("- Black knight on c6")
    print("- Pawns on e4 (white) and e5 (black)")
    
    # Check what's actually on the board
    queen_pos = None
    bishop_pos = None
    
    for row in range(8):
        for col in range(8):
            piece = board.get_piece(row, col)
            if piece == 'Q':  # White queen
                queen_file = chr(97 + col)
                queen_rank = str(8 - row)
                queen_pos = f"{queen_file}{queen_rank}"
            elif piece == 'B' and row == 7 and col == 5:  # White bishop on f1
                bishop_pos = "f1"
    
    print(f"\n🔍 ACTUAL POSITIONS:")
    print(f"White queen: {queen_pos}")
    print(f"White bishop on f1: {'Present' if bishop_pos else 'MISSING'}")
    
    # Now test the illegal move h5f1
    print(f"\n❌ TESTING ILLEGAL MOVE: h5f1")
    print("This should be illegal because:")
    print("1. Queen on h5 cannot reach f1 in one move")
    print("2. Queen would need to move diagonally through occupied squares")
    print("3. Even if path was clear, h5-f1 is not a valid queen move")
    
    illegal_move = "h5f1"
    
    # Check if this move would be in the queen's legal moves
    queen_moves = board.generate_piece_moves(3, 7, 'Q')  # h5 = row 3, col 7
    print(f"\nQueen legal moves from h5: {queen_moves[:10]}...")
    
    if illegal_move in queen_moves:
        print(f"❌ ERROR: {illegal_move} is in queen's generated moves!")
    else:
        print(f"✅ CORRECT: {illegal_move} is NOT in queen's generated moves")
    
    # Test move validation
    is_legal = board.is_legal_move(illegal_move)
    print(f"\nMove validation result: {'LEGAL' if is_legal else 'ILLEGAL'}")
    
    if is_legal:
        print("❌ CRITICAL ERROR: Illegal move was marked as legal!")
        print("This explains why your bishop was deleted.")
        return False
    else:
        print("✅ CORRECT: Move properly marked as illegal")
    
    # Try to make the illegal move
    print(f"\n🧪 ATTEMPTING TO EXECUTE ILLEGAL MOVE...")
    success = board.make_move(illegal_move)
    
    if success:
        print("❌ CATASTROPHIC ERROR: Illegal move was executed!")
        print("The bishop would have been incorrectly deleted.")
        
        # Check if bishop is gone
        bishop_after = None
        for row in range(8):
            for col in range(8):
                if board.get_piece(row, col) == 'B' and row == 7 and col == 5:
                    bishop_after = "f1"
        
        if not bishop_after:
            print("❌ CONFIRMED: Bishop was incorrectly deleted!")
        
        return False
    else:
        print("✅ SUCCESS: Illegal move was properly rejected!")
        print("Your bishop is safe.")
        
        # Verify bishop is still there
        bishop_still_there = board.get_piece(7, 5) == 'B'
        if bishop_still_there:
            print("✅ CONFIRMED: Bishop still on f1")
        else:
            print("❌ ERROR: Bishop missing even though move was rejected!")
        
        return True

def analyze_queen_movement():
    """Analyze why h5f1 should be illegal."""
    print("\n🔬 ANALYZING QUEEN MOVEMENT h5→f1")
    print("=" * 40)
    
    # Queen on h5 = (3, 7), f1 = (7, 5)
    from_row, from_col = 3, 7  # h5
    to_row, to_col = 7, 5      # f1
    
    row_diff = to_row - from_row    # 7 - 3 = 4
    col_diff = to_col - from_col    # 5 - 7 = -2
    
    print(f"From h5 ({from_row},{from_col}) to f1 ({to_row},{to_col})")
    print(f"Row difference: {row_diff}")
    print(f"Col difference: {col_diff}")
    
    # Check if it's a valid queen move pattern
    is_horizontal = row_diff == 0
    is_vertical = col_diff == 0  
    is_diagonal = abs(row_diff) == abs(col_diff)
    
    print(f"\nMove pattern analysis:")
    print(f"Horizontal (same rank): {is_horizontal}")
    print(f"Vertical (same file): {is_vertical}")
    print(f"Diagonal: {is_diagonal}")
    
    if not (is_horizontal or is_vertical or is_diagonal):
        print("❌ CONCLUSION: This is NOT a valid queen move!")
        print("   Queen can only move horizontally, vertically, or diagonally.")
    else:
        print("✅ Pattern is valid, but path might be blocked")

def main():
    """Run the specific illegal move test."""
    print("🐛 SPECIFIC ILLEGAL MOVE BUG INVESTIGATION")
    print("Sequence: e2e4 b8c6 d1h5 e7e5 h5f1")
    print("=" * 60)
    
    analyze_queen_movement()
    scenario_passed = test_specific_scenario()
    
    print("\n" + "=" * 60)
    if scenario_passed:
        print("✅ ILLEGAL MOVE PROPERLY HANDLED")
        print("Your bishop should be safe from this illegal move.")
    else:
        print("❌ ILLEGAL MOVE BUG CONFIRMED")
        print("This explains why your bishop was deleted.")
        print("The validation system needs further fixes.")
    
    print(f"\n🌐 You can test this at: http://localhost:8080")
    print("Try the exact sequence: e2e4 b8c6 d1h5 e7e5 h5f1")

if __name__ == "__main__":
    main()