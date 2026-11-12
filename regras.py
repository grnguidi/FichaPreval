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


# ---------------- Livro: tipos de dano, efeitos e condições ----------------
TIPOS_DANO = [  # (nome, grupo, nota)
    ("Impacto", "Físico", ""), ("Cortante", "Físico", ""), ("Perfurante", "Físico", ""),
    ("Fogo", "Elemental", ""), ("Veneno", "Elemental", ""), ("Magia", "Elemental", ""),
    ("Magia Pura", "Elemental", "ignora RD"), ("Sagrado", "Elemental", ""), ("Relâmpago", "Elemental", "não tem RD"),
    ("Elétrico", "Elemental", ""), ("Necrótico", "Elemental", ""), ("Glacial", "Elemental", ""),
    ("Psíquico", "Mental", ""), ("Êxtase", "Mental", ""), ("Melódico", "Mental", ""), ("Radiante", "Mental", ""),
    ("Direto", "Outro", "ignora RD e resistências (perda de Vida de condição, quedas…)"),
]
NOMES_DANO = [t[0] for t in TIPOS_DANO]
DANO_SEM_RD = {"Magia Pura", "Relâmpago", "Direto"}
DANO_MENTAL = {t[0] for t in TIPOS_DANO if t[1] == "Mental"}

EFEITOS_LIVRO = [  # (nome, gravidade, descrição) — capítulo "Efeitos"
    ("Abalado", "Fraco", "−2 em jogadas de ataque e testes de perícia."),
    ("Caído", "Fraco", "−2 em ataques corpo a corpo; move 4,5 m rastejando ou usa ação de movimento para levantar. −2 de CA contra corpo a corpo, +2 contra à distância."),
    ("Amedrontado", "Médio", "Desvantagem em jogadas de ataque e testes de perícia."),
    ("Confuso", "Médio", "Move-se ao acaso (1d4 de direção a cada 1,5 m); −2 em Fortitude e Atletismo para ficar de pé."),
    ("Agarrado", "Médio", "Desprevenido (−2 de CA) e imóvel; ataques à distância contra o agarrão podem acertar o alvo errado (1–5 em 1d10)."),
    ("Enredado", "Médio", "Deslocamento pela metade; −2 de CA e em jogadas de ataque."),
    ("Lento", "Médio", "Toda forma de movimento reduzida à metade."),
    ("Condenado", "Forte", "Custos de Mana e de Vigor aumentam em 50%."),
    ("Aterrorizado", "Forte", "Não pode se aproximar da criatura que causou o efeito."),
    ("Exposto", "Forte", "Ataques contra a criatura têm +2 e, se acertarem, +1 dado de dano do maior dado."),
    ("Fragilizado", "Forte", "Redução de Dano zerada e resistências anuladas (imunidades não)."),
    ("Atordoado", "Extremo", "Não pode realizar ações."),
    ("Inconsciente", "Extremo", "Não age, fica caído, larga o que segura, não fala; falha em todos os testes e é acertado sem jogada de ataque."),
    ("Paralisado", "Extremo", "Não age; ataques contra ele têm vantagem e todo acerto corpo a corpo é crítico."),
]
NOTA_EFEITOS = ("Salvo indicação contrária, um efeito dura 1 turno. Se durar mais, o afetado faz um teste de resistência "
                "no fim de cada turno (Fortitude para físicos, Vontade para mentais) contra a DT de quem causou.")

# Condições (barras de 100 nos jogadores). Teste para receber metade e o que acontece ao encher a barra.
CONDICAO_TESTE = {"Veneno": "Fortitude", "Podridão": "Fortitude", "Sangramento": "Fortitude", "Congelamento": "Fortitude",
                  "Sono": "Vontade", "Loucura": "Vontade", "Morte": "Vontade"}
CONDICAO_ATIVA = {
    # turnos: 0 = até o fim do combate; pct_turno: % da Vida máx. por turno; pct_ja: % perdido na hora
    "Veneno": {"turnos": 5, "pct_turno": 5, "desc": "Sofre 5% da Vida máxima por turno, por 5 turnos."},
    "Podridão": {"turnos": 0, "pct_turno": 3, "desc": "Sofre 3% da Vida máxima por turno até o fim do combate."},
    "Sangramento": {"pct_ja": 25, "desc": "Perde 25% da Vida máxima na hora, ignorando resistências e RD."},
    "Congelamento": {"turnos": 2, "pct_ja": 10, "desc": "Perde 10% da Vida máxima na hora e fica com a CA pela metade por 2 turnos."},
    "Sono": {"turnos": 1, "desc": "Fica Inconsciente por 1 turno; nada remove esse efeito."},
    "Loucura": {"turnos": 0, "desc": "Recebe o dobro de dano mental e falha em todo teste de Vontade até o fim do combate."},
    "Morte": {"desc": "Morre na hora, consumido pelas raízes da Intérprete."},
}
CONDICAO_DESCANSO_CURTO = 25   # pontos que um descanso curto tira de cada barra


def receber_condicao(acumulado, maximo, pontos, sucesso_teste):
    """Pontos de condição vindos de um inimigo. Sucesso no teste: metade (para baixo).
    Devolve (recebidos, novo_acumulado, ativou). Ao encher a barra o efeito ativa e ela volta a zero."""
    recebidos = pontos // 2 if sucesso_teste else pontos
    novo = max(0, acumulado + recebidos)
    if maximo > 0 and novo >= maximo:
        return recebidos, 0, True
    return recebidos, novo, False


def defesas_contra_dano(valor, tipo, d, rng, fragilizado=False, loucura=False):
    """Dano recebido pela ficha: rola a RD (1d4 a cada 20 de TEN, contra qualquer golpe) e depois aplica
    resistência (metade, para baixo). Magia Pura e Relâmpago ignoram RD; 'Direto' ignora tudo.
    Devolve (dano_final, [notas])."""
    notas = []
    if valor <= 0:
        return valor, notas
    total = valor
    if tipo == "Direto":
        return total, notas
    if loucura and tipo in DANO_MENTAL:
        total *= 2
        notas.append("Loucura: dano mental em dobro")
    rd = 0 if fragilizado or tipo in DANO_SEM_RD else int(d.get("rd", 0))
    if rd:
        rolos = [rng(4) for _ in range(rd)]
        total = max(0, total - sum(rolos))
        notas.append(f"RD {rd}d4 [{', '.join(map(str, rolos))}] −{sum(rolos)}")
    elif fragilizado and d.get("rd"):
        notas.append("Fragilizado: sem RD")
    if tipo and tipo in d.get("resistencias", []) and not fragilizado:
        total //= 2
        notas.append(f"resistência a {tipo}: metade")
    return total, notas


# ---------------- Perícias, descanso, Poção Espiritual, desgaste ----------------
def rolar_pericia(bonus, dados, rng):
    """Teste fora de combate: rola `dados` d20 e fica com o maior (vantagem cumulativa) + bônus."""
    d = [rng(20) for _ in range(max(1, dados))]
    return {"d20": d, "natural": max(d), "bonus": bonus, "total": max(d) + bonus}


def rolar_defesa(bonus, com_vantagem, rng):
    d = [rng(20) for _ in range(2 if com_vantagem else 1)]
    return {"d20": d, "natural": max(d), "bonus": bonus, "total": max(d) + bonus}


DESCANSOS_CURTOS_MAX = 2


def descanso(tipo, maximos, atuais, condicoes):
    """tipo 'curto': recupera metade de Vida, Mana e Vigor e 25 pontos de cada condição.
    'longo': recupera tudo e zera as condições. maximos/atuais: {'vida','mana','vigor'};
    condicoes: {nome: acumulado}. Devolve (novos_atuais, novas_condicoes)."""
    novos = {}
    for k, mx in maximos.items():
        at = atuais.get(k, mx)
        novos[k] = mx if tipo == "longo" else min(mx, at + mx // 2)
    cond = {n: (0 if tipo == "longo" else max(0, v - CONDICAO_DESCANSO_CURTO)) for n, v in condicoes.items()}
    return novos, cond


def pocao_espiritual_dados(nivel, curva_vit):
    """(metade do nível + metade da Curva da Vitalidade) d10, mínimo 2 dados."""
    return max(2, nivel // 2 + curva_vit // 2)


DESGASTE_TURNOS = 3   # turnos afiados; o crítico reinicia; ao acabar a arma fica 1 turno sem uso


def desgaste_apos_ataque(usados, critico):
    """Devolve (usados, desgastou). O crítico reinicia a contagem."""
    if critico:
        return 0, False
    usados += 1
    return (usados, True) if usados >= DESGASTE_TURNOS else (usados, False)


# ---------------- Arcano nos dados de condição dos encantamentos ----------------
_COND_ENC = re.compile(r"(\d+d\d+(?:\s*\+\s*\d+d\d+)*(?:\s*\+\s*\d+(?!\d|\s*d\d))?)\s+(?:pontos\s+)?de\s+"
                       r"(Veneno|Podridão|Sangramento|Congelamento|Sono|Loucura|Morte)", re.I)
DADO_INFERIOR = {12: 10, 10: 8, 8: 6, 6: 4, 4: 4, 20: 12}


def condicoes_do_encantamento(descricao):
    """Lista de (expressão, condição) com os dados de condição da descrição."""
    out = []
    for m in _COND_ENC.finditer(descricao or ""):
        nome = next(c for c in CONDICOES if c.lower() == m.group(2).lower())
        out.append((re.sub(r"\s+", " ", m.group(1)), nome))
    return out


def escalar_arcano(expr, arcano, condicao):
    """A cada 20 de ARC, uma cópia dos dados de condição; a cada 15, mais 1 dado um tamanho abaixo do
    maior dado (d12→d10→…→d4). Morte só recebe os dados inferiores. Valores fixos não copiam."""
    arc = cap(arcano)
    dados = [(int(q), int(f)) for q, f in re.findall(r"(\d+)d(\d+)", expr)]
    fixo = sum(int(x) for x in re.findall(r"\+\s*(\d+)(?!\d|d)", expr))
    if not dados:
        return expr
    copias = 0 if condicao == "Morte" else arc // 20
    inferiores = arc // 15
    soma = {}
    for q, f in dados:
        soma[f] = soma.get(f, 0) + q * (1 + copias)
    maior = max(f for _, f in dados)
    if inferiores:
        inf = DADO_INFERIOR.get(maior, 4)
        soma[inf] = soma.get(inf, 0) + inferiores
    partes = [f"{q}d{f}" for f, q in sorted(soma.items(), key=lambda x: -x[0])]
    return " + ".join(partes) + (f" + {fixo}" if fixo else "")


# ---------------- Carga extra ----------------
PECAS_SET_PESO = ("Capacete", "Manopla", "Calça", "Bota")   # pesam 1 cada; o Peitoral pesa como a armadura


def peso_pecas_set(pecas):
    """pecas: {peça: {'set','nome'}}. Conta 1 por Capacete/Manopla/Calça/Bota equipado."""
    return sum(1 for p in PECAS_SET_PESO if (pecas.get(p) or {}).get("set") or (pecas.get(p) or {}).get("nome"))


def carga_extra_itens(inventario, itens_livro):
    """Itens que aumentam a Carga (Mochila +5). Só conta uma Mochila."""
    por_nome = {i["nome"].lower(): i for i in itens_livro}
    extra = 0
    for it in inventario:
        u = (por_nome.get(str(it.get("item", "")).strip().lower()) or {}).get("uso", {})
        extra = max(extra, int(u.get("carga", 0)))
    return extra


def peso_inventario(inventario):
    """Soma carga × quantidade de cada linha."""
    tot = 0.0
    for it in inventario:
        try:
            c = float(str(it.get("carga", 0) or 0).replace(",", "."))
        except ValueError:
            c = 0.0
        try:
            q = max(1, int(str(it.get("qtd", 1) or 1)))
        except ValueError:
            q = 1
        tot += c * q
    return tot



# ---------------- Talentos com escolha (arma, escola, condição, perícia) ----------------
ESCOLHA_TALENTO = {
    "Maestria": "arma", "Maestria dupla": "arma", "Domínio": "arma",
    "Matrícula": "escola", "Matrícula avançada": "escola_ou_mana",
    "Condição Endurecida": "condicao", "Mestre das Perícias": "pericia",
}
ROTULO_ESCOLHA = {"arma": "Arma", "escola": "Escola", "escola_ou_mana": "Escola ou −2 de mana",
                  "condicao": "Condição", "pericia": "Perícia"}
MATRICULA_MANA2 = "−2 de mana"


def efeitos_escolhas(talentos_slots, escolhas):
    """talentos_slots: {slot: nome do talento}; escolhas: {slot: valor escolhido}.
    Devolve o que cada talento de escolha faz, só para o que foi escolhido, e os que ainda faltam escolher."""
    out = {"maestria": [], "dominio": {}, "escolas": [], "mana": 0, "espaco": 0, "todas_escolas": False,
           "cond_extra": {}, "pericia_mestre": [], "pendentes": []}
    nomes = {n for n in talentos_slots.values() if n}
    for slot in sorted(talentos_slots, key=lambda x: (x == "extra", int(x) if x.isdigit() else 99)):
        nome = talentos_slots[slot]
        tipo = ESCOLHA_TALENTO.get(nome)
        if not tipo:
            continue
        v = str(escolhas.get(slot) or "").strip()
        if not v:
            out["pendentes"].append(nome)
            continue
        if nome in ("Maestria", "Maestria dupla"):
            if v not in out["maestria"]:
                out["maestria"].append(v)
        elif nome == "Domínio":
            out["dominio"][v] = out["dominio"].get(v, 0) + 1 + (1 if "Arma de família" in nomes else 0)
        elif nome == "Matrícula":
            if v not in out["escolas"]:
                out["escolas"].append(v)
            out["mana"], out["espaco"] = max(out["mana"], 1), 1
        elif nome == "Matrícula avançada":
            if v == MATRICULA_MANA2:
                out["mana"] = 2
            elif v not in out["escolas"]:
                out["escolas"].append(v)
        elif nome == "Condição Endurecida":
            out["cond_extra"][v] = out["cond_extra"].get(v, 0) + 20
        elif nome == "Mestre das Perícias":
            if v not in out["pericia_mestre"]:
                out["pericia_mestre"].append(v)
    if "Matrícula Suprema" in nomes and out["escolas"]:
        out["todas_escolas"] = True
        out["mana"] = min(3, max(out["mana"], 1))
    return out


def desconto_matricula(esc, escola, mana, espaco):
    """Custo de Mana e espaço de um encantamento depois da Matrícula (mínimo 1). mana pode ser None."""
    if not esc.get("mana") or not (esc.get("todas_escolas") or escola in esc.get("escolas", [])):
        return mana, espaco
    m = None if mana is None else (mana if mana <= 0 else max(1, mana - esc["mana"]))
    return m, max(1, espaco - esc.get("espaco", 0))
