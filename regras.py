# -*- coding: utf-8 -*-
"""Regras de Prevalecentes (PREVA 3.1) — cálculos puros, sem interface."""
import math
import re

ATRIBUTOS = ["VIT", "MEN", "TEN", "FOR", "DES", "INT", "FE", "ARC"]
NOMES_ATR = {"VIT": "Vitalidade", "MEN": "Mente", "TEN": "Tenacidade", "FOR": "Força",
             "DES": "Destreza", "INT": "Inteligência", "FE": "Fé", "ARC": "Arcano"}
ATR_POR_NOME = {v: k for k, v in NOMES_ATR.items()}
VALORES_INICIAIS = [16, 14, 12, 11, 10, 9, 8, 7]
NIVEL_MAX = 30

# Perícias fora de combate: nome -> atributos possíveis (usa o maior), requer treino
PERICIAS = [
    ("Acrobacia", ["DES"], False), ("Adestramento", ["MEN"], True),
    ("Agricultura", ["INT", "DES"], True), ("Artes", ["MEN"], False),
    ("Atletismo", ["FOR"], False), ("Ciências", ["INT"], False),
    ("Costura", ["INT", "DES"], True), ("Crime", ["DES"], False),
    ("Furtividade", ["DES"], False), ("Gastronomia", ["INT", "DES"], False),
    ("História", ["FE"], False), ("Intuição", ["FE"], False),
    ("Investigação", ["INT"], False), ("Medicina", ["INT"], True),
    ("Navegação", ["INT", "DES"], False), ("Percepção", ["ARC"], False),
    ("Performance", ["MEN"], False), ("Persuasão", ["MEN"], False),
    ("Prevalência", None, True), ("Religião", ["FE"], False),
    ("Sorte", ["ARC"], False), ("Tática", ["ARC"], False),
    ("Tecnologia", ["INT"], True),
]
PERICIAS_ATAQUE = [("Luta", ["FOR", "DES"]), ("Pontaria", ["DES"]),
                   ("Feitiçaria", ["INT"]), ("Desejo", ["FE"])]
PERICIAS_DEFESA = [("Fortitude", "TEN", "Fortitude de Ferro"), ("Reflexo", "DES", "Reflexos de Gato"),
                   ("Astúcia", "MEN", "Mente Blindada"), ("Vontade", "FE", "Vontade Inabalável")]
RESISTENCIAS = [(20, "Fogo"), (30, "Cortante"), (40, "Impacto"), (50, "Veneno"),
                (60, "Sangramento"), (70, "Magia"), (80, "Magia Pura"), (90, "Sagrado")]
CONDICOES = ["Veneno", "Podridão", "Sangramento", "Congelamento", "Sono", "Loucura", "Morte"]
LIMIARES_ACOES = [15, 30, 45, 55, 65, 75, 85, 95]
ACERTO_ARMA = {1: 0, 2: 0, 3: 1, 4: 1, 5: 2, 6: 2, 7: 3, 8: 3, 9: 4, 10: 5}
REQ_ENCANT_NIVEL = {1: 10, 2: 15, 3: 25, 4: 30, 5: 40, 6: 45, 7: 55, 8: 65, 9: 75, 10: 85}


def cap(v):
    return max(0, min(99, int(v)))


def curva(p):
    """Curva do atributo (tabela da ficha: 5→1 … 95→58, 99→60)."""
    p = cap(p)
    total = 0
    for marco in range(5, 100, 5):
        if p < marco:
            break
        total += 1 if marco <= 20 else 2 if marco <= 35 else 3 if marco <= 55 else 4 if marco <= 75 else 5
    if p >= 99:
        total += 2
    return total


def bonus_combate(p):
    p = cap(p)
    return 5 if p >= 99 else p // 20


def vantagem(p):
    return cap(p) >= 60


BONUS_SEM_ALMA = 2  # "Jogando sem uma Alma": +2 pontos de atributo por nível


def pontos_de_nivel(nivel, sem_alma=False):
    """Pontos recebidos por subir de nível (sem a distribuição inicial)."""
    nivel = max(1, min(NIVEL_MAX, nivel))
    return (10 + (BONUS_SEM_ALMA if sem_alma else 0)) * (nivel - 1) + 5 * (nivel // 3)


def ganho_no_nivel(nivel, sem_alma=False):
    return 10 + (5 if nivel % 3 == 0 else 0) + (BONUS_SEM_ALMA if sem_alma else 0)


def nivel_alma(nivel):
    return nivel // 3


def max_nivel_arma(nivel):
    return min(10, math.ceil(nivel / 2))


def slots_talismas(nivel, talentos):
    n = min(5, 1 + nivel // 6)
    if "Colecionador de Talismãs" in talentos:
        n += 1
    if "Relicário" in talentos:
        n += 1
    return n


def derivadas(a, nivel, talentos, vida_dados_soma, armadura_ca=0, escudo_ca=0, ca_extra=0):
    """a: dict de atributos efetivos. talentos: set de nomes escolhidos."""
    c = {k: curva(a[k]) for k in ATRIBUTOS}
    bc = {k: bonus_combate(a[k]) for k in ATRIBUTOS}
    d = {}
    d["curva"], d["bc"] = c, bc
    d["vida_dados"] = c["VIT"] + (3 if "Vida Dura" in talentos else 0)
    d["vida"] = 10 + 5 * (nivel - 1) + vida_dados_soma
    mana = 2 * cap(a["MEN"]) + 2 * c["MEN"]
    if "Mente Infinita" in talentos:
        mana = int(mana * 1.5)
    d["mana"] = mana
    d["vigor"] = 20 + cap(a["FOR"]) + c["FOR"] + (10 if "Fôlego de Guerreiro" in talentos else 0)
    d["vigor_regen"] = c["FOR"] // 4
    d["descoberta"] = 10 + 10 * (cap(a["ARC"]) // 15)
    ca_ten = min(4, cap(a["TEN"]) // 20)
    d["ca_ten"] = ca_ten
    d["ca"] = max(10, min(25, 10 + ca_ten + armadura_ca + escudo_ca + ca_extra))
    carga = 10 + 2 * cap(a["TEN"]) + cap(a["FOR"]) // 2 + c["TEN"]
    carga += (10 if "Mochileiro" in talentos else 0) + (30 if "Mula de Carga" in talentos else 0)
    d["carga"] = carga
    des = cap(a["DES"])
    mov = 9 + (3 * (1 + (des - 30) // 15) if des >= 30 else 0) + (3 if "Pé Ligeiro" in talentos else 0)
    d["movimento"] = mov
    acoes = sum(1 for t in LIMIARES_ACOES if des >= t)
    if "Mão Extra" in talentos and des >= 40:
        acoes += 1
    d["acoes_extras"] = acoes
    d["iniciativa_dados"] = 1 + des // 20
    d["iniciativa_bonus"] = bc["DES"]
    d["rd"] = min(4, cap(a["TEN"]) // 20)
    ten_res = cap(a["TEN"]) + (10 if "Pele Grossa" in talentos else 0)
    d["resistencias"] = [nome for lim, nome in RESISTENCIAS if ten_res >= lim]
    d["n3"] = nivel // 3
    d["dt_feiticaria"] = 10 + bc["INT"] + nivel // 3
    d["dt_desejo"] = 10 + bc["FE"] + nivel // 3
    esp = 1 + (cap(a["INT"]) + cap(a["FE"])) // 6
    esp += (1 if "Cabeça Cheia" in talentos else 0) + (1 if "Mente Expandida" in talentos else 0)
    d["espacos_encant"] = esp
    d["contra_encant"] = max(cap(a["INT"]), cap(a["FE"])) // 10
    d["dados_extra_magia"] = cap(a["INT"]) // 30
    d["dados_extra_feitico"] = cap(a["FE"]) // 30
    d["pericias_treinadas_max"] = 5 + max(cap(a["INT"]), cap(a["MEN"])) // 10 + (1 if "Treinado" in talentos else 0)
    d["alma_nivel"] = nivel_alma(nivel)
    d["alma_usos"] = 2 + d["alma_nivel"] // 3
    d["alma_ativas"] = 1 + sum(1 for x in (10, 20, 30) if nivel >= x)
    d["talismas"] = slots_talismas(nivel, talentos)
    d["max_nivel_arma"] = max_nivel_arma(nivel)
    return d


def pericia_fora(a, nivel, atrs, treinada):
    melhor = max(atrs, key=lambda k: cap(a[k]))
    val = cap(a[melhor])
    bonus = nivel // 2 + (curva(val) if treinada else 0)
    return melhor, bonus, 1 + val // 20


# ---------------- Armas ----------------
def req_arma(arma, nv):
    return {r["attr"]: r["base"] + r["por_nivel"] * (nv - 1) for r in arma["req"]}


def req_falta(reqs, a):
    return [f"{NOMES_ATR[k][:3].upper()} {v} (tem {cap(a[k])})" for k, v in reqs.items() if a[k] < v]


def req_uso_duplo(r1, r2):
    out = {}
    for k in set(r1) | set(r2):
        x, y = r1.get(k, 0), r2.get(k, 0)
        out[k] = max(x, y) + min(x, y) // 2
    return out


def dano_com_dados(dano, extra):
    if extra <= 0:
        return dano
    dados = re.findall(r"(\d+)d(\d+)", dano)
    if not dados:
        return dano
    maior = max(int(f) for _, f in dados)
    for i, (q, f) in enumerate(dados):
        if int(f) == maior:
            return re.sub(rf"\b{q}d{f}\b", f"{int(q) + extra}d{f}", dano, count=1)
    return dano


# ---------------- Encantamentos ----------------
def status_versao(v, dominio, a, nivel, tem_impl_inicial=False):
    """Retorna lista de motivos que impedem aprender (vazia = pode)."""
    motivos = []
    for r in v["req_attrs"]:
        if a[r["attr"]] < r["valor"]:
            motivos.append(f"{r['valor']} {NOMES_ATR[r['attr']]} (tem {cap(a[r['attr']])})")
    nmin = 2 * v["nivel"]
    if nivel < nmin and not (v["nivel"] == 1 and tem_impl_inicial):
        motivos.append(f"nível {nmin}")
    return motivos


# ---------------- Talentos ----------------
def status_talento(t, nivel_slot, escolhidos_antes, a, pericias_treinadas, armas_equipadas, ja_escolhidos):
    motivos = []
    if t["nivel"] > nivel_slot:
        motivos.append(f"nível {t['nivel']}")
    req = t["requisito"]
    if req:
        m = re.match(r"99 de (\w+)", req)
        if m:
            k = ATR_POR_NOME.get(m.group(1))
            if k and a[k] < 99:
                motivos.append(req)
        elif req.startswith("Treinado em "):
            p = req[len("Treinado em "):]
            if p not in pericias_treinadas:
                motivos.append(req)
        elif req in GRUPOS_ARMA:
            if not (GRUPOS_ARMA[req] & set(armas_equipadas)):
                motivos.append(f"arma equipada: {req}")
        elif req not in escolhidos_antes:
            motivos.append(f"talento: {req}")
    if t["nome"] in ja_escolhidos and "repetir" not in t["descricao"]:
        motivos.append("já escolhido")
    if t["nome"] == "Mão Extra" and a["DES"] < 40:
        motivos.append("40 Destreza")
    return motivos


GRUPOS_ARMA = {
    "Adagas": {"Adaga"}, "Espadas": {"Espada"}, "Espada Grande": {"Espada Grande"},
    "Katana": {"Katana"}, "Machado Grande": {"Machado Grande"}, "Bastão": {"Bastão"},
    "Lança-Arma": {"Lança-Arma"}, "Lâmina-Dínamo": {"Lâmina-Dínamo"}, "Arco": {"Arco"},
    "Besta Pesada": {"Besta Pesada"}, "Lira": {"Lira"}, "Cajados e Selos": {"Cajado", "Selo"},
}


# ---------------- Efeitos de talentos ----------------
# "perm": vale sempre. "sit": só quando o jogador liga o interruptor "ativo agora".
# Vida Dura, Fôlego de Guerreiro, Mochileiro, Mula de Carga, Pé Ligeiro, Pele Grossa, Cabeça Cheia, Mente Expandida,
# Treinado, Mão Extra, Mente Infinita, Colecionador de Talismãs, Relicário e os +2 de defesa já entram em derivadas().
EFEITOS_TALENTOS = {
    "Passos Leves": {"tipo": "perm", "ca": 1, "nota": "sem Armadura Pesada ou Colossal"},
    "Contra-encantador": {"tipo": "perm", "contra": 1},
    "Mão Verde": {"tipo": "perm", "pericia": {"Agricultura": 2}},
    "Voz dos Animais": {"tipo": "perm", "pericia": {"Adestramento": 2}},
    "Engenheiro": {"tipo": "perm", "pericia": {"Tecnologia": 2}},
    "Sombra Perfeita": {"tipo": "perm", "pericia": {"Crime": 2}},
    "Olhar Aguçado": {"tipo": "perm", "descoberta": 2},
    "Identidade Forte": {"tipo": "perm", "dt_alma": 2},
    "Estudioso": {"tipo": "perm", "aprendizado": 3},
    "Primeiro passo": {"tipo": "sit", "ca": 1, "mov": 3, "nota": "primeiro turno do combate"},
    "Provocador": {"tipo": "sit", "ca": 2, "nota": "contra o alvo provocado"},
    "Defensor da Base": {"tipo": "sit", "ca": 2, "nota": "lutando dentro da Base"},
    "Calmaria": {"tipo": "sit", "acerto": 2, "nota": "agiu por último, primeira rodada"},
    "Oportunista": {"tipo": "sit", "acerto": 2, "nota": "Golpe de Oportunidade"},
    "Ataque Cruzado": {"tipo": "sit", "acerto": 2, "nota": "ataque bônus após acertar o primeiro"},
    "Pares Afinados": {"tipo": "sit", "acerto": 2, "nota": "ataque bônus com duas armas do mesmo grupo"},
    "Mão de Falcão": {"tipo": "sit", "acerto": 2, "nota": "Mirar em Ponto Cego"},
    "Caçador de Fraquezas": {"tipo": "sit", "acerto": 2, "dano_nivel": 1, "nota": "atacando um Ponto Chave"},
    "Maestria": {"tipo": "sit", "acerto": 1, "nota": "com a arma escolhida"},
    "Extasiado": {"tipo": "sit", "iniciativa": 5, "nota": "não ser o primeiro na iniciativa"},
    "Navegante Nato": {"tipo": "sit", "pericia": {"Navegação": 3}, "nota": "em viagens"},
    "Voz Encantadora": {"tipo": "sit", "pericia": {"Artes": 2}, "nota": "ao se apresentar em público"},
}
ARMADURAS_PESADAS = {"Armadura Pesada", "Armadura Reforçada", "Armadura Colossal"}


def efeitos_talentos(talentos, ativos, armadura=""):
    """Soma os efeitos dos talentos escolhidos: permanentes sempre, situacionais só se estiverem em `ativos`."""
    out = {"ca": 0, "mov": 0, "acerto": 0, "iniciativa": 0, "descoberta": 0, "contra": 0, "dt_alma": 0,
           "aprendizado": 0, "dano_nivel": 0, "pericia": {}}
    for nome in sorted(talentos):
        ef = EFEITOS_TALENTOS.get(nome)
        if not ef or (ef["tipo"] == "sit" and nome not in ativos):
            continue
        if nome == "Passos Leves" and armadura in ARMADURAS_PESADAS:
            continue
        for k, v in ef.items():
            if k == "pericia":
                for p, b in v.items():
                    out["pericia"][p] = out["pericia"].get(p, 0) + b
            elif k in out:
                out[k] += v
    return out


# ---------------- Dados ----------------
_TERMO = re.compile(r"([+-]?)\s*(\d+)\s*d\s*(\d+)|([+-]?)\s*(\d+)")


def rolar_expr(expr, rng, dobrar=False):
    """Rola uma expressão como '3d6 + 1d4 + 2'. rng(faces) devolve 1..faces.
    dobrar=True (crítico) rola o dobro de dados; modificadores fixos não dobram.
    Devolve (total, partes) com partes = [(texto, [valores], subtotal)]."""
    total, partes = 0, []
    for m in _TERMO.finditer(expr or ""):
        if m.group(2):
            sinal = -1 if m.group(1) == "-" else 1
            q, f = int(m.group(2)), int(m.group(3))
            q = q * 2 if dobrar else q
            vals = [rng(f) for _ in range(q)]
            sub = sinal * sum(vals)
            partes.append((f"{'-' if sinal < 0 else ''}{q}d{f}", vals, sub))
        else:
            sinal = -1 if m.group(4) == "-" else 1
            sub = sinal * int(m.group(5))
            partes.append((f"{sub:+d}", [], sub))
        total += sub
    return total, partes


def rolar_ataque(bonus, com_vantagem, margem, rng):
    """1d20 (2d20 com vantagem, fica o maior) + bônus. Crítico: natural >= margem (dobra dados);
    só o 20 acerta garantido. Desastre: natural 1."""
    d = [rng(20) for _ in range(2 if com_vantagem else 1)]
    nat = max(d)
    return {"d20": d, "natural": nat, "bonus": bonus, "total": nat + bonus,
            "critico": nat >= margem, "garantido": nat == 20, "desastre": nat == 1}


def custo_mana(versao):
    m = re.search(r"(\d+)", str(versao.get("mana", "")))
    return int(m.group(1)) if m else None


_DANO_ENC = re.compile(r"\d+d\d+(?:\s*\+\s*\d+d\d+)*(?:\s*\+\s*\d+(?!d))?")


def dano_do_encantamento(descricao):
    """Primeira expressão de dados da descrição (ex.: '4d6 + 2'), ou None."""
    m = _DANO_ENC.search(descricao or "")
    return re.sub(r"\s+", " ", m.group(0)) if m else None
