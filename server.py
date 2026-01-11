from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit, join_room, leave_room
import arcade

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 500
SCREEN_TITLE = "Пин Понг!"


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

socketio = SocketIO(app)

# Dictionary to store users and their assigned rooms
users = {}


# Handle new user joining
@socketio.on('join')
def handle_join(username):
    users[request.sid] = username  # Store username by session ID
    join_room(username)  # Each user gets their own "room"
    emit("message", f"{username} joined the chat", room=username)

# Handle user messages
@socketio.on('message')
def handle_message(data):
    username = users.get(request.sid, "Anonymous")
    emit("message", f"{data}", broadcast=True)
    f.write(f"{data}\n")

# Handle disconnects
@socketio.on('disconnect')
def handle_disconnect():
    username = users.pop(request.sid, "Anonymous")
    emit("message", f"{username} left the chat", broadcast=True)

if __name__ == '__main__':
    with open("data.txt", "w") as f:
        socketio.run(app, debug=True)
class MenuView(arcade.View):
    def __init__(self):
        super().__init__()

    def on_draw(self):
        self.clear()
        arcade.draw_text("Меню", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50,
                         arcade.color.WHITE, font_size=40, anchor_x="center")
        arcade.draw_text("Нажмите M для возврата в игру", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                         arcade.color.WHITE, font_size=20, anchor_x="center")
        arcade.draw_text("Кликните здесь или нажмите ESC — выход", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 30,
                         arcade.color.RED, font_size=16, anchor_x="center")

    def on_mouse_press(self, x, y, button, modifiers):
        arcade.close_window()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.M:
            game_view = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
            game_view.setup()
            self.window.show_view(game_view)
        elif key == arcade.key.ESCAPE:
            arcade.close_window()
