import arcade

#Задачи:
#Написать локально для 2 игроков
#Разобраться с физикой
#Нарисовать текстуры

# Задаём размер окна
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Пин Понг!"

class MyGame(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        arcade.set_background_color(arcade.color.ASH_GREY)

    def setup(self):
        # Создаём игрока
        self.ball = arcade.Sprite(":resources:images/pinball/pool_cue_ball.png", 0.5)
        self.player1 = arcade.Sprite(":resources:images/pinball/pool_cue_ball.png", 0.5)
        self.player2 = arcade.Sprite(":resources:images/pinball/pool_cue_ball.png", 0.5)
        self.player1.center_x = 200
        self.player1.center_y = 200
        self.player2.center_x = 300
        self.player2.center_y = 200
        self.ball.center_x = 200
        self.ball.center_y = 300
        self.ball.change_x = 3
        self.ball.change_y = -4
        
        self.player_list = arcade.SpriteList()
        self.balll = arcade.SpriteList()
        self.balll.append(self.ball)
        self.player_list.append(self.player1)
        self.player_list.append(self.player2)
        
    def on_update(self, delta_time):
        self.ball.update()

        if self.ball.top > SCREEN_HEIGHT or self.ball.bottom < 0:
            self.ball.change_y *= -1
        if self.ball.right > SCREEN_WIDTH or self.ball.left < 0:
            self.ball.change_x *= -1

    def on_draw(self): 
        """Отрисовка всех спрайтов"""
        self.clear()
        self.player_list.draw()
        self.balll.draw()

def main():
    game = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    game.setup()
    arcade.run()


if __name__ == "__main__":
    main()