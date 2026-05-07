import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI

app = Flask(__name__)

# Configura tu API Key mediante variables de entorno (más seguro)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Definición de la identidad de la IA
SYSTEM_PROMPT = """
Eres StarIA, una inteligencia artificial avanzada diseñada para WhatsApp. 
Fuiste creada y fundada por Forrester Studio, cuyo dueño y fundador es Oscar Rafael.
Tu personalidad:
- Eres profesional pero cercana, con un toque tecnológico e innovador.
- Si te preguntan tu nombre, respondes que eres StarIA.
- Si preguntan quién te creó o fundó, mencionas orgullosamente a Forrester Studio y a Oscar Rafael.
- Hablas con seguridad y siempre buscas ayudar al usuario con sus dudas.
"""

@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    incoming_msg = request.values.get('Body', '')
    
    try:
        # Llamada a la API con el contexto de StarIA
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": incoming_msg}
            ]
        )
        ai_text = response.choices[0].message.content
    except Exception as e:
        ai_text = "Lo siento, brou, tuve un pequeño error técnico. ¿Podemos intentar de nuevo?"
        print(f"Error: {e}")

    # Respuesta formato TwiML para Twilio
    twilio_resp = MessagingResponse()
    msg = twilio_resp.message()
    msg.body(ai_text)

    return str(twilio_resp)

if __name__ == "__main__":
    # El puerto debe ser dinámico para servidores como Render o Railway
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
