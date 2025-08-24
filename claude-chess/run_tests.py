#!/usr/bin/env python3
"""
Test runner for the Claude Chess Engine.
Runs all available tests and reports results.
"""

import subprocess
import sys
import os

def run_test(test_file, description):
    """Run a single test file and return success status."""
    print(f"\n🧪 Running {description}...")
    print("=" * 50)
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=False, 
                              text=True, 
                              timeout=30)
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED (exit code: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT")
        return False
    except Exception as e:
        print(f"💥 {description} - ERROR: {e}")
        return False

def main():
    """Run all tests."""
    print("🎯 CLAUDE CHESS ENGINE TEST SUITE")
    print("=" * 50)
    
    # List of tests to run
    tests = [
        ("test_illegal_captures.py", "Illegal Capture Prevention Tests"),
        ("test_illegal_move_validation.py", "Illegal Move Validation Tests"),
        ("test_specific_illegal_move.py", "Specific Illegal Move Scenario"),
        ("test_legal_moves.py", "Legal Move Generation Tests"),
        ("test_captured_pieces.py", "Captured Pieces Tracking Tests"),
        ("test_castling_notation.py", "Castling Notation Tests"),
        ("test_check_display.py", "Check Display Tests"),
        ("test_board_coordinates.py", "Board Coordinate Tests"),
        ("test_board_stability.py", "Board Stability Tests"),
        ("test_advanced_scenarios.py", "Advanced Game Scenarios"),
        ("test_utf8_encoding.py", "UTF-8 Encoding Tests"),
        ("test_comprehensive_chess.py", "Comprehensive Chess Engine Tests"),
    ]
    
    # Track results
    passed = 0
    failed = 0
    
    # Run each test
    for test_file, description in tests:
        if os.path.exists(test_file):
            if run_test(test_file, description):
                passed += 1
            else:
                failed += 1
        else:
            print(f"⚠️  {description} - FILE NOT FOUND: {test_file}")
            failed += 1
    
    # Summary
    total = passed + failed
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ The chess engine is working correctly.")
    else:
        print(f"\n❌ {failed} TEST(S) FAILED!")
        print("🐛 There are issues that need to be fixed.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)