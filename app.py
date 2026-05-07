import os
import requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# CONFIGURACIÓN: Ahora las sacamos de las variables de entorno de Render
# Si no las encuentra, pondrá un mensaje de error
API_KEY = os.environ.get("VERCEL_API_KEY")
URL = "https://ai-gateway.vercel.sh/v1/chat/completions"

# Memoria por usuario (Número de teléfono)
user_memory = {}

SYSTEM_PROMPT = """
Eres StarIA, una IA avanzada creada por Forrester Studio.
Tu fundador es Oscar Rafael. Hablas de forma innovadora, técnica y cercana ('brou').
Mantén el hilo de la conversación y ayuda en todo lo que puedas.
"""

@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    user_id = request.values.get('From', '')
    user_msg = request.values.get('Body', '')

    if not API_KEY:
        return "Error: No se configuró la VERCEL_API_KEY en Render."

    # Gestión de memoria
    if user_id not in user_memory:
        user_memory[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    user_memory[user_id].append({"role": "user", "content": user_msg})
    
    # Mantener System + últimos 10 mensajes
    if len(user_memory[user_id]) > 11:
        user_memory[user_id] = [user_memory[user_id][0]] + user_memory[user_id][-10:]

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": user_memory[user_id]
    }

    try:
        response = requests.post(URL, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            ai_reply = result['choices'][0]['message']['content']
            user_memory[user_id].append({"role": "assistant", "content": ai_reply})
        else:
            ai_reply = "Hubo un detalle con mi conexión a Vercel, brou. ¿Reintentamos?"
            print(f"Error Vercel: {response.text}")
    except Exception as e:
        ai_reply = "Error de conexión en el server. Avisale a Oscar Rafael."
        print(f"Error Conexión: {e}")

    resp = MessagingResponse()
    resp.message(ai_reply)
    return str(resp)

@app.route("/", methods=['GET'])
def health():
    return "<h1>StarIA Online</h1><p>Forrester Studio en control.</p>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
