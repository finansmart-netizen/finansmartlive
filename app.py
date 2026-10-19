from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import json
import os

# Configuramos Flask para que busque el HTML en la carpeta 'templates'
app = Flask(__name__, template_folder='templates')
CORS(app)

# --- CONFIGURACIÓN DE GEMINI ---
# Render leerá esta variable desde su panel de Environment
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
# Modelo recomendado: gemini-1.5-flash (rápido y gratuito)
MODELO = "gemini-1.5-flash" 
URL_GEMINI = f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO}:generateContent?key={GEMINI_API_KEY}"

def consultar_gemini(prompt):
    if not GEMINI_API_KEY:
        return "Error: Falta configurar GEMINI_API_KEY en las variables de entorno de Render."
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(URL_GEMINI, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        # Extraer el texto de la respuesta de Gemini
        return data['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"Error conectando con Gemini: {str(e)}"

# --- RUTA PRINCIPAL (Carga el HTML) ---
@app.route('/')
def index():
    # Busca el index.html dentro de la carpeta templates
    return render_template('index.html')

# --- API: CLASIFICAR FACTURA ---
@app.route('/api/clasificar', methods=['POST'])
def clasificar():
    data = request.json
    contexto = data.get('contexto', 'Comercio general')
    glosa = data.get('glosa', '')
    proveedor = data.get('proveedor', '')
    
    prompt = f"""
    Eres un contador peruano experto en PCGE. Clasifica esta factura.
    Contexto del negocio: {contexto}
    Proveedor: {proveedor}
    Glosa: {glosa}
    
    Responde ÚNICAMENTE con un JSON válido (sin markdown, sin texto extra) con esta estructura:
    {{"cuenta": "código de cuenta (ej. 6011, 636)", "razon": "explicación breve"}}
    """
    
    respuesta_ia = consultar_gemini(prompt)
    
    try:
        # Limpiar la respuesta por si Gemini devuelve markdown
        inicio = respuesta_ia.find('{')
        fin = respuesta_ia.rfind('}') + 1
        json_str = respuesta_ia[inicio:fin]
        return jsonify(json.loads(json_str))
    except:
        return jsonify({"cuenta": "6011", "razon": "Fallback por formato inesperado de Gemini"})

# --- API: CHAT FINANCIERO ---
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    pregunta = data.get('pregunta', '')
    db_contexto = data.get('db', 'No hay asientos registrados')
    contexto_negocio = data.get('contexto', '')
    
    prompt = f"""
    Eres un contador y asesor financiero. Responde a la pregunta del usuario basándote en sus datos reales.
    
    DATOS DE LA EMPRESA (Libro Diario):
    {db_contexto}
    
    CONTEXTO DEL NEGOCIO: {contexto_negocio}
    
    PREGUNTA DEL USUARIO: "{pregunta}"
    
    Responde de forma amigable, profesional y directa. Usa los datos para calcular totales si es necesario.
    """
    
    respuesta_ia = consultar_gemini(prompt)
    return jsonify({"respuesta": respuesta_ia})

# --- ARRANQUE DEL SERVIDOR ---
if __name__ == '__main__':
    # Render usa el puerto definido en la variable PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
