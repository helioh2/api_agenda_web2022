

def validar_json(json) -> dict:
    
    erros = {}  

    if json["nome"] == "":
        erros["nome"] = "Nome não pode vir vazio."
    
    if len(json["nome"]) <= 2:
        erros["nome"] = "Nome deve ter no mínimo 2 caracteres"
    
    if len(json["telefone"]) < 8 or len(json["telefone"]) > 12:
        erros["telefone"] = "Telefone deve ter entre 8 e 12 caracteres."

    return erros

