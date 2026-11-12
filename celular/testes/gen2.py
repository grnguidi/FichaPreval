import os, sys, json, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import regras as R
from dados_prevalecentes import DADOS
random.seed(3)
casos = []
nomes = list(R.EFEITOS_TALENTOS) + ['Vida Dura', 'Treinado']
for i in range(2000):
    seq = [random.randint(1, 100) for _ in range(80)]
    it = iter(seq); rng = lambda f: (next(it) % f) + 1
    expr = random.choice(['3d6 + 1d4 + 2', '2d8+3', '1d6 - 1', '10d10', '4d6 + 2', 'abc', '2 d 6+1'])
    dob = random.random() < .5
    tot, partes = R.rolar_expr(expr, rng, dob)
    it2 = iter(seq); rng2 = lambda f: (next(it2) % f) + 1
    mg = random.randint(16, 20); atk = R.rolar_ataque(random.randint(0, 12), random.random() < .5, mg, rng2)
    tal = set(random.sample(nomes, 6)); ativos = set(random.sample(sorted(tal), 3)); arm = random.choice(['', 'Armadura Leve', 'Armadura Pesada'])
    v = random.choice([v for e in DADOS['encantamentos'] for v in e['versoes']])
    casos.append({'seq': seq, 'expr': expr, 'dob': dob, 'atk_in': [atk['bonus'], len(atk['d20']) == 2, None], 'tal': sorted(tal), 'ativos': sorted(ativos), 'arm': arm,
                  'desc': v['descricao'], 'mana': v['mana'],
                  'out': {'expr': [tot, [list(p) for p in partes]], 'atk': atk, 'ef': R.efeitos_talentos(tal, ativos, arm),
                          'dano': R.dano_do_encantamento(v['descricao']), 'custo': R.custo_mana(v)}})
    casos[-1]['atk_in'][2] = mg
# margem guardada: recompute with stored
for c in casos:
    pass
json.dump(casos, open('casos2.json', 'w'), ensure_ascii=False)
