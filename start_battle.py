#!/usr/bin/env python3
"""
Simple launcher script for the Chess Engine Battle system
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from engine_battle import main
    main()
except ImportError as e:
    print(f"Error importing engine_battle: {e}")
    print("Please make sure all required files are present.")
except KeyboardInterrupt:
    print("\nExiting...")
except Exception as e:
    print(f"Error running battle system: {e}")
    import traceback
    traceback.print_exc()