from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap5
from openai import OpenAI
from dotenv import load_dotenv
from db import db, db_config
from models import User, Message

load_dotenv()

client = OpenAI()
app = Flask(__name__)
bootstrap = Bootstrap5(app)
db_config(app)


@app.route('/')
def index():
    return render_template('landing.html')



@app.route('/chat', methods=['GET', 'POST'])
def chat():
    user = db.session.query(User).first()
    generos_preferidos = user.generos_preferidos or ""

    if request.method == 'GET':
        return render_template('chat.html', messages=user.messages, generos_preferidos=generos_preferidos)

    intent = request.form.get('intent')

    user_message = ""

    # Si el intent es uno de los géneros preferidos del usuario
    if intent and intent.startswith("Recomiendame una película de"):
        genero = intent.split("de")[-1].strip()
        user_message = f"Recomiéndame una película de {genero}"

    # Si el intent es 'Enviar', procesamos el mensaje del usuario
    elif intent == "Enviar":
        user_message = request.form.get('message')

    else:
        user_message = "No entiendo esa solicitud."

    # Guardar nuevo mensaje en la BD
    db.session.add(Message(content=user_message, author="user", user=user))
    db.session.commit()

    messages_for_llm = [{
        "role": "system",
        "content": f"Eres un chatbot que recomienda películas, te llamas 'Next Moby'. Tu rol es responder recomendaciones de manera breve y concisa. No repitas recomendaciones. Debes recordar el nombre del usuario ({user.nombre}) y sus géneros preferidos ({user.generos_preferidos}) todo el tiempo.",
    }]

    for message in user.messages:
        messages_for_llm.append({
            "role": message.author,
            "content": message.content,
        })

    chat_completion = client.chat.completions.create(
        messages=messages_for_llm,
        model="gpt-4o",
        temperature=1
    )

    model_recommendation = chat_completion.choices[0].message.content
    db.session.add(Message(content=model_recommendation, author="assistant", user=user))
    db.session.commit()

    return render_template('chat.html', messages=user.messages, generos_preferidos=generos_preferidos)



@app.route('/user/<username>')
def user(username):
    favorite_movies = [
        'The Shawshank Redemption',
        'The Godfather',
        'The Dark Knight',
    ]
    return render_template('user.html', username=username, favorite_movies=favorite_movies)


@app.post('/recommend')
def recommend():
    user = db.session.query(User).first()
    data = request.get_json()
    user_message = data['message']
    new_message = Message(content=user_message, author="user", user=user)
    db.session.add(new_message)
    db.session.commit()

    messages_for_llm = [{
        "role": "system",
        "content": "Eres un chatbot que recomienda películas, te llamas 'Next Moby'. Tu rol es responder recomendaciones de manera breve y concisa. No repitas recomendaciones.",
    }]

    for message in user.messages:
        messages_for_llm.append({
            "role": message.author,
            "content": message.content,
        })

    chat_completion = client.chat.completions.create(
        messages=messages_for_llm,
        model="gpt-4o",
    )

    message = chat_completion.choices[0].message.content

    return {
        'recommendation': message,
        'tokens': chat_completion.usage.total_tokens,
    }


@app.route('/user/update/<int:id>', methods=['GET', 'POST'])
def update_user(id):
    user = db.session.query(User).get(id)
    
    if request.method == 'POST':
        if user:
            # Se actualizan los campos con los datos enviados desde el formulario
            user.nombre = request.form['nombre']
            user.email = request.form['email']
            user.generos_preferidos = request.form['generos_preferidos'].lower()
            
            # Guardan los cambios en la base de datos
            db.session.commit()
            
            # Se redirige de nuevo a la misma página con un mensaje de éxito como parámetro en la URL
            return redirect(url_for('update_user', id=id, success='Información del usuario fue actualizada'))
        
        else:
            return redirect(url_for('update_user', id=id, error='Usuario no encontrado'))

    # Si es GET, mostramos el formulario con los datos del usuario
    return render_template('update_user.html', user=user)