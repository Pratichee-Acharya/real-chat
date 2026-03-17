from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit
from datetime import datetime

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

app = Flask(__name__)
socketio = SocketIO(app)

users = {}  # {session_id: username}

@app.route("/")
def index():
    return render_template("chat.html")

# USER JOIN
@socketio.on("join")
def handle_join(username):
    users[request.sid] = username

    print("Users:", users)  # debug

    time = datetime.now().strftime("%H:%M:%S")
    send({
        "user": "System",
        "msg": f"{username} joined the chat",
        "time": time
    }, broadcast=True)

    emit("users", list(users.values()), broadcast=True)
    logging.info(f"{username} joined the chat")

# MESSAGE EVENT
@socketio.on("message")
def handle_message(data):
    username = data["user"]
    message = data["msg"]

    time = datetime.now().strftime("%H:%M:%S")

    send({
        "user": username,
        "msg": message,
        "time": time
    }, broadcast=True)
    logging.info(f"{username}: {message}")

# USER DISCONNECT
@socketio.on("disconnect")
def handle_disconnect():
    if request.sid in users:
        username = users[request.sid]
        del users[request.sid]

        time = datetime.now().strftime("%H:%M:%S")

        send({
            "user": "System",
            "msg": f"{username} left the chat",
            "time": time
        }, broadcast=True)

        emit("users", list(users.values()), broadcast=True)
        logging.info(f"{username} left the chat")

if __name__ == "__main__":
    socketio.run(app, port=5000)