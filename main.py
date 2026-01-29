import arcade
import time
import random
import os
import socket

# === ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ===
TOTAL_POINTS = 0

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 500
SCREEN_TITLE = "Пин Понг!"

def create_blank_paddle_texture(width=20, height=100):
    img = arcade.Texture.create_filled(
        name="blank_paddle",
        size=(width, height),
        color=arcade.color.WHITE
    )
    return img

def get_local_ip():
    try:
        # Надёжный способ получить локальный IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# === ГЛАВНОЕ МЕНЮ ===
class MainMenu(arcade.View):
    def on_draw(self):
        self.clear()
        arcade.draw_text("🏓 ПИН-ПОНГ 🏓", SCREEN_WIDTH//2, SCREEN_HEIGHT - 60,
                         arcade.color.WHITE, font_size=30, anchor_x="center")
        arcade.draw_text(f"Очки: {TOTAL_POINTS}", SCREEN_WIDTH//2, SCREEN_HEIGHT - 100,
                         arcade.color.YELLOW, font_size=18, anchor_x="center")

        buttons = [
            ("[1] Играть", SCREEN_HEIGHT - 180),
            ("[2] Онлайн", SCREEN_HEIGHT - 220),
            ("[ESC] Выйти", 50)
        ]
        for text, y in buttons:
            arcade.draw_text(text, SCREEN_WIDTH//2, y, arcade.color.WHITE, font_size=20, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.KEY_1:
            game = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
            game.setup()
            self.window.show_view(game)
        elif key == arcade.key.KEY_2:
            self.window.show_view(OnlineMenu())
        elif key == arcade.key.ESCAPE:
            arcade.close_window()

# === ОНЛАЙН МЕНЮ ===
class OnlineMenu(arcade.View):
    def __init__(self):
        super().__init__()
        self.mode = None  # "create" or "join"
        self.input_ip = ""
        self.local_ip = get_local_ip()
        self.connected_clients = ["192.168.1.15", "192.168.1.22"]  # эмуляция

    def on_draw(self):
        self.clear()
        arcade.draw_text("🌐 ОНЛАЙН ИГРА 🌐", SCREEN_WIDTH//2, SCREEN_HEIGHT - 60,
                         arcade.color.BLUE, font_size=30, anchor_x="center")

        if self.mode is None:
            arcade.draw_text("[C] Создать сервер", SCREEN_WIDTH//2, SCREEN_HEIGHT - 150,
                             arcade.color.GREEN, font_size=20, anchor_x="center")
            arcade.draw_text("[J] Присоединиться", SCREEN_WIDTH//2, SCREEN_HEIGHT - 190,
                             arcade.color.ORANGE, font_size=20, anchor_x="center")
            arcade.draw_text("[ESC] Назад", SCREEN_WIDTH//2, 50,
                             arcade.color.GRAY, font_size=18, anchor_x="center")
        elif self.mode == "create":
            arcade.draw_text(f"✅ Сервер запущен", SCREEN_WIDTH//2, SCREEN_HEIGHT - 120,
                             arcade.color.LIME_GREEN, font_size=22, anchor_x="center")
            arcade.draw_text(f"Ваш IP: {self.local_ip}", SCREEN_WIDTH//2, SCREEN_HEIGHT - 160,
                             arcade.color.CYAN, font_size=18, anchor_x="center")
            arcade.draw_text("Подключились:", SCREEN_WIDTH//2, SCREEN_HEIGHT - 200,
                             arcade.color.WHITE, font_size=16, anchor_x="center")
            y = SCREEN_HEIGHT - 230
            for client in self.connected_clients:
                arcade.draw_text(f"• {client}", SCREEN_WIDTH//2, y,
                                 arcade.color.YELLOW, font_size=14, anchor_x="center")
                y -= 20
            arcade.draw_text("[ESC] Назад", SCREEN_WIDTH//2, 50,
                             arcade.color.GRAY, font_size=18, anchor_x="center")
        elif self.mode == "join":
            arcade.draw_text("Введите IP сервера:", SCREEN_WIDTH//2, SCREEN_HEIGHT - 150,
                             arcade.color.WHITE, font_size=20, anchor_x="center")
            arcade.draw_text(self.input_ip + "_", SCREEN_WIDTH//2, SCREEN_HEIGHT - 190,
                             arcade.color.CYAN, font_size=22, anchor_x="center")
            arcade.draw_text("[ENTER] Подключиться | [ESC] Отмена", SCREEN_WIDTH//2, 50,
                             arcade.color.GRAY, font_size=16, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if self.mode is None:
            if key == arcade.key.C:
                self.mode = "create"
            elif key == arcade.key.J:
                self.mode = "join"
                self.input_ip = ""
            elif key == arcade.key.ESCAPE:
                self.window.show_view(MainMenu())
        elif self.mode == "join":
            if key == arcade.key.ENTER:
                if self.input_ip.strip():
                    # Здесь можно было бы начать подключение
                    pass
                self.window.show_view(MainMenu())
            elif key == arcade.key.BACKSPACE:
                self.input_ip = self.input_ip[:-1]
            elif key == arcade.key.ESCAPE:
                self.mode = None
            elif 32 <= key <= 126:  # печатаемые символы
                self.input_ip += chr(key)
        elif self.mode == "create":
            if key == arcade.key.ESCAPE:
                self.mode = None

# === ИГРА ===
class MyGame(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        arcade.set_background_color(arcade.color.ASH_GREY)
        self.last_paddle_hit = None

    def setup(self):
        if os.path.exists("pong.png"):
            self.player1 = arcade.Sprite("pong.png", 0.5)
            self.player2 = arcade.Sprite("pong.png", 0.5)
        else:
            texture = create_blank_paddle_texture()
            self.player1 = arcade.Sprite(texture=texture, scale=1.0)
            self.player2 = arcade.Sprite(texture=texture, scale=1.0)

        self.ball = arcade.Sprite(":resources:images/pinball/pool_cue_ball.png", 0.5)

        self.player1.center_x = 100
        self.player1.center_y = 250
        self.player2.center_x = 900
        self.player2.center_y = 250
        self.ball.center_x = 500
        self.ball.center_y = 250
        self.ball.change_x = random.choice([-4, 4])
        self.ball.change_y = random.randint(-2, 2)

        self.player_list = arcade.SpriteList()
        self.ball_list = arcade.SpriteList()
        self.boost_list = arcade.SpriteList()

        self.player_list.append(self.player1)
        self.player_list.append(self.player2)
        self.ball_list.append(self.ball)

        self.p_s = 3
        self.P1 = 0
        self.P2 = 0

        self.speed_boost_end = 0
        self.size_boost_end = 0
        self.gravity_boost_end = 0

        self.last_spawn_time = time.time()
        self.spawn_interval = 8.0

        self.original_height1 = self.player1.height
        self.original_height2 = self.player2.height

    def spawn_boost(self):
        boost_sprite = arcade.Sprite(":resources:images/items/star.png", 0.4)
        boost_sprite.center_x = random.randint(200, 800)
        boost_sprite.center_y = random.randint(50, SCREEN_HEIGHT - 50)
        boost_sprite.boost_type = random.choice(["speed", "size", "gravity"])
        boost_sprite.lifetime = time.time() + 10
        self.boost_list.append(boost_sprite)

    def apply_boost(self, boost_type, player_side):
        now = time.time()
        duration = 5
        if boost_type == "speed":
            self.speed_boost_end = now + duration
        elif boost_type == "size":
            self.size_boost_end = now + duration
            if player_side == "left":
                self.player1.height = int(self.original_height1 * 1.5)
            else:
                self.player2.height = int(self.original_height2 * 1.5)
        elif boost_type == "gravity":
            self.gravity_boost_end = now + duration

    def on_update(self, delta_time):
        global TOTAL_POINTS
        now = time.time()

        if now - self.last_spawn_time > self.spawn_interval:
            self.spawn_boost()
            self.last_spawn_time = now

        for boost in self.boost_list[:]:
            if now > boost.lifetime:
                boost.remove_from_sprite_lists()

        if now < self.speed_boost_end:
            self.p_s = 3 * 1.5
        else:
            self.p_s = 3

        if now > self.size_boost_end:
            self.player1.height = self.original_height1
            self.player2.height = self.original_height2

        if now < self.gravity_boost_end:
            self.ball.change_y -= 0.2

        self.ball.update()
        self.player1.update()
        self.player2.update()

        if self.ball.top >= SCREEN_HEIGHT or self.ball.bottom <= 0:
            self.ball.change_y *= -1

        if self.ball.right >= SCREEN_WIDTH:
            self.P1 += 1
            TOTAL_POINTS += 1
            self.restart()
            return
        elif self.ball.left <= 0:
            self.P2 += 1
            self.restart()
            return

        if arcade.check_for_collision(self.ball, self.player1):
            self.collisions(self.player1)
            self.last_paddle_hit = "left"
        elif arcade.check_for_collision(self.ball, self.player2):
            self.collisions(self.player2)
            self.last_paddle_hit = "right"

        hit_boosts = arcade.check_for_collision_with_list(self.ball, self.boost_list)
        for boost in hit_boosts:
            if self.last_paddle_hit is not None:
                self.apply_boost(boost.boost_type, self.last_paddle_hit)
            boost.remove_from_sprite_lists()

        for paddle in [self.player1, self.player2]:
            if paddle.top > SCREEN_HEIGHT:
                paddle.top = SCREEN_HEIGHT
            if paddle.bottom < 0:
                paddle.bottom = 0

    def on_draw(self):
        self.clear()
        self.player_list.draw()
        self.ball_list.draw()
        self.boost_list.draw()
        arcade.draw_text(f"{self.P1} : {self.P2}", SCREEN_WIDTH//2, SCREEN_HEIGHT - 30,
                         arcade.color.WHITE, font_size=24, anchor_x="center")
        arcade.draw_text("[M] Меню", 50, 20, arcade.color.GRAY, font_size=14)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.W:
            self.player1.change_y = self.p_s
        elif key == arcade.key.S:
            self.player1.change_y = -self.p_s
        if key == arcade.key.UP:
            self.player2.change_y = self.p_s
        elif key == arcade.key.DOWN:
            self.player2.change_y = -self.p_s
        elif key == arcade.key.M:
            menu = MainMenu()
            self.window.show_view(menu)  # ✅ РАБОЧИЙ ВЫХОД В МЕНЮ

    def on_key_release(self, key, modifiers):
        if key in (arcade.key.W, arcade.key.S):
            self.player1.change_y = 0
        if key in (arcade.key.UP, arcade.key.DOWN):
            self.player2.change_y = 0

    def restart(self):
        self.ball.center_x = 500
        self.ball.center_y = 250
        self.ball.change_x = random.choice([-4, 4])
        self.ball.change_y = random.randint(-3, 3) or -2
        self.last_paddle_hit = None

    def collisions(self, paddle):
        offset = self.ball.width / 2
        if paddle.center_x < SCREEN_WIDTH / 2:
            self.ball.center_x = paddle.right + offset
        else:
            self.ball.center_x = paddle.left - offset
        self.ball.change_x *= -1.03
        self.ball.change_y += paddle.change_y * 0.4
        self.ball.change_y = max(-7, min(7, self.ball.change_y))
        if abs(self.ball.change_x) > 15:
            self.ball.change_x = 15 if self.ball.change_x > 0 else -15

# === ЗАПУСК ===
def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    menu = MainMenu()
    window.show_view(menu)
    arcade.run()

if __name__ == "__main__":
    main()