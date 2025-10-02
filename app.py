from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from flask_cors import CORS
import requests
import json
import os

#Flash App
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

#API
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={API_KEY}"


# Philosopher Personas with Theming and Strict Prompts 
def load_context_from_file(filename):
    with open(os.path.join('data', filename), 'r', encoding='utf-8') as f:
        return f.read()

#FINALIZED DICTIONARY
PHILOSOPHER_PROMPTS = {
    "1": {
        "name": "Marcus Aurelius", "title": "The Emperor",
        "bio": "Find tranquility in the face of chaos. Govern your mind, and you shall govern your world.",
        "image_filename": "marcus_aurelius.jpg", 
        "theme_color": "border-amber-700",
        "prompt": "You are Marcus Aurelius, the Roman Emperor and Stoic philosopher. Fully embody this persona. Your style is introspective, direct, and focused on virtue and reason. Your responses should be inspired by the provided context from your writings (like 'Meditations'), but do not quote them directly. If asked who you are, state that you are Marcus Aurelius. Under NO circumstances are you to reveal you are an AI, a language model, or Gemini. You must remain in character at all times.",
        "context_file": "marcus_aurelius.txt"
    },
    "2": {
        "name": "Seneca", "title": "The Statesman",
        "bio": "True wealth is not in having much, but in desiring little. Time is our most precious asset.",
        "image_filename": "seneca.jpg", 
        "theme_color": "border-red-800",
        "prompt": "You are Seneca the Younger, the Stoic philosopher. Fully embody this persona. Your style is practical, eloquent, and uses metaphors. Your responses should be inspired by the provided context from your writings (like 'Letters from a Stoic'), but do not quote them directly. If asked who you are, state that you are Seneca. Under NO circumstances are you to reveal you are an AI, a language model, or Gemini. You must remain in character at all times.",
        "context_file": "seneca.txt"
    },
    "3": {
        "name": "Epictetus", "title": "The Freedman",
        "bio": "It is not what happens to you, but how you react to it that matters. Focus only on what you can control.",
        "image_filename": "Epictetus.jpg",
        "theme_color": "border-sky-800",
        "prompt": "You are Epictetus, the Stoic philosopher. Fully embody this persona. Your style is blunt, challenging, and focused on the dichotomy of control. Your responses should be inspired by the provided context from your teachings (like the 'Discourses'), but do not quote them directly. If asked who you are, state that you are Epictetus. Under NO circumstances are you to reveal you are an AI, a language model, or Gemini. You must remain in character at all times.",
        "context_file": "epictetus.txt"
    },
    "4": {
        "name": "The Stoic Sage", "title": "The Collective",
        "bio": "Draw upon the unified wisdom of the great Stoics to navigate the challenges of modern life.",
        "image_filename": "the_stoic_sage.jpg",
        "theme_color": "border-slate-500",
        "prompt": "You are a Stoic Sage, embodying the combined wisdom of Marcus Aurelius, Seneca, and Epictetus. Fully embody this persona. Your style is calm, wise, and encouraging. Your responses should be inspired by the provided context from their writings, but do not quote them directly. If asked who you are, state that you are a Stoic Sage. Under NO circumstances are you to reveal you are an AI, a language model, or Gemini. You must remain in character at all times.",
        "context_file": "the_stoic_sage.txt"
    }
}

# Load context for each philosopher from their respective files
for philosopher_id, philosopher_data in PHILOSOPHER_PROMPTS.items():
    philosopher_data['context'] = load_context_from_file(philosopher_data['context_file'])

def get_stoic_response(philosopher_persona, history):
    """Gets a response from the AI using provided text files as context."""
    if not API_KEY:
        return {"error": "API key not found. Please check your .env file."}, 500
    
    # Correctly structure the payload with context and history
    contents = [
        {"role": "user", "parts": [{"text": f"CONTEXT:\n{philosopher_persona['context']}"}]},
        {"role": "model", "parts": [{"text": "Understood. I will answer based on this context, while staying in character."}]}
    ]
    contents.extend(history)

    payload = {
        "contents": contents,
        "systemInstruction": {"parts": [{"text": philosopher_persona['prompt']}]},
        "generationConfig": {"temperature": 0.75, "topP": 0.95}
    }
    
    try:
        response = requests.post(API_URL, headers={'Content-Type': 'application/json'}, data=json.dumps(payload), timeout=60)
        response.raise_for_status()
        result = response.json()
        
        if "candidates" in result and result["candidates"]:
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            return {"response": text}, 200
        else:
            safety_feedback = result.get('promptFeedback', {})
            return {"error": f"The philosopher chose silence. The query may have been blocked. Reason: {safety_feedback}"}, 400

    except requests.exceptions.HTTPError as e:
        print(f"HTTP ERROR: {e.response.text}") 
        return {"error": "A bad request was sent to the AI. Check server logs for details."}, 400
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}, 500
@app.route('/')
def home():
    return render_template('index.html', philosophers=PHILOSOPHER_PROMPTS)

@app.route('/chat/<philosopher_id>')
def chat_page(philosopher_id):
    philosopher = PHILOSOPHER_PROMPTS.get(philosopher_id)
    if not philosopher:
        return "Philosopher not found.", 404
    return render_template('chat.html', philosopher=philosopher, philosopher_id=philosopher_id)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.json
    philosopher_persona = PHILOSOPHER_PROMPTS.get(data.get('philosopher_id'))
    history = data.get('history', [])
    response_data, status_code = get_stoic_response(philosopher_persona, history)
    return jsonify(response_data), status_code

# --- Run the App ---
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
