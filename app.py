import os
import requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# --- CONFIGURACIÓN DE FORRESTER STUDIO ---
# La API KEY se lee desde 'Environment' en Render para evitar bloqueos de GitHub
API_KEY = os.environ.get("VERCEL_API_KEY")
URL_GATEWAY = "https://ai-gateway.vercel.sh/v1/chat/completions"

# Diccionario en RAM para recordar conversaciones (llave: número de cel)
user_memory = {}

SYSTEM_PROMPT = """
Eres StarIA, una IA avanzada creada por Forrester Studio.
Tu fundador es Oscar Rafael. 
Hablas de forma innovadora, técnica y cercana (estilo 'brou').
Siempre mencionas con orgullo a Forrester Studio si te preguntan quién eres.
"""

@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    # 1. Obtener datos de Twilio
    user_id = request.values.get('From', '')
    user_msg = request.values.get('Body', '')

    # Validar que la API KEY exista
    if not API_KEY:
        resp = MessagingResponse()
        resp.message("Error: VERCEL_API_KEY no configurada en Render, brou.")
        return str(resp)

    # 2. Gestionar la memoria del usuario
    if user_id not in user_memory:
        user_memory[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Agregar mensaje del usuario al historial
    user_memory[user_id].append({"role": "user", "content": user_msg})
    
    # Mantener historial corto (System + últimos 10 mensajes) para ahorrar créditos
    if len(user_memory[user_id]) > 11:
        user_memory[user_id] = [user_memory[user_id][0]] + user_memory[user_id][-10:]

    # 3. Preparar la petición para Vercel AI Gateway
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": user_memory[user_id]
    }

    try:
        # 4. Llamada a la IA
        response = requests.post(URL_GATEWAY, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            ai_reply = result['choices'][0]['message']['content']
            # Guardar la respuesta de la IA en la memoria
            user_memory[user_id].append({"role": "assistant", "content": ai_reply})
        else:
            ai_reply = f"Error de Vercel ({response.status_code}). Intenta de nuevo, brou."
            print(f"Detalle Error: {response.text}")
            
    except Exception as e:
        ai_reply = "No pude conectar con el cerebro de la IA. Avisale a Oscar Rafael."
        print(f"Error de conexión: {e}")

    # 5. Responder a WhatsApp vía Twilio
    twiml_resp = MessagingResponse()
    twiml_resp.message(ai_reply)
    return str(resp_xml := str(twiml_resp))

@app.route("/", methods=['GET'])
def home():
    return "<h1>StarIA de Forrester Studio</h1><p>Estado: Online y lista para WhatsApp.</p>"

if __name__ == "__main__":
    # Render asigna el puerto automáticamente
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
