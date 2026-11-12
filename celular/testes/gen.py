import os, sys, json, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import regras as R
from dados_prevalecentes import DADOS
random.seed(7)
TAL_ESP = ["Vida Dura","Mente Infinita","Fôlego de Guerreiro","Mochileiro","Mula de Carga","Pé Ligeiro","Mão Extra","Pele Grossa",
           "Cabeça Cheia","Mente Expandida","Treinado","Colecionador de Talismãs","Relicário"]
casos = []
for i in range(3000):
    a = {k: random.randint(-3, 120) for k in R.ATRIBUTOS}
    nivel = random.randint(1, 30)
    tal = set(random.sample(TAL_ESP, random.randint(0, 5)))
    soma = random.randint(0, 200)
    ca = (random.randint(0, 8), random.randint(0, 3), random.randint(-2, 3))
    d = R.derivadas(a, nivel, tal, soma, *ca)
    per = [R.pericia_fora(a, nivel, atrs or ["ARC"], random.random() < .5) for _, atrs, _ in R.PERICIAS]
    arma = random.choice(DADOS["armas"]); nv = random.randint(1, 10)
    rq = R.req_arma(arma, nv)
    e = random.choice(DADOS["encantamentos"]); v = random.choice(e["versoes"]); impl = random.random() < .3
    ti = random.randrange(len(DADOS["talentos"])); t = DADOS["talentos"][ti]; slot = random.choice(range(2, 31, 2))
    antes = set(x["nome"] for x in random.sample(DADOS["talentos"], 20))
    trein = set(n for n, _, _ in random.sample(R.PERICIAS, 6))
    armas_eq = [x["nome"] for x in random.sample(DADOS["armas"], 2)]
    ja = set(random.sample(sorted(antes), 3))
    sem = random.random() < .5
    casos.append({"in": dict(a=a, nivel=nivel, tal=sorted(tal), soma=soma, ca=ca, arma=arma["nome"], nv=nv, enc=e["nome"], ver=v["nivel"],
                             impl=impl, tal_nome=ti, slot=slot, antes=sorted(antes), trein=sorted(trein), armas_eq=armas_eq, ja=sorted(ja), sem=sem,
                             dano=random.choice(arma["tabela"])["dano"], extra=random.randint(0, 3), pers=[random.random() < .5 for _ in R.PERICIAS]),
                  "out": dict(d={k: (sorted(x.items()) if isinstance(x, dict) else x) for k, x in d.items()},
                              rq=sorted(rq.items()), falta=R.req_falta(rq, a), sv=R.status_versao(v, e["dominio"], a, nivel, impl),
                              st=R.status_talento(t, slot, antes, a, trein, armas_eq, ja), pts=R.pontos_de_nivel(nivel, sem),
                              ganho=R.ganho_no_nivel(nivel, sem), duplo=sorted(R.req_uso_duplo(rq, R.req_arma(DADOS["armas"][0], 1)).items()))})
    # pericias with fixed treinadas flags
    casos[-1]["out"]["per"] = [list(R.pericia_fora(a, nivel, atrs or ["ARC"], f)) for (_, atrs, _), f in zip(R.PERICIAS, casos[-1]["in"]["pers"])]
    casos[-1]["out"]["dano"] = R.dano_com_dados(casos[-1]["in"]["dano"], casos[-1]["in"]["extra"])
json.dump(casos, open('casos.json', 'w'), ensure_ascii=False)
json.dump(DADOS, open('dados.json', 'w'), ensure_ascii=False)
print(len(casos))
