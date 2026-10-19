from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import json
import os

app = Flask(__name__, template_folder='templates')
CORS(app)

# Leer API Key de Render
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
MODELO = "gemini-1.5-flash" 

def consultar_gemini(prompt):
    if not GEMINI_API_KEY:
        return "ERROR_API_KEY_FALTANTE"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO}:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        # Si Google responde con error (Key inválida, etc.), lanzamos excepción
        response.raise_for_status() 
        data = response.json()
        return data['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"ERROR_GEMINI: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/clasificar', methods=['POST'])
def clasificar():
    data = request.json
    glosa = data.get('glosa', '')
    proveedor = data.get('proveedor', '')
    contexto = data.get('contexto', 'Comercio general')
    
    prompt = f"""
    Eres un contador peruano experto. Clasifica esta factura en una cuenta PCGE.
    Contexto: {contexto}. Proveedor: {proveedor}. Glosa: {glosa}.
    Responde SOLO con JSON: {{"cuenta": "ej 6011", "razon": "explicación"}}
    """
    
    respuesta = consultar_gemini(prompt)
    
    # Si Gemini falló, te avisamos
    if "ERROR" in respuesta:
        return jsonify({"cuenta": "6011", "razon": respuesta})
        
    try:
        inicio = respuesta.find('{')
        fin = respuesta.rfind('}') + 1
        return jsonify(json.loads(respuesta[inicio:fin]))
    except:
        return jsonify({"cuenta": "6011", "razon": "Fallback JSON"})

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    pregunta = data.get('pregunta', '')
    db_contexto = data.get('db', 'No hay asientos')
    contexto = data.get('contexto', '')
    
    prompt = f"""
    Eres un contador experto. Datos de la empresa:\n{db_contexto}\nContexto: {contexto}\nPregunta del usuario: "{pregunta}"
    Responde de forma natural.
    """
    
    respuesta = consultar_gemini(prompt)
    
    # Si hay error de conexión, lo mostramos en el chat
    if "ERROR" in respuesta:
        return jsonify({"respuesta": f"⚠️ Fallo de conexión: {respuesta}"})
        
    return jsonify({"respuesta": respuesta})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
