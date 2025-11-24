from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = "tkcsecret"
socketio = SocketIO(app, cors_allowed_origins="*")

ROOMS = {}  # room_name -> {"users": set(), "history": []}
MAX_HISTORY = 100

def add_message(room, user, msg):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    room_obj = ROOMS.setdefault(room, {"users": set(), "history": []})
    room_obj["history"].append({"user": user, "msg": msg, "time": ts})
    if len(room_obj["history"]) > MAX_HISTORY:
        room_obj["history"].pop(0)

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("join")
def on_join(data):
    room = data["room"]
    user = data["user"]
    join_room(room)
    ROOMS.setdefault(room, {"users": set(), "history": []})
    ROOMS[room]["users"].add(user)

    emit("user_joined", {"user": user}, room=room)
    emit("room_users", {"users": list(ROOMS[room]["users"])}, room=room)
    # send chat history
    emit("history", {"history": ROOMS[room]["history"]}, room=request.sid)

@socketio.on("leave")
def on_leave(data):
    room = data["room"]
    user = data["user"]
    leave_room(room)
    if room in ROOMS and user in ROOMS[room]["users"]:
        ROOMS[room]["users"].remove(user)
        emit("user_left", {"user": user}, room=room)
        emit("room_users", {"users": list(ROOMS[room]["users"])}, room=room)

@socketio.on("send_message")
def handle_message(data):
    room = data["room"]
    user = data["user"]
    msg = data["msg"]
    add_message(room, user, msg)
    emit("message", {"user": user, "msg": msg, "time": datetime.utcnow().strftime("%H:%M")}, room=room)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
