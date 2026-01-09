import arcade
import time
import random
from pyglet.graphics import Batch
import socketio
#Задачи:
#Написать локально для 2 игроков
#Разобраться с физикой

# Задаём размер окна
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 500
SCREEN_TITLE = "Пин Понг!"


sio = socketio.Client()

@sio.event
def connect():
    print("Подключились к серверу")
    sio.emit('join', 'player1')

@sio.event
def message(data):
    print(f"📩 Получено сообщение: {data}")

@sio.event
def disconnect():
    print("Отключились от сервера")


# class MenuView(arcade.View): ТЫ В КОМЕНТАХ К КОМИТУ НАПИСАЛ РОКЕТКИ АХАХАХАХАХХАХАХАХАХАХАХАХАХАХАХАХАХХАХАХАХАХАХА
#     def __init__(self):
#         super().__init__()

#     def on_draw(self):
#         self.clear()
#         arcade.draw_text("Меню", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50,
#                          arcade.color.WHITE, font_size=40, anchor_x="center")
#         arcade.draw_text("Нажмите M для возврата в игру", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
#                          arcade.color.WHITE, font_size=20, anchor_x="center")
#         arcade.draw_text("Кликните здесь или нажмите ESC — выход", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 30,
#                          arcade.color.RED, font_size=16, anchor_x="center")

#     def on_mouse_press(self, x, y, button, modifiers):
#         arcade.close_window()

#     def on_key_press(self, key, modifiers):
#         if key == arcade.key.M:
#             game_view = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
#             game_view.setup()
#             self.window.show_view(game_view)
#         elif key == arcade.key.ESCAPE:
#             arcade.close_window()



class MyGame(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        arcade.set_background_color(arcade.color.ASH_GREY)
      

    def setup(self):
        # Создаём игрока
        self.ball = arcade.Sprite(":resources:images/pinball/pool_cue_ball.png", 0.5)
        self.player1 = arcade.Sprite("pong.png", 0.5)
        self.player2 = arcade.Sprite("pong.png", 0.5)
        self.player1.center_x = 100
        self.player1.center_y = 250
        self.player2.center_x = 900
        self.player2.center_y = 250
        self.ball.center_x = 200
        self.ball.center_y = 300
        self.ball.change_x = [-4, 4][random.randint(0, 1)]
        self.ball.change_y = random.randint(-2, 2)
        
        self.player_list = arcade.SpriteList()
        self.balll = arcade.SpriteList()
        self.balll.append(self.ball)
        self.player_list.append(self.player1)
        self.player_list.append(self.player2)
        self.p_s = 3

        self.P1 = 0
        self.P2 = 0

        sio.connect('http://127.0.0.1:5000')
        time.sleep(0.5)


    def on_update(self, delta_time):
        self.ball.update()
        self.player1.update()
        self.player2.update()

        self.batch = Batch()
        self.main_text1 = arcade.Text("Твои очки: " + str(self.P1), SCREEN_WIDTH / 5 - 20, SCREEN_HEIGHT / 3 + 250,
                                     arcade.color.BLUE_GRAY, font_size=20, anchor_x="center", batch=self.batch)
        self.main_text2 = arcade.Text("Его очки: " + str(self.P2), SCREEN_WIDTH - 200, SCREEN_HEIGHT / 3 + 250,
                                     arcade.color.BLUE_GRAY, font_size=20, anchor_x="center", batch=self.batch)
        

        if self.ball.top > SCREEN_HEIGHT or self.ball.bottom < 0:
            self.ball.change_y *= -1
        if self.ball.right > SCREEN_WIDTH:
            time.sleep(0.5)
            self.P1 += 1
            self.restart()
        elif self.ball.left < 0:
            self.P2 += 1
            time.sleep(0.5)
            self.restart()
            
        if arcade.check_for_collision(self.ball, self.player1):
            self.collisions(self.player1)
            self.p_s *= 1.03
        if arcade.check_for_collision(self.ball, self.player2):
            self.collisions(self.player2)
            self.p_s *= 1.03
        if self.player1.bottom <= 0:
            self.player1.change_y = 0
        if self.player1.top >= SCREEN_HEIGHT:
            self.player1.change_y = 0
        if self.player2.bottom <= 0:
            self.player2.change_y = 0
        if self.player2.top >= SCREEN_HEIGHT:
            self.player2.change_y = 0
        
        sio.emit("message", f"py:{self.player1.center_y}")

    def on_draw(self): 
        """Отрисовка всех спрайтов"""
        self.clear()
        self.player_list.draw()
        self.balll.draw()
        self.batch.draw()


    def on_key_press(self, key, modifiers):
        if key == arcade.key.S:
            self.player1.change_y = -self.p_s
        elif key == arcade.key.W:
            self.player1.change_y = self.p_s
        if key == arcade.key.DOWN:
            self.player2.change_y = -self.p_s
        elif key == arcade.key.UP:
            self.player2.change_y = self.p_s
        # if key == arcade.key.M:
        #     menu_view = MenuView()
        #     self.show_view(menu_view)
          
        
    def on_key_release(self, key, modifiers):
        if key == arcade.key.S:
            self.player1.change_y = 0
        if key == arcade.key.W:
            self.player1.change_y = 0
        if key == arcade.key.DOWN:
            self.player2.change_y = 0
        if key == arcade.key.UP:
            self.player2.change_y = 0
    
    def restart(self):
        self.player1.center_x = 100
        self.player1.center_y = 250
        self.player2.center_x = 900
        self.player2.center_y = 250
        self.ball.center_x = 500
        self.ball.center_y = 250
        self.ball.change_x = [-4, 4][random.randint(0, 1)]
        self.ball.change_y = random.randint(-3, 3)
        if self.ball.change_y <= 0.9 and self.ball.change_y >= -0.9:
            self.ball.change_y = random.randint(-0.9, -3)
        self.p_s = 3

    def collisions(self, paddle):
        if paddle.center_x < SCREEN_WIDTH / 2:
            self.ball.center_x = paddle.right + self.ball.width / 2
        else:
            self.ball.center_x = paddle.left - self.ball.width / 2
        self.ball.change_x = -self.ball.change_x
        self.ball.change_y += paddle.change_y * 0.4
        self.ball.change_y = max(-7.0, min(7.0, self.ball.change_y))
        speed_factor = 1.03
        self.ball.change_x *= speed_factor
        MAX_SPEED_X = 15.0
        if abs(self.ball.change_x) > MAX_SPEED_X:
            self.ball.change_x = MAX_SPEED_X if self.ball.change_x > 0 else -MAX_SPEED_X


        
def main():
    game = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    game.setup()
    arcade.run()


if __name__ == "__main__":
    main()
    sio.disconnect()