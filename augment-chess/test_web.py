#!/usr/bin/env python3
"""
Test the web interface to make sure it's working.
"""

import requests
import json
import time
import sys

def test_web_server(port=8081):
    """Test if the web server is running and responding."""
    base_url = f"http://localhost:{port}"
    
    try:
        # Test if server is running
        print(f"Testing web server at {base_url}...")
        
        # Test main page
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ Main page accessible")
        else:
            print(f"❌ Main page returned status {response.status_code}")
            return False
        
        # Test API endpoints
        print("\nTesting API endpoints...")
        
        # Test board state
        response = requests.get(f"{base_url}/api/board", timeout=5)
        if response.status_code == 200:
            board_data = response.json()
            print("✅ Board API working")
            print(f"   Chess960: {board_data.get('chess960', False)}")
            print(f"   Position ID: {board_data.get('position_id', 'N/A')}")
        else:
            print(f"❌ Board API returned status {response.status_code}")
        
        # Test legal moves
        response = requests.get(f"{base_url}/api/legal_moves", timeout=5)
        if response.status_code == 200:
            moves_data = response.json()
            print(f"✅ Legal moves API working ({len(moves_data.get('legal_moves', []))} moves)")
        else:
            print(f"❌ Legal moves API returned status {response.status_code}")
        
        # Test game info
        response = requests.get(f"{base_url}/api/game_info", timeout=5)
        if response.status_code == 200:
            info_data = response.json()
            print("✅ Game info API working")
            print(f"   Game over: {info_data.get('game_over', False)}")
            print(f"   Evaluation: {info_data.get('evaluation', 'N/A')}")
        else:
            print(f"❌ Game info API returned status {response.status_code}")
        
        # Test Chess960 setup
        print("\nTesting Chess960 functionality...")
        chess960_data = {"position_id": 356}
        response = requests.post(f"{base_url}/api/setup_chess960", 
                               json=chess960_data, timeout=5)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Chess960 setup working")
                print(f"   Set up position {result.get('position_id')}")
            else:
                print("❌ Chess960 setup failed")
        else:
            print(f"❌ Chess960 setup returned status {response.status_code}")
        
        # Test move making
        print("\nTesting move making...")
        move_data = {"move": "e2e4"}
        response = requests.post(f"{base_url}/api/make_move", 
                               json=move_data, timeout=5)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Move making working")
            else:
                print("❌ Move making failed (might be illegal move)")
        else:
            print(f"❌ Move making returned status {response.status_code}")
        
        print(f"\n🎉 Web server is running successfully at {base_url}")
        print("You can now open this URL in your web browser to play chess!")
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to web server at {base_url}")
        print("Make sure the server is running with: python main.py --web --port 8081")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ Web server at {base_url} is not responding (timeout)")
        return False
    except Exception as e:
        print(f"❌ Error testing web server: {e}")
        return False

if __name__ == "__main__":
    port = 8081
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port number")
            sys.exit(1)
    
    print("🌐 CHESS ENGINE WEB INTERFACE TEST")
    print("=" * 40)
    
    success = test_web_server(port)
    sys.exit(0 if success else 1)
