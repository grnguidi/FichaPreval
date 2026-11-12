#!/bin/sh
# Confere que as regras do celular (regras.js) dão os mesmos resultados que as do PC (regras.py).
# Requer Python 3 e Node.js.  Uso: sh celular/testes/rodar.sh
cd "$(dirname "$0")" && python3 gen.py >/dev/null && python3 gen2.py >/dev/null && python3 gen3.py >/dev/null && node cmp.js && node cmp2.js && node cmp3.js && rm -f casos.json casos2.json casos3.json dados.json regras_montado.js
