from datetime import datetime, timedelta, timezone
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

from flask_pydantic_spec import FlaskPydanticSpec, Response

from flask_jwt_extended import create_access_token,get_jwt,get_jwt_identity, \
                               unset_jwt_cookies, jwt_required, JWTManager


app = Flask(__name__)

spec = FlaskPydanticSpec("flask", title="Contatos API")
spec.register(app)

app.config["JWT_SECRET_KEY"] = "please-remember-to-change-me!!!"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
jwt = JWTManager(app)

setup_database(app)

db.init_app(app)
migrate = Migrate(app, db)

PER_PAGE = 10

CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})  # TODO: Adicionar restrições de domínio

logging.getLogger('flask_cors').level = logging.DEBUG


@app.after_request
def refresh_expiring_jwts(response):
    """
    Atualiza o token de autenticação se estiver faltando menos de 30 minutos
    para expirar
    """
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            data = response.get_json()
            if type(data) is dict:
                data["access_token"] = access_token 
                response.data = json.dumps(data)
        return response
    except (RuntimeError, KeyError):
        # Caso em que não há um JWT válido. Basta retornar a resposta original
        return response


@spec.validate(resp=Response(HTTP_200=ContatosPaginatedSchema))
@app.get("/contatos")
@jwt_required()
def contatos_json():

    id_usuario = get_jwt_identity()

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


@app.get("/contatos/<id_>")
@jwt_required()
def contato(id_):

    id_usuario = get_jwt_identity()

    contato = (
        Contato.query                                # objeto Query
                .filter_by(id_usuario=id_usuario)    # objeto Query
                .filter_by(id=id_)                   # objeto Query   
                .first()  # Contato
    )

    if not contato:
        return {"erro": "Usuario não existe"}, NOT_FOUND

    return json.dumps(contato.to_json())


@app.post("/contatos")
@jwt_required()
def adicionar_contato_action():

    id_usuario = get_jwt_identity()

    resultado_validacao = validar_json(request.json)

    if resultado_validacao:  # se ele não for {}
        return resultado_validacao, UNPROCESSABLE_ENTITY

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
@jwt_required()
def remover_contato_action(id_):

    id_usuario = get_jwt_identity()

    contato = Contato.query.filter_by(id=id_).filter_by(id_usuario=id_usuario).first()

    if not contato:
        return {"erro": "Usuário não existe"}, NOT_FOUND

    if contato.id_usuario != id_usuario:
        return {"erro": "Contato não pertence ao usuário"}, UNAUTHORIZED


    db.session.delete(contato)
    db.session.commit()

    return json.dumps(contato.to_json())


@app.put("/contatos/<id_>")
@jwt_required()
def put_contato(id_):

    id_usuario = get_jwt_identity()

    contato = Contato.query.filter_by(id=id_).filter_by(id_usuario=id_usuario).first()

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
@jwt_required()
def patch_contato(id_):

    id_usuario = get_jwt_identity()

    contato = Contato.query.filter_by(id=id_).filter_by(id_usuario=id_usuario).first()

    if not contato:
        return {"erro": "Contato nao existe"}, UNPROCESSABLE_ENTITY

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


@app.post("/token")
def login_action():

    username = request.json.get("username", None)
    senha = request.json.get("senha", None)

    if not username or not senha:
        return {"erro": "Username e/ou senha não fornecidos"}, 401

    ## AUTENTICAÇÃO
    usuario: Usuario = Usuario.query.filter_by(username=username).first()

    if not usuario:
        return {"erro": "Usuario não existe"}, BAD_REQUEST

    if not usuario.check_password(senha):
        return {"erro": "Senha incorreta"}, BAD_REQUEST  ## TODO: pesquisar qual seria o codigo mais correto

    # else
    
    access_token = create_access_token(identity=usuario.id)
    response = {"access_token":access_token}
    return response


@app.get('/usuario')
@jwt_required()
def my_profile():
    
    id_usuario = get_jwt_identity()

    usuario: Usuario = Usuario.query.filter_by(id=id_usuario).first()
    
    dict_usuario = usuario.as_dict()
    del dict_usuario["password_hash"]

    return json.dumps(dict_usuario)


@app.delete("/token")
def logout_action():

    response = json.dumps({"msg": "logout successful"})
    unset_jwt_cookies(response)
    return response