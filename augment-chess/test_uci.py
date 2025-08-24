#!/usr/bin/env python3
"""
Simple UCI test script to verify the chess engine works correctly.
"""

import subprocess
import sys
import time

def test_uci_engine():
    """Test the UCI engine with basic commands."""
    print("Testing UCI engine...")
    
    # Start the engine
    process = subprocess.Popen(
        [sys.executable, "main.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    def send_command(cmd):
        """Send a command to the engine and get response."""
        print(f"Sending: {cmd}")
        process.stdin.write(cmd + "\n")
        process.stdin.flush()
        time.sleep(0.1)  # Give engine time to respond
    
    def read_output():
        """Read available output from engine."""
        output = ""
        while True:
            try:
                line = process.stdout.readline()
                if not line:
                    break
                output += line
                print(f"Received: {line.strip()}")
                if line.strip() in ["uciok", "readyok"] or line.startswith("bestmove"):
                    break
            except:
                break
        return output
    
    try:
        # Test UCI initialization
        send_command("uci")
        output = read_output()
        assert "uciok" in output, "Engine did not respond with uciok"
        
        # Test ready
        send_command("isready")
        output = read_output()
        assert "readyok" in output, "Engine did not respond with readyok"
        
        # Test new game
        send_command("ucinewgame")
        
        # Test position setup
        send_command("position startpos")
        
        # Test search
        send_command("go depth 3")
        output = read_output()
        assert "bestmove" in output, "Engine did not return a best move"
        
        # Test with moves
        send_command("position startpos moves e2e4 e7e5")
        send_command("go depth 2")
        output = read_output()
        assert "bestmove" in output, "Engine did not return a best move after moves"
        
        print("✓ All UCI tests passed!")
        
    except Exception as e:
        print(f"✗ UCI test failed: {e}")
        return False
    finally:
        # Clean up
        try:
            send_command("quit")
            process.wait(timeout=2)
        except:
            process.terminate()
    
    return True

if __name__ == "__main__":
    success = test_uci_engine()
    sys.exit(0 if success else 1)
