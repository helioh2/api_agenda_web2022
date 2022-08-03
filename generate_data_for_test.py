from datetime import timedelta
from random import randrange
from datetime import datetime

import lorem
from app import app
from model import db, Contato
import names

app.app_context().push()

N = 100


def choose_random_date_between(start_date, end_date):
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    if days_between_dates <= 0:
        return start_date
    random_number_of_days = randrange(days_between_dates)
    random_date = start_date + timedelta(days=random_number_of_days)
    return random_date


for i in range(N):
    nome = names.get_full_name()
    telefone = "".join([str(randrange(0, 10)) for _ in range(8)])
    data_nascimento = choose_random_date_between(
        datetime.strptime("01/01/1980", "%d/%m/%Y"),
        datetime.strptime("31/12/2012", "%d/%m/%Y"),
    )
    detalhes = lorem.paragraph()

    contato = Contato(
        nome=nome,
        telefone=telefone,
        data_nascimento=data_nascimento,
        detalhes=detalhes,
        id_usuario=2,
    )

    db.session.add(contato)

db.session.commit()
