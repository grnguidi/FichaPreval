# -*- coding: utf-8 -*-
"""Fichas da mesa: uma pasta `fichas/` ao lado do programa, com um .json por jogador (o mesmo formato
que o app de celular exporta e o programa de PC abre).

Durante a sessão, o celular do jogador baixa a ficha daqui, devolve cada mudança, e o programa do mestre
avisa o celular quando o arquivo muda por outro caminho (o mestre abriu o .json no PC e salvou, por exemplo).
A "versão" de um arquivo é um hash do conteúdo: quem tem a mesma versão não precisa baixar de novo.

O mestre é quem cuida da lista (criar, importar e excluir fichas, pela janela "Fichas da mesa" da sessão):
`_mesa.json` guarda o nome de exibição de cada ficha e quem é o dono. Os nomes de PADRAO nascem sempre; o mestre
acrescenta outros. Uma ficha fica presa ao primeiro jogador que a escolhe: ele cria um código, e só entra de novo
quem souber o código, até o mestre liberar."""
import base64
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
        d = os.path.dirname(sys.executable)
        if sys.platform == "darwin" and ".app/Contents/MacOS" in d:   # Mac: pasta onde está o .app
            d = os.path.dirname(os.path.dirname(os.path.dirname(d)))
        return d
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
        """Cria a pasta e os arquivos dos jogadores de sempre que faltam (as outras fichas, quem cria é o mestre);
        guarda uma cópia datada do que já existe."""
        with self.lock:
            os.makedirs(self.pasta, exist_ok=True)
            ind = self._indice()
            for n in PADRAO:
                c = self._caminho(slug(n))
                if not os.path.exists(c):
                    self._escrever(c, {})
                ind.setdefault("nomes", {}).setdefault(slug(n), n)
            self._gravar_indice(ind)
            self._pronta = True
        if backup:
            self.backup_da_sessao()

    def _garantir(self):
        if not self._pronta:
            self.iniciar(backup=False)

    def _caminho(self, s):
        return os.path.join(self.pasta, s + ".json")

    def caminho(self, s):
        """Caminho do .json de uma ficha (para o mestre abrir no programa)."""
        return self._caminho(s)

    # --- índice (_mesa.json): nome de exibição de cada ficha
    def _indice(self):
        try:
            with open(os.path.join(self.pasta, "_mesa.json"), encoding="utf-8") as f:
                d = json.load(f)
            return d if isinstance(d, dict) else {}
        except (OSError, ValueError):
            return {}

    def _gravar_indice(self, ind):
        try:
            self._escrever(os.path.join(self.pasta, "_mesa.json"), ind)
        except OSError:
            pass

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

    def resumo(self, s):
        """O que a lista mostra de uma ficha: {'tem', 'personagem', 'nivel', 'player', 'foto'}; 'foto' é a versão
        do arquivo quando a ficha tem foto ('' se não tem). Guardado por versão, para não reler a cada consulta."""
        v = self.ver(s)
        with self.lock:
            c = self._cache.get(("resumo", s))
            if c and c[0] == v:
                return dict(c[1])
        d = self.ler(s)[0]
        idt = (d or {}).get("identidade") or {}
        foto = (d or {}).get("foto")
        r = {"tem": d is not None, "personagem": str(idt.get("nome") or "").strip()[:60], "nivel": idt.get("nivel") or "",
             "player": str(idt.get("player") or "").strip()[:40],
             "foto": v if isinstance(foto, str) and foto.startswith("data:image/") else ""}
        with self.lock:
            self._cache[("resumo", s)] = (v, r)
        return dict(r)

    def foto(self, s):
        """(bytes, tipo MIME) da foto da ficha, ou (None, '')."""
        d = self.ler(s)[0] if s else None
        f = (d or {}).get("foto")
        if not isinstance(f, str) or not f.startswith("data:image/") or ";base64," not in f[:40]:
            return None, ""
        try:
            cab, b64 = f.split(",", 1)
            tipo = cab[5:].split(";")[0]
            if tipo not in ("image/jpeg", "image/png", "image/gif", "image/webp"):
                return None, ""
            return base64.b64decode(b64), tipo
        except (ValueError, TypeError):
            return None, ""

    def nome(self, s):
        ind = self._indice().get("nomes") or {}
        if ind.get(s):
            return str(ind[s])
        return self.resumo(s)["player"] or s.replace("-", " ").title()

    def lista(self):
        """[{'nome', 'slug', 'tem', 'personagem', 'nivel', 'foto'}]: toda ficha .json da pasta, na ordem em que o
        mestre as criou (as de sempre primeiro)."""
        self._garantir()
        ind = self._indice()
        nomes, donos = (ind.get("nomes") or {}), {k for k, v in (ind.get("donos") or {}).items() if isinstance(v, dict) and v.get("codigo")}
        try:
            arqs = sorted(f[:-5] for f in os.listdir(self.pasta) if f.endswith(".json") and f[:-5] and slug(f[:-5]) == f[:-5])
        except OSError:
            arqs = []
        ordem = [s for s in nomes if s in arqs] + [s for s in arqs if s not in nomes]
        out = []
        for s in ordem:
            r = self.resumo(s)
            out.append({"nome": str(nomes.get(s) or r["player"] or s.replace("-", " ").title()), "slug": s, "tem": r["tem"],
                        "personagem": r["personagem"], "nivel": r["nivel"], "foto": r["foto"], "presa": s in donos})
        return out

    # --- o mestre cuida da lista
    def criar(self, nome, dados=None):
        """Cria uma ficha da mesa (vazia, ou já com o conteúdo de um .json). Devolve o slug, ou '' se o nome não serve."""
        self._garantir()
        base = slug(nome)
        if not base:
            return ""
        with self.lock:
            s, n = base, 2
            while os.path.exists(self._caminho(s)):
                s, n = "%s-%d" % (base[:27], n), n + 1
            self._escrever(self._caminho(s), {k: v for k, v in dados.items() if k != "_salvo"} if e_ficha(dados) else {})
            ind = self._indice()
            ind.setdefault("nomes", {})[s] = str(nome).strip()[:40]
            self._gravar_indice(ind)
        return s

    # --- dono: a ficha fica presa ao primeiro jogador que a escolhe (ele cria um código)
    def dono(self, s):
        """{'codigo', 'quando'} de quem escolheu a ficha, ou None se ela está livre."""
        d = (self._indice().get("donos") or {}).get(s)
        return dict(d) if isinstance(d, dict) and d.get("codigo") else None

    def conferir_dono(self, s, codigo):
        """'' se pode entrar; 'codigo' se falta criar o código (ficha livre); 'presa' se a ficha é de outra pessoa.
        Na primeira escolha, o código informado passa a ser o da ficha."""
        codigo = str(codigo or "").strip()[:12]
        with self.lock:
            ind = self._indice()
            d = (ind.get("donos") or {}).get(s)
            if isinstance(d, dict) and d.get("codigo"):
                return "" if codigo == d["codigo"] else "presa"
            if len(codigo) < 3:
                return "codigo"
            ind.setdefault("donos", {})[s] = {"codigo": codigo, "quando": time.strftime("%d/%m/%Y %H:%M")}
            self._gravar_indice(ind)
            return ""

    def liberar(self, s):
        """O mestre solta a ficha: o próximo que a escolher vira o dono (o conteúdo continua)."""
        with self.lock:
            ind = self._indice()
            if (ind.get("donos") or {}).pop(s, None) is None:
                return False
            self._gravar_indice(ind)
            return True

    def fixa(self, s):
        return s in {slug(n) for n in PADRAO}

    def excluir(self, s):
        """Tira a ficha da mesa; o arquivo vai para fichas/backup/ (nada se perde). As fichas de sempre (PADRAO)
        não saem da lista: só são esvaziadas."""
        self._garantir()
        if not s or slug(s) != s:
            return False
        if self.fixa(s):
            with self.lock:
                d, bruto = self._ler_arq(s)
                if e_ficha(d):
                    self._copia(s, bruto, "excluida")
                self._escrever(self._caminho(s), {})
                ind = self._indice()
                (ind.get("donos") or {}).pop(s, None)
                self._gravar_indice(ind)
                self._cache.pop(s, None)
                self._cache.pop(("resumo", s), None)
            return True
        with self.lock:
            try:
                with open(self._caminho(s), "rb") as f:
                    bruto = f.read()
            except OSError:
                return False
            if e_ficha(self._ler_arq(s)[0]):
                self._copia(s, bruto, "excluida")
            try:
                os.remove(self._caminho(s))
            except OSError:
                return False
            ind = self._indice()
            (ind.get("nomes") or {}).pop(s, None)
            (ind.get("donos") or {}).pop(s, None)
            self._gravar_indice(ind)
            self._cache.pop(s, None)
            self._cache.pop(("resumo", s), None)
        return True

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
