@app.route("/chat", methods=['POST'])
def chat_api():
    data = request.get_json()
    user_msg = data.get("mensaje", "")
    user_id = data.get("user_id", "terminal_user")

    # 1. Obtener historial de MongoDB (para que recuerde al usuario de terminal)
    try:
        chats = get_db()
        doc = chats.find_one({"user_id": user_id})
        messages = doc["messages"] if doc else [{"role": "system", "content": SYSTEM_PROMPT}]
    except:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    messages.append({"role": "user", "content": user_msg})

    # 2. Llamar a la IA con TU API KEY (la que ya tienes en Render)
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "openai/gpt-4o-mini", "messages": messages[-10:]}
    
    response = requests.post(URL_GATEWAY, headers=headers, json=payload)
    ai_reply = response.json()['choices'][0]['message']['content']

    # 3. Guardar en MongoDB
    messages.append({"role": "assistant", "content": ai_reply})
    get_db().update_one({"user_id": user_id}, {"$set": {"messages": messages}}, upsert=True)

    return jsonify({"respuesta": ai_reply})
    
