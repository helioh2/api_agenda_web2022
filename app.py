import datetime
from http.client import BAD_REQUEST, NOT_FOUND, UNAUTHORIZED, UNPROCESSABLE_ENTITY
import json
from time import strptime
from typing import List
from flask import (
    Flask,
    session,
    escape,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_sqlalchemy import Pagination, SQLAlchemy

from model import Contato, Usuario, db

import psycopg2
import psycopg2.extras
from flask_migrate import Migrate

from flask_session import Session

from validacao_input import validar_json


app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:root@localhost:5432/agenda'

db.init_app(app)
migrate = Migrate(app, db)

PER_PAGE = 10


## Usuario 1 --> * Contato

@app.get("/")
def main():
    return render_template("index.html", data=datetime.datetime.utcnow())


@app.get("/about/")
def about():
    return render_template("about.html")

@app.get("/contatos")
def contatos_json():

     # Pegar usuario logado, se existir:
    usuario = None
    if "user" in session.keys():
        usuario = session["user"]

    if not usuario:
        return {"erro": "Usuário não logado"}, UNAUTHORIZED

    # busca_str = "%" + request.args.get("busca") + "%"
    id_usuario = usuario.id
    
    contatos:List[Contato] = (
        Contato.query                                # objeto Query
                .filter_by(id_usuario=id_usuario)    # objeto Query
                # .filter(Contato.nome.ilike(busca_str))  # objeto Query
                .all()  # List[Contato]
    )

    if not contatos:
        return [], NOT_FOUND

    return json.dumps([contato.as_dict() for contato in contatos])


@app.get("/contatos/<id_>")
def contato(id_):

    id_usuario = 2   ## TODO: depois trocar pela validação de sessão

    contato = (
        Contato.query                                # objeto Query
                .filter_by(id_usuario=id_usuario)    # objeto Query
                .filter_by(id=id_)                   # objeto Query   
                .first()  # Contato
    )

    if not contato:
        # resp = make_response(status=NOT_FOUND, )
        # resp.status_code = NOT_FOUND
        # resp.json({"erro": "Usuario não existe"})
        return {"erro": "Usuario não existe"}, NOT_FOUND

    return json.dumps(contato.as_dict())






@app.post("/contatos")
def adicionar_contato_action():

    resultado_validacao = validar_json(request.json)

    if resultado_validacao:  # se ele não for {}
        return resultado_validacao, UNPROCESSABLE_ENTITY

    # usuario = session["user"]

    # if not usuario:
    #     return "É NECESSÁRIO ESTAR LOGADO PARA ADICIONAR CONTATO"  # TODO: MELHORAR

    #else
    nome = request.json["nome"]
    telefone = request.json["telefone"]
    data_nascimento = request.json["data_nascimento"]
    detalhes = request.json["detalhes"]
   
    contato = Contato(
        nome=nome, 
        telefone=telefone, 
        data_nascimento=data_nascimento,
        detalhes=detalhes,
        id_usuario=2)

    db.session.add(contato)  # adiciona ou atualiza
    db.session.commit()

    ## TODO: SETAR ID NO RETORNO
    
    return json.dumps(contato.as_dict())


@app.delete("/contatos/<id_>")
def remover_contato_action(id_):

    contato = Contato.query.filter_by(id=id_).first()

    if not contato:
        return {"erro": "Usuário não existe"}

    db.session.delete(contato)
    db.session.commit()

    return json.dumps(contato.as_dict())


@app.put("/contatos/<id_>")
def put_contato(id_):

    contato = Contato.query.filter_by(id=id_).first()

    if not contato:
        return {"erro": "Usuario nao existe"}, UNPROCESSABLE_ENTITY

    # id_ = request.json["id"]
    nome = request.json["nome"]
    telefone = request.json["telefone"]
    data_nascimento = request.json["data_nascimento"]
    detalhes = request.json["detalhes"]
   
    contato = Contato(
        id=id_,
        nome=nome, 
        telefone=telefone, 
        data_nascimento=data_nascimento,
        detalhes=detalhes,
        id_usuario=2)

    db.session.merge(contato)  # adiciona ou atualiza
    db.session.commit()

    return json.dumps(contato.as_dict())

    

@app.patch("/contatos/<id_>")
def patch_contato(id_):
    contato = Contato.query.filter_by(id=id_).first()

    if not contato:
        return {"erro": "Usuario nao existe"}, UNPROCESSABLE_ENTITY

    for nome_campo, valor in request.json.items():
        # ex: "nome"  -> "Marcos Tacalepau Nesse Carrinho"
        try:
            setattr(contato, nome_campo, valor)
        except:
            continue  ## ALTERNATIVA: DAR ERRO
        
    db.session.merge(contato)  # adiciona ou atualiza
    db.session.commit()

    return json.dumps(contato.as_dict())


@app.post("/usuarios")
def cadastrar_usuario_action():

    username = request.json.get("username")
    senha = request.json.get("senha")

    usuario = Usuario.query.filter_by(username=username).first()

    if usuario:
        return {"erro": "Usuario já existe"}, BAD_REQUEST

    #else
    usuario = Usuario(username=username)

    usuario.set_password(senha)

    db.session.add(usuario) ## INSERT

    db.session.commit() ## COMMIT DA TRANSAÇÃO

    dict_usuario = usuario.as_dict()
    del dict_usuario["password_hash"]

    return json.dumps(dict_usuario)


@app.post("/sessions")
def login_action():

    username = request.json.get("username")
    senha = request.json.get("senha")

    ## AUTENTICAÇÃO
    usuario: Usuario = Usuario.query.filter_by(username=username).first()

    if not usuario:
        return {"erro": "Usuario não existe"}, BAD_REQUEST

    if not usuario.check_password(senha):
        return {"erro": "Senha incorreta"}, BAD_REQUEST  ## TODO: pesquisar qual seria o codigo mais correto

    # else
    session["user"] = usuario

    dict_usuario = usuario.as_dict()
    del dict_usuario["password_hash"]

    return json.dumps(dict_usuario)


@app.delete("/sessions/<id_>")
def logout_action(id_):

    usuario = session.get("user")
    session.pop("user")

    dict_usuario = usuario.as_dict()
    del dict_usuario["password_hash"]

    return json.dumps(dict_usuario)


@app.get("/form_test_xss")
def form_test_xss():
    return render_template("form_test.html")


@app.post("/form_test_action")
def form_test_action():
    campo = request.form["campo"]

    return "<p> {} </p>".format(escape(campo))

