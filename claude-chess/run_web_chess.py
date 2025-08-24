#!/usr/bin/env python3
"""
Launch the enhanced interactive web chess interface.
"""

from chess_engine import WebGUI

def main():
    print("🎯 LAUNCHING ENHANCED INTERACTIVE WEB CHESS")
    print("=" * 50)
    print()
    print("🎯 MAJOR TIMING FIX - TRUE REAL-TIME MOVES:")
    print("✅ Your moves appear INSTANTLY on click")
    print("✅ Engine calculation happens separately")
    print("✅ NO MORE waiting for both moves together!")
    print()
    print("Enhanced Interactive Features:")
    print("✅ Real-time move highlighting")
    print("✅ Animated piece selection")
    print("✅ Show/hide legal moves") 
    print("✅ Engine thinking indicator")
    print("✅ Move timing and evaluation")
    print("✅ Undo moves")
    print("✅ Enhanced visual feedback")
    print("✅ Pulsing animations")
    print("✅ Interactive move history")
    print()
    print("=" * 50)
    
    try:
        # Create web GUI with enhanced features
        web_gui = WebGUI(
            chess960=False,
            human_color='white', 
            engine_depth=3,
            port=8080
        )
        
        print(f"🌐 Starting web server on http://localhost:8080")
        print("Click the URL above or open it in your browser")
        print()
        print("Interactive Features Available:")
        print("• Click pieces to select and see legal moves")
        print("• Click destination to move")
        print("• Use 'Show Legal Moves' to highlight all moves")
        print("• Use 'Undo Move' to take back moves")
        print("• Watch engine thinking animations")
        print("• See move timing and evaluation")
        print()
        print("Press Ctrl+C to stop the server")
        
        web_gui.run()
        
    except KeyboardInterrupt:
        print("\n👋 Web chess server stopped.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()