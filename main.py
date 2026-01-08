import arcade
import time
import random

#Задачи:
#Написать локально для 2 игроков
#Разобраться с физикой

# Задаём размер окна
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 500
SCREEN_TITLE = "Пин Понг!"

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
        
    def on_update(self, delta_time):
        self.ball.update()
        self.player1.update()
        self.player2.update()


        if self.ball.top > SCREEN_HEIGHT or self.ball.bottom < 0:
            self.ball.change_y *= -1
        if self.ball.right > SCREEN_WIDTH or self.ball.left < 0:
            time.sleep(1)
            self.restart()
            
        if arcade.check_for_collision(self.ball, self.player1):
            self.collisions(self.player1)
            self.p_s *= 1.03
        if arcade.check_for_collision(self.ball, self.player2):
            self.collisions(self.player2)
            self.p_s *= 1.03

    def on_draw(self): 
        """Отрисовка всех спрайтов"""
        self.clear()
        self.player_list.draw()
        self.balll.draw()
    
    def on_key_press(self, key, modifiers):
        if key == arcade.key.S:
            self.player1.change_y = -self.p_s
        elif key == arcade.key.W:
            self.player1.change_y = self.p_s
        if key == arcade.key.DOWN:
            self.player2.change_y = -self.p_s
        elif key == arcade.key.UP:
            self.player2.change_y = self.p_s
        
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
        self.p_s = 3
        print(f"{self.ball.change_x}/{self.ball.change_y}")
    
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