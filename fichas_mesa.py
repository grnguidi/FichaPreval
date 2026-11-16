# -*- coding: utf-8 -*-
"""Fichas da mesa: uma pasta `fichas/` ao lado do programa, com um .json por jogador (o mesmo formato
que o app de celular exporta e o programa de PC abre).

Durante a sessão, o celular do jogador baixa a ficha daqui, devolve cada mudança, e o programa do mestre
avisa o celular quando o arquivo muda por outro caminho (o mestre abriu o .json no PC e salvou, por exemplo).
A "versão" de um arquivo é um hash do conteúdo: quem tem a mesma versão não precisa baixar de novo."""
import hashlib
import json
import os
import re
import shutil
import sys
import threading
import time
import unicodedata

PADRAO = ["Bruno", "Carol", "Kaua", "Enrico", "Guidi"]
LIMITE_BYTES = 3_000_000


def _base():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


PASTA = os.path.join(_base(), "fichas")


def slug(nome):
    """'Kauã Silva' -> 'kaua-silva' (só letras minúsculas, números, '-' e '_'; vazio se não sobrar nada)."""
    t = unicodedata.normalize("NFKD", str(nome or "")).encode("ascii", "ignore").decode("ascii").lower()
    t = re.sub(r"[^a-z0-9_-]+", "-", t).strip("-_")
    return t[:30]


def e_ficha(d):
    return isinstance(d, dict) and isinstance(d.get("identidade"), dict)


class Fichas:
    def __init__(self, pasta=None):
        self.pasta = pasta or PASTA
        self.lock = threading.Lock()
        self._cache = {}          # slug -> ((mtime_ns, tamanho), versão)
        self._pronta = False

    # --- pasta
    def iniciar(self, backup=True):
        """Cria a pasta e os arquivos dos jogadores que faltam; guarda uma cópia datada do que já existe."""
        with self.lock:
            os.makedirs(self.pasta, exist_ok=True)
            for n in PADRAO:
                c = self._caminho(slug(n))
                if not os.path.exists(c):
                    self._escrever(c, {})
            self._pronta = True
        if backup:
            self.backup_da_sessao()

    def _garantir(self):
        if not self._pronta:
            self.iniciar(backup=False)

    def _caminho(self, s):
        return os.path.join(self.pasta, s + ".json")

    def _escrever(self, caminho, dados):
        tmp = caminho + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            json.dump(dados, f, ensure_ascii=False, indent=1)
            f.write("\n")
        os.replace(tmp, caminho)

    def _ler_arq(self, s):
        try:
            with open(self._caminho(s), "rb") as f:
                bruto = f.read()
            d = json.loads(bruto.decode("utf-8-sig"))
            return d if isinstance(d, dict) else {}, bruto
        except (OSError, ValueError):
            return {}, b""

    # --- consulta
    def ver(self, s):
        """Versão atual do arquivo ('' se não existe). Só relê o arquivo se mudou (data/tamanho)."""
        if not s:
            return ""
        self._garantir()
        try:
            st = os.stat(self._caminho(s))
        except OSError:
            return ""
        chave = (st.st_mtime_ns, st.st_size)
        with self.lock:
            c = self._cache.get(s)
            if c and c[0] == chave:
                return c[1]
            _, bruto = self._ler_arq(s)
            v = hashlib.sha1(bruto).hexdigest()[:16]
            self._cache[s] = (chave, v)
            return v

    def ler(self, s):
        """(ficha ou None, versão, data da última mudança em ms)."""
        self._garantir()
        if not s:
            return None, "", 0
        with self.lock:
            d, bruto = self._ler_arq(s)
            try:
                mt = int(os.stat(self._caminho(s)).st_mtime * 1000)
            except OSError:
                mt = 0
        return (d if e_ficha(d) else None), (hashlib.sha1(bruto).hexdigest()[:16] if bruto else ""), mt

    def lista(self):
        """[{'nome', 'slug', 'tem'}]: os jogadores de sempre primeiro, depois qualquer outro .json da pasta."""
        self._garantir()
        out, vistos = [], set()
        for n in PADRAO:
            s = slug(n)
            out.append({"nome": n, "slug": s, "tem": self.ler(s)[0] is not None})
            vistos.add(s)
        try:
            nomes = sorted(os.listdir(self.pasta))
        except OSError:
            nomes = []
        for f in nomes:
            if f.endswith(".json") and f[:-5] not in vistos and slug(f[:-5]) == f[:-5] and f[:-5]:
                s = f[:-5]
                d = self.ler(s)[0]
                nome = ((d or {}).get("identidade", {}).get("player") or "").strip() or s.replace("-", " ").title()
                out.append({"nome": nome, "slug": s, "tem": d is not None})
        return out

    # --- escrita
    def gravar(self, s, ficha, base=None, forcar=False):
        """Grava a ficha de `s`. `base` é a versão que o celular tinha: se o arquivo mudou desde então por outro
        caminho, devolve conflito (a menos que `forcar`). Devolve {'ok', 'ver', 'mtime'} ou {'ok': False, 'conflito': True, ...}."""
        self._garantir()
        if not s or not e_ficha(ficha):
            return {"ok": False, "erro": "ficha inválida"}
        ficha = {k: v for k, v in ficha.items() if k != "_salvo"}
        with self.lock:
            atual_d, bruto = self._ler_arq(s)
            ver_atual = hashlib.sha1(bruto).hexdigest()[:16] if bruto else ""
            existe = e_ficha(atual_d)
            if existe and not forcar and base is not None and base != ver_atual:
                return {"ok": False, "conflito": True, "ver": ver_atual}
            if existe and forcar:
                self._copia(s, bruto, "antes")
            self._escrever(self._caminho(s), ficha)
            self._cache.pop(s, None)
        with self.lock:
            _, bruto = self._ler_arq(s)
            try:
                mt = int(os.stat(self._caminho(s)).st_mtime * 1000)
            except OSError:
                mt = int(time.time() * 1000)
        return {"ok": True, "ver": hashlib.sha1(bruto).hexdigest()[:16], "mtime": mt}

    # --- cópias de segurança
    def _copia(self, s, bruto, rotulo):
        try:
            pasta = os.path.join(self.pasta, "backup")
            os.makedirs(pasta, exist_ok=True)
            with open(os.path.join(pasta, "%s_%s_%s.json" % (s, rotulo, time.strftime("%Y-%m-%d_%H%M%S"))), "wb") as f:
                f.write(bruto)
        except OSError:
            pass

    def backup_da_sessao(self):
        """Cópia datada de todas as fichas com conteúdo, feita quando a mesa abre."""
        try:
            destino = os.path.join(self.pasta, "backup", time.strftime("sessao_%Y-%m-%d_%H%M%S"))
            copiou = False
            for f in sorted(os.listdir(self.pasta)):
                c = os.path.join(self.pasta, f)
                if f.endswith(".json") and os.path.isfile(c) and e_ficha(self._ler_arq(f[:-5])[0]):
                    os.makedirs(destino, exist_ok=True)
                    shutil.copy2(c, os.path.join(destino, f))
                    copiou = True
            return destino if copiou else ""
        except OSError:
            return ""
