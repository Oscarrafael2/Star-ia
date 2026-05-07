import os
import requests
from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from pymongo import MongoClient

# 1. PRIMERO CREAMOS LA APP
app = Flask(__name__)

# 2. CONFIGURACIÓN (Variables de entorno)
API_KEY = os.environ.get("VERCEL_API_KEY")
MONGO_URI = os.environ.get("MONGO_URI")
URL_GATEWAY = "https://ai-gateway.vercel.sh/v1/chat/completions"

SYSTEM_PROMPT = """
Eres StarIA, una IA experta en programación creada por Forrester Studio.
Tu fundador es Oscar Rafael.
Hablas de forma innovadora y cercana (estilo 'brou').
Tu objetivo es ayudar a devs a programar mejor.
"""

# Conexión a MongoDB
_mongo_client = None
_db = None

def get_db():
    global _mongo_client, _db
    if _db is None:
        if not MONGO_URI:
            raise Exception("Falta MONGO_URI en Render")
        _mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        _db = _mongo_client.staria_db.history
    return _db

def build_twiml(message: str):
    twiml = MessagingResponse()
    twiml.message(message)
    resp = app.make_response(str(twiml))
    resp.headers['Content-Type'] = 'text/xml'
    return resp

# --- RUTA PARA LA TERMINAL (CLI) ---
@app.route("/chat", methods=['POST'])
def chat_api():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    user_msg = data.get("mensaje", "")
    user_id = data.get("user_id", "terminal_user")

    # Lógica de respuesta (puedes mover esto a una función para no repetir)
    respuesta = procesar_ia(user_id, user_msg)
    return jsonify({"respuesta": respuesta})

# --- RUTA PARA WHATSAPP (TWILIO) ---
@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    user_id = request.values.get('From', 'unknown')
    user_msg = request.values.get('Body', '')
    
    ai_reply = procesar_ia(user_id, user_msg)
    return build_twiml(ai_reply)

def procesar_ia(user_id, user_msg):
    """Función central para manejar la IA y la memoria"""
    try:
        chats = get_db()
        doc = chats.find_one({"user_id": user_id})
        messages = doc["messages"] if doc else [{"role": "system", "content": SYSTEM_PROMPT}]
    except:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    messages.append({"role": "user", "content": user_msg})
    
    # Mantener historial corto
    if len(messages) > 11:
        messages = [messages[0]] + messages[-10:]

    try:
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {"model": "openai/gpt-4o-mini", "messages": messages}
        response = requests.post(URL_GATEWAY, headers=headers, json=payload, timeout=20)
        
        if response.status_code == 200:
            ai_reply = response.json()['choices'][0]['message']['content']
        else:
            ai_reply = "Brou, hubo un error con la IA. Intenta de nuevo."
    except:
        ai_reply = "Error de conexión con el cerebro de StarIA."

    # Guardar en Mongo
    messages.append({"role": "assistant", "content": ai_reply})
    try:
        get_db().update_one({"user_id": user_id}, {"$set": {"messages": messages}}, upsert=True)
    except:
        pass

    return ai_reply

@app.route("/", methods=['GET'])
def home():
    return "<h1>Servidor StarIA Activo</h1><p>Forrester Studio - AI CLI & WhatsApp</p>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
            
