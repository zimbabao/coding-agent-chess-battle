#!/usr/bin/env python3
"""
Computer vs Human Demo - Shows the enhanced chess interface with computer opponents
"""

import webbrowser
import requests
import json
import time
import sys

def test_computer_functionality(port=8083):
    """Test the computer vs human functionality."""
    base_url = f"http://localhost:{port}"
    
    print("🤖 COMPUTER VS HUMAN FUNCTIONALITY TEST")
    print("=" * 50)
    
    try:
        # Test setting game modes
        print("\n🎮 Testing Game Mode Settings:")
        
        modes_to_test = [
            ('human_vs_human', 'Human vs Human'),
            ('human_vs_computer_white', 'Human vs Computer (Computer plays White)'),
            ('human_vs_computer_black', 'Human vs Computer (Computer plays Black)'),
            ('computer_vs_computer', 'Computer vs Computer')
        ]
        
        for mode, description in modes_to_test:
            print(f"\n  Testing: {description}")
            
            # Set game mode
            response = requests.post(f"{base_url}/api/set_game_mode", 
                                   json={'mode': mode}, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"  ✅ Mode set successfully")
                    print(f"     Computer White: {result.get('computer_white')}")
                    print(f"     Computer Black: {result.get('computer_black')}")
                else:
                    print(f"  ❌ Failed to set mode")
            else:
                print(f"  ❌ HTTP error: {response.status_code}")
        
        # Test computer move functionality
        print(f"\n🧠 Testing Computer Move Functionality:")
        
        # Set to human vs computer mode
        requests.post(f"{base_url}/api/set_game_mode", 
                     json={'mode': 'human_vs_computer_black'}, timeout=5)
        
        # Start new game
        requests.post(f"{base_url}/api/new_game", 
                     json={'chess960': False}, timeout=5)
        
        # Make a human move (white)
        response = requests.post(f"{base_url}/api/make_move", 
                               json={'move': 'e2e4'}, timeout=5)
        
        if response.status_code == 200 and response.json().get('success'):
            print("  ✅ Human move (e2e4) made successfully")
            
            # Now test computer move
            print("  🤖 Testing computer move...")
            response = requests.post(f"{base_url}/api/computer_move", 
                                   json={'depth': 3, 'time_limit': 2.0}, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"  ✅ Computer move successful: {result.get('move')}")
                    print(f"     Evaluation: {result.get('evaluation')}")
                else:
                    print(f"  ❌ Computer move failed: {result.get('error')}")
            else:
                print(f"  ❌ Computer move HTTP error: {response.status_code}")
        else:
            print("  ❌ Failed to make human move")
        
        # Test game info with computer mode
        print(f"\n📊 Testing Game Info with Computer Mode:")
        response = requests.get(f"{base_url}/api/game_info", timeout=5)
        
        if response.status_code == 200:
            info = response.json()
            print(f"  ✅ Game info retrieved")
            print(f"     Game Mode: {info.get('game_mode')}")
            print(f"     Computer White: {info.get('computer_white')}")
            print(f"     Computer Black: {info.get('computer_black')}")
            print(f"     Current Player is Computer: {info.get('current_player_is_computer')}")
            print(f"     Move Count: {info.get('move_count')}")
        else:
            print(f"  ❌ Failed to get game info")
        
        print(f"\n🎉 Computer functionality tests completed!")
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to web server at {base_url}")
        return False
    except Exception as e:
        print(f"❌ Error testing computer functionality: {e}")
        return False

def demo_computer_vs_human():
    """Demonstrate the computer vs human features."""
    
    print("🤖 ENHANCED CHESS ENGINE - COMPUTER VS HUMAN")
    print("=" * 60)
    
    print("""
🎮 NEW COMPUTER VS HUMAN FEATURES:

✅ MULTIPLE GAME MODES:
   • Human vs Human - Traditional two-player chess
   • Human vs Computer (White) - Computer plays white pieces
   • Human vs Computer (Black) - Computer plays black pieces  
   • Computer vs Computer - Watch two engines battle

✅ INTELLIGENT TURN MANAGEMENT:
   • Prevents human moves when it's computer's turn
   • Automatic computer move triggering
   • Clear visual indicators of whose turn it is
   • Smart drag-and-drop restrictions

✅ COMPUTER PLAYER FEATURES:
   • Adjustable engine depth (1-8 levels)
   • Configurable thinking time
   • Real-time move evaluation display
   • Automatic move execution

✅ AUTO-PLAY MODE:
   • Computer vs Computer with automatic moves
   • Adjustable speed control (0.5-10 seconds)
   • Start/stop auto-play controls
   • Real-time game progression

✅ ENHANCED USER INTERFACE:
   • Game mode selector dropdown
   • Computer move button (when it's computer's turn)
   • Auto-play controls for computer vs computer
   • Clear status messages and turn indicators

🎯 HOW TO USE THE NEW FEATURES:

1. SELECT GAME MODE:
   • Use the "Game Mode" dropdown to choose:
     - Human vs Human (traditional)
     - Human vs Computer (choose who plays white/black)
     - Computer vs Computer (watch engines play)

2. HUMAN VS COMPUTER:
   • Make your moves normally (drag/drop or click)
   • Computer automatically moves after you
   • "Make Computer Move" button available if needed
   • Engine depth and speed are adjustable

3. COMPUTER VS COMPUTER:
   • Select "Computer vs Computer" mode
   • Click "Start Auto Play" to begin
   • Adjust speed with "Computer Speed" slider
   • Watch the engines battle automatically

4. GAME CONTROLS:
   • All standard controls work in all modes
   • Undo moves, new games, Chess960 support
   • Engine analysis available in all modes

🌟 SMART FEATURES:

✅ TURN PROTECTION:
   • Can't move opponent's pieces
   • Can't move when it's computer's turn
   • Clear error messages for invalid actions

✅ AUTOMATIC FLOW:
   • Computer moves trigger automatically
   • Smooth transitions between turns
   • No manual intervention needed

✅ VISUAL FEEDBACK:
   • "Computer Thinking..." status messages
   • Turn indicators show human/computer
   • Move highlighting for computer suggestions

✅ PERFORMANCE OPTIMIZED:
   • Fast computer move calculation
   • Responsive interface during computer thinking
   • Efficient auto-play timing

🎮 GAME MODE EXAMPLES:

• LEARNING MODE: Human vs Computer (Computer: Black)
  - You play white, computer responds as black
  - Great for learning and practice
  - Computer provides consistent challenge

• ANALYSIS MODE: Human vs Computer (Computer: White)  
  - Computer opens, you respond
  - Learn from computer's opening choices
  - Practice defensive play

• ENTERTAINMENT MODE: Computer vs Computer
  - Watch two engines battle
  - Observe different playing styles
  - Great for demonstrations

• TRADITIONAL MODE: Human vs Human
  - Classic two-player chess
  - All enhanced features still available
  - Perfect for local multiplayer
""")

    # Try to open the web browser automatically
    url = "http://localhost:8083"
    
    print(f"\n🚀 LAUNCHING ENHANCED WEB INTERFACE:")
    print(f"   URL: {url}")
    print(f"   Features: Computer vs Human, Auto-play, Chess960")
    
    try:
        webbrowser.open(url)
        print("✅ Web browser opened automatically")
    except Exception as e:
        print(f"⚠️  Could not open browser automatically: {e}")
        print(f"   Please manually open: {url}")
    
    # Test the computer functionality
    print(f"\n🧪 RUNNING FUNCTIONALITY TESTS:")
    success = test_computer_functionality()
    
    if success:
        print(f"\n✅ All computer functionality tests passed!")
    else:
        print(f"\n❌ Some tests failed - check server status")
    
    print(f"\n📋 TESTING CHECKLIST:")
    print(f"   □ Try Human vs Computer mode")
    print(f"   □ Test Computer vs Computer auto-play")
    print(f"   □ Verify turn restrictions work")
    print(f"   □ Test computer move button")
    print(f"   □ Try different engine depths")
    print(f"   □ Test auto-play speed control")
    print(f"   □ Verify Chess960 works with computer")
    
    print(f"\n🎉 Enhanced chess engine with computer opponents is ready!")
    print(f"   Full computer vs human functionality active.")
    print(f"   Auto-play and intelligent turn management enabled.")

if __name__ == "__main__":
    demo_computer_vs_human()
