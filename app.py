from flask import Flask, render_template, jsonify, request
import random

app = Flask(__name__)

game_state = {
    "board": [],
    "called_numbers": [],
    "marked": [[False for _ in range(5)] for _ in range(5)]
}

def generate_board():
    board = []
    # B: 1-15, I: 16-30, N: 31-45, G: 46-60, O: 61-75
    for i in range(5):
        col = random.sample(range(i * 15 + 1, (i + 1) * 15 + 1), 5)
        board.append(col)
    
    # Transpose to get rows
    rows = [[board[j][i] for j in range(5)] for i in range(5)]
    rows[2][2] = "FREE"
    return rows

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/new-game', methods=['GET'])
def new_game():
    game_state["board"] = generate_board()
    game_state["called_numbers"] = []
    game_state["marked"] = [[False for _ in range(5)] for _ in range(5)]
    game_state["marked"][2][2] = True
    return jsonify({"board": game_state["board"]})

@app.route('/api/draw-number', methods=['GET'])
def draw_number():
    available = [n for n in range(1, 76) if n not in game_state["called_numbers"]]
    if not available:
        return jsonify({"error": "No more numbers"}), 400
    
    number = random.choice(available)
    game_state["called_numbers"].append(number)
    return jsonify({"number": number})

@app.route('/api/check-win', methods=['POST'])
def check_win():
    marked = request.json.get('marked')
    
    # Check rows and columns
    for i in range(5):
        if all(marked[i][j] for j in range(5)): return jsonify({"win": True})
        if all(marked[j][i] for j in range(5)): return jsonify({"win": True})
    
    # Check diagonals
    if all(marked[i][i] for i in range(5)): return jsonify({"win": True})
    if all(marked[i][4-i] for i in range(5)): return jsonify({"win": True})
    
    return jsonify({"win": False})

if __name__ == '__main__':
    app.run(debug=True)
