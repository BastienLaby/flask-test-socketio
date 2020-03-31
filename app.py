import random
import time
from collections import defaultdict

from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room


class Config(object):
    FLASK_ENV = "development"
    FLASK_DEBUG = True


app = Flask("flaskapp", template_folder="./templates", static_folder="./static")
app.config.from_object(Config)
socketio = SocketIO(app)


# routes


@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")


# socketio

# To receive WebSocket messages from the client,
# the application defines event handlers using the socketio.on decorator
# To send events, a Flask server can use the send() and emit() functions
# send() function sends a standard message of string or JSON type to the client
# emit() function sends a message under a custom event name


def generate_name():
    random.seed(time.time())
    number = random.randint(1, 999)
    return f'Michel{number:03d}'


users_rooms = defaultdict(list)


@socketio.on("connect", namespace="/test")  # "connect" is a reserved event name
def connect():
    username = generate_name()
    users_rooms[username] = []
    emit("server_message", {
        "type": "connection_feedback",
        "prefix": f"client",
        "message": f"Welcome {username}. You are now connected !",
        "username": username
    })


@socketio.on("simple_message", namespace="/test")
def simple_message(message):
    """
    Emit the received message back to the client.
    """
    emit("server_message", {
        "type": "simple_message_feedback",
        "prefix": f"client",
        "message": f'Message {message["message"]} received by the server'
    })


@socketio.on("broadcast_message", namespace="/test")
def broadcast_message(message):
    """
    Emit the received message to all connected clients.
    """
    emit("server_message", {
        "type": "broadcast_message",
        "prefix": f"all",
        "message": message["message"],
    }, broadcast=True)  # send to all connected clients


@socketio.on("room_message", namespace="/test")
def room_message(message):
    """
    Send the received message to every client in the given room
    """
    emit("server_message", {
            "type": "room_message",
            "prefix": message["room"],
            "message": message["message"]
        },
        room=message["room"]  # send to every client which has joined the room
    )


@socketio.on("user_join_room", namespace="/test")
def user_join_room(message):
    """
    Join the given client to the given room and send feedback messages.
    """
    room = message["room"]
    username = message["username"]
    if room not in users_rooms[username]:
        users_rooms[username].append(room)
        join_room(room)

        emit("server_message", {
            "type": "room_joined",
            "prefix": f"client",
            "message": f"You joined the room #{room}",
            "room": f'{room}'
        })

        emit("server_message", {
                "type": "user_joined_room",
                "prefix": f"#{room}",
                "message": f"User #{username} has joined the room"
            },
            room=room
        )

        emit("server_message", {
            "type": "rooms_updated",
            "rooms": users_rooms[username]
        })


@socketio.on("user_leave_room", namespace="/test")
def user_leave_room(message):
    """
    Pop the client from the room and send feedback messages.
    """
    room = message["room"]
    username = message["username"]
    if room in users_rooms[username]:
        users_rooms[username].remove(room)
    leave_room(room)
    emit("server_message", {
            "type": "user_leave_room",
            "prefix": f"#{room}",
            "message": f"User #{username} left the room"
        },
        room=room
    )
    emit("server_message", {
        "type": "rooms_updated",
        "rooms": users_rooms[username]
    })


if __name__ == '__main__':
    socketio.run(app, debug=True)
