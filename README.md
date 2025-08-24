# Coding Agent Chess Battle

A comparative study of two chess engines developed by different AI coding assistants, featuring comprehensive chess implementations with UCI support and Chess960 compatibility.

## Project Overview

This repository contains two distinct chess engine implementations:

- **`augment-chess/`** - A comprehensive Python chess engine with full Chess960 support
- **`claude-chess/`** - An alternative chess engine implementation with multiple interface options

Both engines provide complete chess functionality including standard rules, Chess960 support, UCI protocol compatibility, and various user interfaces.

## Chess Engines Comparison

### Augment Chess Engine (`augment-chess/`)

A feature-rich chess engine with extensive Chess960 support:

- **Complete rule implementation** including castling, en passant, promotions
- **Full Chess960 support** with all 960 starting positions
- **UCI protocol** compatibility for chess GUIs
- **Multiple interfaces**: CLI, web interface, and UCI mode
- **Advanced search**: Minimax with alpha-beta pruning, quiescence search
- **Comprehensive evaluation**: Material, position, mobility, king safety

### Claude Chess Engine (`claude-chess/`)

An alternative implementation with multiple interface options:

- **Complete chess logic** with proper move validation
- **Multiple interfaces**: CLI, GUI (tkinter), web interface
- **Chess960 support** 
- **AI engine** with minimax algorithm and alpha-beta pruning
- **Comprehensive test suite**

## Quick Start

### Running Augment Chess

```bash
cd augment-chess/

# UCI mode (for chess GUIs)
python main.py

# Interactive mode
python main.py --interactive

# Web interface
python main.py --web

# Chess960 mode
python main.py --chess960 --position 356
```

### Running Claude Chess

```bash
cd claude-chess/

# Interactive CLI
python chess_engine.py

# Web interface
python run_web_chess.py

# Run tests
python run_tests.py
```

## Features Comparison

| Feature | Augment Chess | Claude Chess |
|---------|---------------|--------------|
| UCI Protocol | ✅ | ❓ |
| Chess960 | ✅ Full (960 positions) | ✅ Basic |
| Web Interface | ✅ | ✅ |
| GUI Interface | ❌ | ✅ (tkinter) |
| Interactive CLI | ✅ | ✅ |
| Test Suite | ✅ | ✅ Comprehensive |
| Search Algorithm | Alpha-beta + Quiescence | Minimax + Alpha-beta |
| Performance Testing | ✅ (perft) | ✅ |

## Installation

Both engines use only Python standard library - no external dependencies required.

```bash
git clone <repository-url>
cd coding-agent-chess-battle

# Choose which engine to run
cd augment-chess/  # or cd claude-chess/
```

## Testing

### Augment Chess Tests
```bash
cd augment-chess/
python main.py --test
python main.py --test-chess960
python demo_chess960.py
```

### Claude Chess Tests
```bash
cd claude-chess/
python run_tests.py
python test_comprehensive_chess.py
python timing_test.py
```

## Usage in Chess GUIs

Both engines can be used with UCI-compatible chess GUIs like Arena, ChessBase, or for creating Lichess bots.

### Arena Chess GUI Setup
1. Download Arena from http://www.playwitharena.de/
2. Install and run Arena
3. Go to Engines → Install New Engine
4. Browse to either engine directory
5. Select the appropriate Python file

## Development and Comparison

This repository serves as a comparison between different approaches to chess engine development:

- **Architecture differences**: How different AI assistants structure chess engines
- **Feature implementation**: Comparison of Chess960, UCI, and interface implementations  
- **Testing approaches**: Different strategies for validating chess logic
- **Performance characteristics**: Speed and accuracy comparisons

## Chess960 Support

Both engines support Chess960 (Fischer Random Chess) with 960 possible starting positions:

- **Augment Chess**: Complete implementation with position ID system (0-959)
- **Claude Chess**: Basic Chess960 support with random position generation

## Contributing

This project is primarily for comparison purposes, but contributions are welcome:

- Performance benchmarking between engines
- Feature parity improvements
- Additional test cases
- Documentation improvements

## License

Open source - feel free to use, modify, and distribute both engines.

## Acknowledgments

- Chess programming community
- UCI protocol specification  
- Fischer Random Chess (Chess960) standards
- AI coding assistants that developed these engines