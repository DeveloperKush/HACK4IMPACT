import os
import json
import uuid
from datetime import datetime

from flask import Blueprint, request, jsonify

diary_bp = Blueprint("diary", __name__)

DIARY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "diary.json")


def _load_diary():
    try:
        with open(DIARY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_diary(data):
    with open(DIARY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


@diary_bp.route("/diary/save", methods=["POST"])
def diary_save():
    data = request.get_json(silent=True) or {}
    user_uuid = data.get("uuid", str(uuid.uuid4()))
    entry_text = data.get("entry", "").strip()
    mood = data.get("mood", "neutral")

    if not entry_text:
        return jsonify({"error": "Diary entry cannot be empty."}), 400

    diary = _load_diary()
    if user_uuid not in diary:
        diary[user_uuid] = []

    diary[user_uuid].append({
        "id": str(uuid.uuid4()),
        "text": entry_text,
        "mood": mood,
        "timestamp": datetime.now().isoformat(),
    })

    _save_diary(diary)

    return jsonify({
        "uuid": user_uuid,
        "message": "Diary entry saved anonymously.",
        "total_entries": len(diary[user_uuid]),
    })


@diary_bp.route("/diary/<user_uuid>", methods=["GET"])
def diary_get(user_uuid):
    diary = _load_diary()
    entries = diary.get(user_uuid, [])
    return jsonify({"uuid": user_uuid, "entries": entries})
