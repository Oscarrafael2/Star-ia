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

@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    user_id = request.values.get('From', '')
    user_msg = request.values.get('Body', '')

    if not API_KEY:
        twiml = MessagingResponse()
        twiml.message("Falta la API KEY en Render, brou.")
        return str(twiml)

    # Memoria
    if user_id not in user_memory:
        user_memory[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    user_memory[user_id].append({"role": "user", "content": user_msg})
    
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

    try:
        response = requests.post(URL_GATEWAY, headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            ai_reply = result['choices'][0]['message']['content']
            user_memory[user_id].append({"role": "assistant", "content": ai_reply})
        else:
            ai_reply = f"Error de Vercel: {response.status_code}"
    except Exception as e:
        ai_reply = "Error de conexión, brou."

    # --- AQUÍ ESTABA EL ERROR, YA ESTÁ CORREGIDO ---
    twiml = MessagingResponse()
    twiml.message(ai_reply)
    return str(twiml) # Enviamos el objeto twiml convertido a texto

@app.route("/", methods=['GET'])
def home():
    return "<h1>StarIA de Forrester Studio</h1>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
