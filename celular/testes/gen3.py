"""Casos para as regras novas (dano, condições, descanso, Arcano, carga). Compara com cmp3.js."""
import json, os, random, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(AQUI, ".."), os.path.join(AQUI, "..", "..")]
import regras as R  # noqa: E402
import build  # noqa: E402
from dados_prevalecentes import DADOS  # noqa: E402

open(os.path.join(AQUI, "regras_montado.js"), "w", encoding="utf-8").write(build.regras_js())
rnd = random.Random(7)
descs = [v["descricao"] for e in DADOS["encantamentos"] for v in e["versoes"]]
casos = []
for _ in range(3000):
    fila = [rnd.randint(1, 20) for _ in range(12)]
    it = iter(fila)
    rng = lambda f, it=it: (next(it) - 1) % f + 1  # noqa: E731
    d = {"rd": rnd.randint(0, 4), "resistencias": rnd.sample([x[1] for x in R.RESISTENCIAS], rnd.randint(0, 3))}
    valor, tipo = rnd.randint(-5, 80), rnd.choice(R.NOMES_DANO + [""])
    frag, louc = rnd.random() < .2, rnd.random() < .2
    dano = R.defesas_contra_dano(valor, tipo, d, rng, frag, louc)
    ac, mx, pts, suc = rnd.randint(0, 120), rnd.choice([0, 100, 60]), rnd.randint(0, 90), rnd.random() < .5
    maxs = {"vida": rnd.randint(1, 300), "mana": rnd.randint(0, 200), "vigor": rnd.randint(1, 150)}
    ats = {k: rnd.randint(0, v) for k, v in maxs.items()}
    conds = {c: rnd.randint(0, 100) for c in rnd.sample(R.CONDICOES, 3)}
    tipo_d = rnd.choice(["curto", "longo"])
    desc = rnd.choice(descs)
    arc = rnd.randint(0, 99)
    enc = [[e, c, R.escalar_arcano(e, arc, c)] for e, c in R.condicoes_do_encantamento(desc)]
    pecas = {p: ({"set": rnd.choice(["", "Predador"]), "nome": rnd.choice(["", "x"])}) for p in ("Capacete", "Peitoral", "Manopla", "Calça", "Bota", "Arma")}
    inv = [{"item": rnd.choice(["Mochila", "Tocha", "mochila", "Corda"]), "carga": rnd.choice(["1", "2,5", "", "x"]), "qtd": rnd.choice(["", "3", "0", "a"])} for _ in range(rnd.randint(0, 4))]
    casos.append({"fila": fila, "d": d, "valor": valor, "tipo": tipo, "frag": frag, "louc": louc, "dano": list(dano),
                  "cond": [ac, mx, pts, suc, list(R.receber_condicao(ac, mx, pts, suc))],
                  "desc_tipo": tipo_d, "maxs": maxs, "ats": ats, "conds": conds, "descanso": list(R.descanso(tipo_d, maxs, ats, conds)),
                  "nv": rnd.randint(1, 30), "cv": rnd.randint(0, 60), "desc": desc, "arc": arc, "enc": enc,
                  "pecas": pecas, "peso_set": R.peso_pecas_set(pecas), "inv": inv, "extra": R.carga_extra_itens(inv, DADOS["itens"]),
                  "peso_inv": R.peso_inventario(inv)})
    casos[-1]["pocao"] = R.pocao_espiritual_dados(casos[-1]["nv"], casos[-1]["cv"])
    nomes_esc = list(R.ESCOLHA_TALENTO) + ["Matrícula Suprema", "Arma de família", "Vida Dura", ""]
    slots = {str(2 * i + 2): rnd.choice(nomes_esc) for i in range(rnd.randint(0, 8))}
    if rnd.random() < .3: slots["extra"] = rnd.choice(nomes_esc)
    opc = ["Espada", "Adaga", "Magias Lunares", "Feitiços de Fogo", R.MATRICULA_MANA2, "Veneno", "Sono", "Acrobacia", ""]
    escolhas = {sl: rnd.choice(opc) for sl in slots if rnd.random() < .85}
    esc = R.efeitos_escolhas(slots, escolhas)
    escola, mana = rnd.choice(["Magias Lunares", "Feitiços de Fogo", "Magias de Morte"]), rnd.choice([None, 0, 1, 3, 10])
    esp = rnd.randint(1, 4)
    props = rnd.sample(R.NOMES_PROPRIEDADES + ["Elemental (Fogo)", "Elemental (Veneno)", "Sagrada", "Inventada"], rnd.randint(0, 5))
    arma = rnd.choice(DADOS["armas"]); linha = rnd.choice(arma["tabela"])
    casos[-1].update(props=props, linha_dano=linha["dano"], linha_crit=linha["critico"],
                     ef_props=R.efeito_props(props, linha["dano"], linha["critico"]), mx_props=(mxp := rnd.randint(0, 5)), prob_props=R.problemas_props(props, mxp),
                     req_props=R.req_com_props(R.req_arma(arma, linha["nivel"]), props), req_arma=R.req_arma(arma, linha["nivel"]))
    casos[-1].update(slots=slots, escolhas=escolhas, esc=esc, escola=escola, mana=mana, esp=esp,
                     desconto=list(R.desconto_matricula(esc, escola, mana, esp)))
acoes = [[x["nome"], x["texto"], R.acao_arma(x["nome"], x["texto"])] for a in DADOS["armas"] for x in a.get("acoes") or []]
textos = [t["descricao"] for t in DADOS["talentos"]] + [t.get("efeito", "") for t in DADOS["talismas"]]
usos = [[t, list(R.usos_limitados(t) or []) or None] for t in textos]
extras = []
for _ in range(500):
    n = rnd.randint(0, 8); tipos = [rnd.choice(["Comum", "Bônus", "", "x"]) for _ in range(rnd.randint(0, 9))]
    nv, aj, nc = rnd.randint(0, 10), rnd.sample([t for _, t in R.ALMA_AJUSTES], rnd.randint(0, 4)), rnd.randint(1, 4)
    ne = R.alma_nivel_efetivo(nv, aj, nc)
    tab = rnd.choice(list(R.ALMA_TABELAS))
    c = rnd.choice([0, 7, 99, 1234, 56789, 2000000, 1000999])
    txt = rnd.choice(["2 de ouro, 35 de prata", "35 pratas", "120 contos", "1 Contilha e 3 ouros", "muito", "", "12", "4 Contos de prata"])
    extras.append({"n": n, "tipos": tipos, "turno": list(R.acoes_do_turno(n, tipos)), "nv": nv, "aj": aj, "nc": nc, "ne": ne, "tab": tab,
                   "val": R.alma_valor(tab, ne), "dtaj": R.alma_dt_ajuste(aj), "c": c, "sep": R.separar_moedas(c), "fmt": R.formatar_dinheiro(c),
                   "txt": txt, "ler": R.ler_dinheiro(txt), "preco": R.preco_em_contos(txt), "metas": R.recompensa_metas(rnd.randint(-1, 7)),
                   "metas_in": None})
    extras[-1]["metas_in"] = rnd.randint(-1, 7); extras[-1]["metas"] = R.recompensa_metas(extras[-1]["metas_in"])
sets_t = []
for _ in range(300):
    at = [(x["nome"], q, x["p2"], x["p4"] if q >= 4 else "") for x in rnd.sample(DADOS["sets"], rnd.randint(0, 4)) for q in [rnd.choice([2, 3, 4])]]
    arc, tal = rnd.randint(0, 120), rnd.sample(["Mente Arcana", "Senhor das Condições", "Outro"], rnd.randint(0, 3))
    ex = rnd.choice(["2d6 + 1", "1d8", "3d12 + 2d4 + 5", "2d10"]); cn = rnd.choice(["Morte", "Veneno", "Sono"])
    ae = list(R.arcano_escala(arc, set(tal)))
    sets_t.append({"at": at, "conds": R.condicoes_de_set(at), "arc": arc, "tal": tal, "ae": ae, "ex": ex, "cn": cn,
                   "esc": R.escalar_arcano(ex, ae[0], cn, ae[1])})
equip_t = []
fam_tal = [t["nome"] for t in DADOS["talismas"]]
for _ in range(400):
    sets_q = {x["nome"]: rnd.choice([1, 2, 3, 4]) for x in rnd.sample(DADOS["sets"], rnd.randint(0, 8))}
    tals = rnd.sample(fam_tal, rnd.randint(0, 6))
    chaves = [f"set:{n}:{k}" for n in sets_q for k in (2, 4)] + [f"tal:{R.talisma_familia_nivel(t)[0]}" for t in tals]
    ativos = rnd.sample(chaves, rnd.randint(0, len(chaves))) if chaves else []
    ctx = {"carga_pct": rnd.randint(0, 100), "fome": rnd.randint(0, 6), "casco": rnd.choice(["", "Impacto", "Perfurante"]), "mov_base": rnd.choice([9, 12, 15])}
    r_ = R.efeitos_equipamento(sets_q, tals, set(ativos), ctx)
    fila_ = [rnd.randint(1, 20) for _ in range(40)]
    it_ = iter(fila_)
    d_ = {"rd": rnd.randint(0, 3), "resistencias": [], "rd_tipo": r_["rd"]}
    valor_, tipo_ = rnd.randint(1, 90), rnd.choice(R.NOMES_DANO)
    dano_ = list(R.defesas_contra_dano(valor_, tipo_, d_, lambda f, it=it_: (next(it) - 1) % f + 1))
    pct_, tp_ = rnd.randint(0, 30), rnd.choice(["curto", "longo"])
    mx_ = {"vida": 100, "mana": 50, "vigor": 20}
    equip_t.append({"sets": sets_q, "tals": tals, "ativos": ativos, "ctx": ctx, "r": r_, "fila": fila_, "d": d_, "valor": valor_, "tipo": tipo_,
                    "dano": dano_, "pct": pct_, "tp": tp_, "mx": mx_, "desc": list(R.descanso(tp_, mx_, {"vida": 10, "mana": 5, "vigor": 3}, {}, pct_))})
corpo_t = []
for _ in range(600):
    c = R.corpo_padrao(rnd.randint(0, 4), rnd.randint(0, 4), rnd.randint(0, 4))
    for t in ("olhos", "bracos", "pernas"):
        for m in c[t]:
            m["perdido"] = rnd.random() < .35
            if t == "bracos": m["mao"] = rnd.random() < .7
    if rnd.random() < .3: c["outros"] = [{"nome": "Cauda", "perdido": rnd.random() < .5}]
    if rnd.random() < .1: c = rnd.choice([None, {}, {"olhos": "x"}, []])
    pm = R.penalidades_membros(c)
    g, des = rnd.choice(DADOS["armas"])["nome"], rnd.randint(0, 99)
    dano = rnd.choice(["1d8", "2d6 + 1d4", "3d10+2", "5", "1d4 + 1"])
    corpo_t.append({"c": c, "norm": R.normalizar_corpo(c), "p": pm, "g": g, "des": des, "arma": list(R.penalidade_arma_membros(pm, g, des)),
                    "mov": R.movimento_com_membros(rnd.choice([9, 12, 15]), pm), "mov_in": None, "sort": [list(x) for x in R.membros_para_sortear(c)],
                    "dano": dano, "tirar": R.tirar_dado(dano), "grau": (gr := rnd.choice([0, 1, 2, 3, 4, 5, 7, "x"] if False else [0, 1, 2, 3, 4, 5, 7])),
                    "ig": (ig := rnd.random() < .5), "poder": R.poderes_culto(gr, ig), "fe": (fe := rnd.randint(0, 120)), "nv": (nv := rnd.randint(1, 30)),
                    "dtm": R.dt_milagre({"FE": fe}, nv)})
    corpo_t[-1]["mov_in"] = None
rec = [[p_, e, R.recarrega(p_, e)] for p_ in list(R.NIVEL_RECARGA) for e in R.EVENTO_RECARGA]
json.dump({"casos": casos, "itens": DADOS["itens"], "acoes": acoes, "usos": usos, "extras": extras, "rec": rec, "sets": sets_t, "equip": equip_t, "corpo": corpo_t}, open(os.path.join(AQUI, "casos3.json"), "w", encoding="utf-8"), ensure_ascii=False)
print(len(casos), "casos")
