import os
from dotenv import load_dotenv
load_dotenv()  # loads .env into os.environ

from flask import Flask, render_template
from flask_socketio import SocketIO

# -- Create app & extensions ------------------------------------------------

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24).hex()
socketio = SocketIO(app, cors_allowed_origins="*")

# -- Register Blueprints ----------------------------------------------------

from routes.fact_checker import fact_checker_bp
from routes.therapist import therapist_bp
from routes.diary import diary_bp
from routes.telemedicine import telemedicine_bp

app.register_blueprint(fact_checker_bp)
app.register_blueprint(therapist_bp)
app.register_blueprint(diary_bp)
app.register_blueprint(telemedicine_bp)

# -- Register SocketIO events (peer-match) ----------------------------------

from routes.peer_match import register_socketio_events
register_socketio_events(socketio)

# -- Pages -------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("new.html")

@app.route("/fact.html")
def fact_page():
    return render_template("fact.html")

@app.route("/health.html")
def health_page():
    return render_template("health.html")

@app.route("/med.html")
def med_page():
    return render_template("med.html")

@app.route("/new.html")
def new_page():
    return render_template("new.html")


# -- Run --------------------------------------------------------------------

if __name__ == "__main__":
    from rag.dataprep import build_index
    print("[Jan-Sahayak] Building RAG index from data/ folder...")
    count = build_index()
    print(f"[Jan-Sahayak] Index ready — {count} chunks in ChromaDB.")
    print("[Jan-Sahayak] Server starting on http://localhost:5000")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
