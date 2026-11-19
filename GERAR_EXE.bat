@echo off
chcp 65001 >nul
title Gerar ConestogaConnection.exe
cd /d "%~dp0"

set "PY="
where py >nul 2>nul && set "PY=py"
if not defined PY (where python >nul 2>nul && set "PY=python")
if not defined PY (
  echo.
  echo  Python nao encontrado.
  echo  Instale em https://www.python.org/downloads/  ^(marque "Add python.exe to PATH"^)
  echo  e rode este arquivo de novo.
  echo.
  pause
  exit /b 1
)

echo == Instalando PyInstaller e reportlab (PDF)...
%PY% -m pip install --upgrade -r requirements.txt -r requirements-build.txt
if errorlevel 1 goto erro

echo == Gerando o executavel...
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed --collect-all reportlab --hidden-import pdf_ficha --hidden-import assistente --hidden-import sessao --hidden-import ponte_sessao --hidden-import grupo --hidden-import grupo_ui --hidden-import fichas_ui --hidden-import foto --hidden-import paleta --hidden-import tunel --hidden-import regras_texto --hidden-import pagina_celular --hidden-import fichas_mesa --hidden-import bestiario --hidden-import mestre_dados --hidden-import mestre_web --hidden-import pagina_mestre --name ConestogaConnection --icon conestoga.ico --add-data "icone.png;." --add-data "fontes;fontes" prevalecentes.py
if errorlevel 1 goto erro

copy /y "dist\ConestogaConnection.exe" "ConestogaConnection.exe" >nul
rmdir /s /q build >nul 2>nul
rmdir /s /q dist >nul 2>nul
del /q ConestogaConnection.spec >nul 2>nul
echo.
echo  Pronto! ConestogaConnection.exe foi criado nesta pasta.
echo.
pause
exit /b 0

:erro
echo.
echo  Algo deu errado. Leia as mensagens acima.
pause
exit /b 1
