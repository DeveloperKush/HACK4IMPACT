import os

from flask import Blueprint, request, jsonify

therapist_bp = Blueprint("therapist", __name__)

# ---------------------------------------------------------------------------
# Groq client – created lazily so the app boots without a key set
# ---------------------------------------------------------------------------

_groq_client = None


def _get_groq_client():
    global _groq_client
    if _groq_client is None:
        try:
            from groq import Groq  # pip install groq

            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                raise EnvironmentError(
                    "GROQ_API_KEY environment variable is not set. "
                    "Export it before starting the server."
                )
            _groq_client = Groq(api_key=api_key)
        except ImportError:
            raise ImportError(
                "The 'groq' package is not installed. Run: pip install groq"
            )
    return _groq_client


# ---------------------------------------------------------------------------
# System prompt – Rogerian / person-centred therapist
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are Jan-Sahayak's compassionate AI therapist. You practice Rogerian (person-centred) therapy.

Core principles:
• Unconditional positive regard – never judge, shame, or lecture.
• Empathic reflection – mirror the user's feelings back to them.
• Genuine curiosity – ask one focused open-ended question at a time.
• Safety first – if ANY message contains suicidal ideation, self-harm, or a crisis:
  - Acknowledge the pain warmly.
  - Immediately share crisis helplines:
      iCall: 9152987821
      Vandrevala Foundation: 1860-2662-345
      AASRA: 91-22-27546669
  - Do NOT proceed to other topics until the user feels heard.

Style guidelines:
• Respond in the same language the user writes in (Hindi, Hinglish, or English).
• Keep replies concise (3-5 sentences) unless the user needs more depth.
• Never give medical diagnoses or prescribe medication.
• Do not repeat the same question twice in a session.
• Always end with an open, gentle invitation for the user to continue sharing.
"""

# Track per-session conversation history using a simple in-memory dict.
# Key = session_id (passed from front-end), Value = list of message dicts.
_sessions: dict = {}


def _is_crisis(text: str) -> bool:
    keywords = [
        "suicide", "suicidal", "kill myself", "end my life",
        "want to die", "no reason to live", "self-harm", "hurt myself",
    ]
    lower = text.lower()
    return any(k in lower for k in keywords)


def therapist_respond(user_message: str, session_id: str = "default") -> dict:
    """Send user_message to Groq and return the assistant reply."""
    client = _get_groq_client()

    # Initialise history for new sessions
    if session_id not in _sessions:
        _sessions[session_id] = []

    history = _sessions[session_id]

    # Append the new user turn
    history.append({"role": "user", "content": user_message})

    # Build the full message list for the API call
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",   # fast & accurate – swap if needed
        messages=messages,
        temperature=0.7,
        max_tokens=512,
    )

    assistant_reply = completion.choices[0].message.content.strip()

    # Persist the assistant reply in history
    history.append({"role": "assistant", "content": assistant_reply})

    # Keep history bounded (last 20 turns = 10 exchanges)
    if len(history) > 20:
        _sessions[session_id] = history[-20:]

    return {
        "response": assistant_reply,
        "category": "ai",
        "is_crisis": _is_crisis(user_message),
    }


# ---------------------------------------------------------------------------
# Flask route
# ---------------------------------------------------------------------------

@therapist_bp.route("/mental-health/chat", methods=["POST"])
def mental_health_chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    session_id = data.get("session_id", "default")

    if not message:
        return jsonify({"error": "Please enter a message."}), 400

    try:
        result = therapist_respond(message, session_id)
    except EnvironmentError as exc:
        return jsonify({"error": str(exc)}), 503
    except ImportError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        return jsonify({"error": f"AI error: {exc}"}), 500

    return jsonify(result)


@therapist_bp.route("/mental-health/reset", methods=["POST"])
def reset_session():
    """Clear conversation history for a given session."""
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id", "default")
    _sessions.pop(session_id, None)
    return jsonify({"status": "Session reset."})
