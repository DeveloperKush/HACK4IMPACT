from flask import Blueprint, request, jsonify

telemedicine_bp = Blueprint("telemedicine", __name__)

TRIAGE_DISCLAIMER = (
    "⚠️ IMPORTANT: This is NOT a medical diagnosis. This tool provides "
    "basic first-aid guidance only. Please visit your nearest Primary Health "
    "Centre (PHC) or hospital for proper medical attention."
)

SYMPTOM_DATABASE = {
    "chest_pain": {
        "keywords": ["chest pain", "chest tightness", "heart pain", "seene mein dard", "chhati dard"],
        "severity": "EMERGENCY",
        "condition": "Possible cardiac event",
        "first_aid": [
            "Have the person sit upright in a comfortable position.",
            "If they have prescribed nitroglycerin, help them take it.",
            "Give an aspirin (300mg) if not allergic — ask them to chew it slowly.",
            "Loosen any tight clothing around chest and neck.",
            "Keep the person calm and still — do NOT let them walk or exert.",
        ],
        "action": "🚨 CALL 108 (AMBULANCE) IMMEDIATELY. Travel to the nearest hospital NOW."
    },
    "breathing": {
        "keywords": ["breathing difficulty", "breathless", "cant breathe", "short of breath", "saans", "dum ghutna", "asthma attack"],
        "severity": "EMERGENCY",
        "condition": "Respiratory distress",
        "first_aid": [
            "Help the person sit upright — do NOT lay them flat.",
            "If they have an inhaler, help them use it (2 puffs, wait 1 minute, repeat).",
            "Open windows/doors for fresh air. Remove any tight clothing.",
            "If due to choking: perform the Heimlich manoeuvre (abdominal thrusts).",
            "Stay calm and count breaths — if below 10 or above 30 per minute, it's critical.",
        ],
        "action": "🚨 CALL 108 NOW. This can be life-threatening. Rush to hospital."
    },
    "fever": {
        "keywords": ["fever", "high temperature", "bukhar", "taap", "badan garam"],
        "severity": "MODERATE",
        "condition": "Fever / Possible infection",
        "first_aid": [
            "Give paracetamol (500mg for adults, weight-based for children).",
            "Apply a cool, damp cloth on the forehead.",
            "Ensure the person drinks plenty of fluids — ORS, water, or coconut water.",
            "Keep the room ventilated. Use light clothing.",
            "If fever is above 103°F (39.4°C) or persists more than 3 days, seek medical care.",
        ],
        "action": "📋 Visit your nearest PHC if fever persists beyond 2-3 days or is very high."
    },
    "diarrhea": {
        "keywords": ["diarrhea", "loose motions", "dast", "pet kharab", "vomiting", "ulti", "dehydration"],
        "severity": "MODERATE",
        "condition": "Diarrhea / Dehydration risk",
        "first_aid": [
            "Start ORS (Oral Rehydration Solution) immediately — 1 packet in 1 litre clean water.",
            "If no ORS: mix 6 level teaspoons sugar + ½ teaspoon salt in 1 litre boiled/clean water.",
            "Give small, frequent sips — do NOT give large amounts at once.",
            "Continue breastfeeding if the patient is an infant.",
            "Zinc tablets (20mg/day for children) for 10-14 days speeds recovery.",
        ],
        "action": "📋 Visit PHC if: blood in stool, unable to drink, sunken eyes, or lasts >2 days."
    },
    "snake_bite": {
        "keywords": ["snake bite", "saanp", "saamp katna", "snake"],
        "severity": "EMERGENCY",
        "condition": "Snake bite",
        "first_aid": [
            "Keep the person CALM and STILL. Do NOT let them walk or run.",
            "Immobilise the bitten limb below heart level. Remove rings/watches.",
            "Do NOT cut the wound, suck the venom, or apply a tourniquet.",
            "Do NOT apply ice, herbal paste, or any traditional remedy.",
            "Note the time of bite and snake appearance if possible (for antivenom selection).",
        ],
        "action": "🚨 RUSH TO HOSPITAL IMMEDIATELY. Antivenom is the ONLY effective treatment. Call 108."
    },
    "burn": {
        "keywords": ["burn", "jalana", "jal gaya", "aag", "boiling water", "garam pani"],
        "severity": "HIGH",
        "condition": "Burn injury",
        "first_aid": [
            "Run cool (not cold) water over the burn for at least 20 minutes.",
            "Do NOT apply ice, butter, toothpaste, or any home remedy.",
            "Remove clothing/jewellery near the burn UNLESS stuck to skin.",
            "Cover with a clean, non-stick bandage or clean cloth.",
            "Give paracetamol for pain. Keep the person hydrated.",
        ],
        "action": "🏥 Go to hospital if: burn is larger than the palm, on face/hands/joints, or skin is white/charred."
    },
    "headache": {
        "keywords": ["headache", "sir dard", "sar dard", "migraine", "head pain"],
        "severity": "LOW",
        "condition": "Headache",
        "first_aid": [
            "Take paracetamol (500mg) with water.",
            "Rest in a quiet, dark room.",
            "Apply a cold or warm compress on the forehead.",
            "Drink water — dehydration is a common cause.",
            "Gently massage the temples in circular motions.",
        ],
        "action": "📋 Visit doctor if: sudden severe headache, headache with fever/stiff neck, or recurring headaches."
    },
    "fracture": {
        "keywords": ["fracture", "broken bone", "haddi", "haddi tooti", "bone break", "fall injury"],
        "severity": "HIGH",
        "condition": "Possible fracture",
        "first_aid": [
            "Do NOT move the injured limb. Immobilise it in the position found.",
            "Use a makeshift splint (sticks, rolled newspaper) padded with cloth.",
            "Apply ice wrapped in cloth to reduce swelling — 20 minutes on, 20 off.",
            "If there is an open wound, cover with a clean cloth. Do NOT push bone back.",
            "Give paracetamol for pain (NOT aspirin — it increases bleeding).",
        ],
        "action": "🏥 Travel to hospital for X-ray and proper treatment. Do NOT delay."
    },
    "wound": {
        "keywords": ["bleeding", "cut", "wound", "chot", "khoon", "ghaav", "laceration"],
        "severity": "MODERATE",
        "condition": "Wound / Bleeding",
        "first_aid": [
            "Apply firm pressure with a clean cloth for at least 10 minutes.",
            "Elevate the injured area above heart level if possible.",
            "Once bleeding slows, clean the wound with clean water.",
            "Apply an antiseptic (Dettol/Betadine) and cover with a clean bandage.",
            "Check tetanus vaccination status — get a booster if >5 years since last shot.",
        ],
        "action": "🏥 Go to hospital if: bleeding won't stop, wound is deep, or caused by rusty/dirty object."
    },
    "pregnancy": {
        "keywords": ["pregnancy", "pregnant", "labour", "delivery", "garbhvati", "pet dard pregnant"],
        "severity": "HIGH",
        "condition": "Pregnancy-related concern",
        "first_aid": [
            "If in labour: keep the mother calm, lying on her left side.",
            "Time the contractions — hospital when 5 minutes apart for 1 hour.",
            "Do NOT give any medication without doctor's advice.",
            "If heavy bleeding: elevate legs, keep warm, and rush to hospital.",
            "Ensure ASHA worker / ANM is contacted if in rural area.",
        ],
        "action": "🏥 All deliveries should ideally happen at a health facility. Contact 108 or nearest PHC/CHC."
    },
}


def triage_symptoms(user_input):
    """Match symptoms against the database and return triage information."""
    msg = user_input.lower()
    matched = []

    for key, data in SYMPTOM_DATABASE.items():
        for keyword in data["keywords"]:
            if keyword in msg:
                matched.append({
                    "condition": data["condition"],
                    "severity": data["severity"],
                    "first_aid": data["first_aid"],
                    "action": data["action"],
                })
                break  # Avoid duplicate matches for same condition

    if not matched:
        return {
            "matched": False,
            "message": (
                "I couldn't identify specific symptoms from your description. "
                "Please try describing your symptoms in more detail, for example: "
                "'I have chest pain and difficulty breathing' or 'high fever for 3 days'."
            ),
            "disclaimer": TRIAGE_DISCLAIMER,
            "results": [],
        }

    # Sort by severity
    severity_order = {"EMERGENCY": 0, "HIGH": 1, "MODERATE": 2, "LOW": 3}
    matched.sort(key=lambda x: severity_order.get(x["severity"], 99))

    return {
        "matched": True,
        "results": matched,
        "disclaimer": TRIAGE_DISCLAIMER,
    }


@telemedicine_bp.route("/telemedicine/chat", methods=["POST"])
def telemedicine_chat():
    data = request.get_json(silent=True) or {}
    symptoms = data.get("symptoms", "").strip()
    if not symptoms:
        return jsonify({"error": "Please describe your symptoms."}), 400

    result = triage_symptoms(symptoms)
    return jsonify(result)
