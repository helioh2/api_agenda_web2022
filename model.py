

from datetime import date, datetime
from enum import Enum
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from pydantic import BaseModel, constr

db = SQLAlchemy()


class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password) -> bool:
        return check_password_hash(self.password_hash, password)

    def as_dict(self):
       return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}


class Contato(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    telefone = db.Column(db.String(20), unique=False, nullable=False)
    data_nascimento = db.Column(db.Date, unique=False, nullable=False)
    detalhes = db.Column(db.String, unique=False, nullable=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey(Usuario.id), nullable=False)

    def __repr__(self):
        return '<Contato %r>' % self.nome

    def to_json(self):
       return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}


class ContatoSchema(BaseModel):
    id: int
    nome: constr(min_length=2, max_length=80)
    telefone: constr(min_length=8, max_length=12)
    data_nascimento: date
    detalhes: str
    id_usuario: int

    class Config:
        orm_mode = True


class RelLinkEnum(str, Enum):
    prev = "prev"
    next = "next"
    current = "current"


class PageLinkSchema(BaseModel):
    rel: RelLinkEnum
    href: str


class ContatosPaginatedSchema(BaseModel):
    items: list[ContatoSchema]
    page: int
    per_page: int
    total: int
    _links: list[PageLinkSchema]
