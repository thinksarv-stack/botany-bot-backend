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
# CORS enabled for cross-origin mobile browser requests
CORS(app)

# --- GEMINI CONFIG ---
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("WARNING: GEMINI_API_KEY not found in environment variables!")

genai.configure(api_key=API_KEY)
# Using Gemini 2.5 Flash for high-speed response
model = genai.GenerativeModel('gemini-2.5-flash')

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "online", "message": "Botany AI Pro Backend is live"}), 200

# --- ROUTE 1: AI PREDICTION ---
@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No image uploaded"}), 400
    
    try:
        img_bytes = request.files['file'].read()
        img = Image.open(io.BytesIO(img_bytes))
        
        prompt = (
            "Analyze this vegetable/plant image for diseases. "
            "Return ONLY a valid JSON object with exactly these keys: "
            '{"v": "vegetable_name", "d": "disease_name_or_none", "t": "treatment_advice"}'
        )
        
        response = model.generate_content([prompt, img])
        raw_text = response.text.strip()
        clean_json = raw_text.replace('```json', '').replace('```', '').strip()
        
        result_data = json.loads(clean_json)
        return jsonify({
            "status": "success",
            "data": result_data
        }), 200
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- ROUTE 2: PDF GENERATION ---
@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.get_json()
        veg = data.get('v', 'Unknown Vegetable')
        dis = data.get('d', 'Healthy / No Disease')
        treat = data.get('t', 'No specific treatment required.')

        # Initialize PDF (A4 size)
        pdf = FPDF()
        pdf.add_page()
        
        # --- PDF DESIGN ---
        # Green Header Bar
        pdf.set_fill_color(46, 204, 113) 
        pdf.rect(0, 0, 210, 40, 'F')
        
        # App Title
        pdf.set_font("Helvetica", 'B', 24)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 20, "BOTANY AI SCOUT REPORT", ln=True, align='C')
        
        pdf.set_font("Helvetica", size=10)
        pdf.cell(0, 5, "Advanced AI-Powered Plant Diagnosis", ln=True, align='C')
        pdf.ln(25)
        
        # Diagnosis Details
        pdf.set_text_color(44, 62, 80) # Dark Blue-Grey
        pdf.set_font("Helvetica", 'B', 16)
        pdf.cell(0, 10, f"Analysis Results for: {veg}", ln=True)
        pdf.ln(5)
        
        # Status
        pdf.set_font("Helvetica", 'B', 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(40, 10, "Current Status:", border=0)
        
        pdf.set_font("Helvetica", size=12)
        status_color = (231, 76, 60) if dis.lower() != "none" and dis.lower() != "healthy" else (39, 174, 96)
        pdf.set_text_color(*status_color)
        pdf.cell(0, 10, f"{dis}", ln=True)
        pdf.ln(5)
        
        # Treatment Section
        pdf.set_text_color(44, 62, 80)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, "Recommended Treatment / Advice:", ln=True)
        
        pdf.set_font("Helvetica", size=11)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 8, treat)
        
        # Footer
        pdf.set_y(-30)
        pdf.set_font("Helvetica", 'I', 8)
        pdf.set_text_color(128, 128, 128)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        pdf.cell(0, 10, f"Report Generated on: {now} | Botany AI Cloud Service", align='C')

        # Output PDF to a response object
        pdf_output = pdf.output(dest='S')
        response = make_response(pdf_output)
        response.headers.set('Content-Disposition', 'attachment', filename=f'Botany_Report_{veg}.pdf')
        response.headers.set('Content-Type', 'application/pdf')
        return response

    except Exception as e:
        print(f"PDF Error: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to generate PDF"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

