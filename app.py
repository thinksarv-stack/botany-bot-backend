import os
import io
import json
import datetime
import google.generativeai as genai
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from PIL import Image
from fpdf import FPDF

app = Flask(__name__)
CORS(app) # Crucial for Netlify to communicate with Render

# --- GEMINI CONFIG ---
API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

@app.route('/', methods=['GET'])
def health():
    return jsonify({"status": "active"}), 200

# Endpoint 1: Analyze Image
@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file"}), 400
    try:
        img_bytes = request.files['file'].read()
        img = Image.open(io.BytesIO(img_bytes))
        prompt = "Analyze this plant image. Return ONLY JSON: {'v': 'vegetable_name', 'd': 'disease', 't': 'treatment'}"
        response = model.generate_content([prompt, img])
        clean_json = response.text.strip().replace('```json', '').replace('```', '')
        return jsonify({"status": "success", "data": json.loads(clean_json)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Endpoint 2: Generate PDF Report
@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.get_json()
        veg = data.get('v', 'Unknown')
        dis = data.get('d', 'Healthy')
        treat = data.get('t', 'N/A')

        pdf = FPDF()
        pdf.add_page()
        
        # Style & Branding
        pdf.set_fill_color(46, 204, 113) 
        pdf.rect(0, 0, 210, 40, 'F')
        pdf.set_font("Helvetica", 'B', 22)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 20, "BOTANY AI PRO REPORT", ln=True, align='C')
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", 'B', 14)
        pdf.ln(30)
        pdf.cell(0, 10, f"Vegetable: {veg}", ln=True)
        
        pdf.set_text_color(200, 0, 0) if dis.lower() != 'none' else pdf.set_text_color(0, 150, 0)
        pdf.cell(0, 10, f"Diagnosis: {dis}", ln=True)
        
        pdf.ln(5)
        pdf.set_text_color(50, 50, 50)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, "Recommended Treatment:", ln=True)
        pdf.set_font("Helvetica", size=11)
        pdf.multi_cell(0, 7, treat)
        
        pdf.set_y(-30)
        pdf.set_font("Helvetica", 'I', 8)
        pdf.cell(0, 10, f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d')}", align='C')

        response = make_response(pdf.output(dest='S'))
        response.headers.set('Content-Type', 'application/pdf')
        response.headers.set('Content-Disposition', 'attachment', filename='report.pdf')
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
