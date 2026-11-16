# Testes do celular (regras.js x regras.py)

`rodar.sh` confere que o app de celular calcula igual ao PC. Precisa de Python 3 e Node.js.

| Gerador (Python) | Comparador (Node) | O que cobre |
|---|---|---|
| `gen.py` | `cmp.js` | 3000 fichas aleatórias: atributos, Vida/Mana/Vigor, CA, perícias, ataques |
| `gen2.py` | `cmp2.js` | 2000 casos de equipamento, encantamentos e ações de arma |
| `gen3.py` | `cmp3.js` | 3000 casos das regras novas (propriedades, Alma, Metas) |

Os arquivos `casos*.json` e `dados.json` são temporários (o script apaga) e estão no `.gitignore`.
