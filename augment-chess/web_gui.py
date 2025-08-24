#!/usr/bin/env python3
"""
Web GUI for Chess Engine with Chess960 support.
Provides a web interface for playing both standard chess and Chess960.
"""

import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from chess_engine import ChessEngine
from utils import *

class ChessWebHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, chess_engine=None, **kwargs):
        self.chess_engine = chess_engine
        # Game mode: 'human_vs_human', 'human_vs_computer', 'computer_vs_computer'
        self.game_mode = 'human_vs_human'
        self.computer_white = False  # Is white controlled by computer?
        self.computer_black = False  # Is black controlled by computer?
        self.auto_play_active = False  # For computer vs computer
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/' or path == '/index.html':
            self.serve_html()
        elif path == '/api/board':
            self.get_board_state()
        elif path == '/api/legal_moves':
            self.get_legal_moves()
        elif path == '/api/game_info':
            self.get_game_info()
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(post_data)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return
        
        if path == '/api/make_move':
            self.make_move(data)
        elif path == '/api/new_game':
            self.new_game(data)
        elif path == '/api/undo_move':
            self.undo_move()
        elif path == '/api/get_best_move':
            self.get_best_move(data)
        elif path == '/api/setup_chess960':
            self.setup_chess960(data)
        elif path == '/api/set_game_mode':
            self.set_game_mode(data)
        elif path == '/api/computer_move':
            self.computer_move(data)
        else:
            self.send_error(404)
    
    def serve_html(self):
        """Serve the main HTML page."""
        html_content = self.get_html_content()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def get_board_state(self):
        """Get current board state as JSON."""
        board_data = {
            'board': self.chess_engine.board.board,
            'colors': self.chess_engine.board.colors,
            'to_move': self.chess_engine.board.to_move,
            'castling_rights': self.chess_engine.board.castling_rights,
            'en_passant_square': self.chess_engine.board.en_passant_square,
            'halfmove_clock': self.chess_engine.board.halfmove_clock,
            'fullmove_number': self.chess_engine.board.fullmove_number,
            'chess960': self.chess_engine.chess960,
            'position_id': self.chess_engine.position_id
        }
        
        self.send_json_response(board_data)
    
    def get_legal_moves(self):
        """Get legal moves as JSON."""
        legal_moves = self.chess_engine.get_legal_moves()
        moves_data = [str(move) for move in legal_moves]
        self.send_json_response({'legal_moves': moves_data})
    
    def get_game_info(self):
        """Get game information."""
        game_over, reason = self.chess_engine.is_game_over()
        evaluation = self.chess_engine.evaluate_position()
        
        info = {
            'game_over': game_over,
            'game_over_reason': reason,
            'evaluation': evaluation,
            'chess960': self.chess_engine.chess960,
            'position_id': self.chess_engine.position_id,
            'move_count': len(self.chess_engine.game_history),
            'game_mode': self.game_mode,
            'computer_white': self.computer_white,
            'computer_black': self.computer_black,
            'current_player_is_computer': self.is_current_player_computer()
        }

        self.send_json_response(info)

    def is_current_player_computer(self):
        """Check if the current player is controlled by computer."""
        if self.chess_engine.board.to_move == 0:  # White's turn
            return self.computer_white
        else:  # Black's turn
            return self.computer_black
    
    def make_move(self, data):
        """Make a move."""
        move_str = data.get('move')
        if not move_str:
            self.send_error(400, "Missing move")
            return
        
        success = self.chess_engine.make_move(move_str)
        self.send_json_response({'success': success})
    
    def new_game(self, data):
        """Start a new game."""
        chess960 = data.get('chess960', False)
        position_id = data.get('position_id')
        
        if chess960:
            if position_id is not None:
                try:
                    self.chess_engine.setup_chess960_position(position_id)
                except ValueError as e:
                    self.send_error(400, str(e))
                    return
            else:
                position_id = self.chess_engine.generate_random_chess960_position()
        else:
            self.chess_engine = ChessEngine(chess960=False)
        
        self.send_json_response({
            'success': True,
            'chess960': chess960,
            'position_id': position_id
        })
    
    def undo_move(self):
        """Undo the last move."""
        success = self.chess_engine.undo_move()
        self.send_json_response({'success': success})
    
    def get_best_move(self, data):
        """Get the best move from the engine."""
        depth = data.get('depth', 4)
        time_limit = data.get('time_limit', 5.0)
        
        # Run search in a separate thread to avoid blocking
        def search_thread():
            best_move = self.chess_engine.get_best_move(depth, time_limit)
            return str(best_move) if best_move else None
        
        # For simplicity, run synchronously (in production, use async)
        best_move = search_thread()
        self.send_json_response({'best_move': best_move})
    
    def setup_chess960(self, data):
        """Set up a specific Chess960 position."""
        position_id = data.get('position_id')
        if position_id is None:
            self.send_error(400, "Missing position_id")
            return
        
        try:
            self.chess_engine.setup_chess960_position(position_id)
            self.send_json_response({
                'success': True,
                'position_id': position_id
            })
        except ValueError as e:
            self.send_error(400, str(e))

    def set_game_mode(self, data):
        """Set the game mode (human vs human, human vs computer, etc.)."""
        mode = data.get('mode', 'human_vs_human')

        if mode == 'human_vs_human':
            self.game_mode = 'human_vs_human'
            self.computer_white = False
            self.computer_black = False
            self.auto_play_active = False
        elif mode == 'human_vs_computer_white':
            self.game_mode = 'human_vs_computer'
            self.computer_white = True
            self.computer_black = False
            self.auto_play_active = False
        elif mode == 'human_vs_computer_black':
            self.game_mode = 'human_vs_computer'
            self.computer_white = False
            self.computer_black = True
            self.auto_play_active = False
        elif mode == 'computer_vs_computer':
            self.game_mode = 'computer_vs_computer'
            self.computer_white = True
            self.computer_black = True
            self.auto_play_active = True
        else:
            self.send_error(400, "Invalid game mode")
            return

        self.send_json_response({
            'success': True,
            'mode': self.game_mode,
            'computer_white': self.computer_white,
            'computer_black': self.computer_black
        })

    def computer_move(self, data):
        """Make a computer move."""
        if not self.is_current_player_computer():
            self.send_error(400, "Current player is not computer-controlled")
            return

        depth = data.get('depth', 4)
        time_limit = data.get('time_limit', 3.0)

        # Get best move from engine
        best_move = self.chess_engine.get_best_move(depth, time_limit)

        if best_move:
            # Make the move
            success = self.chess_engine.make_move(str(best_move))
            if success:
                self.send_json_response({
                    'success': True,
                    'move': str(best_move),
                    'evaluation': self.chess_engine.evaluate_position()
                })
            else:
                self.send_json_response({'success': False, 'error': 'Failed to make move'})
        else:
            self.send_json_response({'success': False, 'error': 'No legal moves available'})
    
    def send_json_response(self, data):
        """Send JSON response."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def get_html_content(self):
        """Get the HTML content for the chess interface."""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chess Engine with Chess960 Support</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f0f0f0;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
        }
        .game-controls {
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 10px;
        }
        .control-group {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        button {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            background-color: #007bff;
            color: white;
            cursor: pointer;
        }
        button:hover {
            background-color: #0056b3;
        }
        button:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        .chess-board {
            display: grid;
            grid-template-columns: repeat(8, 60px);
            grid-template-rows: repeat(8, 60px);
            gap: 1px;
            margin: 20px auto;
            border: 2px solid #333;
            width: fit-content;
        }
        .square {
            width: 60px;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 36px;
            cursor: pointer;
            user-select: none;
            position: relative;
            transition: all 0.2s ease;
        }
        .square:hover {
            transform: scale(1.05);
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }
        .square.dragging {
            opacity: 0.7;
            transform: scale(1.1);
            z-index: 1000;
        }
        .square.drag-over {
            background-color: #ffeb3b !important;
            box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
        }
        .light {
            background-color: #f0d9b5;
        }
        .dark {
            background-color: #b58863;
        }
        .selected {
            background-color: #ffff00 !important;
        }
        .legal-move {
            background-color: #90EE90 !important;
            box-shadow: inset 0 0 5px rgba(0,100,0,0.5);
        }
        .legal-move::after {
            content: '●';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: rgba(0,100,0,0.7);
            font-size: 20px;
            pointer-events: none;
        }
        .legal-move.has-piece::after {
            content: '✕';
            color: rgba(200,0,0,0.8);
            font-size: 24px;
        }
        .game-info {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 20px;
        }
        .info-panel {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
        }
        .chess960-controls {
            background-color: #e3f2fd;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .chess960-controls h3 {
            margin-top: 0;
        }
        input[type="number"] {
            padding: 5px;
            border: 1px solid #ccc;
            border-radius: 3px;
            width: 80px;
        }
        .status {
            text-align: center;
            margin: 10px 0;
            font-weight: bold;
            padding: 10px;
            border-radius: 5px;
            transition: all 0.3s ease;
        }
        .status.thinking {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
        }
        .error {
            color: red;
        }
        .success {
            color: green;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Chess Engine with Chess960 Support</h1>
            <div id="status" class="status">Click or drag pieces to move • Green dots show legal moves • ✕ shows captures</div>
        </div>
        
        <div class="chess960-controls">
            <h3>Game Mode & Chess960 Settings</h3>
            <div class="control-group">
                <label>
                    Game Mode:
                    <select id="game-mode" onchange="setGameMode()">
                        <option value="human_vs_human">Human vs Human</option>
                        <option value="human_vs_computer_white">Human vs Computer (Computer plays White)</option>
                        <option value="human_vs_computer_black">Human vs Computer (Computer plays Black)</option>
                        <option value="computer_vs_computer">Computer vs Computer</option>
                    </select>
                </label>
            </div>
            <div class="control-group">
                <label>
                    <input type="checkbox" id="chess960-mode"> Enable Chess960
                </label>
                <label>
                    Position ID (0-959): <input type="number" id="position-id" min="0" max="959" value="518">
                </label>
                <button onclick="setupChess960()">Setup Position</button>
                <button onclick="randomChess960()">Random Position</button>
            </div>
        </div>
        
        <div class="game-controls">
            <div class="control-group">
                <button onclick="newGame()">New Game</button>
                <button onclick="undoMove()">Undo Move</button>
                <button onclick="getBestMove()" id="best-move-btn">Get Best Move</button>
                <button onclick="makeComputerMove()" id="computer-move-btn" style="display:none;">Make Computer Move</button>
                <button onclick="toggleAutoPlay()" id="auto-play-btn" style="display:none;">Start Auto Play</button>
            </div>
            <div class="control-group">
                <label>Engine Depth: <input type="number" id="engine-depth" min="1" max="8" value="4"></label>
                <label>Computer Speed: <input type="number" id="computer-speed" min="0.5" max="10" step="0.5" value="2"> seconds</label>
            </div>
        </div>
        
        <div class="chess-board" id="chess-board"></div>
        
        <div class="game-info">
            <div class="info-panel">
                <h3>Game Information</h3>
                <div id="game-info"></div>
            </div>
            <div class="info-panel">
                <h3>Move History</h3>
                <div id="move-history"></div>
            </div>
        </div>
    </div>

    <script>
        let selectedSquare = null;
        let legalMoves = [];
        let gameState = null;
        let gameMode = 'human_vs_human';
        let computerWhite = false;
        let computerBlack = false;
        let autoPlayInterval = null;
        let autoPlayActive = false;
        
        const pieceSymbols = {
            0: '', // EMPTY
            1: '♟', // PAWN
            2: '♞', // KNIGHT
            3: '♝', // BISHOP
            4: '♜', // ROOK
            5: '♛', // QUEEN
            6: '♚'  // KING
        };
        
        const whitePieceSymbols = {
            0: '', // EMPTY
            1: '♙', // PAWN
            2: '♘', // KNIGHT
            3: '♗', // BISHOP
            4: '♖', // ROOK
            5: '♕', // QUEEN
            6: '♔'  // KING
        };
        
        function initializeBoard() {
            const board = document.getElementById('chess-board');
            board.innerHTML = '';

            for (let rank = 7; rank >= 0; rank--) {
                for (let file = 0; file < 8; file++) {
                    const square = document.createElement('div');
                    square.className = 'square ' + ((rank + file) % 2 === 0 ? 'dark' : 'light');
                    square.dataset.square = rank * 8 + file;

                    // Add click handler
                    square.onclick = () => onSquareClick(rank * 8 + file);

                    // Add drag and drop handlers
                    square.ondragstart = (e) => onDragStart(e, rank * 8 + file);
                    square.ondragover = (e) => onDragOver(e);
                    square.ondragenter = (e) => onDragEnter(e);
                    square.ondragleave = (e) => onDragLeave(e);
                    square.ondrop = (e) => onDrop(e, rank * 8 + file);
                    square.ondragend = (e) => onDragEnd(e);

                    board.appendChild(square);
                }
            }

            updateBoard();
        }
        
        function updateBoard() {
            fetch('/api/board')
                .then(response => response.json())
                .then(data => {
                    gameState = data;
                    
                    for (let square = 0; square < 64; square++) {
                        const element = document.querySelector(`[data-square="${square}"]`);
                        const piece = data.board[square];
                        const color = data.colors[square];

                        if (piece === 0) {
                            element.textContent = '';
                            element.draggable = false;
                            element.classList.remove('has-piece');
                        } else {
                            element.textContent = color === 0 ? whitePieceSymbols[piece] : pieceSymbols[piece];
                            // Only make pieces draggable if it's their turn
                            element.draggable = (color === data.to_move);
                            element.classList.add('has-piece');

                            // Add visual indication for draggable pieces
                            if (color === data.to_move) {
                                element.style.cursor = 'grab';
                            } else {
                                element.style.cursor = 'default';
                            }
                        }
                    }
                    
                    updateGameInfo();

                    // Check if computer should move after board update
                    setTimeout(checkForComputerMove, 500);
                });
        }
        
        function updateGameInfo() {
            fetch('/api/game_info')
                .then(response => response.json())
                .then(data => {
                    // Update global game mode variables
                    gameMode = data.game_mode;
                    computerWhite = data.computer_white;
                    computerBlack = data.computer_black;

                    const info = document.getElementById('game-info');
                    const toMove = gameState.to_move === 0 ? 'White' : 'Black';
                    const playerType = data.current_player_is_computer ? 'Computer' : 'Human';

                    let infoHtml = `
                        <p><strong>To Move:</strong> ${toMove} (${playerType})</p>
                        <p><strong>Game Mode:</strong> ${formatGameMode(data.game_mode)}</p>
                        <p><strong>Evaluation:</strong> ${data.evaluation}</p>
                        <p><strong>Move Count:</strong> ${data.move_count}</p>
                        <p><strong>Chess960:</strong> ${data.chess960 ? 'Yes' : 'No'}</p>
                    `;

                    if (data.chess960 && data.position_id !== null) {
                        infoHtml += `<p><strong>Position ID:</strong> ${data.position_id}</p>`;
                    }

                    if (data.game_over) {
                        infoHtml += `<p><strong>Game Over:</strong> ${data.game_over_reason}</p>`;
                        stopAutoPlay();
                    }

                    info.innerHTML = infoHtml;

                    // Update button visibility
                    updateButtonVisibility(data);
                });
        }
        
        let draggedSquare = null;

        function onSquareClick(square) {
            // Check if it's computer's turn
            const currentPlayerIsComputer = (gameState.to_move === 0 && computerWhite) ||
                                          (gameState.to_move === 1 && computerBlack);

            if (currentPlayerIsComputer && gameMode !== 'human_vs_human') {
                setStatus('It\'s the computer\'s turn! Please wait.', 'error');
                return;
            }

            if (selectedSquare === null) {
                // Select square if it has a piece of the current player
                if (gameState.board[square] !== 0 && gameState.colors[square] === gameState.to_move) {
                    selectedSquare = square;
                    highlightSquare(square, 'selected');
                    showLegalMoves(square);
                }
            } else {
                // Try to make a move
                const move = squareToAlgebraic(selectedSquare) + squareToAlgebraic(square);
                makeMove(move);
                clearHighlights();
                selectedSquare = null;
            }
        }

        function onDragStart(e, square) {
            // Check if it's computer's turn
            const currentPlayerIsComputer = (gameState.to_move === 0 && computerWhite) ||
                                          (gameState.to_move === 1 && computerBlack);

            if (currentPlayerIsComputer && gameMode !== 'human_vs_human') {
                e.preventDefault();
                setStatus('It\'s the computer\'s turn! Please wait.', 'error');
                return false;
            }

            // Only allow dragging pieces of the current player
            if (gameState.board[square] === 0 || gameState.colors[square] !== gameState.to_move) {
                e.preventDefault();
                return false;
            }

            draggedSquare = square;
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', square.toString());

            // Add dragging class for visual feedback
            e.target.classList.add('dragging');
            e.target.style.cursor = 'grabbing';

            // Show legal moves for the dragged piece
            clearHighlights();
            highlightSquare(square, 'selected');
            showLegalMoves(square);

            setTimeout(() => {
                e.target.style.opacity = '0.5';
            }, 0);
        }

        function onDragOver(e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
        }

        function onDragEnter(e) {
            e.preventDefault();
            if (draggedSquare !== null) {
                e.target.classList.add('drag-over');
            }
        }

        function onDragLeave(e) {
            e.target.classList.remove('drag-over');
        }

        function onDrop(e, targetSquare) {
            e.preventDefault();
            e.target.classList.remove('drag-over');

            if (draggedSquare !== null && draggedSquare !== targetSquare) {
                // Try to make the move
                const move = squareToAlgebraic(draggedSquare) + squareToAlgebraic(targetSquare);
                makeMove(move);
            }

            clearHighlights();
            selectedSquare = null;
        }

        function onDragEnd(e) {
            // Clean up drag state
            e.target.classList.remove('dragging');
            e.target.style.opacity = '';
            e.target.style.cursor = gameState && gameState.colors[parseInt(e.target.dataset.square)] === gameState.to_move ? 'grab' : 'default';

            // Remove drag-over class from all squares
            document.querySelectorAll('.square').forEach(square => {
                square.classList.remove('drag-over');
            });

            draggedSquare = null;
        }
        
        function highlightSquare(square, className) {
            const element = document.querySelector(`[data-square="${square}"]`);
            element.classList.add(className);
        }
        
        function clearHighlights() {
            document.querySelectorAll('.square').forEach(square => {
                square.classList.remove('selected', 'legal-move', 'has-piece', 'drag-over');
            });
        }
        
        function showLegalMoves(fromSquare) {
            fetch('/api/legal_moves')
                .then(response => response.json())
                .then(data => {
                    legalMoves = data.legal_moves;
                    const fromAlgebraic = squareToAlgebraic(fromSquare);

                    legalMoves.forEach(move => {
                        if (move.startsWith(fromAlgebraic)) {
                            const toSquare = algebraicToSquare(move.substring(2, 4));
                            const element = document.querySelector(`[data-square="${toSquare}"]`);

                            // Add legal-move class
                            element.classList.add('legal-move');

                            // Add capture indicator if there's a piece on the target square
                            if (gameState.board[toSquare] !== 0) {
                                element.classList.add('has-piece');
                            }
                        }
                    });
                });
        }
        
        function makeMove(move) {
            // Check if it's human's turn in human vs computer mode
            const currentPlayerIsComputer = (gameState.to_move === 0 && computerWhite) ||
                                          (gameState.to_move === 1 && computerBlack);

            if (currentPlayerIsComputer && gameMode === 'human_vs_computer') {
                setStatus('It\'s the computer\'s turn!', 'error');
                return;
            }

            fetch('/api/make_move', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({move: move})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateBoard();
                    setStatus('Move made: ' + move, 'success');

                    // Check if computer should move next
                    setTimeout(checkForComputerMove, 500);
                } else {
                    setStatus('Illegal move: ' + move, 'error');
                }
            });
        }
        
        function newGame() {
            const chess960 = document.getElementById('chess960-mode').checked;
            const positionId = chess960 ? parseInt(document.getElementById('position-id').value) : null;
            
            fetch('/api/new_game', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({chess960: chess960, position_id: positionId})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateBoard();
                    setStatus('New game started', 'success');
                    if (data.chess960) {
                        setStatus(`Chess960 game started (Position ${data.position_id})`, 'success');
                    }
                } else {
                    setStatus('Failed to start new game', 'error');
                }
            });
        }
        
        function undoMove() {
            fetch('/api/undo_move', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateBoard();
                        setStatus('Move undone', 'success');
                    } else {
                        setStatus('No move to undo', 'error');
                    }
                });
        }
        
        function getBestMove() {
            const depth = parseInt(document.getElementById('engine-depth').value);
            const button = event.target;

            // Disable button and show thinking status
            button.disabled = true;
            button.textContent = 'Thinking...';
            setStatus(`Engine thinking at depth ${depth}...`, 'thinking');

            fetch('/api/get_best_move', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({depth: depth, time_limit: 5.0})
            })
            .then(response => response.json())
            .then(data => {
                if (data.best_move) {
                    setStatus(`Engine suggests: ${data.best_move}`, 'success');
                    // Highlight the suggested move
                    const fromSquare = algebraicToSquare(data.best_move.substring(0, 2));
                    const toSquare = algebraicToSquare(data.best_move.substring(2, 4));

                    clearHighlights();
                    highlightSquare(fromSquare, 'selected');
                    highlightSquare(toSquare, 'legal-move');

                    // Auto-make the move after a short delay
                    setTimeout(() => {
                        makeMove(data.best_move);
                    }, 1000);
                } else {
                    setStatus('No best move found', 'error');
                }
            })
            .catch(error => {
                setStatus('Error getting best move', 'error');
                console.error('Error:', error);
            })
            .finally(() => {
                // Re-enable button
                button.disabled = false;
                button.textContent = 'Get Best Move';
            });
        }
        
        function setupChess960() {
            const positionId = parseInt(document.getElementById('position-id').value);
            
            fetch('/api/setup_chess960', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({position_id: positionId})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateBoard();
                    setStatus(`Chess960 position ${positionId} set up`, 'success');
                    document.getElementById('chess960-mode').checked = true;
                } else {
                    setStatus('Failed to set up Chess960 position', 'error');
                }
            });
        }
        
        function randomChess960() {
            const randomId = Math.floor(Math.random() * 960);
            document.getElementById('position-id').value = randomId;
            setupChess960();
        }

        function formatGameMode(mode) {
            switch(mode) {
                case 'human_vs_human': return 'Human vs Human';
                case 'human_vs_computer': return computerWhite ? 'Human vs Computer (Computer: White)' : 'Human vs Computer (Computer: Black)';
                case 'computer_vs_computer': return 'Computer vs Computer';
                default: return mode;
            }
        }

        function setGameMode() {
            const mode = document.getElementById('game-mode').value;

            fetch('/api/set_game_mode', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({mode: mode})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    gameMode = data.mode;
                    computerWhite = data.computer_white;
                    computerBlack = data.computer_black;

                    setStatus(`Game mode set to: ${formatGameMode(data.mode)}`, 'success');
                    updateGameInfo();

                    // Start auto-play if computer vs computer
                    if (mode === 'computer_vs_computer') {
                        setTimeout(startAutoPlay, 1000);
                    } else {
                        stopAutoPlay();
                    }

                    // Check if computer should move immediately
                    setTimeout(checkForComputerMove, 500);
                } else {
                    setStatus('Failed to set game mode', 'error');
                }
            });
        }

        function updateButtonVisibility(gameInfo) {
            const computerMoveBtn = document.getElementById('computer-move-btn');
            const autoPlayBtn = document.getElementById('auto-play-btn');
            const bestMoveBtn = document.getElementById('best-move-btn');

            // Show computer move button if current player is computer (but not in auto-play)
            if (gameInfo.current_player_is_computer && gameMode !== 'computer_vs_computer') {
                computerMoveBtn.style.display = 'inline-block';
                bestMoveBtn.style.display = 'none';
            } else {
                computerMoveBtn.style.display = 'none';
                bestMoveBtn.style.display = 'inline-block';
            }

            // Show auto-play button for computer vs computer
            if (gameMode === 'computer_vs_computer') {
                autoPlayBtn.style.display = 'inline-block';
                autoPlayBtn.textContent = autoPlayActive ? 'Stop Auto Play' : 'Start Auto Play';
            } else {
                autoPlayBtn.style.display = 'none';
            }
        }

        function checkForComputerMove() {
            fetch('/api/game_info')
                .then(response => response.json())
                .then(data => {
                    if (data.current_player_is_computer && !data.game_over) {
                        if (gameMode === 'computer_vs_computer' && autoPlayActive) {
                            // Auto-play is handling this
                            return;
                        } else if (gameMode === 'human_vs_computer') {
                            // Make computer move automatically in human vs computer
                            setTimeout(makeComputerMove, 1000);
                        }
                    }
                });
        }

        function makeComputerMove() {
            const depth = parseInt(document.getElementById('engine-depth').value);
            const button = document.getElementById('computer-move-btn');

            if (button) {
                button.disabled = true;
                button.textContent = 'Computer Thinking...';
            }

            setStatus('Computer is thinking...', 'thinking');

            fetch('/api/computer_move', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({depth: depth, time_limit: 3.0})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    setStatus(`Computer played: ${data.move}`, 'success');
                    updateBoard();
                } else {
                    setStatus(`Computer move failed: ${data.error}`, 'error');
                }
            })
            .catch(error => {
                setStatus('Error making computer move', 'error');
                console.error('Error:', error);
            })
            .finally(() => {
                if (button) {
                    button.disabled = false;
                    button.textContent = 'Make Computer Move';
                }
            });
        }

        function startAutoPlay() {
            if (autoPlayInterval) return; // Already running

            autoPlayActive = true;
            const speed = parseFloat(document.getElementById('computer-speed').value) * 1000;

            autoPlayInterval = setInterval(() => {
                fetch('/api/game_info')
                    .then(response => response.json())
                    .then(data => {
                        if (data.game_over) {
                            stopAutoPlay();
                            return;
                        }

                        if (data.current_player_is_computer) {
                            makeComputerMove();
                        }
                    });
            }, speed);

            setStatus('Auto-play started', 'success');
            updateGameInfo();
        }

        function stopAutoPlay() {
            if (autoPlayInterval) {
                clearInterval(autoPlayInterval);
                autoPlayInterval = null;
            }
            autoPlayActive = false;
            updateGameInfo();
        }

        function toggleAutoPlay() {
            if (autoPlayActive) {
                stopAutoPlay();
                setStatus('Auto-play stopped', 'success');
            } else {
                startAutoPlay();
            }
        }
        
        function setStatus(message, type) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = 'status ' + type;

            // Auto-clear status messages after a few seconds (except for permanent ones)
            if (type === 'success' || type === 'error') {
                setTimeout(() => {
                    status.textContent = 'Click or drag pieces to move • Green dots show legal moves • ✕ shows captures';
                    status.className = 'status';
                }, 3000);
            }
        }
        
        function squareToAlgebraic(square) {
            const file = String.fromCharCode(97 + (square % 8));
            const rank = Math.floor(square / 8) + 1;
            return file + rank;
        }
        
        function algebraicToSquare(algebraic) {
            const file = algebraic.charCodeAt(0) - 97;
            const rank = parseInt(algebraic[1]) - 1;
            return rank * 8 + file;
        }
        
        // Initialize the board when the page loads
        window.onload = initializeBoard;
    </script>
</body>
</html>
        '''

class WebGUI:
    def __init__(self, port=8080, chess960=False, position_id=None):
        self.port = port
        self.chess_engine = ChessEngine(chess960=chess960, position_id=position_id)
        self.server = None
        self.server_thread = None
    
    def start(self):
        """Start the web server."""
        def handler(*args, **kwargs):
            ChessWebHandler(*args, chess_engine=self.chess_engine, **kwargs)
        
        self.server = HTTPServer(('localhost', self.port), handler)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        print(f"Chess web interface started at http://localhost:{self.port}")
        print("Press Ctrl+C to stop the server")
    
    def stop(self):
        """Stop the web server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.server_thread:
            self.server_thread.join()

if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    chess960 = '--chess960' in sys.argv
    position_id = None
    
    if '--position' in sys.argv:
        try:
            pos_index = sys.argv.index('--position') + 1
            position_id = int(sys.argv[pos_index])
        except (IndexError, ValueError):
            print("Invalid position ID")
            sys.exit(1)
    
    # Start web GUI
    web_gui = WebGUI(chess960=chess960, position_id=position_id)
    
    try:
        web_gui.start()
        # Keep the main thread alive
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down web server...")
        web_gui.stop()
        sys.exit(0)
