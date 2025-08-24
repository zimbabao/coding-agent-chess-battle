#!/usr/bin/env python3
"""
Test script to debug timing issues with immediate display.
This will help identify exactly when output appears.
"""

import sys
import time

def test_immediate_output():
    """Test if output appears immediately"""
    print("=== TIMING TEST ===")
    print("This should appear immediately", end="")
    sys.stdout.flush()
    print(" - FLUSHED")
    
    print("Now waiting 2 seconds...")
    sys.stdout.flush()
    time.sleep(2)
    
    print("This appears after 2 seconds")
    sys.stdout.flush()

def test_chess_timing():
    """Simulate the chess engine timing"""
    print("\n=== SIMULATED CHESS TIMING ===")
    
    # Simulate user input
    print("Enter your move (simulated): e2e4")
    sys.stdout.flush()
    
    # Simulate human move processing
    print("\nYou played: e2e4")
    sys.stdout.flush()
    
    # Simulate board display (abbreviated)
    print("Board updated with your move:")
    print("  e4 has a pawn now")
    sys.stdout.flush()
    
    # Pause before engine
    print("\nPausing for 1 second...")
    sys.stdout.flush()
    time.sleep(1)
    
    # Engine thinking
    print("Engine thinking...")
    sys.stdout.flush()
    
    # Simulate engine calculation
    time.sleep(0.5)
    
    # Engine move
    print("Engine move: Nc6")
    sys.stdout.flush()
    
    print("\nDone - did you see each step separately?")

if __name__ == "__main__":
    test_immediate_output()
    test_chess_timing()