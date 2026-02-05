import os
import io
import json
import google.generativeai as genai
from flask import Flask, request, jsonify
from PIL import Image

app = Flask(__name__)

# Config Gemini
API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No image"}), 400
    
    try:
        # Read image from request
        img_bytes = request.files['file'].read()
        img = Image.open(io.BytesIO(img_bytes))
        
        # Super-fast instruction for Gemini
        prompt = "Analyze this vegetable for disease. Return ONLY JSON: {'v': 'name', 'd': 'disease_name', 't': 'treatment'}"
        
        response = model.generate_content([prompt, img])
        
        # Clean JSON and send
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return jsonify({"status": "success", "data": json.loads(clean_json)})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)