from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import json
import os

app = Flask(__name__, template_folder='templates')
CORS(app)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
# Usamos el modelo estándar de la API
MODELO = "gemini-1.5-flash" 

def consultar_gemini(prompt):
    if not GEMINI_API_KEY:
        return "⚠️ ERROR: No has configurado GEMINI_API_KEY en las variables de entorno de Render."
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO}:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        # Esto lanzará un error si Google rechaza la petición
        response.raise_for_status() 
        data = response.json()
        return data['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        # Si falla, devolvemos el error real al chat
        return f"❌ Error de conexión con Gemini: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    pregunta = data.get('pregunta', '')
    db_contexto = data.get('db', 'No hay asientos')
    contexto = data.get('contexto', '')
    
    prompt = f"""
    Eres un contador experto. Datos de la empresa:\n{db_contexto}\nContexto: {contexto}\nPregunta del usuario: "{pregunta}"
    Responde de forma natural y directa.
    """
    
    respuesta = consultar_gemini(prompt)
    return jsonify({"respuesta": respuesta})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
