#!/usr/bin/env python3
"""
Simple launcher script for the Chess Engine Battle system

This script serves as the entry point for the chess engine battle application.
It handles importing and launching the main battle system with proper error
handling for common issues like missing dependencies or user interruption.
"""

import sys
import os

# Add current directory to Python path to ensure proper module imports
# This allows the script to find engine_battle and other modules regardless
# of where the script is executed from
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Import and execute the main battle system entry point
    from engine_battle import main
    main()
except ImportError as e:
    # Handle missing dependencies or module import errors
    print(f"Error importing engine_battle: {e}")
    print("Please make sure all required files are present.")
except KeyboardInterrupt:
    # Gracefully handle Ctrl+C interruption from user
    print("\nExiting...")
except Exception as e:
    # Catch any other unexpected errors and display full traceback for debugging
    print(f"Error running battle system: {e}")
    import traceback
    traceback.print_exc()