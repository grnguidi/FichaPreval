# -*- coding: utf-8 -*-
"""Mesa pela internet: abre um túnel do PC do mestre com o cloudflared (Cloudflare Quick Tunnel).

Não precisa de conta nem de mexer no roteador. O cloudflared é um programa da Cloudflare; se não estiver
no PC, é baixado uma vez (do GitHub oficial) para a pasta ~/.prevalecentes. O endereço muda a cada sessão.
Eventos na fila: ("tunel", estado, texto) com estado em "baixando", "abrindo", "ok", "erro", "fechado".
"""
import os
import platform
import re
import shutil
import subprocess
import sys
import threading
import urllib.request

PASTA = os.path.join(os.path.expanduser("~"), ".prevalecentes")
BASE = "https://github.com/cloudflare/cloudflared/releases/latest/download/"
RE_URL = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


def nome_download():
    """Arquivo do cloudflared para este sistema (None = não há download direto; instale à mão)."""
    arq = platform.machine().lower()
    if sys.platform.startswith("win"):
        return "cloudflared-windows-amd64.exe" if "64" in arq else "cloudflared-windows-386.exe"
    if sys.platform.startswith("linux"):
        return "cloudflared-linux-" + ("arm64" if arq in ("aarch64", "arm64") else "amd64")
    return None   # macOS: brew install cloudflared


def achar():
    """Caminho do cloudflared já presente (ao lado do programa, na pasta do app ou no PATH), ou None."""
    nomes = ["cloudflared.exe", "cloudflared"] + ([nome_download()] if nome_download() else [])
    pastas = [os.path.dirname(os.path.abspath(sys.argv[0] or ".")), os.getcwd(), PASTA]
    for p in pastas:
        for n in nomes:
            c = os.path.join(p, n)
            if os.path.isfile(c) and os.path.getsize(c) > 1_000_000:
                return c
    return shutil.which("cloudflared")


class Tunel:
    def __init__(self, porta, fila, programa=None):
        self.porta, self.fila, self.programa = porta, fila, programa
        self.proc = None
        self.url = ""
        self.estado = "fechado"
        self._parar = False

    def _avisar(self, estado, texto=""):
        self.estado = estado
        self.fila.put(("tunel", estado, texto))

    def precisa_baixar(self):
        return not (self.programa or achar())

    def abrir(self):
        self._parar = False
        threading.Thread(target=self._tarefa, daemon=True).start()

    def _baixar(self):
        nome = nome_download()
        if not nome:
            raise OSError("Instale o cloudflared neste sistema (no macOS: brew install cloudflared).")
        os.makedirs(PASTA, exist_ok=True)
        destino = os.path.join(PASTA, nome)
        req = urllib.request.Request(BASE + nome, headers={"User-Agent": "FichaPrevalecentes"})
        with urllib.request.urlopen(req, timeout=30) as r, open(destino + ".parte", "wb") as f:
            total, lido, ultimo = int(r.headers.get("Content-Length") or 0), 0, -1
            while True:
                bloco = r.read(262144)
                if not bloco:
                    break
                if self._parar:
                    raise OSError("cancelado")
                f.write(bloco)
                lido += len(bloco)
                pct = lido * 100 // total if total else 0
                if pct != ultimo:
                    ultimo = pct
                    self._avisar("baixando", f"{pct}%" if total else f"{lido // 1048576} MB")
        if lido < 1_000_000:
            raise OSError("o download veio incompleto")
        os.replace(destino + ".parte", destino)
        if not sys.platform.startswith("win"):
            os.chmod(destino, 0o755)
        return destino

    def _tarefa(self):
        try:
            prog = self.programa or achar()
            if not prog:
                self._avisar("baixando", "0%")
                prog = self._baixar()
            self._avisar("abrindo")
            extra = {"creationflags": 0x08000000} if sys.platform.startswith("win") else {}   # sem janela preta
            self.proc = subprocess.Popen(
                [prog, "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{self.porta}"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                text=True, encoding="utf-8", errors="replace", **extra)
            ultimas = []
            for linha in self.proc.stdout:
                ultimas = (ultimas + [linha.strip()])[-6:]
                m = RE_URL.search(linha)
                if m and not self.url:
                    self.url = m.group(0)
                    self._avisar("ok", self.url)
            self.proc.wait()
            if self._parar:
                self._avisar("fechado")
            elif self.url:
                self.url = ""
                self._avisar("erro", "O túnel caiu. Abra de novo (o link muda).")
            else:
                self._avisar("erro", "O túnel não abriu. " + " ".join(ultimas)[-220:])
        except (OSError, ValueError) as e:
            self.url = ""
            self._avisar("fechado" if self._parar else "erro", "" if self._parar else f"Não consegui abrir o túnel: {e}")

    def fechar(self):
        self._parar = True
        self.url = ""
        p = self.proc
        if p and p.poll() is None:
            try:
                p.terminate()
            except OSError:
                pass
