import os
from flask import Flask, render_template, request, jsonify
from groq import Groq
from pcge_data import PCGE_DICCIONARIO # Importamos la base de datos

app = Flask(__name__)

@app.route('/')
def inicio():
    return render_template('index.html')

@app.route('/api/clasificar', methods=['POST'])
def clasificar():
    datos = request.json
    descripcion = datos.get('descripcion', '').upper()
    
    if not descripcion:
        return jsonify({"error": "Falta la descripción"}), 400

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return jsonify({"cuenta": "2011", "fuente": "Error: Falta API KEY en Render"})

    client = Groq(api_key=api_key)
    
    # Le pasamos la base de datos estructurada a la IA
    prompt = f"""
    Eres un contador peruano experto en el PCGE. 
    Tienes la siguiente base de datos de cuentas contables jerarquizada:
    {PCGE_DICCIONARIO}

    Clasifica esta factura: "{descripcion}"
    Responde ÚNICAMENTE con el código numérico de la cuenta (4 o 5 dígitos) que mejor se adapte. Sin explicaciones.
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}]
        )
        cuenta_ia = completion.choices[0].message.content.strip()
        # Limpiar para que solo devuelva números
        cuenta_ia = ''.join(filter(str.isdigit, cuenta_ia)) 
        
        return jsonify({
            "cuenta": cuenta_ia,
            "fuente": "IA (Groq) + Base de Datos PCGE Completa"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
