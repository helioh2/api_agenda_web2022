

def validar_form(form) -> dict:
    
    erros = {}  

    if form["nome"] == "":
        erros["nome"] = "Nome não pode vir vazio."
    
    if len(form["nome"]) <= 2:
        erros["nome"] = "Nome deve ter no mínimo 2 caracteres"
    
    if len(form["telefone"]) < 8 or len(form["telefone"]) > 12:
        erros["telefone"] = "Telefone deve ter entre 8 e 12 caracteres."

    return erros

