
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# 1. Ruta para mostrar tu panel visual (HTML)
@app.route('/')
def inicio():
    return render_template('index.html')

# 2. Ruta para la IA (Por ahora simulada para que veas que funciona)
@app.route('/api/clasificar', methods=['POST'])
def clasificar():
    datos = request.json
    descripcion = datos.get('descripcion', '').upper()
    
    # Simulamos que la IA piensa por 1 segundo
    print(f"🤖 Analizando: {descripcion}")
    
    # Lógica básica de prueba
    cuenta = "2011"
    if "LUZ" in descripcion or "AGUA" in descripcion: cuenta = "6361"
    if "FLETE" in descripcion or "TRANSPORTE" in descripcion: cuenta = "6311"
    if "BALDE" in descripcion: cuenta = "251"
    
    return jsonify({
        "cuenta": cuenta,
        "fuente": "Simulación Python (Pronto Ollama)"
    })

if __name__ == '__main__':
    print("🚀 Servidor corriendo en http://localhost:5000")
app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
