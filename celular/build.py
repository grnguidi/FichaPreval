"""Gera o app de celular em ../docs (publicado pelo GitHub Pages).

Uso:  py celular/build.py
Junta estilo, dados do livro (de dados_prevalecentes.py), regras.js e src/js/*.js (o app) num index.html só,
e copia manifest, service worker e ícones. Também gera ../pagina_celular.py: a mesma ficha, que o
PC do mestre serve aos celulares da mesa durante a sessão (sessao.py). Os efeitos de talento vêm de regras.py, para que
PC e celular usem a mesma tabela.
"""
import base64
import json
import os
import re
import shutil
import sys
import zlib

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
SAIDA = os.path.join(RAIZ, "docs")
sys.path.insert(0, RAIZ)
import regras  # noqa: E402
from dados_prevalecentes import DADOS  # noqa: E402


def ler(*p):
    with open(os.path.join(AQUI, *p), encoding="utf-8") as f:
        return f.read()


def app_js():
    """Junta celular/src/js/*.js (em ordem numérica) no app.js: tudo no mesmo escopo, como antes da divisão."""
    pasta = os.path.join(AQUI, "src", "js")
    return "".join(ler("src", "js", n) for n in sorted(os.listdir(pasta)) if n.endswith(".js"))


def regras_js():
    """regras.js com as tabelas que vêm de regras.py (efeitos de talento e listas do livro), para PC e celular ficarem iguais."""
    efeitos = json.dumps(regras.EFEITOS_TALENTOS, ensure_ascii=False)
    livro = json.dumps({k: (sorted(v) if isinstance(v, (set, frozenset)) else v) for k, v in {
        "TIPOS_DANO": regras.TIPOS_DANO, "DANO_SEM_RD": regras.DANO_SEM_RD, "EFEITOS_LIVRO": regras.EFEITOS_LIVRO,
        "NOTA_EFEITOS": regras.NOTA_EFEITOS, "CONDICAO_TESTE": regras.CONDICAO_TESTE, "CONDICAO_ATIVA": regras.CONDICAO_ATIVA,
        "CONDICAO_DESCANSO_CURTO": regras.CONDICAO_DESCANSO_CURTO, "DESCANSOS_CURTOS_MAX": regras.DESCANSOS_CURTOS_MAX,
        "DESGASTE_TURNOS": regras.DESGASTE_TURNOS, "PECAS_SET_PESO": regras.PECAS_SET_PESO, "DADO_INFERIOR": regras.DADO_INFERIOR,
        "ESCOLHA_TALENTO": regras.ESCOLHA_TALENTO, "ROTULO_ESCOLHA": regras.ROTULO_ESCOLHA, "MATRICULA_MANA2": regras.MATRICULA_MANA2,
        "PROPRIEDADES": regras.PROPRIEDADES, "ELEMENTOS_PROP": regras.ELEMENTOS_PROP,
        "TIPOS_ACAO": regras.TIPOS_ACAO, "ACOES_LIVRO": regras.ACOES_LIVRO, "NIVEL_RECARGA": regras.NIVEL_RECARGA,
        "EVENTO_RECARGA": regras.EVENTO_RECARGA, "RECURSOS_ARMA": regras.RECURSOS_ARMA, "ALMA_TABELAS": regras.ALMA_TABELAS,
        "ALMA_CATEGORIAS": regras.ALMA_CATEGORIAS, "ALMA_EXECUCAO": regras.ALMA_EXECUCAO, "ALMA_AJUSTES": regras.ALMA_AJUSTES,
        "CAMINHOS": regras.CAMINHOS, "ETAPAS_META": regras.ETAPAS_META, "METAS_MAX": regras.METAS_MAX,
        "CONTOS_POR": regras.CONTOS_POR, "MOEDAS": regras.MOEDAS,
    }.items()}, ensure_ascii=False)
    js = re.sub(r"const EFEITOS_TALENTOS = \{.*?\};", lambda m: f"const EFEITOS_TALENTOS = {efeitos};", ler("regras.js"), count=1, flags=re.S)
    return js.replace("const LIVRO = {};", f"const LIVRO = {livro};", 1)


def main():
    dados = json.loads(json.dumps(DADOS))
    for e in dados["encantamentos"]:          # campos que o app de mesa não usa
        for v in e["versoes"]:
            for k in ("base", "mana_num", "req_cajado", "req_selo"):
                v.pop(k, None)
    dj = json.dumps(dados, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    js_regras = regras_js()
    pwa = ('<link rel="manifest" href="manifest.webmanifest">\n<link rel="icon" href="icone-192.png">\n'
           '<link rel="apple-touch-icon" href="icone-192.png">')
    base = (ler("src", "index.tpl.html").replace("/*CSS*/", ler("src", "estilo.css"))
            .replace("/*DADOS*/", dj).replace("/*REGRAS*/", js_regras).replace("/*APP*/", app_js()))
    html = base.replace("<!--PWA-->", pwa)
    os.makedirs(SAIDA, exist_ok=True)
    with open(os.path.join(SAIDA, "index.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    for nome in ("manifest.webmanifest", "sw.js", "icone-192.png", "icone-512.png"):
        shutil.copy(os.path.join(AQUI, "src", nome), os.path.join(SAIDA, nome))
    open(os.path.join(SAIDA, ".nojekyll"), "w").close()
    # versão servida pelo mestre na rede local (sem manifest/service worker: é http e só vale durante a sessão)
    mesa = base.replace("<!--PWA-->", "")
    b64 = base64.b64encode(zlib.compress(mesa.encode("utf-8"), 9)).decode("ascii")
    linhas = "\n".join(f'    "{b64[i:i + 100]}"' for i in range(0, len(b64), 100))
    with open(os.path.join(RAIZ, "pagina_celular.py"), "w", encoding="utf-8", newline="\n") as f:
        f.write('"""Ficha do celular servida pelo PC do mestre na sessão local.\n\n'
                'ARQUIVO GERADO por celular/build.py — não edite à mão; mude celular/src e rode o build."""\n'
                "import base64\nimport zlib\n\n_B = (\n" + linhas + "\n)\n\n"
                'HTML = zlib.decompress(base64.b64decode(_B)).decode("utf-8")\n')
    print(f"docs/index.html gerado ({len(html) // 1024} KB) · pagina_celular.py ({len(b64) // 1024} KB)")


if __name__ == "__main__":
    main()
