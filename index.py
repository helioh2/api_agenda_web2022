from datetime import datetime
from http.client import BAD_REQUEST, NOT_FOUND, UNAUTHORIZED, UNPROCESSABLE_ENTITY
import json
import logging
from flask import (
    Flask,
    session,
    request,
)
from config import setup_database

from model import Contato, ContatosPaginatedSchema, Usuario, db

from flask_migrate import Migrate

from flask_session import Session
from utils import pagination_to_json

from validacao_input import validar_json

from flask_cors import CORS

from flask_sqlalchemy import Pagination

from flask_pydantic_spec import FlaskPydanticSpec, Response, Request


app = Flask(__name__)

spec = FlaskPydanticSpec("flask", title="Contatos API")
spec.register(app)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

setup_database(app)

db.init_app(app)
migrate = Migrate(app, db)

PER_PAGE = 10

CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})  # TODO: Adicionar restrições de domínio

logging.getLogger('flask_cors').level = logging.DEBUG


def verificar_login():
    # Pegar usuario logado, se existir:
    usuario = None
    if "user" in session.keys():
        usuario = session["user"]

    if not usuario:
        raise ValueError   ## TODO: Criar exceção especifica

    return usuario

@app.get("/contatos")
@spec.validate(resp=Response(HTTP_200=ContatosPaginatedSchema)
def contatos_json():

    try:
        usuario = verificar_login()
    except:
        return {"erro": "Usuário não logado"}, UNAUTHORIZED

    id_usuario = usuario.id

    if request.args.get("page"):
        page = int(request.args.get("page"))  ## pode dar erro
    else:
        page = 1

    if request.args.get("nome"):
        busca_str = "%" + request.args.get("nome") + "%"
        contatos:Pagination = (
            Contato.query                                # objeto Query
                    .filter_by(id_usuario=id_usuario)    # objeto Query
                    .filter(Contato.nome.ilike(busca_str))  # objeto Query
                    .paginate(page=page, per_page=PER_PAGE)  # Pagination
        )
    else:
    
        contatos:Pagination = (
            Contato.query                                # objeto Query
                    .filter_by(id_usuario=id_usuario)    # objeto Query
                    .paginate(page=page, per_page=PER_PAGE)  # Pagination

        )


    contatos_json = pagination_to_json(contatos, "http://localhost:5000")

    return contatos_json


# @app.get("/contatos_fixo")
# def contatos_json_sem_login():

#      # Pegar usuario logado, se existir:
#     usuario = None
#     if "user" in session.keys():
#         usuario = session["user"]

#     if not usuario:
#         return {"erro": "Usuário não logado"}, UNAUTHORIZED

#     id_usuario = usuario.id
    
#     contatos:List[Contato] = (
#         Contato.query                                # objeto Query
#                 .filter_by(id_usuario=id_usuario)    # objeto Query
#                 # .filter(Contato.nome.ilike(busca_str))  # objeto Query
#                 .all()  # List[Contato]
#     )

#     if not contatos:
#         return [], NOT_FOUND

#     return json.dumps([contato.to_json() for contato in contatos])


@app.get("/contatos/<id_>")
def contato(id_):

    try:
        usuario = verificar_login()
    except:
        return {"erro": "Usuário não logado"}, UNAUTHORIZED

    id_usuario = usuario.id


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

    return json.dumps(contato.to_json())






@app.post("/contatos")
def adicionar_contato_action():

    try:
        usuario = verificar_login()
    except:
        return {"erro": "Usuário não logado"}, UNAUTHORIZED

    id_usuario = usuario.id


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
        id_usuario=id_usuario)

    db.session.add(contato)  # adiciona ou atualiza
    db.session.commit()

    ## TODO: SETAR ID NO RETORNO
    
    return json.dumps(contato.to_json())


@app.delete("/contatos/<id_>")
def remover_contato_action(id_):

    try:
        usuario = verificar_login()
    except:
        return {"erro": "Usuário não logado"}, UNAUTHORIZED

    id_usuario = usuario.id

    contato = Contato.query.filter_by(id=id_).first()

    if not contato:
        return {"erro": "Usuário não existe"}, NOT_FOUND

    if contato.id_usuario != id_usuario:
        return {"erro": "Contato não pertence ao usuário"}, UNAUTHORIZED


    db.session.delete(contato)
    db.session.commit()

    return json.dumps(contato.to_json())


@app.put("/contatos/<id_>")
def put_contato(id_):

     # Pegar usuario logado, se existir:
    usuario = None
    if "user" in session.keys():
        usuario = session["user"]

    if not usuario:
        return {"erro": "Usuário não logado"}, UNAUTHORIZED

    id_usuario = usuario.id

    contato = Contato.query.filter_by(id=id_).first()

    if not contato:
        return {"erro": "Usuario nao existe"}, UNPROCESSABLE_ENTITY

    if contato.id_usuario != id_usuario:
        return {"erro": "Contato não pertence ao usuário"}, UNAUTHORIZED

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

    return json.dumps(contato.to_json())

    

@app.patch("/contatos/<id_>")
def patch_contato(id_):

    try:
        usuario = verificar_login()
    except:
        return {"erro": "Usuário não logado"}, UNAUTHORIZED

    id_usuario = usuario.id

    contato = Contato.query.filter_by(id=id_).first()

    if not contato:
        return {"erro": "Usuario nao existe"}, UNPROCESSABLE_ENTITY

    if contato.id_usuario != id_usuario:
        return {"erro": "Contato não pertence ao usuário"}, UNAUTHORIZED

    for nome_campo, valor in request.json.items():
        # ex: "nome"  -> "Marcos Tacalepau Nesse Carrinho"
        try:
            setattr(contato, nome_campo, valor)
        except:
            continue  ## ALTERNATIVA: DAR ERRO
        
    db.session.merge(contato)  # adiciona ou atualiza
    db.session.commit()

    return json.dumps(contato.to_json())


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

    dict_usuario = usuario.to_json()
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

    dict_usuario = usuario.to_json()
    del dict_usuario["password_hash"]

    return json.dumps(dict_usuario)


@app.delete("/sessions/<id_>")
def logout_action(id_):

    usuario = session.get("user")
    session.pop("user")

    dict_usuario = usuario.to_json()
    del dict_usuario["password_hash"]

    return json.dumps(dict_usuario)