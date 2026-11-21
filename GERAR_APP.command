#!/bin/bash
# Gera ConestogaConnection.app no Mac (equivalente do GERAR_EXE.bat). Duplo clique ou ./GERAR_APP.command
cd "$(dirname "$0")"
. ./_achar_python.sh || exit 1

echo "== Instalando dependências..."
"$PY" -m pip install --upgrade -r requirements.txt -r requirements-build.txt || exit 1

echo "== Gerando o app..."
ICONE=""; [ -f conestoga.icns ] && ICONE="--icon conestoga.icns"
"$PY" -m PyInstaller --noconfirm --clean --windowed --collect-all reportlab \
  --hidden-import pdf_ficha --hidden-import assistente --hidden-import sessao --hidden-import ponte_sessao \
  --hidden-import grupo --hidden-import grupo_ui --hidden-import fichas_ui --hidden-import foto --hidden-import paleta --hidden-import dados_fisicos \
  --hidden-import tunel --hidden-import regras_texto --hidden-import pagina_celular --hidden-import fichas_mesa \
  --hidden-import bestiario --hidden-import mestre_dados --hidden-import mestre_web --hidden-import pagina_mestre \
  --name ConestogaConnection $ICONE --add-data "icone.png:." --add-data "fontes:fontes" prevalecentes.py || exit 1

rm -rf ConestogaConnection.app && mv dist/ConestogaConnection.app . 
rm -rf build dist ConestogaConnection.spec
echo; echo "Pronto! ConestogaConnection.app foi criado nesta pasta."
