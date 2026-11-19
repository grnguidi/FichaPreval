#!/bin/bash
# Abre o Conestoga connection no Mac (duplo clique). Na 1ª vez, instala as dependências.
cd "$(dirname "$0")"

. ./_achar_python.sh || exit 1

if ! "$PY" -c "import reportlab, segno, PIL" 2>/dev/null; then
  echo "== Instalando dependências (só na primeira vez)..."
  "$PY" -m pip install --user -r requirements.txt || { read -n 1 -s -r -p "Falhou. Tecle algo..."; exit 1; }
fi

exec "$PY" prevalecentes.py
