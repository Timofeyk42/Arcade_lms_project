import arcade

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
        self.player = arcade.Sprite(":resources:images/animated_characters/female_person/femalePerson_idle.png", 0.5)
        self.player.center_x = 100
        self.player.center_y = 200
        self.player_speed_x = 5
        self.player_speed_y = -1
        
        self.player_list = arcade.SpriteList()
        self.player_list.append(self.player)
        
        
        # Создаём стены (вернее, пол в этом конкретном случае)
        self.wall_list = arcade.SpriteList()
        for x in range(0, 1000, 64):
            wall = arcade.Sprite(":resources:images/tiles/grassMid.png", 0.5)
            wall.center_x = x
            wall.center_y = 32
            self.wall_list.append(wall)
        
        # Создаём физический движок
        self.physics_engine = arcade.PhysicsEngineSimple(
            self.player, 
            self.wall_list
        )

    def on_update(self, delta_time):
        # Обновляем физический движок
        self.physics_engine.update()
        
        # Обновляем движение игрока
        self.player.change_x = self.player_speed_x
        self.player.change_y = self.player_speed_y

    def on_draw(self):
        """Отрисовка всех спрайтов"""
        self.clear()
        self.player_list.draw()
        self.wall_list.draw()

def main():
    game = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    game.setup()
    arcade.run()


if __name__ == "__main__":
    main()