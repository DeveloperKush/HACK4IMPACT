import uuid

from flask import request
from flask_socketio import emit, join_room, leave_room

peer_queue = []       # List of waiting SIDs
active_pairs = {}     # sid -> partner_sid


def register_socketio_events(socketio):
    """Register all peer-match SocketIO events on the given socketio instance."""

    @socketio.on("join_queue")
    def handle_join_queue():
        sid = request.sid
        if sid in active_pairs:
            emit("system_message", {"message": "You are already in a chat."})
            return

        if peer_queue and peer_queue[0] != sid:
            partner_sid = peer_queue.pop(0)
            room = f"peer_{uuid.uuid4().hex[:8]}"
            join_room(room, sid=sid)
            join_room(room, sid=partner_sid)
            active_pairs[sid] = {"partner": partner_sid, "room": room}
            active_pairs[partner_sid] = {"partner": sid, "room": room}
            emit("peer_matched", {"room": room, "message": "You are now connected with an anonymous peer. Be kind. 💙"}, room=room)
        else:
            if sid not in peer_queue:
                peer_queue.append(sid)
            emit("system_message", {"message": "Waiting for a peer to connect... You'll be matched soon."})

    @socketio.on("send_peer_message")
    def handle_peer_message(data):
        sid = request.sid
        if sid not in active_pairs:
            emit("system_message", {"message": "You are not in a chat. Join the queue first."})
            return
        room = active_pairs[sid]["room"]
        emit("peer_message", {
            "message": data.get("message", ""),
            "sender": "peer" if request.sid != active_pairs[sid]["partner"] else "you",
        }, room=room, include_self=False)
        emit("peer_message", {
            "message": data.get("message", ""),
            "sender": "you",
        }, to=sid)

    @socketio.on("leave_chat")
    def handle_leave_chat():
        sid = request.sid
        if sid in active_pairs:
            partner = active_pairs[sid]["partner"]
            room = active_pairs[sid]["room"]
            emit("peer_disconnected", {"message": "Your peer has left the chat."}, to=partner)
            leave_room(room, sid=sid)
            leave_room(room, sid=partner)
            del active_pairs[sid]
            if partner in active_pairs:
                del active_pairs[partner]
        elif sid in peer_queue:
            peer_queue.remove(sid)
        emit("system_message", {"message": "You have left the chat."})

    @socketio.on("disconnect")
    def handle_disconnect():
        sid = request.sid
        if sid in active_pairs:
            handle_leave_chat()
        elif sid in peer_queue:
            peer_queue.remove(sid)
