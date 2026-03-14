"""
routes/fact_checker.py — Dual-mode RAG Fact Checker Blueprint.

Mode 1 (retrieval): ChromaDB finds high-confidence matching chunks
                    → Groq answers grounded in those chunks.
Mode 2 (LLM brain): No good match in local data
                    → Groq answers from its own knowledge with a disclaimer.
"""

import io

from flask import Blueprint, request, jsonify

fact_checker_bp = Blueprint("fact_checker", __name__)


# ---------------------------------------------------------------------------
# OCR helper (unchanged)
# ---------------------------------------------------------------------------

def extract_text_from_image(image_bytes: bytes) -> str:
    try:
        from PIL import Image
        import pytesseract
        img = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(img, lang="eng+hin")
        return text.strip() if text.strip() else "[No text detected in image]"
    except ImportError:
        return "[ERROR] Pillow/pytesseract not installed."
    except Exception as e:
        return f"[OCR Error] {e}. Please enter text manually."


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@fact_checker_bp.route("/verify", methods=["POST"])
@fact_checker_bp.route("/fact-check/verify", methods=["POST"])
def verify():
    """
    Accept text or image upload.
    Returns JSON:
      {
        "query": str,
        "mode": "retrieval" | "llm_fallback",
        "answer": str,
        "sources": [str, ...],
        "best_confidence": float,
        "chunks_used": int
      }
    """
    query = None

    # --- Image upload ---
    if "image" in request.files:
        file = request.files["image"]
        if file.filename:
            query = extract_text_from_image(file.read())
            if query.startswith("["):
                return jsonify({"error": query, "results": []}), 200

    # --- Plain text ---
    if not query:
        data = request.get_json(silent=True) or {}
        query = (
            data.get("text", "").strip()
            or request.form.get("text", "").strip()
        )

    if not query:
        return jsonify({"error": "Please provide text or an image to verify."}), 400

    try:
        from rag.llmrag import fact_check
        result = fact_check(query)
    except EnvironmentError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        return jsonify({"error": f"RAG pipeline error: {exc}"}), 500

    return jsonify(result)
