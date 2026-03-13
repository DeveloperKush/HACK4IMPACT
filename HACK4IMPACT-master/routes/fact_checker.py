import io

from flask import Blueprint, request, jsonify

fact_checker_bp = Blueprint("fact_checker", __name__)

_chroma_collection = None


def get_chroma():
    global _chroma_collection
    if _chroma_collection is None:
        from chroma_utils import init_collection, seed_data
        _chroma_collection = init_collection()
        seed_data(_chroma_collection)
    return _chroma_collection


def extract_text_from_image(image_bytes):
    """Run OCR on image bytes. Returns extracted text or error string."""
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


@fact_checker_bp.route("/verify", methods=["POST"])
def verify():
    """Accept text or image, query the vector store, return matching facts."""
    text = None

    # Image upload Check
    if "image" in request.files:
        file = request.files["image"]
        if file.filename:
            image_bytes = file.read()
            text = extract_text_from_image(image_bytes)
            if text.startswith("["):
                return jsonify({"error": text, "results": []}), 200

    if not text:
        data = request.get_json(silent=True) or {}
        text = data.get("text", "").strip() or request.form.get("text", "").strip()

    if not text:
        return jsonify({"error": "Please provide text or an image to verify.", "results": []}), 400

    from chroma_utils import query_facts
    matches = query_facts(text, n_results=3, collection=get_chroma())

    results = []
    for m in matches:
        results.append({
            "fact": m["text"],
            "confidence": m["confidence"],
            "category": m["metadata"].get("category", ""),
            "scheme": m["metadata"].get("scheme", ""),
        })

    return jsonify({
        "query": text,
        "results": results,
    })
