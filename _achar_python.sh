# Usado por INICIAR.command e GERAR_APP.command: define $PY com um Python 3 cujo tkinter abre janela.
# (O Python que vem com as Ferramentas de Linha de Comando da Apple tem um Tk 8.5 que trava em alguns macOS.)
PY=""
for c in /Library/Frameworks/Python.framework/Versions/Current/bin/python3 \
         /Library/Frameworks/Python.framework/Versions/3.*/bin/python3 \
         /usr/local/bin/python3.13 /usr/local/bin/python3.12 /usr/local/bin/python3.11 /usr/local/bin/python3.10 \
         /opt/homebrew/bin/python3.13 /opt/homebrew/bin/python3.12 /opt/homebrew/bin/python3.11 /opt/homebrew/bin/python3.10 \
         python3.13 python3.12 python3.11 python3 python; do
  p="$(command -v "$c" 2>/dev/null)" || continue
  if "$p" -c "import tkinter; tkinter.Tk().destroy()" >/dev/null 2>&1; then PY="$p"; break; fi
done
if [ -z "$PY" ]; then
  echo "Não achei um Python 3 com tkinter funcionando."
  echo "Instale o Python de https://www.python.org/downloads/macos/ (instalador 'universal2') e rode de novo."
  echo "(O Python da Apple/Xcode tem um Tk antigo que não abre janelas neste macOS.)"
  read -n 1 -s -r -p "Tecle algo para fechar..."; exit 1
fi
