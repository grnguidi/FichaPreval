# -*- coding: utf-8 -*-
"""Bestiário (capítulo "Criando inimigos" do livro 3.2): os números base de cada categoria de inimigo.

Pega a linha do inimigo Comum do NMP (Nível Médio dos Personagens) e ajusta pela categoria. Entre duas linhas da tabela,
o valor é interpolado ("use a linha mais próxima ou um valor entre as duas"). Sem interface: só contas."""
import math
import re

TIERS = ["Lacaio", "Comum", "Forte", "Animal", "Prevalecente", "Deus"]
CONDICOES = ["Veneno", "Podridão", "Sangramento", "Congelamento", "Sono", "Loucura", "Morte"]

# Inimigo Comum por NMP: (NMP, Vida, CA, Ataque, DT, Dano por turno)
LINHAS = [
    (1, 15, 9, 0, 11, "2d4"),
    (5, 60, 11, 2, 12, "2d6"),
    (10, 95, 15, 5, 15, "4d8"),
    (15, 275, 18, 7, 17, "5d10"),
    (20, 330, 21, 7, 18, "8d8 + 6"),
    (25, 440, 24, 10, 21, "9d10 + 6"),
    (30, 480, 26, 10, 23, "12d10"),
]

# Ajustes por categoria
AJUSTES = {
    "Lacaio":       {"quantos": "2 a 3 por jogador", "vida": 2, "ca": -1, "atk": -1, "dano": 2, "golpes": 1, "por_jogador": False, "postura": 0.20, "cond_pts": 5},
    "Comum":        {"quantos": "1 por jogador", "vida": 6, "ca": 0, "atk": 0, "dano": 3, "golpes": 2, "por_jogador": False, "postura": 0.20, "cond_pts": 10},
    "Forte":        {"quantos": "Sozinho ou liderando um grupo", "vida": 9, "ca": 2, "atk": 2, "dano": 4, "golpes": 2, "por_jogador": False, "postura": 0.20, "cond_pts": 15},
    "Animal":       {"quantos": "1, mini-chefe", "vida": 24, "ca": 4, "atk": 5, "dano": 8, "golpes": 2, "por_jogador": True, "postura": 0.20, "cond_pts": 20},
    "Prevalecente": {"quantos": "1 por país", "vida": 26, "ca": 6, "atk": 8, "dano": 10, "golpes": 2, "por_jogador": True, "postura": 0.20, "cond_pts": 25},
    "Deus":         {"quantos": "1 por Andar", "vida": 36, "ca": 8, "atk": 10, "dano": 11.5, "golpes": 2, "por_jogador": True, "postura": 0.25, "cond_pts": 38},
}

# Vida de condição por NMP (faixas) e categoria, para um grupo de 4 jogadores
VIDA_CONDICAO = [
    (1, 2, [5, 10, 15, 20, 25, 50]), (3, 4, [5, 15, 20, 25, 30, 60]), (5, 6, [10, 20, 30, 40, 45, 90]),
    (7, 8, [20, 40, 55, 70, 80, 160]), (9, 10, [30, 55, 75, 95, 110, 220]), (11, 12, [35, 75, 100, 125, 150, 300]),
    (13, 15, [50, 100, 135, 170, 200, 400]), (16, 18, [75, 145, 195, 245, 290, 580]), (19, 20, [90, 180, 240, 300, 360, 720]),
    (21, 25, [105, 215, 285, 355, 430, 860]), (26, 30, [120, 235, 315, 395, 470, 940]),
]
AFINIDADES = {"imune": 0, "resistente": 2.0, "vulneravel": 0.5}   # multiplicador do valor da tabela (imune: nunca ativa)
# O que acontece quando a barra de uma condição zera num inimigo (% da Vida máxima; Animal, Prevalecente e Deus sofrem metade dos proporcionais)
EFEITO_CONDICAO = {
    "Veneno": {"turnos": 5, "pct_turno": 5, "txt": "Sofre 5% da Vida máxima por turno, por 5 turnos."},
    "Podridão": {"turnos": 0, "pct_turno": 3, "txt": "Sofre 3% da Vida máxima por turno até o fim do combate."},
    "Sangramento": {"pct_ja": 25, "txt": "Perde 25% da Vida máxima na hora (ignora resistências e RD)."},
    "Congelamento": {"turnos": 2, "pct_ja": 10, "txt": "Perde 10% da Vida máxima na hora e fica com a CA pela metade por 2 turnos."},
    "Sono": {"turnos": 1, "txt": "Fica Inconsciente por 1 turno; nada remove esse efeito."},
    "Loucura": {"turnos": 0, "txt": "Recebe o dobro de dano mental e falha em todo teste de Vontade até o fim do combate."},
    "Morte": {"txt": "Lacaio, Comum e Forte morrem. Animal e Prevalecente perdem 50% da Vida máxima; Deus perde 25%."},
}
MEIA_PCT_TIERS = {"Animal", "Prevalecente", "Deus"}


def _media_dados(expr):
    """Média de '8d8 + 6' (dados e valores fixos somados)."""
    total = 0.0
    for m in re.finditer(r"(\d+)d(\d+)|([+-]?\s*\d+)", expr or ""):
        if m.group(1):
            total += int(m.group(1)) * (int(m.group(2)) + 1) / 2
        else:
            total += int(m.group(3).replace(" ", ""))
    return total


def _interpola(nmp, coluna):
    """Valor da coluna numérica (1=Vida, 2=CA, 3=Ataque, 4=DT) para um NMP qualquer, entre duas linhas da tabela."""
    nmp = max(1, min(30, int(nmp)))
    for (n0, *v0), (n1, *v1) in zip(LINHAS, LINHAS[1:]):
        if n0 <= nmp <= n1:
            t = (nmp - n0) / (n1 - n0)
            a, b = v0[coluna - 1], v1[coluna - 1]
            return a + (b - a) * t
    return LINHAS[-1][coluna]


def _dano_base(nmp):
    """(média de dano por turno do Comum no NMP, expressão de dados quando o NMP cai exatamente numa linha da tabela, senão '')."""
    nmp = max(1, min(30, int(nmp)))
    for l0, l1 in zip(LINHAS, LINHAS[1:]):
        if l0[0] <= nmp <= l1[0]:
            m0, m1 = _media_dados(l0[5]), _media_dados(l1[5])
            t = (nmp - l0[0]) / (l1[0] - l0[0])
            exato = next((l[5] for l in LINHAS if l[0] == nmp), "")
            return m0 + (m1 - m0) * t, exato
    return _media_dados(LINHAS[-1][5]), LINHAS[-1][5]


def dados_da_media(media):
    """Expressão de dados com essa média ('13d10 + 1' para 72): o dano de um golpe é rolado, não fixo.
    O dado cresce com o valor (d4 até 7, d6 até 19, d8 até 59, d10 até 199, d12 acima); o resto vira bônus fixo."""
    m = max(0, int(round(media)))
    if m < 2:
        return str(m)
    f = 4 if m < 8 else 6 if m < 20 else 8 if m < 60 else 10 if m < 200 else 12
    q = max(1, int(m // ((f + 1) / 2)))
    fixo = int(round(m - q * (f + 1) / 2))
    return f"{q}d{f}" + (f" + {fixo}" if fixo > 0 else f" - {-fixo}" if fixo < 0 else "")


def vida_de_condicao(tier, nmp, jogadores=4):
    """Pontos da barra de cada condição. Animal, Prevalecente e Deus: valor × jogadores ÷ 4."""
    i = TIERS.index(tier)
    nmp = max(1, min(30, int(nmp)))
    base = next(l for a, b, l in VIDA_CONDICAO if a <= nmp <= b)[i]
    if tier in MEIA_PCT_TIERS:
        base = base * max(1, int(jogadores)) / 4
    return int(round(base))


def pontos_por_golpe(tier, nmp):
    """Pontos de condição que o inimigo aplica por golpe ou habilidade que aplica condição."""
    return int(AJUSTES[tier]["cond_pts"] + int(nmp) // 2)


def calcular(tier, nmp, jogadores=4):
    """Números de partida de um inimigo. Tudo pode ser trocado à mão depois."""
    if tier not in AJUSTES:
        raise ValueError("categoria desconhecida")
    aj = AJUSTES[tier]
    nmp = max(1, min(30, int(nmp)))
    jog = max(1, int(jogadores))
    fator_j = jog / 4 if aj["por_jogador"] else 1
    vida = int(math.ceil(_interpola(nmp, 1) * aj["vida"] * fator_j))
    ca = int(round(_interpola(nmp, 2))) + aj["ca"]
    atk = int(round(_interpola(nmp, 3))) + aj["atk"]
    dt = int(round(_interpola(nmp, 4))) + aj["ca"]
    media_base, exato = _dano_base(nmp)
    dano_turno = int(round(media_base * aj["dano"]))
    golpes = aj["golpes"]
    mult = ("%g" % aj["dano"])
    out = {
        "tier": tier, "nmp": nmp, "jogadores": jog, "quantos": aj["quantos"],
        "vida": vida, "ca": ca, "ataque": atk, "dt": dt, "resistencia": atk,
        "dano_turno": dano_turno, "dano_expr": (f"{mult} × ({exato})" if exato else f"{mult} × (≈ {int(round(media_base))} de média)"),
        "golpes": golpes, "dano_golpe": int(round(dano_turno / golpes)), "dano_golpe_dados": dados_da_media(dano_turno / golpes),
        "postura": int(math.ceil(vida * aj["postura"])),
        "vida_condicao": vida_de_condicao(tier, nmp, jog), "cond_por_golpe": pontos_por_golpe(tier, nmp),
        "morte": EFEITO_CONDICAO["Morte"]["txt"],
    }
    if tier == "Deus":
        out["extra_deus"] = ("A Redução de Dano fixa (Tenacidade, sets) vale metade contra golpes de Deus. Aura: no início de cada rodada, toda criatura a até 18 m "
                             f"sofre {15 + nmp // 2} pontos de uma condição do Deus (teste de resistência reduz à metade). Morte tira só 25% da Vida máxima.")
    return out


def recarga_apos_ativar(maximo, ativacoes):
    """Quando uma condição é ativada, a barra volta com o valor máximo +50% (a 3ª ativação, +100%). `ativacoes` já conta a que acabou de acontecer."""
    return int(round(maximo * (2.0 if ativacoes >= 3 else 1.5)))
