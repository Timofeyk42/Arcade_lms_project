import arcade
import random
import socketio
import time

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 500
SCREEN_TITLE = "🏓 Сетевой Пин-Понг"

class GameState:
    MENU = 0
    CONNECTING = 1
    WAITING = 2
    PLAYING = 3

class PongGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)
        
        # Состояние игры
        self.game_state = GameState.MENU
        self.username = f"Player_{random.randint(1000, 9999)}"
        self.position = None
        
        # Сетевые компоненты
        self.sio = socketio.Client()
        self.setup_socket_events()
        self.connection_status = "отключён"
        self.connection_error = None
        
        # Игровые объекты
        self.ball = None
        self.paddle = None
        self.opponent_paddle = None
        self.score = 0
        self.opponent_score = 0
        
        # Управление
        self.paddle_speed = 7
        self.paddle_dy = 0
        self.keys_pressed = set()
        
        # UI
        self.waiting_players = 1
        self.menu_selection = 0

    def setup_socket_events(self):
        @self.sio.event
        def connect():
            self.connection_status = "подключён"
            self.connection_error = None
            print("✅ Подключено к серверу")
            self.sio.emit('join', {'username': self.username})
        
        @self.sio.event
        def disconnect():
            self.connection_status = "отключён"
            if self.game_state != GameState.MENU:
                self.game_state = GameState.MENU
            print("❌ Отключено от сервера")
        
        @self.sio.event
        def game_state(data):
            # Инициализация спрайтов при первом получении состояния
            if not self.ball:
                self.ball = arcade.SpriteCircle(10, arcade.color.WHITE)
            if not self.paddle:
                self.paddle = arcade.SpriteSolidColor(15, 100, arcade.color.BLUE)
            if not self.opponent_paddle:
                self.opponent_paddle = arcade.SpriteSolidColor(15, 100, arcade.color.RED)
            
            # Обновляем мяч
            self.ball.center_x = data['ball']['x']
            self.ball.center_y = data['ball']['y']
            
            # Обновляем ракетки и счёт
            players = list(data['players'].values())
            scores = list(data['scores'].values())
            
            if len(players) > 0:
                # Определяем нашу позицию при первом подключении
                if self.position is None:
                    self.position = players[0]['position']
                
                # Находим нашу ракетку
                for player in players:
                    if player['position'] == self.position:
                        self.paddle.center_x = player['x']
                        self.paddle.center_y = player['y']
                        self.score = player.get('score', 0)
                    else:
                        self.opponent_paddle.center_x = player['x']
                        self.opponent_paddle.center_y = player['y']
                        self.opponent_score = player.get('score', 0)
            
            # Переходим в состояние игры если 2 игрока
            if len(players) >= 2 and self.game_state == GameState.WAITING:
                self.game_state = GameState.PLAYING
        
        @self.sio.event
        def players_update(data):
            self.waiting_players = data['count']
            if self.waiting_players >= 2 and self.game_state == GameState.WAITING:
                self.game_state = GameState.PLAYING
        
        @self.sio.event
        def error(data):
            self.connection_error = data.get('message', 'Ошибка подключения')
            print(f"❌ Ошибка сервера: {self.connection_error}")
            self.game_state = GameState.MENU

    def connect_to_server(self):
        """Синхронное подключение с таймаутом"""
        try:
            self.game_state = GameState.CONNECTING
            self.connection_status = "подключение..."
            self.sio.connect('http://127.0.0.1:8000', transports=['websocket'], wait=True, wait_timeout=5)
            time.sleep(0.3)  # Дать время на инициализацию
            if self.sio.connected:
                self.game_state = GameState.WAITING
                self.connection_status = "подключён"
                return True
            else:
                self.connection_error = "Таймаут подключения"
                self.game_state = GameState.MENU
                return False
        except Exception as e:
            self.connection_error = f"Ошибка: {str(e)[:50]}"
            print(f"❌ Ошибка подключения: {e}")
            self.game_state = GameState.MENU
            return False

    def on_draw(self):
        # ИСПРАВЛЕНО: start_render() заменён на clear()
        self.clear()
        
        if self.game_state == GameState.MENU:
            self.draw_menu()
        elif self.game_state == GameState.CONNECTING:
            self.draw_connecting()
        elif self.game_state == GameState.WAITING:
            self.draw_waiting()
        elif self.game_state == GameState.PLAYING:
            self.draw_game()
        
        # Индикатор подключения (в правом нижнем углу)
        status_color = arcade.color.GREEN if self.connection_status == "подключён" else arcade.color.RED
        arcade.draw_circle_filled(SCREEN_WIDTH - 20, 20, 8, status_color)
        arcade.draw_text(self.connection_status, SCREEN_WIDTH - 100, 12, 
                        arcade.color.WHITE, 12, anchor_x="right")

    def draw_menu(self):
        arcade.draw_text("🏓 СЕТЕВОЙ ПИН-ПОНГ", SCREEN_WIDTH/2, SCREEN_HEIGHT - 80,
                        arcade.color.WHITE, 42, anchor_x="center", font_name="Arial")
        
        options = ["▶ Подключиться к серверу", "✏ Сменить ник", "🚪 Выйти"]
        for i, option in enumerate(options):
            color = arcade.color.YELLOW if i == self.menu_selection else arcade.color.LIGHT_GRAY
            arcade.draw_text(option, SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - i*60,
                           color, 24, anchor_x="center", font_name="Arial")
        
        arcade.draw_text(f"Ник: {self.username}", SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 80,
                       arcade.color.BLUE, 20, anchor_x="center")
        
        if self.connection_error:
            arcade.draw_text(f"⚠️ {self.connection_error}", SCREEN_WIDTH/2, 50,
                           arcade.color.RED, 16, anchor_x="center")

    def draw_connecting(self):
        arcade.draw_text("Подключение к серверу...", SCREEN_WIDTH/2, SCREEN_HEIGHT/2,
                        arcade.color.WHITE, 32, anchor_x="center")
        arcade.draw_text("Порт: 5001", SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 40,
                        arcade.color.GRAY, 18, anchor_x="center")
        arcade.draw_text("Нажмите ESC для отмены", SCREEN_WIDTH/2, 50,
                        arcade.color.DIM_GRAY, 16, anchor_x="center")

    def draw_waiting(self):
        arcade.draw_text("Ожидание второго игрока...", SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 50,
                       arcade.color.WHITE, 32, anchor_x="center")
        arcade.draw_text(f"Игроков: {self.waiting_players}/2", SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 20,
                       arcade.color.LIGHT_BLUE, 28, anchor_x="center")
        arcade.draw_text("Нажмите ESC для выхода", SCREEN_WIDTH/2, 50,
                       arcade.color.GRAY, 18, anchor_x="center")

    def draw_game(self):
        # Центральная пунктирная линия
        for y in range(0, SCREEN_HEIGHT, 40):
            arcade.draw_rectangle_filled(SCREEN_WIDTH/2, y + 20, 4, 25, arcade.color.WHITE)
        
        # Ракетки и мяч
        if self.paddle:
            self.paddle.draw()
        if self.opponent_paddle:
            self.opponent_paddle.draw()
        if self.ball:
            self.ball.draw()
        
        # Счёт
        arcade.draw_text(str(self.score), SCREEN_WIDTH/4, SCREEN_HEIGHT - 70,
                       arcade.color.WHITE, 48, anchor_x="center", font_name="Arial")
        arcade.draw_text(str(self.opponent_score), 3*SCREEN_WIDTH/4, SCREEN_HEIGHT - 70,
                       arcade.color.WHITE, 48, anchor_x="center", font_name="Arial")
        
        # Подсказка управления
        arcade.draw_text("W/S — управление ракеткой", 10, 10,
                       arcade.color.GRAY, 14)

    def on_update(self, delta_time):
        if self.game_state != GameState.PLAYING or not self.paddle:
            return
        
        # Обработка управления
        if arcade.key.W in self.keys_pressed:
            self.paddle_dy = self.paddle_speed
        elif arcade.key.S in self.keys_pressed:
            self.paddle_dy = -self.paddle_speed
        else:
            self.paddle_dy = 0
        
        # Обновление позиции ракетки
        self.paddle.center_y += self.paddle_dy
        self.paddle.center_y = max(50, min(SCREEN_HEIGHT - 50, self.paddle.center_y))
        
        # Отправка позиции на сервер (с ограничением частоты)
        if self.sio.connected and self.game_state == GameState.PLAYING:
            self.sio.emit('player_move', {
                'dy': self.paddle_dy,
                'y': self.paddle.center_y
            })

    def on_key_press(self, key, modifiers):
        self.keys_pressed.add(key)
        
        if self.game_state == GameState.MENU:
            if key == arcade.key.UP:
                self.menu_selection = (self.menu_selection - 1) % 3
            elif key == arcade.key.DOWN:
                self.menu_selection = (self.menu_selection + 1) % 3
            elif key == arcade.key.ENTER:
                if self.menu_selection == 0:  # Подключиться
                    self.connect_to_server()
                elif self.menu_selection == 1:  # Сменить ник
                    self.username = f"Player_{random.randint(1000, 9999)}"
                elif self.menu_selection == 2:  # Выйти
                    self.close()
            elif key == arcade.key.ESCAPE:
                self.close()
        
        elif self.game_state in [GameState.CONNECTING, GameState.WAITING]:
            if key == arcade.key.ESCAPE:
                if self.sio.connected:
                    self.sio.disconnect()
                self.game_state = GameState.MENU
        
        elif self.game_state == GameState.PLAYING:
            if key == arcade.key.ESCAPE:
                if self.sio.connected:
                    self.sio.disconnect()
                self.game_state = GameState.MENU
                self.position = None
                self.ball = None
                self.paddle = None
                self.opponent_paddle = None

    def on_key_release(self, key, modifiers):
        self.keys_pressed.discard(key)

    def on_close(self):
        if self.sio.connected:
            self.sio.disconnect()
            time.sleep(0.2)  # Дать время на корректное отключение
        super().on_close()

def main():
    print("🚀 Запуск клиента...")
    print("⚠️  Убедитесь, что сервер запущен на порту 5001")
    window = PongGame()
    arcade.run()

if __name__ == "__main__":
    main()