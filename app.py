import os
import io
import json
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image

app = Flask(__name__)
# CORS enable karna zaroori hai taaki aapka phone browser Render se baat kar sake
CORS(app)

# --- GEMINI CONFIG ---
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("WARNING: GEMINI_API_KEY not found in environment variables!")

genai.configure(api_key=API_KEY)
# We use 2.5-flash for maximum speed and lower latency
model = genai.GenerativeModel('gemini-2.5-flash')

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "online", "message": "Botany AI Backend is running"}), 200

@app.route('/predict', methods=['POST'])
def predict():
    # Validation: Check if image exists in request
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No image uploaded"}), 400
    
    try:
        # 1. Image ko memory mein read karein
        img_bytes = request.files['file'].read()
        img = Image.open(io.BytesIO(img_bytes))
        
        # 2. Strict Prompt for JSON output
        prompt = (
            "Analyze this vegetable/plant image for diseases. "
            "Return ONLY a valid JSON object with exactly these keys: "
            '{"v": "vegetable_name", "d": "disease_name_or_none", "t": "treatment_advice"}'
        )
        
        # 3. Gemini API call
        response = model.generate_content([prompt, img])
        
        # 4. Clean JSON (Gemini sometimes adds markdown backticks)
        raw_text = response.text.strip()
        clean_json = raw_text.replace('```json', '').replace('```', '').strip()
        
        # 5. Parse and Return
        result_data = json.loads(clean_json)
        return jsonify({
            "status": "success",
            "data": result_data
        }), 200
    
    except Exception as e:
        print(f"Error during prediction: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Internal Server Error",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    # Render assigns a port via environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
