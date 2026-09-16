import re

with open('servidor.py', 'r', encoding='utf-8') as f:
    conteudo = f.read()

import_novo = '''    autenticar_operador, listar_operadores, ha_operadores,
    get_diretores, salvar_diretor, editar_diretor, excluir_diretor
)'''
conteudo = conteudo.replace('autenticar_operador, listar_operadores, ha_operadores\n)', import_novo)


rotas_get = '''
        if path == "/api/parametros":
            params = get_parametros()
            # Injeta diretores no GET parametros para economizar requisicoes!
            params["diretores"] = get_diretores()
            self.responder_json(200, params)
            return'''

conteudo = conteudo.replace('''        if path == "/api/parametros":
            params = get_parametros()
            self.responder_json(200, params)
            return''', rotas_get)

rotas_post = '''
        # API DIRETORES
        if path == "/api/diretores":
            try:
                acao = dados.get("acao")
                if acao == "CRIAR":
                    salvar_diretor(dados["cargo"], dados["nome"], dados["portaria"])
                elif acao == "EDITAR":
                    editar_diretor(dados["id"], dados["cargo"], dados["nome"], dados["portaria"])
                elif acao == "EXCLUIR":
                    excluir_diretor(dados["id"])
                self.responder_json(200, {"sucesso": True})
            except Exception as e:
                self.responder_json(400, {"sucesso": False, "erro": str(e)})
            return
            
        if path == "/api/parametro":'''

conteudo = conteudo.replace('        if path == "/api/parametro":', rotas_post)

with open('servidor.py', 'w', encoding='utf-8') as f:
    f.write(conteudo)