import arcade
import random
import socketio
import time
import os

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 500
SCREEN_TITLE = "🏓 Сетевой Пин-Понг"

class GameState:
    MENU = 0
    CONNECTING = 1
    WAITING = 2
    PLAYING = 3
    SKIN_SELECT = 4

class PongGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)
        
        # Состояние игры
        self.game_state = GameState.MENU
        self.username = f"Player_{random.randint(1000, 9999)}"
        self.position = None
        
        # Система скинов
        self.paddle_skins = [
            {"name": "Стандарт", "path": None},
            {"name": "Дерево", "path": "skins/paddle_wood.png"},
            {"name": "Металл", "path": "skins/paddle_metal.png"},
            {"name": "Космос", "path": "skins/paddle_space.png"},
            {"name": "Огонь", "path": "skins/paddle_fire.png"},
        ]
        self.selected_skin_index = 0
        self.skin_textures = {}
        
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
        self.menu_options = ["▶ Подключиться к серверу", "✏ Сменить ник", "🎨 Выбрать скин ракетки", "🚪 Выйти"]
        
        # Предзагрузка текстур
        self.load_skin_textures()

    def load_skin_textures(self):
        """Предзагрузка текстур скинов с обработкой ошибок"""
        for skin in self.paddle_skins:
            if skin["path"] and os.path.exists(skin["path"]):
                try:
                    texture = arcade.load_texture(skin["path"])
                    self.skin_textures[skin["path"]] = texture
                    print(f"✅ Загружен скин: {skin['name']}")
                except Exception as e:
                    print(f"⚠️ Ошибка загрузки скина {skin['name']}: {e}")
                    self.skin_textures[skin["path"]] = None
            else:
                self.skin_textures[skin["path"]] = None

    def create_paddle_sprite(self, is_player=True):
        """Создаёт спрайт ракетки с учётом выбранного скина"""
        skin = self.paddle_skins[self.selected_skin_index]
        texture = self.skin_textures.get(skin["path"]) if skin["path"] else None
        
        if texture:
            sprite = arcade.Sprite(texture=texture)
            sprite.width = 15
            sprite.height = 100
        else:
            # Используем SpriteSolidColor вместо устаревших функций рисования
            color = arcade.color.BLUE if is_player else arcade.color.RED
            sprite = arcade.SpriteSolidColor(15, 100, color)
        
        return sprite

    def setup_socket_events(self):
        @self.sio.event
        def connect():
            self.connection_status = "подключён"
            self.connection_error = None
            print("✅ Подключено к серверу")
            self.sio.emit('join', {'username': self.username, 'skin_index': self.selected_skin_index})
        
        @self.sio.event
        def disconnect():
            self.connection_status = "отключён"
            if self.game_state not in [GameState.MENU, GameState.SKIN_SELECT]:
                self.game_state = GameState.MENU
            print("❌ Отключено от сервера")
        
        @self.sio.event
        def game_state(data):
            if not self.ball:
                self.ball = arcade.SpriteCircle(10, arcade.color.WHITE)
            
            if not self.paddle:
                self.paddle = self.create_paddle_sprite(is_player=True)
            if not self.opponent_paddle:
                self.opponent_paddle = self.create_paddle_sprite(is_player=False)
            
            self.ball.center_x = data['ball']['x']
            self.ball.center_y = data['ball']['y']
            
            players = list(data['players'].values())
            if len(players) > 0:
                if self.position is None:
                    self.position = players[0]['position']
                
                for player in players:
                    is_our_paddle = player['position'] == self.position
                    target_paddle = self.paddle if is_our_paddle else self.opponent_paddle
                    target_paddle.center_x = player['x']
                    target_paddle.center_y = player['y']
                    
                    if is_our_paddle:
                        self.score = player.get('score', 0)
                    else:
                        self.opponent_score = player.get('score', 0)
            
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
        try:
            self.game_state = GameState.CONNECTING
            self.connection_status = "подключение..."
            self.sio.connect('http://127.0.0.1:8000', transports=['websocket'], wait=True, wait_timeout=5)
            time.sleep(0.3)
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
        self.clear()
        
        if self.game_state == GameState.MENU:
            self.draw_menu()
        elif self.game_state == GameState.SKIN_SELECT:
            self.draw_skin_select()
        elif self.game_state == GameState.CONNECTING:
            self.draw_connecting()
        elif self.game_state == GameState.WAITING:
            self.draw_waiting()
        elif self.game_state == GameState.PLAYING:
            self.draw_game()
        
        # Индикатор подключения
        status_color = arcade.color.GREEN if self.connection_status == "подключён" else arcade.color.RED
        arcade.draw_circle_filled(SCREEN_WIDTH - 20, 20, 8, status_color)
        arcade.draw_text(self.connection_status, SCREEN_WIDTH - 100, 12, 
                        arcade.color.WHITE, 12, anchor_x="right")

    def draw_menu(self):
        arcade.draw_text("🏓 СЕТЕВОЙ ПИН-ПОНГ", SCREEN_WIDTH/2, SCREEN_HEIGHT - 80,
                        arcade.color.WHITE, 42, anchor_x="center", font_name="Arial")
        
        for i, option in enumerate(self.menu_options):
            color = arcade.color.YELLOW if i == self.menu_selection else arcade.color.LIGHT_GRAY
            arcade.draw_text(option, SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - i*60,
                           color, 24, anchor_x="center", font_name="Arial")
        
        arcade.draw_text(f"Ник: {self.username}", SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 80,
                       arcade.color.BLUE, 20, anchor_x="center")
        arcade.draw_text(f"Скин: {self.paddle_skins[self.selected_skin_index]['name']}", 
                       SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 50,
                       arcade.color.GREEN, 18, anchor_x="center")
        
        if self.connection_error:
            arcade.draw_text(f"⚠️ {self.connection_error}", SCREEN_WIDTH/2, 50,
                           arcade.color.RED, 16, anchor_x="center")

    def draw_skin_select(self):
        arcade.draw_text("🎨 Выбор скина ракетки", SCREEN_WIDTH/2, SCREEN_HEIGHT - 80,
                        arcade.color.WHITE, 36, anchor_x="center", font_name="Arial")
        
        preview_y = SCREEN_HEIGHT // 2
        skin = self.paddle_skins[self.selected_skin_index]
        
        # Рисуем превью скина
        if skin["path"] and self.skin_textures.get(skin["path"]):
            texture = self.skin_textures[skin["path"]]
            arcade.draw_texture_rectangle(
                SCREEN_WIDTH // 2, preview_y, 
                60, 400,
                texture
            )
        else:
            # Используем современный метод рисования прямоугольника
            color = arcade.color.BLUE if self.selected_skin_index == 0 else arcade.color.PURPLE
            # draw_xywh_rectangle_filled: x, y, width, height, color
            arcade.draw_lbwh_rectangle_filled(
                SCREEN_WIDTH // 2 - 30,  # x (левый нижний угол)
                preview_y - 200,          # y (левый нижний угол)
                60,                       # ширина
                400,                      # высота
                color
            )
        
        arcade.draw_text(f"{skin['name']}", SCREEN_WIDTH/2, preview_y - 250,
                       arcade.color.WHITE, 28, anchor_x="center", bold=True)
        
        arcade.draw_text("← → : выбор скина", SCREEN_WIDTH/2, 100,
                       arcade.color.LIGHT_GRAY, 18, anchor_x="center")
        arcade.draw_text("ENTER/ESC : назад", SCREEN_WIDTH/2, 60,
                       arcade.color.DIM_GRAY, 16, anchor_x="center")

    def draw_connecting(self):
        arcade.draw_text("Подключение к серверу...", SCREEN_WIDTH/2, SCREEN_HEIGHT/2,
                        arcade.color.WHITE, 32, anchor_x="center")
        arcade.draw_text("Порт: 8000", SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 40,
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
        # Центральная пунктирная линия (используем современный метод)
        for y in range(0, SCREEN_HEIGHT, 40):
            # draw_xywh_rectangle_filled: x, y, width, height, color
            arcade.draw_xywh_rectangle_filled(
                SCREEN_WIDTH/2 - 2,  # x
                y + 8,               # y (с центрированием)
                4,                   # ширина
                25,                  # высота
                arcade.color.WHITE
            )
        
        if self.paddle:
            self.paddle.draw()
        if self.opponent_paddle:
            self.opponent_paddle.draw()
        if self.ball:
            self.ball.draw()
        
        arcade.draw_text(str(self.score), SCREEN_WIDTH/4, SCREEN_HEIGHT - 70,
                       arcade.color.WHITE, 48, anchor_x="center", font_name="Arial")
        arcade.draw_text(str(self.opponent_score), 3*SCREEN_WIDTH/4, SCREEN_HEIGHT - 70,
                       arcade.color.WHITE, 48, anchor_x="center", font_name="Arial")
        
        arcade.draw_text("W/S — управление ракеткой", 10, 10,
                       arcade.color.GRAY, 14)

    def on_update(self, delta_time):
        if self.game_state != GameState.PLAYING or not self.paddle:
            return
        
        if arcade.key.W in self.keys_pressed:
            self.paddle_dy = self.paddle_speed
        elif arcade.key.S in self.keys_pressed:
            self.paddle_dy = -self.paddle_speed
        else:
            self.paddle_dy = 0
        
        self.paddle.center_y += self.paddle_dy
        self.paddle.center_y = max(50, min(SCREEN_HEIGHT - 50, self.paddle.center_y))
        
        if self.sio.connected and self.game_state == GameState.PLAYING:
            self.sio.emit('player_move', {
                'dy': self.paddle_dy,
                'y': self.paddle.center_y
            })

    def on_key_press(self, key, modifiers):
        self.keys_pressed.add(key)
        
        if self.game_state == GameState.MENU:
            if key == arcade.key.UP:
                self.menu_selection = (self.menu_selection - 1) % len(self.menu_options)
            elif key == arcade.key.DOWN:
                self.menu_selection = (self.menu_selection + 1) % len(self.menu_options)
            elif key == arcade.key.ENTER:
                if self.menu_selection == 0:
                    self.connect_to_server()
                elif self.menu_selection == 1:
                    self.username = f"Player_{random.randint(1000, 9999)}"
                elif self.menu_selection == 2:
                    self.game_state = GameState.SKIN_SELECT
                elif self.menu_selection == 3:
                    self.close()
            elif key == arcade.key.ESCAPE:
                self.close()
        
        elif self.game_state == GameState.SKIN_SELECT:
            if key == arcade.key.LEFT:
                self.selected_skin_index = (self.selected_skin_index - 1) % len(self.paddle_skins)
            elif key == arcade.key.RIGHT:
                self.selected_skin_index = (self.selected_skin_index + 1) % len(self.paddle_skins)
            elif key in [arcade.key.ENTER, arcade.key.ESCAPE]:
                self.game_state = GameState.MENU
        
        elif self.game_state in [GameState.CONNECTING, GameState.WAITING]:
            if key == arcade.key.ESCAPE:
                if self.sio.connected:
                    self.sio.disconnect()
                self.game_state = GameState.MENU
        
        elif self.game_state == GameState.PLAYING:
            if key == arcade.key.ESCAPE:
                if self.sio.connected:
                    self.sio.disconnect()
                self.reset_game_state()

    def on_key_release(self, key, modifiers):
        self.keys_pressed.discard(key)

    def reset_game_state(self):
        self.game_state = GameState.MENU
        self.position = None
        self.ball = None
        self.paddle = None
        self.opponent_paddle = None
        self.score = 0
        self.opponent_score = 0

    def on_close(self):
        if self.sio.connected:
            self.sio.disconnect()
            time.sleep(0.2)
        super().on_close()

def main():
    print("🚀 Запуск клиента...")
    print("📁 Доступные скины (поместите файлы в папку skins/):")
    print("   paddle_wood.png, paddle_metal.png, paddle_space.png, paddle_fire.png")
    print("⚠️  Убедитесь, что сервер запущен на порту 8000")
    window = PongGame()
    arcade.run()

if __name__ == "__main__":
    main()