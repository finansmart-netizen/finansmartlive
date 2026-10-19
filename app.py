import os
import sqlite3
from flask import Flask, render_template, request, jsonify
from groq import Groq

app = Flask(__name__)
DB_NAME = 'finansmart.db'

# --- 1. CREAR LA BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Tabla de asientos
    c.execute('''CREATE TABLE IF NOT EXISTS asientos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nro INTEGER, fecha TEXT, glosa TEXT, factura TEXT, 
        cuenta TEXT, debe REAL, haber REAL
    )''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def inicio():
    return render_template('index.html')

# --- 2. GUARDAR UN ASIENTO (Llamado desde el HTML) ---
@app.route('/api/guardar-asiento', methods=['POST'])
def guardar_asiento():
    datos = request.json
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Guardamos cada línea del asiento
    for linea in datos['lineas']:
        c.execute("INSERT INTO asientos (nro, fecha, glosa, factura, cuenta, debe, haber) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (datos['nro'], datos['fecha'], datos['glosa'], datos['factura'], 
                   linea['cuenta'], linea['debe'], linea['haber']))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

# --- 3. LEER TODOS LOS ASIENTOS (Para el Libro y para la IA) ---
@app.route('/api/obtener-asientos', methods=['GET'])
def obtener_asientos():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM asientos")
    filas = c.fetchall()
    conn.close()
    
    # Estructuramos los datos para el HTML
    asientos = []
    for fila in filas:
        asientos.append({
            "id": fila[0], "nro": fila[1], "fecha": fila[2], "glosa": fila[3], 
            "factura": fila[4], "cuenta": fila[5], "debe": fila[6], "haber": fila[7]
        })
    return jsonify(asientos)

# --- 4. LA IA CON CONTEXTO REAL (Lee la Base de Datos) ---
@app.route('/api/clasificar', methods=['POST'])
def clasificar():
    datos = request.json
    descripcion = datos.get('descripcion', '').upper()
    giro = datos.get('giro', 'general')
    contexto = datos.get('contexto', '')
    
    # La IA lee los asientos históricos para aprender
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT glosa, cuenta FROM asientos LIMIT 50") # Últimos 50 movimientos
    historial = c.fetchall()
    conn.close()
    
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return jsonify({"error": "Falta API KEY de Groq"}), 500
    
    client = Groq(api_key=api_key)
    
    prompt = f"""
    Eres un contador peruano experto en el PCGE. 
    GIRO DEL NEGOCIO: {giro}
    REGLAS: {contexto}
    HISTORIAL DE MOVIMIENTOS (Aprende de esto):
    {historial}
    
    Clasifica esta nueva factura: "{descripcion}"
    Responde SOLO con el código de la cuenta (ej: 6011).
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}]
        )
        cuenta = completion.choices[0].message.content.strip()
        cuenta = ''.join(filter(str.isdigit, cuenta))
        return jsonify({"cuenta": cuenta, "fuente": "Groq + Historial"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
