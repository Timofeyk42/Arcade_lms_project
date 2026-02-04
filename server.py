from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import time
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

socketio = SocketIO(app, cors_allowed_origins="*")

# Game state
game_state = {
    'players': {},
    'ball': {
        'x': 500,
        'y': 250,
        'dx': 4,
        'dy': 2,
        'radius': 10
    },
    'scores': {'player1': 0, 'player2': 0},
    'game_active': True,
    'last_update': time.time()
}

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 500
PADDLE_HEIGHT = 100
PADDLE_WIDTH = 15

# Handle new player joining
@socketio.on('join')
def handle_join(data):
    username = data.get('username', 'Anonymous')
    player_id = request.sid
    
    # Assign player position
    if len(game_state['players']) == 0:
        position = 'left'
        x = 50
    else:
        position = 'right'
        x = SCREEN_WIDTH - 50
    
    game_state['players'][player_id] = {
        'username': username,
        'position': position,
        'x': x,
        'y': SCREEN_HEIGHT // 2,
        'dy': 0,
        'score': 0
    }
    
    join_room(player_id)
    
    # Send initial game state to new player
    emit('game_state', game_state, room=player_id)
    
    # Notify all players about new player
    emit('player_joined', {
        'username': username,
        'position': position,
        'player_count': len(game_state['players'])
    }, broadcast=True)
    
    print(f"{username} joined the game as {position}")

# Handle player movement
@socketio.on('player_move')
def handle_player_move(data):
    player_id = request.sid
    if player_id in game_state['players']:
        game_state['players'][player_id]['dy'] = data.get('dy', 0)
        game_state['players'][player_id]['y'] = data.get('y', SCREEN_HEIGHT // 2)

# Handle ball position updates (from client prediction)
@socketio.on('ball_update')
def handle_ball_update(data):
    # Server has authority over ball position
    pass

# Game loop - runs on server
def game_loop():
    while True:
        socketio.sleep(0.016)  # ~60 FPS
        
        current_time = time.time()
        dt = current_time - game_state['last_update']
        game_state['last_update'] = current_time
        
        if len(game_state['players']) < 2 or not game_state['game_active']:
            continue
        
        # Update ball position
        ball = game_state['ball']
        ball['x'] += ball['dx']
        ball['y'] += ball['dy']
        
        # Ball collision with top/bottom walls
        if ball['y'] - ball['radius'] <= 0 or ball['y'] + ball['radius'] >= SCREEN_HEIGHT:
            ball['dy'] *= -1
        
        # Ball collision with paddles
        for player_id, player in game_state['players'].items():
            if check_paddle_collision(ball, player):
                ball['dx'] *= -1.05  # Increase speed
                ball['dy'] += player['dy'] * 0.3  # Add spin
                ball['dy'] = max(-10, min(10, ball['dy']))  # Clamp dy
        
        # Ball out of bounds - scoring
        if ball['x'] - ball['radius'] <= 0:
            game_state['scores']['player2'] += 1
            reset_ball()
        elif ball['x'] + ball['radius'] >= SCREEN_WIDTH:
            game_state['scores']['player1'] += 1
            reset_ball()
        
        # Broadcast game state to all players
        socketio.emit('game_state', game_state)

def check_paddle_collision(ball, player):
    paddle_x = player['x']
    paddle_y = player['y']
    
    # Simple collision detection
    if player['position'] == 'left':
        if (ball['x'] - ball['radius'] <= paddle_x + PADDLE_WIDTH // 2 and
            paddle_y - PADDLE_HEIGHT // 2 <= ball['y'] <= paddle_y + PADDLE_HEIGHT // 2):
            return True
    else:
        if (ball['x'] + ball['radius'] >= paddle_x - PADDLE_WIDTH // 2 and
            paddle_y - PADDLE_HEIGHT // 2 <= ball['y'] <= paddle_y + PADDLE_HEIGHT // 2):
            return True
    return False

def reset_ball():
    game_state['ball']['x'] = SCREEN_WIDTH // 2
    game_state['ball']['y'] = SCREEN_HEIGHT // 2
    game_state['ball']['dx'] = 4 if game_state['ball']['dx'] < 0 else -4
    game_state['ball']['dy'] = 2 if random.random() > 0.5 else -2

# Handle disconnects
@socketio.on('disconnect')
def handle_disconnect():
    player_id = request.sid
    if player_id in game_state['players']:
        username = game_state['players'][player_id]['username']
        del game_state['players'][player_id]
        emit('player_left', {'username': username}, broadcast=True)
        print(f"{username} left the game")
        
        # Reset game if only one player remains
        if len(game_state['players']) < 2:
            game_state['game_active'] = False
            game_state['scores'] = {'player1': 0, 'player2': 0}

if __name__ == '__main__':
    # Start game loop in background
    socketio.start_background_task(game_loop)
    socketio.run(app, debug=True, host='0.0.0.0', port=8000)