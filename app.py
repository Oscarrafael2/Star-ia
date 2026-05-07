import os
import requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from pymongo import MongoClient

app = Flask(__name__)

# CONFIGURACIÓN
API_KEY = os.environ.get("VERCEL_API_KEY")
MONGO_URI = os.environ.get("MONGO_URI")
URL_GATEWAY = "https://ai-gateway.vercel.sh/v1/chat/completions"

# Conexión a MongoDB
client = MongoClient(MONGO_URI)
db = client.staria_db
chats = db.history

SYSTEM_PROMPT = "Eres StarIA, una IA creada por Forrester Studio por Oscar Rafael..."

@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    user_id = request.values.get('From', 'unknown')
    user_msg = request.values.get('Body', '')

    # 1. Recuperar historial de la DB
    doc = chats.find_one({"user_id": user_id})
    if doc:
        messages = doc["messages"]
    else:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # 2. Agregar mensaje del usuario y consultar IA
    messages.append({"role": "user", "content": user_msg})
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "openai/gpt-4o-mini", "messages": messages[-10:]}

    try:
        response = requests.post(URL_GATEWAY, headers=headers, json=payload)
        ai_reply = response.json()['choices'][0]['message']['content']
    except:
        ai_reply = "Brou, tuve un error de conexión."

    # 3. Guardar historial actualizado
    messages.append({"role": "assistant", "content": ai_reply})
    chats.update_one({"user_id": user_id}, {"$set": {"messages": messages}}, upsert=True)

    twiml = MessagingResponse()
    twiml.message(ai_reply)
    return str(twiml)

@app.route("/", methods=['GET'])
def home():
    return "<h1>StarIA con Memoria DB Activa</h1>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000)) # Render suele usar el 10000
    app.run(host='0.0.0.0', port=port)
    
