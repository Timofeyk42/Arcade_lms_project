from flask import Flask, request
from flask_socketio import SocketIO, emit
import time
import random
import socket
import sys

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pong_game_secret_key_2026'
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=60, ping_interval=25)

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
    'game_active': True,
    'last_update': time.time()
}

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 500
PADDLE_HEIGHT = 100
PADDLE_WIDTH = 15

def get_local_ip():
    """Надёжное определение локального IP-адреса"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        pass
    
    try:
        return socket.gethostbyname(socket.gethostname())
    except:
        pass
    
    return "127.0.0.1"

def find_free_port(start_port=8000, max_attempts=10):
    """Найти свободный порт, начиная с start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', port))
                return port
        except OSError:
            print(f"⚠️  Порт {port} занят, пробую следующий...")
            continue
    return None

@socketio.on('join')
def handle_join(data):
    username = data.get('username', 'Anonymous')
    skin_index = data.get('skin_index', 0)
    player_id = request.sid
    
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
        'score': 0,
        'skin_index': skin_index
    }
    
    print(f"🎮 {username} (ID: {player_id[:8]}) joined as {position}")
    emit('game_state', get_game_state_for_client(), room=player_id)
    emit('players_update', {'count': len(game_state['players'])}, broadcast=True)

@socketio.on('player_move')
def handle_player_move(data):
    player_id = request.sid
    if player_id in game_state['players']:
        game_state['players'][player_id]['dy'] = data.get('dy', 0)
        game_state['players'][player_id]['y'] = max(50, min(SCREEN_HEIGHT - 50, data.get('y', SCREEN_HEIGHT // 2)))

@socketio.on('disconnect')
def handle_disconnect():
    player_id = request.sid
    if player_id in game_state['players']:
        username = game_state['players'][player_id]['username']
        position = game_state['players'][player_id]['position']
        del game_state['players'][player_id]
        print(f"🚪 {username} left the game")
        emit('players_update', {'count': len(game_state['players'])}, broadcast=True)
        
        if len(game_state['players']) < 2:
            game_state['game_active'] = False
            for pid in game_state['players']:
                game_state['players'][pid]['score'] = 0
            reset_ball()
            print("⏸️ Game paused — waiting for players")

def get_game_state_for_client():
    state = {
        'ball': game_state['ball'].copy(),
        'players': {}
    }
    for pid, player in game_state['players'].items():
        state['players'][pid] = {
            'x': player['x'],
            'y': player['y'],
            'position': player['position'],
            'score': player['score'],
            'skin_index': player.get('skin_index', 0)
        }
    return state

def check_paddle_collision(ball, player):
    paddle_x = player['x']
    paddle_y = player['y']
    
    if player['position'] == 'left':
        return (ball['x'] - ball['radius'] <= paddle_x + PADDLE_WIDTH // 2 and
                paddle_y - PADDLE_HEIGHT // 2 <= ball['y'] <= paddle_y + PADDLE_HEIGHT // 2)
    else:
        return (ball['x'] + ball['radius'] >= paddle_x - PADDLE_WIDTH // 2 and
                paddle_y - PADDLE_HEIGHT // 2 <= ball['y'] <= paddle_y + PADDLE_HEIGHT // 2)

def reset_ball():
    game_state['ball']['x'] = SCREEN_WIDTH // 2
    game_state['ball']['y'] = SCREEN_HEIGHT // 2
    game_state['ball']['dx'] = 4 if random.random() > 0.5 else -4
    game_state['ball']['dy'] = 2 if random.random() > 0.5 else -2

def game_loop():
    print("🎮 Game loop started")
    while True:
        socketio.sleep(0.016)
        
        if len(game_state['players']) < 2 or not game_state['game_active']:
            continue
        
        ball = game_state['ball']
        ball['x'] += ball['dx']
        ball['y'] += ball['dy']
        
        # Столкновение со стенами
        if ball['y'] - ball['radius'] <= 0 or ball['y'] + ball['radius'] >= SCREEN_HEIGHT:
            ball['dy'] *= -1
        
        # Столкновение с ракетками
        for player in game_state['players'].values():
            if check_paddle_collision(ball, player):
                ball['dx'] *= -1.05
                ball['dy'] += player['dy'] * 0.3
                ball['dy'] = max(-10, min(10, ball['dy']))
                break
        
        # Подсчёт очков
        if ball['x'] - ball['radius'] <= 0:
            for pid, p in game_state['players'].items():
                if p['position'] == 'right':
                    p['score'] += 1
                    break
            reset_ball()
        elif ball['x'] + ball['radius'] >= SCREEN_WIDTH:
            for pid, p in game_state['players'].items():
                if p['position'] == 'left':
                    p['score'] += 1
                    break
            reset_ball()
        
        socketio.emit('game_state', get_game_state_for_client())

@app.route('/')
def index():
    return "🏓 Pong Game Server is running!"

if __name__ == '__main__':
    # Автоматический поиск свободного порта
    print("🔍 Поиск свободного порта...")
    port = find_free_port(8000, 10)
    
    if port is None:
        print("❌ Не удалось найти свободный порт в диапазоне 8000-8009")
        sys.exit(1)
    
    # Определяем локальный IP
    local_ip = get_local_ip()
    
    # Проверяем валидность IP
    try:
        socket.inet_aton(local_ip)
    except socket.error:
        print(f"⚠️  Недопустимый IP-адрес обнаружен: {local_ip}")
        print("   Используем 127.0.0.1 как резервный вариант")
        local_ip = "127.0.0.1"
    
    print("\n" + "="*70)
    print("🏓 СЕРВЕР ПИН-ПОНГ ЗАПУЩЕН")
    print("="*70)
    print(f"✅ Сервер работает на: 0.0.0.0:{port}")
    print(f"🏠 Ваш локальный IP:   {local_ip}:{port}")
    print("="*70)
    print("📱 Как подключиться с другого устройства в локальной сети:")
    print(f"   1. Убедитесь, что оба устройства в одной Wi-Fi сети")
    print(f"   2. На клиенте: Настройки сервера → Введите '{local_ip}'")
    print(f"   3. Нажмите 'Подключиться к серверу'")
    print("="*70)
    print("⚠️  Если подключение не работает:")
    print("   • Проверьте брандмауэр (разрешите порт)")
    print("   • Убедитесь, что оба устройства в одной подсети")
    print("="*70 + "\n")
    
    socketio.start_background_task(game_loop)
    
    # Запуск сервера
    try:
        socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
    except Exception as e:
        print(f"❌ Ошибка запуска сервера: {e}")
        print("Попытка запуска на localhost...")
        socketio.run(app, host='127.0.0.1', port=port, debug=False, allow_unsafe_werkzeug=True)