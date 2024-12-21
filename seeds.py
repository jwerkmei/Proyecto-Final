from db import db
from app import app
from models import User, Message

with app.app_context():
    db.create_all()

    user = User(email="test@example.org",nombre="Jurgen Werkmeister",generos_preferidos="western, cinearte, ciencia ficción")
    message = Message(content=f"Hola {user.nombre}. Soy PelisQuest un recomendador de películas, veo que te gustan los generos: {user.generos_preferidos}. ¿Te puedo recomendar alguna película de esos generos o algo distinto?", author="assistant", user=user)

    db.session.add(user)
    db.session.add(message)
    db.session.commit()

    print("Usuario y Mensaje creado!")
