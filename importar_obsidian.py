# -*- coding: utf-8 -*-
"""Importa as fichas de inimigos do Obsidian (.md) para a biblioteca do painel do mestre (mestre/inimigos.json).
Uso: python3 importar_obsidian.py "<pasta Fichas Inimigos>" "<pasta mestre/ do app>"
Pode rodar de novo: inimigos com o mesmo nome são atualizados, não duplicados."""
import hashlib, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bestiario as B
from mestre_dados import Mestre

TIPOS = {"relampago": "Relâmpago", "extase": "Êxtase"}


def lista(txt):
    txt = re.sub(r"\([^)]*\)", "", txt)
    return [x.strip(" .") for x in re.split(r"[,;]", txt) if x.strip(" .") and x.strip().lower() not in ("nenhuma", "nenhum")]


def parse(path, nome_arq):
    linhas = open(path, encoding="utf-8").read().replace("\r", "").split("\n")
    nome, intro = nome_arq, []
    if linhas and " — " in linhas[0] and not linhas[0].startswith(("Pontos", "•")):
        nome = linhas[0].replace("—", "-", 0).strip()
        n, _, sub = nome.partition(" — ")
        nome = n.strip().title() if n.isupper() else n.strip()
        intro.append(sub.strip())
        for l in linhas[1:]:
            if l.startswith("Pontos de Vida"):
                break
            if l.strip():
                intro.append(l.strip())
    txt = "\n".join(linhas)
    g = lambda rx, d="": (re.search(rx, txt) or [None, d])[1]
    d = {"nome": nome, "tier": "Animal", "nmp": 6, "jogadores": 4}
    d["vida"] = int(g(r"Pontos de Vida:\s*(\d+)", 1))
    d["postura"] = int(g(r"Postura\s*(\d+)", 0))
    d["ca"] = int(g(r"Classe de Armadura:\s*(\d+)", 0))
    d["ataque"] = int(g(r"Acerto:\s*\+?(-?\d+)", 8))
    d["dt"] = int(g(r"CD\s*(\d+)", 17))
    d["ini_dados"] = 1 + int(g(r"Iniciativa:\s*(\d+)", 0))
    d["atencao"] = g(r"Aten[çc][ãa]o:\s*([^\n]*)").strip()
    d["resistencias"] = lista(g(r"Resist[êe]ncias:\s*([^\n]*)"))
    d["imunidades"] = lista(g(r"Imunidades:\s*([^\n]*)"))
    d["vulnerabilidades"] = [x.strip() for x in re.findall(r"Sofre \+\d+ de dano (?:de )?([A-Za-zÀ-ú]+)", g(r"(Unico:[^\n]*)"))]
    # condições
    vc = g(r"(Vida de condi[çc][ãa]o:[^\n]*)")
    d["vida_condicao"] = int(g(r"Vida de condi[çc][ãa]o:\s*(\d+)", 0))
    aff = {}
    for rotulo, chave in (("Imune", "imune"), ("Resistente", "resistente"), ("Vulnerável", "vulneravel")):
        m = re.search(rotulo + r"[^:.]*?(?:\(\d+\))?:\s*([^.]*)\.", vc)
        if m:
            for c in B.CONDICOES:
                if c.lower() in m.group(1).lower():
                    aff[c] = chave
    d["afinidades"] = aff
    d["cond_por_golpe"] = int(g(r"Pontos de condi[çc][ãa]o por golpe[^:]*:\s*(\d+)", 0))
    # ações
    gol, hab = [], []
    m = re.search(r"Ações \(Possui[^\n]*\n(.*?)(?:\n-{5,}|\Z)", txt, re.S)
    for b in re.findall(r"^•\s*(.+)$", m.group(1) if m else "", re.M):
        nm, _, resto = b.partition(":")
        if not resto:
            hab.append({"nome": "", "acao": "", "texto": b.strip()}); continue
        ac = re.search(r"\[([^\]]+)\]", nm)
        acao = ac.group(1) if ac else ""
        nm = re.sub(r"\[[^\]]*\]|\(Passiva\)", "", nm).strip()
        if "(Passiva)" in b.split(":")[0]:
            acao = "Passiva"
        dm = re.search(r"Dano\s+([\dd+\-× x]+?)\s+([A-Za-zÀ-ú]+)?(?:[ .,]|$)", resto)
        if dm and re.search(r"\d+d\d+|\d", dm.group(1)) and not re.search(r"teste de", resto[:dm.start()], re.I):
            tp = (dm.group(2) or "")
            gol.append({"nome": nm, "tipo": TIPOS.get(tp.lower(), tp), "dano": dm.group(1).strip(), "bonus": d["ataque"],
                        "efeito": resto.strip()[:500], "alcance": ""})
        else:
            hab.append({"nome": nm, "acao": acao, "texto": resto.strip()})
    d["golpes"], d["habilidades"] = gol, hab
    # pontos chave
    pc = []
    m = re.search(r"Pontos Chave\n(.*?)(?:\n-{5,}|\Z)", txt, re.S)
    for b in re.findall(r"^•\s*(.+)$", m.group(1) if m else "", re.M):
        n, _, e = b.partition(":")
        pc.append({"nome": n.strip(), "efeito": e.strip()})
    d["pontos_chave"] = pc
    m = re.search(r"Set e Drops\n(.*?)(?:\n-{5,}|\Z)", txt, re.S)
    d["set_drops"] = m.group(1).strip() if m else ""
    # texto livre (estados, passivas) entre Vida de condição e QTD de turnos
    m = re.search(r"Vida de condi[çc][ãa]o:.*?\n\n(.*?)\nQTD de turnos", txt, re.S)
    extra = m.group(1).strip() if m else ""
    m2 = re.search(r"Imunidades:[^\n]*\n\n(.*?)\nQTD de turnos", txt, re.S)
    if not extra and m2:
        extra = m2.group(1).strip()
    d["notas"] = extra
    d["descricao"] = "\n".join(intro)
    d["id"] = hashlib.md5(nome.lower().encode()).hexdigest()[:8]
    return d


def main(origem, destino):
    mestre = Mestre(destino)
    for raiz, _, arqs in os.walk(origem):
        for a in sorted(arqs):
            if not a.endswith(".md") or a == "Ficha Base.md":
                continue
            nome = re.sub(r"^Ficha[_ ]", "", a[:-3]).replace("_", " ")
            d = parse(os.path.join(raiz, a), nome)
            d["loot"] = os.path.basename(raiz)   # guarda o andar de origem
            r = mestre.salvar_inimigo(d)
            print("OK ", r["nome"], "| vida", r["vida"], "| golpes", len(r["golpes"]), "| habilidades", len(r["habilidades"]), "| pontos-chave", len(r["pontos_chave"]), "| afin.", r["afinidades"])


if __name__ == "__main__":
    main(*sys.argv[1:3])
