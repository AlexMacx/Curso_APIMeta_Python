from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import http.client
import json

app = Flask(__name__)

#Configuracion de la base de datos SQLITE
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///metapython.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#Modelo de la tabla log
class Log(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    fecha_y_hora = db.Column(db.DateTime, default=datetime.utcnow)
    texto = db.Column(db.TEXT)

#Crear la tabla si no existe
with app.app_context():
    db.create_all()

#Función para ordenar los registros por fecha y hora
def ordenar_fecha_hora(registros):
    return sorted(registros, key=lambda x: x.fecha_y_hora, reverse=True)

@app.route('/')
def index():
    #Obtener todos los registros de la bd
    registros = Log.query.all()
    registros_ordenados = ordenar_fecha_hora(registros)
    return render_template('index.html', registros=registros_ordenados)

mensajes_log = []

#Funcion para agregar mensajes y guardar en la base de datos
def agregar_mensajes_log(texto):
    mensajes_log.append(texto)

    #Guardar el mensaje en la base de datos
    nuevo_registro = Log(texto=texto)
    db.session.add(nuevo_registro)
    db.session.commit()

#Token de verificación para la configuración
TOKEN_MACXICODE = "MACXICODE"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        challenge = verificar_token(request)
        return challenge
    elif request.method == 'POST':
        response = recibir_mensajes(request)
        return response

def verificar_token(req):
    token = req.args.get('hub.verify_token')
    challenge = req.args.get('hub.challenge')

    if challenge and token == TOKEN_MACXICODE:
        return challenge
    else:
        return jsonify({'error':'Token invalido'}), 401

def recibir_mensajes(req):
    try:
        req = request.get_json()
        entry = req['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        objeto_mensaje = value['messages']
        
        if objeto_mensaje:
            messages = objeto_mensaje[0]

            if 'type' in messages:
                tipo = messages['type']

                if tipo == 'interactive':
                    return 0
                
                if 'text' in messages:
                    texto = messages['text']['body']
                    numero = messages['from']
                    if(len(numero)==13):
                        numero = numero[0:2]+numero[3:]
                    #agregar_mensajes_log(json.dumps(texto))
                    #agregar_mensajes_log(json.dumps(numero))
                    enviar_mensajes_whatsapp(texto, numero)

        return jsonify({'message':'EVENT_RECEIVED'})
    except Exception as e:
        return jsonify({'message':'EVENT_RECEIVED'})

def enviar_mensajes_whatsapp(texto, numero):
    texto = texto.lower()

    if 'hola' in texto:
        data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": " Hola, ¿Cómo estás? Bienvenido."
            }
        }
    else:
        data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum."
            }
        }
    #Convertir el diccionario a formato JSON
    data = json.dumps(data)

    tkn = "EAApgHYrrpPkBO4btswwrA9XZB6A1M3yvlJcGNPzJiZAL408gldsuRzkZB6im9Ey10ZClKZBi5VKPZBHwZCXQ4suGM4bo07acyfIcqe6cLaDoCYoeFG5H06ag4DMVWh1bgOO6NrkJnRardjCiTNRZBhRuI3zH0chgLHEpPKf5o73V47lenHweQzgpHZBCoYPLSZBfm3IXhrlAmdlzleUroZAMOBVEz28NCfhjjjJHyMqC6BH"
    bearer = "Bearer "+tkn

    headers = {
        "Content-Type" : "application/json",
        "Authorization" : bearer
    }

    connection = http.client.HTTPSConnection("graph.facebook.com")

    try:
        url_req = "/v21.0/500359583168203/messages"
        connection.request("POST","/v21.0/500359583168203/messages", data, headers) 
        response = connection.getresponse()
        
        agregar_mensajes_log(json.dumps(numero))
        agregar_mensajes_log(json.dumps(response.status))
        agregar_mensajes_log(json.dumps(response.reason))
        agregar_mensajes_log(json.dumps(response.read().decode()))
    except Exception as e:
        agregar_mensajes_log(json.dumps(e))
    finally:
        connection.close()

if __name__=='__main__':
    app.run(host='0.0.0.0',port=80,debug=True)