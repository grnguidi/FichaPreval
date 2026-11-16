# -*- coding: utf-8 -*-
"""Regras de Prevalecentes (PREVA 3.2) — cálculos puros, sem interface."""
import math
import re

ATRIBUTOS = ["VIT", "MEN", "TEN", "FOR", "DES", "INT", "FE", "ARC"]
NOMES_ATR = {"VIT": "Vitalidade", "MEN": "Mente", "TEN": "Tenacidade", "FOR": "Força",
             "DES": "Destreza", "INT": "Inteligência", "FE": "Fé", "ARC": "Arcano"}
ATR_POR_NOME = {v: k for k, v in NOMES_ATR.items()}
VALORES_INICIAIS = [16, 14, 12, 11, 10, 9, 8, 7]
CA_MAX = 30          # 3.2: máxima 30; o que passar é perdido
NIVEL_MAX = 30

# Perícias fora de combate: nome -> atributos possíveis (usa o maior), requer treino
PERICIAS = [
    ("Acrobacia", ["DES"], False), ("Adestramento", ["MEN"], True),
    ("Agricultura", ["INT"], True), ("Alquimia", ["INT"], True), ("Artes", ["MEN"], False),
    ("Atletismo", ["FOR"], False), ("Ciências", ["INT"], False),
    ("Costura", ["INT", "DES"], True), ("Crime", ["DES"], False),
    ("Furtividade", ["DES"], False), ("Gastronomia", ["INT", "DES"], False),
    ("História", ["FE"], False), ("Intuição", ["FE"], False),
    ("Investigação", ["INT"], False), ("Medicina", ["INT"], True),
    ("Navegação", ["INT"], False), ("Percepção", ["ARC"], False),
    ("Performance", ["MEN"], False), ("Persuasão", ["MEN"], False),
    ("Prevalência", None, True), ("Religião", ["FE"], False),
    ("Sorte", ["ARC"], False), ("Tática", ["INT", "MEN"], False),
    ("Tecnologia", ["INT"], True),
]
# O que cada perícia faz (resumo do capítulo de Perícias e das regras que pedem o teste) e onde o livro a usa.
PERICIAS_RESUMO = {
    "Acrobacia": ("Equilíbrio, saltos, quedas, piruetas e escapar de situações que pedem agilidade do corpo, como pular uma barreira com segurança.", ""),
    "Agricultura": ("Horta e Pasto (no livro 3.2 a perícia se chama Horta e Pasto): plantar, colher, cuidar de animais de criação e coletar ervas na natureza (DT 10/20/30/40 + metade do NMP, 1 tentativa por local por dia).", "Horta e Pasto"),
    "Alquimia": ("A perícia das poções: Poções de Mana e de Vigor, antídotos e tônicos. Poções de nível 1 a 4 (DT 10/20/30/40 pela raridade mais rara usada); sucesso rende 2 poções por ingrediente principal, falha perde 1 ingrediente. Quem não é treinado só usa poções compradas ou encontradas. Poções não restauram Vida, só dão vida temporária.", "Poções, Horta, Funções"),
    "Artes": ("Pintura, escultura, escrita e qualquer ofício artístico; também criar e sustentar um disfarce (o teste é contra quem observa e se repete a cada interação).", "Disfarce"),
    "Atletismo": ("Força física aplicada: escalar, nadar, empurrar, arrombar, segurar ou se soltar. Agarrar e Derrubar agora são testes de Fortitude do alvo contra a sua DT (10 + BC de Força + nível ÷ 3).", ""),
    "Ciências": ("Conhecimento acadêmico e natural: matemática, astronomia, criaturas e fenômenos estudados.", ""),
    "Costura": ("Confeccionar e consertar as cinco peças de armadura dos sets com os materiais da receita; a DT é a da raridade do item e uma falha perde materiais.", "Sets"),
    "Crime": ("Abrir fechaduras, desarmar armadilhas, furtar, falsificar e circular no submundo.", "Infiltração"),
    "Furtividade": ("Mover-se sem ser visto ou ouvido. Esconder é Furtividade contra a Percepção de quem pode ver você; cada falha numa infiltração sobe o Alerta.", "Infiltração"),
    "Gastronomia": ("Cozinhar refeições que dão bônus ao grupo e conservar alimentos na estrada; a DT é fixa pelo nível da refeição (10/20/30/40) e não exige treino.", "Alimentos/Expedição"),
    "História": ("Saber sobre o passado, reinos, guerras, linhagens e lendas; argumento de peso num conflito social.", "Conflito Social"),
    "Intuição": ("Perceber intenções, mentiras e o clima de uma conversa; sentir quando algo está errado.", ""),
    "Investigação": ("Procurar pistas, examinar cenas e documentos e ligar os fatos; encontrar o que está escondido numa expedição.", "Expedição"),
    "Medicina": ("Tratar ferimentos, doenças e venenos. No Portão da Morte, um aliado faz Medicina (DT 15) para dar 1 sucesso a quem está Incapaz.", "Portão da Morte"),
    "Navegação": ("Orientar-se e guiar o grupo em viagens por terra e mar; define o tempo da viagem e evita se perder. Não exige treino.", "Viagens"),
    "Percepção": ("Notar o que está à volta: emboscadas, criaturas escondidas, sons e detalhes. É contra ela que os outros testam Furtividade.", ""),
    "Performance": ("Cantar, tocar, atuar e discursar para uma plateia; impressionar ou distrair num conflito social.", "Conflito Social"),
    "Persuasão": ("Convencer, negociar, barganhar e acalmar pela conversa; a principal perícia do conflito social.", "Conflito Social"),
    "Prevalência": ("A força da vontade do personagem ligada à alma, com o atributo que o jogador escolher; usada pelas almas e por talentos como Mente de Aço e Lâmina Dedicada (que agora mexem na DT da Dedicação da Katana).", "Almas"),
    "Religião": ("Deuses, cultos, ritos e criaturas sagradas ou profanas; alguns Feitiços pedem este teste.", "Alguns Feitiços"),
    "Sorte": ("O acaso a seu favor: achar o que precisa, escapar por pouco, encontros e espólios na expedição.", "Expedição"),
    "Tática": ("Ler o campo de batalha, prever o inimigo e planejar o grupo (Inteligência ou Mente, o maior); algumas habilidades e o clima adverso nas viagens pedem este teste.", "Algumas Habilidades"),
    "Tecnologia": ("Mecanismos, ferramentas, forja e engenhocas: consertar, montar e operar; serviços de ferraria pedem este teste.", ""),
    "Luta": ("Ataques corpo a corpo: 1d20 + BC do atributo da arma + nível ÷ 3 + acerto da arma, contra a CA do alvo.", "Ataque corpo a corpo"),
    "Pontaria": ("Ataques à distância (Arco, Besta): 1d20 + BC de Destreza + nível ÷ 3 + acerto da arma, contra a CA do alvo.", "Ataque a distância"),
    "Feitiçaria": ("Conjurar Magias: 1d20 + BC de Inteligência + nível ÷ 3 + acerto do cajado; também lê idiomas arcanos e anula magias inimigas (Contradomínio).", "Magias"),
    "Desejo": ("Conjurar Feitiços: 1d20 + BC de Fé + nível ÷ 3 + acerto do selo; também lê idiomas mortos e anula feitiços inimigos (Contradomínio).", "Feitiços"),
    "Fortitude": ("Defesa do corpo (Tenacidade): resistir a Veneno, Podridão, Sangramento, Congelamento, empurrões e efeitos físicos.", "Defesa"),
    "Reflexo": ("Defesa por agilidade (Destreza): esquivar de áreas, armadilhas e quedas.", "Defesa"),
    "Astúcia": ("Defesa da mente (Mente): perceber truques, ilusões e enganações.", "Defesa"),
    "Vontade": ("Defesa do espírito (Fé): resistir a Sono, Loucura, Morte, medo, provocação e controle mental.", "Defesa"),
}

# O que cada atributo representa (capítulo Atributos) e o que ele move na ficha (Características Derivadas).
ATRIBUTOS_RESUMO = {
    "VIT": ("A força que mantém o corpo de pé: suportar ferimentos e continuar lutando.",
            ["Vida: rola 1d12 por ponto de Curva da Vitalidade (ou 7 por dado)", "Dados da Poção Espiritual"]),
    "MEN": ("O reservatório de energia interior que alimenta habilidades: quanto de mana o personagem canaliza.",
            ["Mana = 2 × Mente + 2 × Curva da Mente", "Astúcia (defesa)", "Artes, Performance e Persuasão",
             "Perícias treinadas: +1 a cada 10 pontos (a maior entre Mente e Inteligência)"]),
    "TEN": ("O vigor físico para correr, esquivar, bloquear e aguentar o peso: o porte do corpo em combate.",
            ["CA: +1 a cada 20 pontos (máx. +4)", "Redução de Dano: 1d4 a cada 20 pontos (máx. 4d4)",
             "Resistências: Fogo 20, Cortante 30, Impacto 40, Veneno 50, Sangramento 60, Magia 70, Magia Pura 80, Sagrado 90",
             "Carga = 10 + 2 × Tenacidade + Força ÷ 2 + Curva da Tenacidade", "Fortitude (defesa)"]),
    "FOR": ("O poder bruto para erguer armas pesadas e desferir golpes devastadores.",
            ["Vigor = 20 + Força + Curva da Força; recupera Curva ÷ 4 por turno", "Ataque e requisitos das armas de Força",
             "Atletismo", "Metade da Força entra na Carga"]),
    "DES": ("Precisão, velocidade e controle: armas leves, flexíveis e à distância.",
            ["Ações extras (Comum ou Bônus) com 15, 30, 45, 55, 65, 75, 85 e 95", "Movimento: +3 m com 30 e a cada 15 acima",
             "Iniciativa: 1d20 a mais a cada 20 pontos", "Reflexo (defesa)", "Ataque das armas de Destreza e Pontaria",
             "Acrobacia, Crime e Furtividade"]),
    "INT": ("A chave para compreender e manipular forças místicas pelo estudo: conjura as Magias.",
            ["Feitiçaria: acerto e DT das Magias", "+1 dado nas Magias a cada 30 pontos",
             "Espaços de encantamento: 1 + (Inteligência + Fé) ÷ 6", "Contradomínio: 1 por combate a cada 10 pontos (a maior entre INT e Fé)",
             "Perícias treinadas: +1 a cada 10 pontos", "Ciências, Investigação, Medicina e Tecnologia"]),
    "FE": ("A conexão com forças sagradas, divinas ou espirituais: conjura os Feitiços (curas, bênçãos, proteções e ataques).",
           ["Desejo: acerto e DT dos Feitiços", "+1 dado nos Feitiços a cada 30 pontos",
            "Espaços de encantamento: 1 + (Inteligência + Fé) ÷ 6", "Contradomínio: 1 por combate a cada 10 pontos", "Vontade (defesa)",
            "História, Intuição e Religião"]),
    "ARC": ("A afinidade com mistérios ocultos e energias sutis: perceber o extraordinário, ampliar as condições dos seus encantamentos e coordenar o uso de cajado e selo.",
            ["Escalonamento das condições dos encantamentos: 1 cópia dos dados a cada 20 e 1 dado inferior a cada 15",
             "Descoberta: +10 a cada 15 pontos", "Percepção e Sorte", "Coordenação do Uso duplo ao conjurar"]),
}


def efeitos_atributo(k, a, d):
    """O que o valor atual do atributo dá agora na ficha (a: atributos efetivos, d: derivadas)."""
    v = cap(a[k])
    out = [f"Curva {d['curva'][k]} fora de combate (perícias: {1 + v // 20}d20) · Bônus de Combate +{d['bc'][k]}"
           + (" · vantagem em combate" if vantagem(a[k]) else "")]
    if k == "VIT":
        out.append(f"{d['vida_dados']} dados de vida · Vida máxima {d['vida']}")
    elif k == "MEN":
        out.append(f"Mana {d['mana']} · Astúcia +{d['bc']['MEN']} · até {d['pericias_treinadas_max']} perícias treinadas")
    elif k == "TEN":
        out.append(f"CA +{d['ca_ten']} · Redução de Dano {str(d['rd']) + 'd4' if d['rd'] else '—'} · Carga {d['carga']}")
        out.append("Resistências: " + (", ".join(d["resistencias"]) if d["resistencias"] else "nenhuma ainda (a primeira vem com 20)"))
    elif k == "FOR":
        out.append(f"Vigor {d['vigor']} · recupera {d['vigor_regen']} por turno")
    elif k == "DES":
        out.append(f"{d['acoes_extras']} ação(ões) extra(s) · Movimento {d['movimento']} m · Iniciativa {d['iniciativa_dados']}d20 +{d['iniciativa_bonus']}")
        prox = next((t for t in LIMIARES_ACOES if v < t), None)
        if prox:
            out.append(f"Próxima ação extra com {prox} de Destreza.")
    elif k == "INT":
        out.append(f"DT de Feitiçaria {d['dt_feiticaria']} · +{d['dados_extra_magia']} dado(s) nas Magias · {d['espacos_encant']} espaços de encantamento"
                   f" · {d['contra_encant']} contra-encantamento(s) por combate")
    elif k == "FE":
        out.append(f"DT de Desejo {d['dt_desejo']} · +{d['dados_extra_feitico']} dado(s) nos Feitiços · {d['espacos_encant']} espaços de encantamento"
                   f" · Vontade +{d['bc']['FE']}")
    elif k == "ARC":
        out.append(f"Condições dos encantamentos: +{v // 20} cópia(s) dos dados e +{v // 15} dado(s) inferior(es) · Descoberta {d['descoberta']}")
    return out


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
    d["ca"] = max(10, min(CA_MAX, 10 + ca_ten + armadura_ca + escudo_ca + ca_extra))
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
    d["iniciativa_dados"] = 1 + des // 20 + (1 if "Animado" in talentos else 0)
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
def atributo_ataque(arma, a=None):
    """Atributo de ataque da arma. A Lira (3.2) usa Inteligência ou Fé, à escolha: com os atributos (a), vale o maior."""
    alt = arma.get("ataque_alt")
    if alt and a:
        return max(alt, key=lambda k: cap(a[k]))
    return arma["ataque"]


def req_arma(arma, nv, a=None):
    out = {}
    for r in arma["req"]:
        attr = r["attr"]
        if r.get("alt") and a:
            attr = max(r["alt"], key=lambda k: cap(a[k]))
        out[attr] = r["base"] + r["por_nivel"] * (nv - 1)
    return out


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


def rolar_expr(expr, rng, dobrar=False, mult=2):
    """Rola uma expressão como '3d6 + 1d4 + 2'. rng(faces) devolve 1..faces.
    dobrar=True (crítico) rola o dobro de dados; modificadores fixos não dobram.
    Devolve (total, partes) com partes = [(texto, [valores], subtotal)]."""
    total, partes = 0, []
    for m in _TERMO.finditer(expr or ""):
        if m.group(2):
            sinal = -1 if m.group(1) == "-" else 1
            q, f = int(m.group(2)), int(m.group(3))
            q = q * mult if dobrar else q
            vals = [rng(f) for _ in range(q)]
            sub = sinal * sum(vals)
            partes.append((f"{'-' if sinal < 0 else ''}{q}d{f}", vals, sub))
        else:
            sinal = -1 if m.group(4) == "-" else 1
            sub = sinal * int(m.group(5))
            partes.append((f"{sub:+d}", [], sub))
        total += sub
    return total, partes


def rolar_ataque(bonus, com_vantagem, margem, rng, desvantagem=False):
    """1d20 (2d20 com vantagem, fica o maior; com desvantagem, fica o menor; as duas se anulam) + bônus.
    Crítico: natural >= margem (dobra dados); só o 20 acerta garantido. Desastre: natural 1."""
    dois = com_vantagem != desvantagem
    d = [rng(20) for _ in range(2 if dois else 1)]
    nat = min(d) if desvantagem and not com_vantagem else max(d)
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
    ("Sangramento", "Físico", "dano de ferimentos abertos; conta como físico"),
    ("Podridão", "Elemental", "conta como Necrótico para resistências"), ("Congelamento", "Elemental", "conta como Glacial para resistências"),
    ("Psíquico", "Mental", ""), ("Êxtase", "Mental", ""), ("Melódico", "Mental", ""), ("Radiante", "Mental", ""),
    ("Direto", "Outro", "ignora RD e resistências (perda de Vida de condição, quedas…)"),
]
NOMES_DANO = [t[0] for t in TIPOS_DANO]
DANO_SEM_RD = {"Magia Pura", "Relâmpago", "Direto"}
DANO_ALIAS_RESISTENCIA = {"Podridão": "Necrótico", "Congelamento": "Glacial"}   # 3.2: tratados como outro tipo para resistências
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
    if not fragilizado:       # redução de talismãs e sets por tipo de dano (Pele de Ferro, Escama de Dragão, Casco...)
        for r in d.get("rd_tipo", []):
            if tipo in r["tipos"]:
                q, f = (int(x) for x in r["dados"].split("d"))
                rolos = [rng(f) for _ in range(q)]
                red = sum(rolos) + int(r.get("fixo", 0))
                total = max(0, total - red)
                notas.append(f"redução {r['dados']}{'+%d' % r['fixo'] if r.get('fixo') else ''} [{', '.join(map(str, rolos))}] −{red}")
    tipo_res = DANO_ALIAS_RESISTENCIA.get(tipo, tipo)
    if tipo and (tipo in d.get("resistencias", []) or tipo_res in d.get("resistencias", [])) and not fragilizado:
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


def descanso(tipo, maximos, atuais, condicoes, curto_vida_pct=0):
    """tipo 'curto': recupera metade de Vida, Mana e Vigor e 25 pontos de cada condição.
    'longo': recupera tudo e zera as condições. maximos/atuais: {'vida','mana','vigor'};
    condicoes: {nome: acumulado}. Devolve (novos_atuais, novas_condicoes)."""
    novos = {}
    for k, mx in maximos.items():
        at = atuais.get(k, mx)
        extra = mx * curto_vida_pct // 100 if k == "vida" and tipo == "curto" else 0     # set Eremita
        novos[k] = mx if tipo == "longo" else min(mx, at + mx // 2 + extra)
    cond = {n: (0 if tipo == "longo" else max(0, v - CONDICAO_DESCANSO_CURTO)) for n, v in condicoes.items()}
    return novos, cond


def pocao_espiritual_dados(nivel, curva_vit):
    """(metade do nível + metade da Curva da Vitalidade) d10, mínimo 2 dados."""
    return max(2, nivel // 2 + curva_vit // 2)


DESGASTE_TURNOS = 3   # turnos afiados; o crítico reinicia; ao acabar a arma fica 1 turno sem uso


def desgaste_apos_ataque(usados, critico, limite=DESGASTE_TURNOS):
    """Devolve (usados, desgastou). O crítico reinicia a contagem. Reforçada: limite 4."""
    if critico:
        return 0, False
    usados += 1
    return (usados, True) if usados >= limite else (usados, False)


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


def escalar_arcano(expr, arcano, condicao, copias_extra=0):
    """A cada 20 de ARC, uma cópia dos dados de condição; a cada 15, mais 1 dado um tamanho abaixo do
    maior dado (d12→d10→…→d4). Morte só recebe os dados inferiores. Valores fixos não copiam.
    copias_extra: cópias a mais do talento Senhor das Condições (não valem para Morte)."""
    arc = cap(arcano)
    dados = [(int(q), int(f)) for q, f in re.findall(r"(\d+)d(\d+)", expr)]
    fixo = sum(int(x) for x in re.findall(r"\+\s*(\d+)(?!\d|d)", expr))
    if not dados:
        return expr
    copias = 0 if condicao == "Morte" else arc // 20 + copias_extra
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


def arcano_escala(arcano, talentos):
    """Arcano usado no escalonamento e cópias extras: Mente Arcana conta +10; Senhor das Condições dá 1 cópia."""
    return cap(arcano) + (10 if "Mente Arcana" in talentos else 0), (1 if "Senhor das Condições" in talentos else 0)


_SET_COND = re.compile(r"(acertos? cr[íi]ticos?|acerto cr[íi]tico|acertos?)\b[^.]*?\baplica\w* (?:mais )?(\d+) pontos de "
                       r"(Veneno|Podridão|Sangramento|Congelamento|Sono|Loucura|Morte)", re.I)


def condicoes_de_set(ativos):
    """Pontos de condição que os sets aplicam ao acertar. ativos: [(nome, peças, efeito2, efeito4)].
    Devolve [{set, pontos, condicao, critico, nota}]. Os números dos sets são fixos: o Arcano não escala."""
    out = []
    for nome, _, e2, e4 in ativos:
        for txt in (e2, e4):
            for m in _SET_COND.finditer(txt or ""):
                nota = []
                if re.search(r"1x por turno", txt, re.I):
                    nota.append("1x por turno")
                m2 = re.search(r"dobram contra ([^.]+?)\.", e4 or "", re.I)
                if m2:
                    nota.append("dobra contra " + m2.group(1))
                out.append({"set": nome, "pontos": int(m.group(2)), "condicao": m.group(3).capitalize(),
                            "critico": "crít" in m.group(1).lower(), "nota": ", ".join(nota)})
    return out


# Refeições (Gastronomia): nível -> (DT do teste, benefício de quem come, até o próximo descanso longo)
REFEICOES = {
    1: (10, "1d10 de vida temporária para cada 4 níveis do personagem (mínimo 1d10)."),
    2: (20, "Vantagem em um teste à escolha."),
    3: (30, "2d10 de vida temporária para cada 4 níveis (mínimo 2d10) e +20 pontos em uma condição à escolha."),
    4: (40, "Pacote completo: +2 de acerto, +1 de CA e de resistências, 4d10 de vida temporária para cada 4 níveis, "
            "−15% de dano recebido e +1 dado de dano para cada 8 níveis durante 1 combate."),
}


# ---------------- Sets e talismãs: efeitos de valor fixo ----------------
# Cada bloco: "sit": rótulo da condição (o efeito só vale com o interruptor ligado; sem "sit" vale sempre), "txt": o que a ficha mostra,
# e os números. Um número em lista é por nível do talismã (+0 a +3).
#   atr {atributo: n} · per {perícia: n} · def {defesa: n} · ca · mov (m) · mana · vigor · acerto · acerto_dist (Arco, Besta)
#   dano · dano_mag (encantamentos) · dano_nivel · dados [[expr, tipo, alvo]] (alvo: "arma", "mag", "tudo" ou lista de armas)
#   rd [{tipos, dados, fixo}] · espacos · contra · cond {condição: n} · mana_pct · cura [expr] · provocar · curto_vida_pct
#   dano_carga (por 20% de peso) · dano_fome (por Poção Espiritual do grupo) · mov_dobra_carga (10% ou menos de peso)
FISICOS = ["Cortante", "Perfurante", "Impacto"]
EFEITOS_SETS = {
    "Predador": {2: {"sit": "primeiro ataque do combate, alvo que ainda não agiu", "txt": "+3 de acerto (e +1 dado de dano)", "acerto": 3}},
    "Mira": {2: {"sit": "ataque à distância contra alvo a mais de 9 m", "txt": "+3 de acerto", "acerto_dist": 3}},
    "Rancor": {2: {"sit": "com menos de 50% da vida", "txt": "+3 de acerto e +3 de dano", "acerto": 3, "dano": 3}},
    "Anatomista": {2: {"sit": "estudando animais", "txt": "+3 em Investigação e Ciências", "per": {"Investigação": 3, "Ciências": 3}},
                   4: {"sit": "atacando um Ponto Chave revelado", "txt": "+2 de acerto (e +1 dado de dano)", "acerto": 2}},
    "Vento": {2: {"txt": "+4,5 m de deslocamento", "mov": 4.5}, 4: {"txt": "mais +4,5 m de deslocamento (total +9 m)", "mov": 4.5}},
    "Fervor Mortal": {4: {"sit": "com 80 ou mais de Morte", "txt": "+2 de acerto (e +1 dado de dano)", "acerto": 2}},
    "Casco": {2: {"txt": "reduz 1d4 + 3 do dano de um tipo físico (o escolhido)", "rd": [{"tipos": "escolha", "dados": "1d4", "fixo": 3}]},
              4: {"txt": "reduz 1d4 + 5 do dano dos três tipos físicos", "subst": True, "rd": [{"tipos": FISICOS, "dados": "1d4", "fixo": 5}]}},
    "Âncora": {2: {"sit": "não se moveu no seu turno", "txt": "+2 de CA (e −3 de dano por golpe)", "ca": 2}},
    "Esquiva": {2: {"txt": "+3 em Reflexo", "def": {"Reflexo": 3}}},
    "Tenaz": {2: {"txt": "+3 em Fortitude", "def": {"Fortitude": 3}}},
    "Lúcido": {2: {"txt": "+3 em Vontade", "def": {"Vontade": 3}}, 4: {"txt": "+15 de vida de condição em Loucura e Sono", "cond": {"Loucura": 15, "Sono": 15}}},
    "Sanador": {2: {"txt": "+3 em Medicina", "per": {"Medicina": 3}}},
    "Alquimista": {2: {"txt": "+3 em Alquimia", "per": {"Alquimia": 3}}},
    "General": {2: {"txt": "+3 em Tática", "per": {"Tática": 3}}},
    "Agronômico": {2: {"txt": "+3 em Agricultura", "per": {"Agricultura": 3}}},
    "Pecuário": {2: {"txt": "+3 em Adestramento", "per": {"Adestramento": 3}}},
    "Tutor": {2: {"sit": "acalmando ou adestrando um animal", "txt": "+3 em Adestramento", "per": {"Adestramento": 3}}},
    "Fluxo": {2: {"txt": "+15 de mana máxima", "mana": 15}},
    "Alma Prevalente": {2: {"txt": "+3 em Prevalência", "per": {"Prevalência": 3}}},
    "Ocultista": {2: {"txt": "+3 em Religião", "per": {"Religião": 3}}},
    "Rastreador": {2: {"txt": "+3 em Percepção e Investigação", "per": {"Percepção": 3, "Investigação": 3}}},
    "Navegante": {2: {"txt": "+3 em Navegação", "per": {"Navegação": 3}}},
    "Colhedor": {2: {"sit": "coletando recursos", "txt": "+3 em Sorte e Investigação", "per": {"Sorte": 3, "Investigação": 3}}},
    "Banquete": {2: {"txt": "+3 em Gastronomia", "per": {"Gastronomia": 3}}},
    "Tecelão": {2: {"txt": "+3 em Costura", "per": {"Costura": 3}}},
    "Forjador": {2: {"sit": "subindo o nível de uma arma", "txt": "+3 em Tecnologia", "per": {"Tecnologia": 3}}},
    "Eremita": {2: {"txt": "descansos curtos recuperam mais 15% da Vida", "curto_vida_pct": 15}},
    "Voz do Povo": {2: {"sit": "cenas sociais com NPCs", "txt": "+3 em Persuasão e Intuição", "per": {"Persuasão": 3, "Intuição": 3}}},
    "Presença": {2: {"txt": "+3 em testes de Provocar (sobe a DT do Provocar)", "provocar": 3}},
    "Máscara": {2: {"txt": "+3 em Artes (Disfarce) e em Crime", "per": {"Artes": 3, "Crime": 3}}},
    "Mercador": {2: {"sit": "negociando preços", "txt": "+3 em Persuasão", "per": {"Persuasão": 3}}},
}
EFEITOS_TALISMAS = {
    "Insígnia do Berserker": {"sit": "perdeu 25% da vida", "txt": ["+5 em Força", "+7 em Força", "+9 em Força", "+10 em Força"], "atr": {"FOR": [5, 7, 9, 10]}},
    "Medalhão da Dor Oculta": {"sit": "sofrendo Sangramento", "txt": ["+2 em Destreza", "+4 em Destreza", "+6 em Destreza", "+8 em Destreza"], "atr": {"DES": [2, 4, 6, 8]}},
    "Medalhão da Fúria do Guerreiro": {"sit": "derrotou um inimigo (2 turnos)", "txt": ["+2 em Força", "+4 em Força", "+6 em Força", "+8 em Força"], "atr": {"FOR": [2, 4, 6, 8]}},
    "Medalhão da Podridão": {"sit": "aplicou Veneno (2 turnos)", "txt": ["+2 em Arcano", "+4 em Arcano", "+6 em Arcano", "+8 em Arcano"], "atr": {"ARC": [2, 4, 6, 8]}},
    "Pingente da Dor": {"sit": "sofreu um crítico", "txt": ["+2 em Força", "+4 em Força", "+6 em Força", "+8 em Força"], "atr": {"FOR": [2, 4, 6, 8]}},
    "Símbolo da Chaga": {"sit": "está envenenado", "txt": ["+2 em Força", "+4 em Força", "+6 em Força", "+8 em Força"], "atr": {"FOR": [2, 4, 6, 8]}},
    "Pingente da Loucura": {"sit": "sofreu feitiço mental (2 turnos)", "txt": ["+2 em Fé", "+4 em Fé", "+6 em Fé", "+8 em Fé"], "atr": {"FE": [2, 4, 6, 8]}},
    "Relíquia do Místico": {"sit": "lançou uma magia (2 turnos)", "txt": ["+3 em Inteligência", "+5 em Inteligência", "+8 em Inteligência", "+10 em Inteligência"], "atr": {"INT": [3, 5, 8, 10]}},
    "Pingente da Fúria Implacável": {"sit": "causou um crítico", "txt": ["+2 m de movimento", "+4 m de movimento", "+6 m de movimento", "+8 m de movimento"], "mov": [2, 4, 6, 8]},
    "Marca do Caçador": {"txt": ["+1 em ataques à distância", "+2 em ataques à distância", "+3 em ataques à distância", "+4 em ataques à distância"], "acerto_dist": [1, 2, 3, 4]},
    "Marca da Chama": {"txt": ["+1d4 de dano de fogo", "+2d4 de dano de fogo", "+3d4 de dano de fogo", "+4d4 de dano de fogo"], "dados": [[["1d4", "2d4", "3d4", "4d4"], "Fogo", "arma"]]},
    "Medalhão da Lâmina Flamejante": {"txt": ["Espadas: +1d4 de fogo", "Espadas: +2d4 de fogo", "Espadas: +3d4 de fogo", "Espadas: +4d4 de fogo"],
                                      "dados": [[["1d4", "2d4", "3d4", "4d4"], "Fogo", ["Espada", "Espada Grande"]]]},
    "Símbolo da Tempestade": {"txt": ["+1d4 de dano elétrico", "+2d4 de dano elétrico", "+3d4 de dano elétrico", "+4d4 de dano elétrico"], "dados": [[["1d4", "2d4", "3d4", "4d4"], "Elétrico", "tudo"]]},
    "Símbolo do Arcano": {"txt": ["+1d4 em magias elementais", "+2d4 em magias elementais", "+3d4 em magias elementais", "+4d4 em magias elementais"], "dados": [[["1d4", "2d4", "3d4", "4d4"], "Elemental", "mag"]]},
    "Estatueta da Bruxa": {"txt": ["+1d6 em encantamentos de Veneno ou Podridão", "+2d6 em encantamentos de Veneno ou Podridão", "+3d6 em encantamentos de Veneno ou Podridão", "+4d6 em encantamentos de Veneno ou Podridão"],
                           "dados": [[["1d6", "2d6", "3d6", "4d6"], "Veneno/Podridão", "mag"]]},
    "Símbolo da Lâmina Sangrenta": {"sit": "alvo sangrando, arma cortante", "txt": ["+1d4 de dano", "+2d4 de dano", "+3d4 de dano", "+4d4 de dano"], "dados": [[["1d4", "2d4", "3d4", "4d4"], "Cortante", "arma"]]},
    "Anel do Gladiador": {"sit": "até 3 turnos depois de um crítico", "txt": "+2d6 de dano físico", "dados": [["2d6", "Físico", "arma"]]},
    "Insígnia do Lorde de Sangue": {"sit": "aplicou Sangramento (3 turnos)", "txt": "+1 nível de dano das armas", "dano_nivel": 1},
    "Contos de Rhadi": {"sit": "Arco ou Besta em curto alcance", "txt": "+1 de dano nas duas armas", "dano": 1},
    "Estresse acumulado em Frasco": {"sit": "com menos da metade da vida", "txt": "+2 de dano em feitiços e magias", "dano_mag": 2},
    "Símbolo da Carga": {"txt": ["+1 de dano físico a cada 20% de peso", "+2 de dano físico a cada 20% de peso", "+3 de dano físico a cada 20% de peso", "+4 de dano físico a cada 20% de peso"], "dano_carga": [1, 2, 3, 4]},
    "Símbolo da Fome": {"txt": ["+1 de dano por Poção Espiritual gasta pelo grupo", "+2 de dano por Poção Espiritual gasta pelo grupo", "+3 de dano por Poção Espiritual gasta pelo grupo", "+4 de dano por Poção Espiritual gasta pelo grupo"], "dano_fome": [1, 2, 3, 4]},
    "Símbolo da Carne": {"sit": "abaixo de 50% da vida, contra ataques físicos", "txt": ["+1 de CA", "+2 de CA", "+3 de CA", "+4 de CA"], "ca": [1, 2, 3, 4]},
    "Medalhão da Pele de Ferro": {"txt": ["Reduz dano cortante em 1d6", "Reduz dano cortante em 2d6", "Reduz dano cortante em 3d6", "Reduz dano cortante em 4d6"],
                                  "rd": [{"tipos": ["Cortante"], "dados": ["1d6", "2d6", "3d6", "4d6"], "fixo": 0}]},
    "Escama de Dragão": {"txt": ["Reduz dano físico em 1d4", "Reduz dano físico em 2d4", "Reduz dano físico em 3d4", "Reduz dano físico em 4d4"],
                         "rd": [{"tipos": FISICOS, "dados": ["1d4", "2d4", "3d4", "4d4"], "fixo": 0}]},
    "Coração de Pedra": {"txt": ["Redução de Dano 1d4 contra Magia", "Redução de Dano 2d4 contra Magia", "Redução de Dano 3d4 contra Magia", "Redução de Dano 4d4 contra Magia"],
                         "rd": [{"tipos": ["Magia"], "dados": ["1d4", "2d4", "3d4", "4d4"], "fixo": 0}]},
    "Escudo Espiritual": {"txt": "Reduz dano mágico em 2d4", "rd": [{"tipos": ["Magia"], "dados": "2d4", "fixo": 0}]},
    "Amuleto da Regeneração": {"txt": ["Cura 1d8 por turno", "Cura 2d8 por turno", "Cura 3d8 por turno", "Cura 4d8 por turno"], "cura": [["1d8", "2d8", "3d8", "4d8"]]},
    "Pulmão de Ferro": {"txt": "+30 de Vigor máximo", "vigor": 30},
    "Anel das Muitas Vozes": {"txt": "+3 espaços de encantamento (só de Espaço 1 ou 2)", "espacos": 3},
    "Selo da Réplica Voraz": {"txt": "+2 contra-encantamentos", "contra": 2},
    "Pergaminho do Oculto": {"txt": ["Reduz o custo de mana em 5%", "Reduz o custo de mana em 10%", "Reduz o custo de mana em 15%", "Reduz o custo de mana em 20%"], "mana_pct": [5, 10, 15, 20]},
    "Colar do Herbolário": {"txt": "+3 em Alquimia", "per": {"Alquimia": 3}},
    "Símbolo Dançante": {"txt": "dobra o movimento com 10% ou menos do inventário ocupado", "mov_dobra_carga": 10},
}


def _v(x, i):
    """Valor de um nível do talismã (lista) ou valor único."""
    return x[min(i, len(x) - 1)] if isinstance(x, list) else x


def talisma_familia_nivel(nome):
    """'Marca do Caçador +2' -> ('Marca do Caçador', 2); sem sufixo -> (nome, 0)."""
    m = re.match(r"^(.*?)\s*\+(\d)$", nome or "")
    return (m.group(1), int(m.group(2))) if m else (nome or "", 0)


def efeitos_equipamento(sets, talismas, ativos=(), ctx=None):
    """Soma os efeitos fixos dos sets (sets: {nome: peças}; 2 peças dão o bônus de 2, 4 dão também o de 4) e dos talismãs
    equipados (talismas: nomes dentro das vagas). Efeitos com condição ("sit") só entram com o interruptor ligado (chave em `ativos`).
    ctx: {"carga_pct": peso carregado em % da carga, "fome": usos de Poção Espiritual do grupo, "casco": tipo físico do Casco}.
    Tirar a peça ou o talismã tira o efeito: nada fica guardado na ficha."""
    ctx = ctx or {}
    out = {"atr": {}, "per": {}, "def": {}, "ca": 0, "mov": 0, "mana": 0, "vigor": 0, "acerto": 0, "acerto_dist": 0, "dano": 0,
           "dano_mag": 0, "dano_nivel": 0, "dados": [], "rd": [], "espacos": 0, "contra": 0, "cond": {}, "mana_pct": 0, "cura": [],
           "provocar": 0, "curto_vida_pct": 0, "lista": []}
    blocos = []
    for nome in sorted(sets):
        for n in (2, 4):
            fx = EFEITOS_SETS.get(nome, {}).get(n)
            if fx and sets[nome] >= n:
                blocos.append((f"set:{nome}:{n}", f"Set {nome} ({n} peças)", fx, 0, nome))
    for t in talismas:
        fam, idx = talisma_familia_nivel(t)
        if fam in EFEITOS_TALISMAS:
            blocos.append((f"tal:{fam}", t, EFEITOS_TALISMAS[fam], idx, fam))
    for chave, rotulo, fx, i, fonte in blocos:
        sit = fx.get("sit", "")
        ligado = (not sit) or chave in ativos
        out["lista"].append({"chave": chave, "fonte": rotulo, "sit": sit, "ligado": ligado, "txt": _v(fx["txt"], i)})
        if not ligado:
            continue
        for k, v in (fx.get("atr") or {}).items():
            out["atr"][k] = out["atr"].get(k, 0) + _v(v, i)
        for k, v in (fx.get("per") or {}).items():
            out["per"][k] = out["per"].get(k, 0) + _v(v, i)
        for k, v in (fx.get("def") or {}).items():
            out["def"][k] = out["def"].get(k, 0) + _v(v, i)
        for k in ("ca", "mov", "mana", "vigor", "acerto", "acerto_dist", "dano", "dano_mag", "dano_nivel", "espacos", "contra",
                  "mana_pct", "provocar", "curto_vida_pct"):
            if k in fx:
                out[k] += _v(fx[k], i)
        for k, v in (fx.get("cond") or {}).items():
            out["cond"][k] = out["cond"].get(k, 0) + _v(v, i)
        for expr, tipo, alvo in fx.get("dados", []):
            out["dados"].append([_v(expr, i), tipo, alvo])
        for c in fx.get("cura", []):
            out["cura"].append(_v(c, i))
        if "dano_carga" in fx:
            out["dano"] += _v(fx["dano_carga"], i) * int(int(ctx.get("carga_pct", 0)) // 20)
        if "dano_fome" in fx:
            out["dano"] += _v(fx["dano_fome"], i) * max(0, int(ctx.get("fome", 0)))
        if "mov_dobra_carga" in fx and ctx.get("carga_pct", 100) <= fx["mov_dobra_carga"]:
            out["mov"] += ctx.get("mov_base", 0)
        if fx.get("subst"):
            out["rd"] = [r for r in out["rd"] if r["fonte"] != fonte]
        for r in fx.get("rd", []):
            tipos = [ctx.get("casco") or "Cortante"] if r["tipos"] == "escolha" else list(r["tipos"])
            out["rd"].append({"tipos": tipos, "dados": _v(r["dados"], i), "fixo": r["fixo"], "fonte": fonte})
    return out


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



# ---------------- Propriedades de armas (capítulo Equipamentos) ----------------
PROPRIEDADES = [
    ("Afiada", "+1 dado de dano, do maior dado da arma."),
    ("Canalizada", "Ação bônus: vantagem no próximo golpe."),
    ("Certeira", "Margem de crítico da arma −1."),
    ("Cruel", "+3 de dano."),
    ("Destruidora", "O crítico vira ×3 (triplica os dados)."),
    ("Discreta", "+5 em Furtividade com a arma equipada."),
    ("Longa", "Alcance da arma +1,5 m."),
    ("Penetrante", "Ignora redução de dano do tipo da arma igual ao nível da arma."),
    ("Poderosa", "+2 de dano. Exige Cruel."),
    ("Equilibrada", "+1 nos testes de ataque com a arma."),
    ("Pesada", "Dado de dano um nível acima (d8→d10; com d12, +1 dado), mas exige o dobro da Força da arma."),
    ("Sagrada", "+1d6 de dano Sagrado contra profanos, mortos-vivos ou de Podridão."),
    ("Profana", "+1d6 de dano Necrótico contra sagrados ou celestiais."),
    ("Elemental", "+1d6 de dano do elemento escolhido (Fogo, Glacial, Elétrico ou Veneno)."),
    ("Reforçada", "Desgaste só depois de 4 turnos afiados."),
    ("Voraz", "No crítico, recupera 1d10 de Vida."),
]
NOMES_PROPRIEDADES = [p[0] for p in PROPRIEDADES]
ELEMENTOS_PROP = ["Fogo", "Glacial", "Elétrico", "Veneno"]
_DADO_ACIMA = {4: 6, 6: 8, 8: 10, 10: 12}


def ler_props(texto):
    """'Afiada, Elemental (Fogo)' -> ['Afiada', 'Elemental (Fogo)']"""
    return [p.strip() for p in str(texto or "").split(",") if p.strip()]


def nome_prop(p):
    return p.split("(")[0].strip()


def problemas_props(props, maximo):
    """Avisos: acima do limite, repetidas, Poderosa sem Cruel, Elemental sem elemento."""
    nomes = [nome_prop(p) for p in props]
    m = []
    if len(props) > maximo:
        m.append(f"{len(props)} propriedades, o limite é {maximo}")
    rep = sorted({n for n in nomes if nomes.count(n) > 1})
    if rep:
        m.append("repetidas: " + ", ".join(rep))
    if "Poderosa" in nomes and "Cruel" not in nomes:
        m.append("Poderosa exige Cruel")
    if any(nome_prop(p) == "Elemental" and "(" not in p for p in props):
        m.append("Elemental sem elemento")
    return m


def subir_dado(expr):
    """Pesada: cada dado sobe um tamanho; se o maior já é d12, ganha +1 dado de d12."""
    dados = [(int(q), int(f)) for q, f in re.findall(r"(\d+)d(\d+)", expr)]
    if not dados:
        return expr
    if max(f for _, f in dados) >= 12:
        return dano_com_dados(expr, 1)
    return re.sub(r"(\d+)d(\d+)", lambda m: f"{m.group(1)}d{_DADO_ACIMA.get(int(m.group(2)), int(m.group(2)))}", expr)


def efeito_props(props, dano, critico):
    """Aplica as propriedades ao ataque. dano: expressão da tabela (já com dados extras por atributo).
    Devolve {'dano', 'margem', 'mult', 'acerto', 'extras': [(expr, tipo, condição)], 'desgaste', 'voraz', 'furtividade', 'forca_x2'}."""
    nomes = [nome_prop(p) for p in props]
    out = {"dano": dano, "margem": int(critico), "mult": 2, "acerto": 0, "extras": [], "desgaste": DESGASTE_TURNOS,
           "voraz": False, "furtividade": 0, "forca_x2": False}
    if "Pesada" in nomes:
        out["dano"] = subir_dado(out["dano"])
        out["forca_x2"] = True
    if "Afiada" in nomes:
        out["dano"] = dano_com_dados(out["dano"], 1)
    fixo = (3 if "Cruel" in nomes else 0) + (2 if "Poderosa" in nomes and "Cruel" in nomes else 0)
    if fixo:
        out["dano"] = f"{out['dano']} + {fixo}"
    if "Certeira" in nomes:
        out["margem"] -= 1
    if "Destruidora" in nomes:
        out["mult"] = 3
    if "Equilibrada" in nomes:
        out["acerto"] = 1
    if "Reforçada" in nomes:
        out["desgaste"] = 4
    out["voraz"] = "Voraz" in nomes
    if "Discreta" in nomes:
        out["furtividade"] = 5
    for p in props:
        n = nome_prop(p)
        if n == "Elemental":
            el = p[p.find("(") + 1:p.rfind(")")].strip() if "(" in p else ""
            if el:
                out["extras"].append(("1d6", el, ""))
        elif n == "Sagrada":
            out["extras"].append(("1d6", "Sagrado", "contra profanos, mortos-vivos ou de Podridão"))
        elif n == "Profana":
            out["extras"].append(("1d6", "Necrótico", "contra sagrados ou celestiais"))
    return out


def req_com_props(reqs, props):
    """Pesada exige o dobro da Força da arma."""
    if "Pesada" in [nome_prop(p) for p in props] and "FOR" in reqs:
        return dict(reqs, FOR=reqs["FOR"] * 2)
    return reqs



# ---------------- Ações em combate (capítulo Combate) ----------------
TIPOS_ACAO = ["Comum", "Bônus", "Movimento", "Reação"]
ACOES_LIVRO = [  # (nome, tipo, teste, descrição) — teste: "ataque", uma perícia, "provocar" ou ""
    ("Atacar", "Comum", "ataque", "Golpe com arma ou encantamento contra a CA do alvo."),
    ("Agarrar", "Comum", "dt_forca", "O alvo faz Fortitude contra a sua DT; se falhar, fica imóvel e repete o teste no início do turno dele (ação de movimento). Seu movimento cai à metade."),
    ("Derrubar", "Comum", "dt_forca", "O alvo faz Fortitude contra a sua DT; se falhar, fica Caído."),
    ("Preparar", "Comum", "", "Prepara uma ação para um evento que você define; ela gasta a sua Reação."),
    ("Apoiar", "Comum", "", "A criatura apoiada tem vantagem no próximo teste."),
    ("Trocar de arma", "Comum", "", "Guarda uma arma e saca outra. Armas de Vigor gastam também a ação bônus; entre arma e cajado/selo custa só 3 m de movimento."),
    ("Usar item", "Comum", "", "Beber uma poção, comer uma refeição pronta, usar um item ou entregá-lo a 1,5 m."),
    ("Esconder", "Comum", "Furtividade", "Furtividade contra a Percepção de quem vê você; fica escondido até atacar, conjurar ou ser achado."),
    ("Mirar", "Bônus", "", "Vantagem na próxima jogada de ataque contra o alvo declarado."),
    ("Provocar", "Bônus", "provocar", "Alvo a 9 m faz Vontade contra a sua DT (+3); se falhar, tem desvantagem contra quem não for você até o fim do próximo turno dele."),
    ("Movimentar", "Movimento", "", "Anda até o seu valor de movimento."),
    ("Levantar", "Movimento", "", "Sai da condição Caído."),
    ("Desengajar", "Movimento", "", "Anda metade do movimento sem provocar golpe de oportunidade."),
    ("Golpe de Oportunidade", "Reação", "ataque", "Ataque contra quem cruza o espaço de 1,5 m em volta de você."),
    ("Incentivar", "Reação", "", "Um aliado a 1,5 m age logo antes de você neste turno."),
]


def dt_provocar(d, nivel):
    """Provocar (3.2): Vontade do alvo contra 10 + BC de Força + nível ÷ 3 + 3."""
    return 10 + d["bc"]["FOR"] + nivel // 3 + 3 + d.get("provocar_extra", 0)


def dt_forca(d, nivel):
    """Agarrar e Derrubar (3.2): Fortitude do alvo contra 10 + BC de Força + nível ÷ 3."""
    return 10 + d["bc"]["FOR"] + nivel // 3


def rolar_ordem_iniciativa(participantes, rng, primeiro="", tentativas=40):
    """Iniciativa do livro: cada um rola 1d20 (mais 1d20 a cada 20 de Destreza), fica com o maior e soma o Bônus de Combate de
    Destreza. Quem empata rola de novo, só os empatados, até todos terem valores diferentes. O primeiro atacante (quem deu o
    golpe que começou o combate) rola com vantagem (o dobro de dados) e age antes de a tabela começar a rodar.
    participantes: [{"nome", "dados", "bonus"}]. Devolve (ordem [[nome, total, bônus]], detalhe {nome: {rolos, bonus, total, rodadas}})."""
    det = {}

    def rolar(p):
        n = max(1, int(p.get("dados", 1))) * (2 if p["nome"] == primeiro else 1)
        rolos = [rng(20) for _ in range(n)]
        b = int(p.get("bonus", 0))
        d = det.setdefault(p["nome"], {"rolos": [], "bonus": b, "total": 0, "rodadas": 0})
        d.update(rolos=rolos, bonus=b, total=max(rolos) + b, rodadas=d["rodadas"] + 1)

    for p in participantes:
        rolar(p)
    for _ in range(tentativas):
        por_valor = {}
        for p in participantes:
            por_valor.setdefault(det[p["nome"]]["total"], []).append(p)
        empatados = [p for g in por_valor.values() if len(g) > 1 for p in g]
        if not empatados:
            break
        for p in empatados:
            rolar(p)
    ordem = [[p["nome"], det[p["nome"]]["total"], det[p["nome"]]["bonus"]] for p in participantes]
    ordem.sort(key=lambda o: (-o[1], -o[2], o[0]))
    return ordem, det


def acoes_do_turno(acoes_extras, tipos_extras):
    """Ações por turno: 1 de cada + as extras da Destreza, cada uma Comum ou Bônus (escolha fixa do jogador;
    sem escolha conta como Comum). Devolve ({tipo: quantidade}, extras sem tipo escolhido)."""
    q = {"Comum": 1, "Bônus": 1, "Movimento": 1, "Reação": 1}
    faltam = 0
    for i in range(acoes_extras):
        t = tipos_extras[i] if i < len(tipos_extras) else ""
        if t not in ("Comum", "Bônus"):
            faltam += 1
            t = "Comum"
        q[t] += 1
    return q, faltam


# ---------------- Usos limitados (talentos, talismãs, Alma) ----------------
_USOS = re.compile(r"\b(\d+|uma|duas|três)\s*(?:x|vez(?:es)?)\s*por\s*(descanso curto|descanso longo|combate|cena|turno|rodada|dia)\b", re.I)
_NUM_PT = {"uma": 1, "duas": 2, "três": 3}
NIVEL_RECARGA = {"turno": 0, "rodada": 0, "combate": 1, "cena": 1, "descanso curto": 2, "descanso longo": 3, "dia": 3}
EVENTO_RECARGA = {"turno": 0, "combate": 1, "curto": 2, "longo": 3}


def usos_limitados(texto):
    """'1x por combate' -> (1, 'combate'); sem limite -> None (vale o primeiro limite do texto)."""
    m = _USOS.search(texto or "")
    if not m:
        return None
    q = m.group(1).lower()
    return (int(q) if q.isdigit() else _NUM_PT[q], m.group(2).lower())


def recarrega(periodo, evento):
    """O evento ('turno', 'combate', 'curto', 'longo') recarrega usos deste período?
    Descanso longo recarrega tudo; o curto, o que é por descanso curto, combate e turno; o fim do combate, combate e turno."""
    return NIVEL_RECARGA.get(periodo, 3) <= EVENTO_RECARGA[evento]


# ---------------- Ações de arma (botão e rolagem) ----------------
_N_TXT = {"um": 1, "uma": 1, "dois": 2, "duas": 2, "três": 3}
_TIPO_ACAO_RE = [("Completa", r"a[çc][ãa]o completa"), ("Reação", r"\brea[çc][ãa]o\b"), ("Bônus", r"a[çc][ãa]o b[ôo]nus"),
                 ("Comum", r"a[çc][ãa]o comum"), ("Movimento", r"a[çc][ãa]o de movimento"), ("Livre", r"a[çc][ãa]o livre")]
_ATAQUE_RE = re.compile(r"\batac|\bataque|\bgolpe|\bestocada|\bdispar|\bcorte\b|teste de acerto|\btiro\b|explos", re.I)


def acao_arma(nome, texto):
    """Lê uma ação de arma do livro: tipo de ação, se rola ataque, níveis de dano a mais/menos,
    vantagem/desvantagem, crítico garantido, multiplicador e teste de resistência do alvo."""
    t = texto or ""
    tl = t.lower()
    out = {"nome": nome, "acao": "", "ataque": False, "delta": 0, "vantagem": 0, "critico": False,
           "acerto_garantido": False, "mult": 0, "teste": "", "dt_attr": "", "passiva": False, "nota": False}
    pos = [(m.start(), tipo) for tipo, rx in _TIPO_ACAO_RE for m in [re.search(rx, tl)] if m]
    if pos:
        out["acao"] = min(pos)[1]
    automatico = tl.startswith("sempre que") and not re.search(r"pode gastar|pode,? como uma rea", tl)
    out["passiva"] = nome.lower().startswith("passiva") or automatico or nome == "Nota"
    # linhas que só explicam a mecânica da arma (sem nome de ação): "•", frases longas, efeitos das Melodias
    out["nota"] = (nome.strip() in ("•", "Nota", "Acúmulos de Melodia", "Paz", "Calma", "Melancolia") or len(nome) > 34
                   or nome[:1].islower())
    out["ataque"] = bool(_ATAQUE_RE.search(nome + " " + t)) and not out["passiva"]
    if re.search(r"(?:fazem|faz) um teste de \w+ contra a sua dt", tl) and "teste de acerto" not in tl and "rolar" not in tl:
        out["ataque"] = False      # Gritar, Dedicação: o alvo testa contra a DT; não há jogada de ataque
    delta = 0
    for m in re.finditer(r"([+\-−]?\s*\d+|um|uma|dois|duas|três)\s*n[íi]ve(?:l|is)\s*(?:de dano\s*)?(acima|a mais|abaixo|a menos|inferior)?", tl):
        q = m.group(1).replace("−", "-").replace(" ", "")
        n = _N_TXT.get(q, None)
        n = abs(int(q)) if n is None else n
        dirx = m.group(2) or ""
        neg = dirx in ("abaixo", "a menos", "inferior") or q.startswith("-")
        if not dirx and not q.startswith(("+", "-")):
            ctx = tl[max(0, m.start() - 12):m.start()]
            if "+" not in ctx and "-" not in ctx and "−" not in ctx:
                continue
        delta += -n if neg else n
    out["delta"] = delta
    if re.search(r"com vantagem", tl):
        out["vantagem"] = 1
    if re.search(r"com desvantagem", tl):
        out["vantagem"] = -1
    out["critico"] = bool(re.search(r"cr[íi]tico (?:autom[áa]tico|garantido)", tl))
    out["acerto_garantido"] = "acerto garantido" in tl
    m = re.search(r"multiplicador do cr[íi]tico [^.]*?para (\d+)x", tl) or re.search(r"x2\s*->\s*x(\d)", tl)
    if m:
        out["mult"] = int(m.group(1))
    m = re.search(r"teste de (fortitude|reflexos?|vontade|ast[úu]cia)\s*(?:contra a sua )?\(?dt\s*\(?10 \+ b[ôo]nus de combate de (\w+)", tl)
    if m:
        out["teste"] = m.group(1).capitalize()
        out["dt_attr"] = ATR_POR_NOME.get(m.group(2).capitalize(), "")
    else:
        m = re.search(r"(?:resist[êe]ncia com|teste de) (fortitude|reflexos?|vontade|ast[úu]cia)", tl)
        if m:
            out["teste"] = m.group(1).capitalize()
    # vários disparos/golpes e munição gasta (flechas, virotes, cartuchos, frascos)
    out.update(golpes=1, ate=False, um_acerto=False, municao=0, municao_tipo="")
    if out["nota"] or out["passiva"]:
        return out
    num = r"(\d+|uma?|dois|duas|três|quatro|cinco)"
    mun = r"(flechas?|virotes?|cartuchos?|frascos?)"
    m = re.search(r"at[ée] (?:o m[áa]ximo de )?" + num + r" " + mun, tl)
    if m:
        out.update(golpes=_N_EXT.get(m.group(1)) or int(m.group(1)), ate=True)
    else:
        m = re.search(r"gast\w* " + num + r" " + mun + r" em uma (?:[úu]nica )?a[çc][ãa]o", tl)
        if m:
            out["golpes"] = _N_EXT.get(m.group(1)) or int(m.group(1))
    m = re.search(r"(?:gast\w*|consome|disparar?) (?:at[ée] (?:o m[áa]ximo de )?)?" + num + r" " + mun, tl)
    if m:
        out.update(municao=_N_EXT.get(m.group(1)) or int(m.group(1)), municao_tipo=m.group(2).rstrip("s"))
    else:
        m = re.search(r"(?<!at[ée] )(?:gastar|gasta) (?:todas|todos)(?: os)? ?" + mun + r"?", tl)
        if m and (m.group(1) or re.search(mun, tl)):
            out.update(municao=-1, municao_tipo=(m.group(1) or re.search(mun, tl).group(1)).rstrip("s"))
    if out["golpes"] > 1 and not out["municao"]:
        out["municao"] = out["golpes"]
    out["um_acerto"] = out["golpes"] > 1 and bool(re.search(r"[úu]nica jogada de acerto|um [úu]nico teste de acerto|mesmo acerto", tl))
    if out["municao"] > 1 and re.search(r"n[íi]vel de dano para cada (?:flecha|virote|cartucho|frasco)", tl):
        out["delta"] *= out["municao"]
    if out["golpes"] > 1 or out["municao"]:
        out["ataque"] = out["ataque"] or bool(re.search(r"dispar|flecha|virote|explos", tl)) and not out["passiva"]
    return out


_N_EXT = {"um": 1, "uma": 1, "dois": 2, "duas": 2, "três": 3, "quatro": 4, "cinco": 5}


RECURSOS_ARMA = {  # contadores da mecânica de cada arma: (nome, máximo; 0 = sem máximo)
    "Adaga": [("Fragmentos de Combo", 0)],
    "Espada Grande": [("Momentum", 5)],
    "Machado Grande": [("Impacto preparado", 3)],
    "Lança-Arma": [("Cartuchos", 5)],
    "Lâmina-Dínamo": [("Cargas", 5), ("Frascos", 5)],
    "Arco": [("Flechas", 30)],
    "Besta Pesada": [("Virotes", 20)],
    "Lira": [("Paz", 5), ("Calma", 5), ("Melancolia", 5)],
}


def linha_dano_nivel(tabela, nv, delta):
    """Linha da tabela da arma para o nível nv + delta (de 1 a 10). Devolve (linha, nível usado)."""
    alvo = max(1, min(10, nv + delta))
    linha = next((x for x in tabela if x["nivel"] == alvo), None) or tabela[-1]
    return linha, alvo


# ---------------- Alma: montador de habilidades (Tabela de valores) ----------------
ALMA_TABELAS = {
    "Dano em alvo único": ["1d4", "1d6", "2d4", "2d6", "2d8", "3d8", "4d8", "5d8", "6d8", "6d10", "8d10", "9d12"],
    "Dano em múltiplos alvos": ["1d4 (desvantagem)", "1d4", "1d6", "1d8", "1d10", "2d8", "3d6", "3d8", "4d8", "5d8", "6d8", "7d8"],
    "Área": ["1,5 m", "3 m", "4,5 m", "6 m", "7,5 m", "9 m", "10,5 m", "12 m", "13,5 m", "15 m", "16,5 m", "18 m"],
    "Aumento de atributo": ["+1", "+2", "+2", "+3", "+3", "+3", "+4", "+4", "+4", "+5", "+6", "+7"],
    "Redução de dano": ["−1", "−2", "−2", "−2", "−3", "−3", "−3", "−4", "−4", "−4", "−5", "−6"],
    "Redução de margem de crítico": ["−1"] * 4 + ["−2"] * 4 + ["−3"] * 4,
    "Efeito negativo": ["Fraco (−5 DT)", "Fraco", "Fraco", "Fraco", "Fraco", "Médio", "Médio", "Médio", "Médio", "Forte", "Forte", "Extremo"],
}
ALMA_CATEGORIAS = ["Dano", "Benefício", "Ofuscamento", "Interlúdio"]
ALMA_EXECUCAO = ["Comum", "Bônus", "Movimento", "Reação", "Completa", "Livre"]
ALMA_AJUSTES = [  # (nível, texto) — "Facilitando e dificultando habilidades"
    (-2, "Execução como ação bônus"), (-2, "Duração de uma cena"),
    (-1, "+4,5 m de alcance"), (-1, "−3 na DT"), (-1, "Execução como movimento ou reação"), (-1, "Troca do teste de perícia"),
    (-1, "Duração de uma rodada"), (-1, "+1,5 m na área afetada"),
    (1, "Exige um teste extra de outra perícia"), (1, "Execução com +1 ação Comum"), (1, "Reduz um atributo do portador em −5 por rodada"),
    (1, "Causa dano em aliados"), (1, "+3 na DT"), (1, "Redução de dano específico"),
    (2, "Execução como ação completa"), (2, "Aplica um efeito negativo no portador"), (2, "Desvantagem no ataque ou vantagem para resistir"),
]


def alma_nivel_efetivo(nivel_alma, ajustes, n_categorias):
    """Nível da alma + ajustes − 1 por categoria a mais (Mesclando Habilidades), entre 0 e 11."""
    soma = sum(v for v, t in ALMA_AJUSTES if t in set(ajustes))
    return max(0, min(11, nivel_alma + soma - max(0, n_categorias - 1)))


def alma_dt_ajuste(ajustes):
    return (3 if "+3 na DT" in ajustes else 0) - (3 if "−3 na DT" in ajustes else 0)


def alma_valor(tabela, nivel_ef):
    vals = ALMA_TABELAS.get(tabela)
    return vals[max(0, min(11, nivel_ef))] if vals else ""


# ---------------- Metas de Vida (Caminhos de ofício) ----------------
CAMINHOS = [
    ("Costureiro", "Costura", ["Costurar uma peça de um Animal do Andar diante do costureiro mentor.",
                               "Costurar peças de 5 Animais diferentes do Andar.",
                               "Costurar um set completo (Capacete, Peitoral, Manopla, Calça e Bota) com itens de um Prevalecente do Andar."]),
    ("Ferreiro", "Tecnologia", ["Subir uma arma de nível na Bigorna Portátil diante do ferreiro mentor.",
                                "Forjar armas de 3 Animais diferentes do Andar.", "Forjar a arma de um Prevalecente do Andar."]),
    ("Cozinheiro", "Gastronomia", ["Preparar uma refeição de nível 2 diante de um chef.", "Criar 5 receitas novas com ingredientes do Andar.",
                                   "Preparar um Banquete de nível 4 para todo o grupo (exige horta e pasto S, na Base nível 6 ou mais)."]),
    ("Cultivador", "Agricultura", ["Cuidar de uma horta por 2 semanas sem perder nenhuma planta.", "Colher 3 espécies diferentes com qualidade A.",
                                   "Colher uma planta com a qualidade máxima que a Base permite (mínimo A)."]),
    ("Pastor", "Adestramento", ["Adestrar um animal da Base.", "Manter 3 animais produzindo por 4 semanas, sem nenhum rejeitar o dono.",
                               "Obter produto de pasto com a qualidade máxima que a Base permite (mínimo A) de dois animais."]),
    ("Explorador", "Navegação", ["Guiar o grupo em 2 viagens sem se perder.", "Registrar 3 rotas novas do Andar (cada uma vira um Mapa Regional).",
                                "Descobrir o caminho até o covil do Prevalecente de um país do Andar."]),
    ("Pesquisador", "Ciências", ["Estudar 5 animais diferentes no Bestiário.", "Completar o registro de uma região (um Lacaio, um Comum, um Forte e um Animal).",
                                 "Descobrir o Coração, o Ponto Chave do Prevalecente de um país do Andar."]),
    ("Curandeiro", "Medicina", ["Tratar 3 aliados com uma condição ativada.", "Preparar 5 poções ou remédios.",
                                "Curar um mal que atinge uma comunidade inteira do Andar (um contágio, por exemplo)."]),
    ("Alquimista", "Alquimia", ["Preparar uma poção de nível 2 diante do alquimista mentor.", "Preparar poções únicas com itens G de 3 Animais diferentes do Andar.",
                                "Preparar uma poção única de nível 4 com um item de um Prevalecente do Andar (exige Horta S, na Base nível 6 ou mais)."]),
    ("Diplomata", "Persuasão", ["Ganhar a confiança de uma tribo ou facção do Andar.", "Resolver 3 conflitos por negociação, sem violência.",
                                "Unir facções do Andar em torno de uma causa, de modo que 3 NPCs com Funções diferentes aceitem acompanhar o grupo."]),
]
ETAPAS_META = ["Aprendiz", "Prática", "Obra-prima"]
METAS_MAX = 5


def recompensa_metas(concluidas):
    """Cada Meta concluída dá 1 talento extra; a primeira dá também +5 pontos em um atributo."""
    n = max(0, min(METAS_MAX, int(concluidas or 0)))
    return {"talentos": n, "pontos": 5 if n >= 1 else 0}


# ---------------- Dinheiro (Contos) ----------------
CONTOS_POR = {"Contilha": 1000000, "ouro": 1000, "prata": 10, "Contos": 1}   # 10 Contos = 1 de prata; 100 de prata = 1 de ouro; 1000 de ouro = 1 Contilha
MOEDAS = ["Contilha", "ouro", "prata", "Contos"]


def preco_em_contos(texto):
    """'4 Contos de prata' -> 40; '15 Contos' -> 15; '2 Contos de ouro' -> 2000; '1 Contilha' -> 1000000."""
    t = (texto or "").lower()
    m = re.search(r"(\d+)\s*contilhas?", t)
    if m:
        return int(m.group(1)) * CONTOS_POR["Contilha"]
    m = re.search(r"(\d+)\s*contos?\s*de\s*(prata|ouro)", t)
    if m:
        return int(m.group(1)) * CONTOS_POR[m.group(2)]
    m = re.search(r"(\d+)\s*contos?", t)
    return int(m.group(1)) if m else None


def separar_moedas(contos):
    """1234 -> {'Contilha': 0, 'ouro': 1, 'prata': 23, 'Contos': 4}"""
    resto, out = max(0, int(contos or 0)), {}
    for k in MOEDAS:
        out[k], resto = divmod(resto, CONTOS_POR[k])
    return out


def formatar_dinheiro(contos):
    m = separar_moedas(contos)
    partes = [f"{m['Contilha']} Contilha" + ("s" if m["Contilha"] > 1 else "")] if m["Contilha"] else []
    partes += [f"{m[k]} de {k}" for k in ("ouro", "prata") if m[k]]
    if m["Contos"] or not partes:
        partes.append(f"{m['Contos']} Conto" + ("" if m["Contos"] == 1 else "s"))
    return ", ".join(partes)


def ler_dinheiro(texto):
    """Lê um valor escrito à mão ('2 de ouro, 35 de prata', '35 pratas', '120 contos'). Sem número -> None."""
    t = (texto or "").lower()
    if not re.search(r"\d", t):
        return None
    total, achou = 0, False
    for rx, mult in ((r"(\d+)\s*contilhas?", CONTOS_POR["Contilha"]), (r"(\d+)\s*(?:contos?\s*)?(?:de\s*)?ouros?", CONTOS_POR["ouro"]),
                     (r"(\d+)\s*(?:contos?\s*)?(?:de\s*)?pratas?", CONTOS_POR["prata"])):
        for m in re.finditer(rx, t):
            total += int(m.group(1)) * mult
            achou = True
        t = re.sub(rx, " ", t)
    for m in re.finditer(r"(\d+)\s*(?:contos?)?", t):
        total += int(m.group(1))
        achou = True
    return total if achou else None
