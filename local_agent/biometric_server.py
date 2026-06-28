"""
Local Agent: DigitalPersona U.are.U 4500 Web Bridge
Este script actúa como puente entre el hardware local (Lector USB) y la aplicación web (Navegador).
El navegador web no puede acceder al puerto USB directamente, así que enviará una solicitud HTTP
a este servidor local (localhost:5000) para solicitar una lectura de huella.

Requisitos:
- Instalar Python 3
- pip install flask flask-cors
- Instalar SDK de DigitalPersona y envolturas para Python (ej. pyfingerprint o similar dependiendo del OS).
"""

from flask import Flask, jsonify
from flask_cors import CORS
import time
import random

app = Flask(__name__)
CORS(app) # Permite peticiones desde localhost o el dominio de la PWA

def scan_real_fingerprint():
    """
    Aquí iría el código real para inicializar el lector U.are.U 4500,
    esperar que el usuario ponga el dedo, capturar la imagen y convertirla a un
    Template ISO/ANSI en Base64.
    """
    # reader = dpfp.Reader()
    # reader.open()
    # template = reader.capture()
    # return base64.b64encode(template)
    
    # Simulación para desarrollo
    time.sleep(2) # Simula tiempo de captura
    return f"SIMULATED_FINGERPRINT_BASE64_{random.randint(1000,9999)}"

@app.route('/api/fingerprint/scan', methods=['GET'])
def scan():
    try:
        template = scan_real_fingerprint()
        return jsonify({
            "status": "success",
            "template_base64": template,
            "format": "ISO_19794_2"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    print("Iniciando Agente Biométrico Local en el puerto 5000...")
    print("El reloj checador web ahora puede comunicarse con el lector de huella.")
    app.run(host='127.0.0.1', port=5000)
