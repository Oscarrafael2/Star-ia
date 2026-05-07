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

SYSTEM_PROMPT = """
Eres StarIA, una IA avanzada creada por Forrester Studio.
Tu fundador es Oscar Rafael.
Hablas de forma innovadora y cercana (estilo 'brou').
"""

# Conexión lazy a MongoDB (no conecta al arrancar, sino cuando se necesita)
_mongo_client = None
_db = None

def get_db():
    global _mongo_client, _db
    if _db is None:
        if not MONGO_URI:
            raise Exception("MONGO_URI no está configurada en las variables de entorno.")
        _mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        _db = _mongo_client.staria_db.history
    return _db

def build_twiml(message: str):
    twiml = MessagingResponse()
    twiml.message(message)
    resp = app.make_response(str(twiml))
    resp.headers['Content-Type'] = 'text/xml'
    return resp

@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    user_id = request.values.get('From', 'unknown')
    user_msg = request.values.get('Body', '').strip()

    if not user_msg:
        return build_twiml("No recibí ningún mensaje, brou.")
    if not API_KEY:
        return build_twiml("Falta la VERCEL_API_KEY en Render.")

    # 1. Recuperar historial de MongoDB
    try:
        chats = get_db()
        doc = chats.find_one({"user_id": user_id})
        if doc and "messages" in doc:
            messages = doc["messages"]
            if not messages or messages[0].get("role") != "system":
                messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
        else:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    except Exception as e:
        print(f"[MongoDB ERROR] {e}")
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # 2. Agregar mensaje del usuario
    messages.append({"role": "user", "content": user_msg})
    if len(messages) > 11:
        messages = [messages[0]] + messages[-10:]

    # 3. Llamar a la IA
    try:
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {"model": "openai/gpt-4o-mini", "messages": messages}
        response = requests.post(URL_GATEWAY, headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
            ai_reply = response.json()['choices'][0]['message']['content']
        else:
            ai_reply = f"Error del gateway ({response.status_code}): {response.text[:200]}"
    except requests.exceptions.Timeout:
        ai_reply = "La IA tardó demasiado, intenta de nuevo brou."
    except Exception as e:
        ai_reply = f"Error de conexión: {str(e)}"

    # 4. Guardar historial en MongoDB
    messages.append({"role": "assistant", "content": ai_reply})
    try:
        chats = get_db()
        chats.update_one({"user_id": user_id}, {"$set": {"messages": messages}}, upsert=True)
    except Exception as e:
        print(f"[MongoDB SAVE ERROR] {e}")

    return build_twiml(ai_reply)

@app.route("/", methods=['GET'])
def home():
    try:
        get_db()
        db_status = "✅ MongoDB conectado"
    except Exception as e:
        db_status = f"❌ MongoDB error: {e}"
    return f"<h1>StarIA de Forrester Studio</h1><p>{db_status}</p>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
