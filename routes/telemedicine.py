from flask import Blueprint, request, jsonify
import requests
import os
import json
import re

try:
    from dotenv import load_dotenv
    # Load environment variables from .env
    load_dotenv()
except ImportError:
    pass

telemedicine_bp = Blueprint("telemedicine", __name__)

# --- CONFIGURATION & CONSTANTS ---
TRIAGE_DISCLAIMER = (
    "IMPORTANT: This is NOT a medical diagnosis. This tool provides "
    "basic first-aid guidance only. Please visit your nearest Primary Health "
    "Centre (PHC) or hospital for proper medical attention."
)

DOCTOR_DATABASE = [
    {"specialty": "Cardiology", "location": "District Hospital", "contact": "1234567890"},
    {"specialty": "Respiratory", "location": "PHC Center", "contact": "0987654321"},
    {"specialty": "General Physician", "location": "Nearest PHC", "contact": "1122334455"},
    {"specialty": "Obstetrics", "location": "CHC Facility", "contact": "6677889900"},
    {"specialty": "Orthopedics", "location": "District Hospital", "contact": "2233445566"},
    {"specialty": "Neurology", "location": "Super Specialty Hospital", "contact": "9988776655"}
]

# --- HELPER FUNCTIONS ---

def get_keyword_fallback(user_input):
    """Manual backup if the AI fails or internet is out."""
    text = user_input.lower()
    
    # Mapping keywords to responses
    patterns = [
        (r"(fever|bukhar|taap)", "fever", "MODERATE", ["Hydration", "Cool compress", "Keep patient in a cool, ventilated area"], "General Physician", False),
        (r"(snake|saanp|saamp)", "snake bite", "EMERGENCY", ["Keep the patient completely still to slow venom spread", "Keep the bitten area below heart level", "Do NOT suck the wound, do NOT cut it, do NOT apply a tight tourniquet", "Rush to the nearest hospital immediately for anti-venom"], "General Physician", True),
        (r"(chest pain|heart attack|chhati dard|seene mein dard)", "chest pain (possible cardiac event)", "EMERGENCY", ["Sit the patient upright to help breathing", "If available, give a crushed Aspirin (300mg) or place Sorbitrate under the tongue", "Loosen tight clothing", "Keep the patient calm and warm", "Rush to hospital immediately"], "Cardiology", True),
        (r"(breath|saans|asthma|dum ghutna)", "breathing difficulty", "EMERGENCY", ["Sit the patient upright", "Loosen tight clothes around neck and chest", "Ensure open fresh air flow", "Keep airways clear"], "Respiratory", True),
        (r"(diarrhea|loose motions|dast|vomiting|ulti)", "dehydration risk", "MODERATE", ["Start ORS (salt-sugar water) immediately", "Give frequent small sips of fluid to prevent dehydration"], "General Physician", False),
        (r"(burn|jalana|jal gaya)", "burn injury", "HIGH", ["Cool the burn under gently running room-temperature water for 15-20 mins", "Cover loosely with clean, dry cloth", "Do NOT apply ice, toothpaste, butter, or ointments"], "General Physician", True),
        (r"(pregnancy|pregnant|labour|garbhvati)", "pregnancy concern", "HIGH", ["Ask the woman to lie on her left side", "Contact local ASHA/ANM worker immediately", "Ensure breathing is normal"], "Obstetrics", True),
        (r"(blood|khoon|bleeding|injury|chot)", "severe bleeding", "EMERGENCY", ["Apply firm direct pressure to the wound using a clean cloth", "Elevate the injured area if possible above heart level", "If blood soaks through, do not remove the cloth, just add more on top"], "General Physician", True)
    ]

    for pattern, cond, sev, aid, spec, urg in patterns:
        if re.search(pattern, text):
            return {
                "symptoms": [cond], "severity": sev, "first_aid": aid,
                "doctor_specialty": spec, "urgent": urg
            }
    
    return None

def groq_extract_symptoms(user_input):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("[DEBUG] GROQ_API_KEY environment variable not found.")
        return get_keyword_fallback(user_input)

    # Groq API endpoint for chat completions
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    system_prompt = (
        "You are a highly capable AI medical triage assistant designed for rural areas where hospitals are far away. "
        "Many patients die on the way, so immediate survival is the absolute priority. "
        "Your goals:\n"
        "1. Identify the possible symptoms based on user input.\n"
        "2. Assess the severity (LOW, MODERATE, HIGH, EMERGENCY).\n"
        "3. For serious/emergency issues, strongly recommend seeing a specific doctor specialty immediately.\n"
        "4. Provide CRUCIAL life-saving FIRST AID to keep the patient alive on the way to the hospital (e.g., stopping severe bleeding, keeping still for snake bites, sitting upright for heart attacks).\n"
        "5. You MAY recommend emergency life-saving medicines ONLY IF it is absolutely critical for survival during the journey to the hospital (e.g., Sorbitrate or Aspirin for a heart attack). Please add a note that this is for emergency transit only.\n"
        "Respond ONLY in JSON format:\n"
        '{"symptoms":["list","of","symptoms"], "severity":"EMERGENCY/HIGH/MODERATE/LOW", "first_aid":["life-saving step 1","step 2"], "doctor_specialty":"Cardiology/General Physician/etc", "urgent":true/false}'
    )

    payload = {
        "model": "llama-3.1-8b-instant",
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the issue: {user_input}"}
        ],
        "temperature": 0.2
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=12)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        
        parsed = json.loads(content)
        # Ensure default keys
        parsed.setdefault("symptoms", [])
        parsed.setdefault("severity", "UNKNOWN")
        parsed.setdefault("first_aid", ["Please visit the nearest PHC immediately. Check airway, breathing, and circulation."])
        parsed.setdefault("doctor_specialty", "General Physician")
        parsed.setdefault("urgent", False)
        
        # Override if somehow 'urgent' isn't explicitly true on emergency
        if parsed["severity"] == "EMERGENCY":
            parsed["urgent"] = True

        return parsed
            
    except requests.exceptions.HTTPError as e:
        print(f"[DEBUG] Groq API HTTP Error: {e}, Response: {e.response.text if e.response else 'No Response'}")
    except Exception as e:
        print(f"[DEBUG] Groq AI Error: {e}")
    
    # If API fails or JSON is bad, use keywords or default
    fallback = get_keyword_fallback(user_input)
    if fallback:
        return fallback
    
    return {
        "symptoms": ["Unspecified medical issue"], "severity": "MODERATE", 
        "first_aid": ["Please visit the nearest Primary Health Centre immediately. We could not process your request fully."], 
        "doctor_specialty": "General Physician", "urgent": False
    }

def recommend_doctor(specialty):
    specialty_lower = specialty.lower()
    for doc in DOCTOR_DATABASE:
        if specialty_lower in doc["specialty"].lower() or doc["specialty"].lower() in specialty_lower:
            return doc
    return DOCTOR_DATABASE[2] # Default to General Physician

# --- ROUTES ---

@telemedicine_bp.route("/telemedicine/chat", methods=["POST"])
def telemedicine_chat():
    data = request.get_json(silent=True) or {}
    user_input = data.get("symptoms", "").strip()

    if not user_input:
        return jsonify({"error": "Please describe how you are feeling."}), 400

    analysis = groq_extract_symptoms(user_input)

    # If both Groq and keyword fallback returned None, use a safe default
    if analysis is None:
        analysis = {
            "symptoms": ["Unspecified medical issue"],
            "severity": "MODERATE",
            "first_aid": ["Please visit the nearest Primary Health Centre immediately."],
            "doctor_specialty": "General Physician",
            "urgent": False
        }

    doctor_info = recommend_doctor(analysis.get("doctor_specialty", "General Physician"))

    results = []
    if analysis.get("symptoms"):
        results.append({
            "condition": ', '.join(analysis["symptoms"]),
            "severity": analysis["severity"],
            "first_aid": analysis["first_aid"],
            "action": f"Consult {doctor_info['specialty']} at {doctor_info['location']}. Contact: {doctor_info['contact']}"
        })

    response = {
        "matched": bool(analysis.get("symptoms")),
        "results": results,
        "disclaimer": TRIAGE_DISCLAIMER,
    }

    if analysis.get("urgent"):
        response["transport_advice"] = "EMERGENCY: Arrange transport (Ambulance 108) immediately. Use the provided first-aid steps to stabilize the patient during the journey to the hospital."

    return jsonify(response)

if __name__ == "__main__":
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(telemedicine_bp)
    app.run(debug=True)
 