import eventlet
eventlet.monkey_patch()
from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit
from datetime import datetime
from flask import session, redirect

import logging

import psycopg2
import os

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE,
    password VARCHAR(100)
)
""")
conn.commit()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

app = Flask(__name__)
socketio = SocketIO(app)

users = {}  # {session_id: username}

app.secret_key = "supersecret"
@app.route("/")
def index():
    if "user" in session:
        return render_template("chat.html")
    return redirect("/login")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, password)
            )
            conn.commit()
        except:
            return "User already exists!"

        return redirect("/login")

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        cursor.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password)
        )
        user = cursor.fetchone()

        if user:
            session["user"] = username
            return redirect("/")

    return render_template("login.html")

# USER JOIN
@socketio.on("join")
def handle_join():
    username = session.get("user")

    if not username:
        return

    users[request.sid] = username

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
    username = session.get("user") 
    message = data.get("msg")     

    if not username or not message:
        return

    time = datetime.now().strftime("%H:%M:%S")

    send({
        "user": username,
        "msg": message,
        "time": time
    }, broadcast=True)

    logging.info(f"{username}: {message}")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

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
    socketio.run(app, host="0.0.0.0", port=5000)
