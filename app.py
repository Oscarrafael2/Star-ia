import os
import requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# CONFIGURACIÓN
API_KEY = os.environ.get("VERCEL_API_KEY")
URL_GATEWAY = "https://ai-gateway.vercel.sh/v1/chat/completions"

user_memory = {}

SYSTEM_PROMPT = """
Eres StarIA, una IA avanzada creada por Forrester Studio.
Tu fundador es Oscar Rafael. 
Hablas de forma innovadora y cercana (estilo 'brou').
"""

def build_twiml(message: str):
    """Helper para siempre devolver un TwiML válido."""
    twiml = MessagingResponse()
    twiml.message(message)
    resp = app.make_response(str(twiml))
    resp.headers['Content-Type'] = 'text/xml'
    return resp

@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    try:
        user_id = request.values.get('From', '')
        user_msg = request.values.get('Body', '').strip()

        if not user_msg:
            return build_twiml("No recibí ningún mensaje, brou.")

        if not API_KEY:
            return build_twiml("Falta la VERCEL_API_KEY en las variables de entorno de Render.")

        # Memoria por usuario
        if user_id not in user_memory:
            user_memory[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

        user_memory[user_id].append({"role": "user", "content": user_msg})

        # Limitar historial a últimos 10 mensajes + system prompt
        if len(user_memory[user_id]) > 11:
            user_memory[user_id] = [user_memory[user_id][0]] + user_memory[user_id][-10:]

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "openai/gpt-4o-mini",
            "messages": user_memory[user_id]
        }

        response = requests.post(URL_GATEWAY, headers=headers, json=payload, timeout=20)

        if response.status_code == 200:
            result = response.json()
            ai_reply = result['choices'][0]['message']['content']
            user_memory[user_id].append({"role": "assistant", "content": ai_reply})
        else:
            # Mostrar el error real para poder debuggear
            ai_reply = f"Error del gateway ({response.status_code}): {response.text[:200]}"

    except requests.exceptions.Timeout:
        ai_reply = "La IA tardó demasiado en responder, intenta de nuevo brou."
    except Exception as e:
        ai_reply = f"Error inesperado: {str(e)}"

    return build_twiml(ai_reply)

@app.route("/", methods=['GET'])
def home():
    return "<h1>StarIA de Forrester Studio — Online ✅</h1>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
