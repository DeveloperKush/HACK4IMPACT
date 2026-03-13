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

# -- Landing page -----------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")

# -- Run --------------------------------------------------------------------

if __name__ == "__main__":
    from routes.fact_checker import get_chroma
    print("[Jan-Sahayak] Initialising ChromaDB vector store...")
    get_chroma()
    print("[Jan-Sahayak] Server starting on http://localhost:5000")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
