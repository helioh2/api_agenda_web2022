import datetime
from http.client import NOT_FOUND
import json
import logging
from time import strptime
from typing import List
from urllib.parse import urlparse
from flask import (
    Flask,
    Response,
    session,
    request,
)
from flask_sqlalchemy import Pagination, SQLAlchemy
from flask_cors import CORS

from model import Contato, Usuario, db

import psycopg2
import psycopg2.extras
from flask_migrate import Migrate

from flask_session import Session
from utils import pagination_to_json

from validacao_form import validar_form



app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:root@localhost:5432/agenda'

db.init_app(app)
migrate = Migrate(app, db)

CORS(app, supports_credentials=True)  # TODO: Adicionar restrições de domínio
logging.getLogger('flask_cors').level = logging.DEBUG

PER_PAGE = 10

@app.get("/contatos")
def contatos():

    ## Pegar usuario logado, se existir:
    usuario = None
    if "user" in session.keys():
        usuario = session["user"]

    if not usuario:
        return {"erro": "Usuário não logado"}

    try:
        page = int(request.args.get("page")) ## pode dar erro de conversão de string que não é inteiro
    except:
        page = 1

    try:
        per_page = int(request.args.get("per_page"))
    except:
        per_page = PER_PAGE

    contatos:Pagination = (
        Contato.query                                # objeto Query
                .filter_by(id_usuario=usuario.id)    # objeto Query
                .paginate(page=page, per_page=per_page)       # objeto Pagination
    )

    # o = urlparse(request.base_url)
    # path = "http://" + o.hostname + ":" + str(o.port) + o.path
    # path = "http://" + o.hostname + ":" + str(o.port) + o.path

    contatos_json = pagination_to_json(contatos, request.path)
    contatos_json["items"] = [contato.as_dict() for contato in contatos.items]

    return contatos_json


@app.get("/contatos/<int:id_>")
def contato(id_):

    ## Pegar usuario logado, se existir:
    usuario = None
    if "user" in session.keys():
        usuario = session["user"]

    if not usuario:
        return {"erro": "Usuário não logado"}

    contato = Contato.query.filter_by(id=id_).first()

    return Response(status=NOT_FOUND) if not contato else contato.as_dict() 


@app.post("/contatos")
def adicionar_contato_action():

    usuario = session["user"]

    if not usuario:
        return {"erro": "Usuário não logado"}

    id_usuario = request.json["id_usuario"]
    if id_usuario != usuario.id:
        return {"erro", f"Usuário logado não tem permissão para adicionar contatos para usuário {id_usuario}"}
    
    resultado_validacao = validar_form(request.json)

    if resultado_validacao:  # se ele não for {}
        contato = dict(request.form)
        return resultado_validacao
    

    nome = request.json["nome"]
    telefone = request.json["telefone"]
    data_nascimento = request.json["data_nascimento"]
    detalhes = request.json["detalhes"]
    
    contato = Contato(
        nome=nome, 
        telefone=telefone, 
        data_nascimento=data_nascimento,
        detalhes=detalhes,
        id_usuario=id_usuario
    )

    db.session.add(contato)
    db.session.commit()
    
    return contato.as_dict()


@app.delete("/contatos/<int:id_>")
def remover_contato_action(id_):

    contato = Contato.query.filter_by(id=id_).first()
    db.session.delete(contato)
    db.session.commit()

    return contato.as_dict()


@app.post("/usuario")
def cadastrar_usuario_action():

    username = request.form.get("username")
    senha = request.form.get("senha")

    usuario = Usuario.query.filter_by(username=username).first()

    if usuario:
        return {"erro": "USUÁRIO JA EXISTE"}

    #else
    usuario = Usuario(username=username)

    usuario.set_password(senha)

    db.session.add(usuario) ## INSERT

    db.session.commit() ## COMMIT DA TRANSAÇÃO

    usuario_json = usuario.as_dict()
    del usuario_json["password_hash"]

    return usuario_json


@app.post("/sessions")
def login_action():

    username = request.json.get("username")
    senha = request.json.get("senha")

    ## AUTENTICAÇÃO
    usuario: Usuario = Usuario.query.filter_by(username=username).first()

    if not usuario:
        return {"erro": "Usuário não existe"} 

    if not usuario.check_password(senha):
        return {"erro": "Senha incorreta"}

    # else
    session["user"] = usuario

    usuario_json = usuario.as_dict()
    del usuario_json["password_hash"]

    return usuario_json  # TODO: isto devolve o cookie da sessão?


@app.delete("/sessions/<username>")
def logout_action(username):

    session["user"] = None

    return {}
