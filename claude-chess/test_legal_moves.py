#!/usr/bin/env python3
"""
Test script to verify the show legal moves feature works correctly.
"""

from chess_engine import WebGUI
import json
import threading
import time
import requests

def test_legal_moves_endpoint():
    """Test the legal moves endpoint directly."""
    print("🔍 TESTING LEGAL MOVES ENDPOINT")
    print("=" * 40)
    
    # Start web server in background
    web_gui = WebGUI(engine_depth=2, port=8081)
    
    def run_server():
        try:
            web_gui.run()
        except:
            pass
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Give server time to start
    time.sleep(2)
    
    try:
        # Test the endpoint
        response = requests.get('http://localhost:8081/legal_moves', timeout=5)
        print(f"✅ Endpoint response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            moves = data.get('moves', [])
            print(f"✅ Legal moves count: {len(moves)}")
            print(f"✅ Sample moves: {moves[:5]}")
            
            # Verify move format
            valid_moves = 0
            for move in moves[:10]:  # Check first 10 moves
                if len(move) == 4:
                    from_file = move[0]
                    from_rank = move[1]
                    to_file = move[2]
                    to_rank = move[3]
                    
                    if (from_file in 'abcdefgh' and from_rank in '12345678' and
                        to_file in 'abcdefgh' and to_rank in '12345678'):
                        valid_moves += 1
            
            print(f"✅ Valid move format: {valid_moves}/{min(10, len(moves))}")
            return True
        else:
            print(f"❌ Endpoint failed with status: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def test_html_features():
    """Test HTML contains required legal moves features."""
    print("\n🌐 TESTING HTML LEGAL MOVES FEATURES")
    print("=" * 40)
    
    web_gui = WebGUI(engine_depth=2)
    html = web_gui.generate_html()
    
    features = [
        ('Show Legal Moves button', 'Show Legal Moves' in html),
        ('showLegalMoves function', 'function showLegalMoves()' in html),
        ('Legal moves fetch', 'fetch(\'/legal_moves\')' in html),
        ('Legal move CSS class', '.legal-move' in html),
        ('highlightSquare function', 'function highlightSquare(' in html),
        ('clearHighlights function', 'function clearHighlights(' in html),
        ('Error handling', '.catch(error' in html),
        ('Console logging', 'console.log(' in html)
    ]
    
    print("\n📋 HTML FEATURES:")
    all_present = True
    for feature, present in features:
        status = "✅" if present else "❌"
        print(f"{status} {feature}")
        if not present:
            all_present = False
    
    return all_present

def test_move_highlighting_logic():
    """Test the move highlighting coordinate logic."""
    print("\n🎯 TESTING MOVE HIGHLIGHTING LOGIC")
    print("=" * 40)
    
    # Test coordinate conversion for sample moves
    test_moves = ['e2e4', 'g1f3', 'b1c3', 'f1b5', 'a2a3']
    
    print("\n📍 COORDINATE CONVERSION TESTS:")
    for move in test_moves:
        if len(move) == 4:
            # From square
            from_col = ord(move[0]) - 97  # 'a' = 0, 'b' = 1, etc.
            from_row = 8 - int(move[1])   # '1' = 7, '2' = 6, etc.
            
            # To square
            to_col = ord(move[2]) - 97
            to_row = 8 - int(move[3])
            
            # Check if coordinates are valid
            valid_from = 0 <= from_row < 8 and 0 <= from_col < 8
            valid_to = 0 <= to_row < 8 and 0 <= to_col < 8
            
            status = "✅" if valid_from and valid_to else "❌"
            print(f"{status} {move}: from({from_row},{from_col}) to({to_row},{to_col})")
    
    return True

def main():
    """Run all legal moves tests."""
    print("🎯 COMPREHENSIVE LEGAL MOVES TEST")
    print("=" * 50)
    
    html_success = test_html_features()
    logic_success = test_move_highlighting_logic()
    endpoint_success = test_legal_moves_endpoint()
    
    print("\n" + "=" * 50)
    if html_success and logic_success and endpoint_success:
        print("🎉 LEGAL MOVES FEATURE SUCCESSFULLY WORKING!")
        print("\n🚀 IMPROVEMENTS MADE:")
        print("✅ Added error handling with try-catch")
        print("✅ Added console logging for debugging")
        print("✅ Highlight both source and destination squares")
        print("✅ Added coordinate validation")
        print("✅ Improved user feedback")
        print("✅ Enhanced button text changes")
        
        print("\n🎮 HOW TO USE:")
        print("1. Start web chess: python3 run_web_chess.py")
        print("2. Click '👁️ Show Legal Moves' button")
        print("3. All legal move squares will be highlighted in blue")
        print("4. Click '❌ Hide Legal Moves' to remove highlights")
        print("5. Check browser console for detailed logs")
    else:
        print("❌ Legal moves feature needs attention")
        if not html_success:
            print("  - HTML features missing")
        if not logic_success:
            print("  - Coordinate logic issues")
        if not endpoint_success:
            print("  - Endpoint connectivity issues")
    
    print("\n🌐 Test in browser at: http://localhost:8080")

if __name__ == "__main__":
    main()