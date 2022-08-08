from datetime import date, datetime
from flask_sqlalchemy import Pagination



def format_field(data):
    if isinstance(data, date) or isinstance(data, datetime):
        return data.strftime("%d/%m/%Y")
    else:
        return data


def pagination_to_json(pagination:Pagination, host_path:str):
    """
    Gera JSON de metadados de paginação a partir de um objeto da classe flask_sqlalchemy.Pagination
    :param obj_pagination: flask_sqlalchemy.Pagination
    :param host_path: String - URL do host
    :return: dict - Exemplo:
        {
            "page": 2,
            "per_page": 25,
            "total": 100,
            "pages": 4,
            "_links": [
                {
                    "rel": "prev",
                    "href": "<host>/api/customers?page=1&results_per_page=25"
                },
                {
                    "rel": "current",
                    "href": "<host>/api/customers?page=2&results_per_page=25"
                },
                {
                    "rel": "next",
                    "href": "<host>/api/customers?page=3&results_per_page=25"
                }
            ]
        }
    Ver mais exemplos nos testes unitários.
    """

    # estrutura basica da pagination que aparecerá no json
    meta = {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
    }

    links = []
    meta["_links"] = links

    if pagination.has_prev:
        add_page_link(links, host_path, "prev", pagination.prev_num, pagination.per_page)

    add_page_link(links, host_path, "current", pagination.page, pagination.per_page)

    if pagination.has_next:
        add_page_link(links, host_path, "next", pagination.next_num, pagination.per_page)

    return meta


def add_page_link(links, path, label, page, per_page):
    """
    Adiciona link de página a uma lista de links
    Exemplos:
    >>> add_page_link([], "https://localhost/api/customers", "prev", 1, 25)
    [{'rel': 'prev', 'href': 'https://localhost/api/customers?page=1&results_per_page=25'}]
    """
    href = generate_page_link(path, page)
    href = add_resultados_pagina_if_exists(href, per_page)
    links.append({"rel": label, "href": href})
    return links


def generate_page_link(path, page):
    """
    Gera link para uma página.
    Exemplos:
    >>> generate_page_link("https://localhost/api/customers", 1)
    'https://localhost/api/customers?page=1'
    """
    href = path
    href = href + "?page={}".format(page)
    return href


def add_resultados_pagina_if_exists(href, per_page):
    """
    Adiciona results_per_page se existe
    Exemplos:
    >>> add_resultados_pagina_if_exists("https://localhost/api/customers?page=1", 25)
    'https://localhost/api/customers?page=1&per_page=25'
    >>> add_resultados_pagina_if_exists("https://localhost/api/customers?page=1", None)
    'https://localhost/api/customers?page=1'
    """
    if per_page is not None:
        href = href + "&per_page={}".format(per_page)
    return str(href)
