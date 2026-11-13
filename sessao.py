# -*- coding: utf-8 -*-
"""Sessão de jogo em rede local: jogadores "levantam a mão" e o mestre recebe o aviso.

O mestre abre um servidor TCP (porta 5757 por padrão) e os jogadores se conectam pelo IP dele.
Só usa a biblioteca padrão do Python. Mensagens: JSON, uma por linha.
"""
import json
import queue
import random
import socket
import threading
import time
import tkinter as tk
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from tkinter import ttk, messagebox
from urllib.parse import parse_qs, urlparse

try:
    import segno   # QR code (pip install segno); sem ele o app funciona, só não mostra o QR
except ImportError:
    segno = None
try:
    from pagina_celular import HTML as PAGINA_FICHA   # ficha completa do celular (gerada por celular/build.py)
except ImportError:
    PAGINA_FICHA = None

import regras as R
try:
    from dados_prevalecentes import DADOS as _DADOS
    ITENS_LIVRO = _DADOS.get("itens", [])
except ImportError:
    ITENS_LIVRO = []

TIPOS_DANO = R.NOMES_DANO                                   # os 16 tipos do livro + "Direto"
EFEITOS = {n: (g, d) for n, g, d in R.EFEITOS_LIVRO}       # efeitos do livro com gravidade e descrição
CONDICOES_SUGERIDAS = [n for n, _, _ in R.EFEITOS_LIVRO]
CAMPOS_FICHA = {"personagem": str, "especie": str, "nivel": int, "vida": int, "vida_max": int, "mana": int,
                "mana_max": int, "vigor": int, "vigor_max": int, "ca": int, "movimento": int, "iniciativa": int,
                "iniciativa_dados": int, "rd": int, "portao": list, "condicoes": list, "sem_alma": bool,
                "inventario": list, "defesas": dict, "resistencias": list, "dinheiro": str, "carga": list}


def limpar_ficha(dados):
    """Aceita só os campos conhecidos do resumo da ficha (dados vindos da rede não são confiáveis)."""
    out = {}
    if not isinstance(dados, dict):
        return out
    for k, tipo in CAMPOS_FICHA.items():
        v = dados.get(k)
        try:
            if tipo is str:
                out[k] = str(v or "")[:40]
            elif tipo is int:
                out[k] = int(v or 0)
            elif tipo is bool:
                out[k] = bool(v)
            elif k == "portao" and isinstance(v, list):
                out[k] = [int(x) for x in v[:2]]
            elif k == "condicoes" and isinstance(v, list):
                out[k] = [[str(c[0])[:20], int(c[1]), int(c[2])] for c in v[:10] if isinstance(c, list) and len(c) == 3]
            elif k == "inventario" and isinstance(v, list):
                out[k] = [{"item": str(i.get("item", ""))[:40], "carga": str(i.get("carga", ""))[:8],
                           "qtd": max(1, int(i.get("qtd") or 1))} for i in v[:40] if isinstance(i, dict)]
            elif k == "defesas" and isinstance(v, dict):
                out[k] = {n: [int(x[0]), bool(x[1])] for n, x in v.items()
                          if n in ("Fortitude", "Reflexo", "Astúcia", "Vontade") and isinstance(x, list) and len(x) == 2}
            elif k == "resistencias" and isinstance(v, list):
                out[k] = [str(x)[:20] for x in v[:12]]
            elif k == "carga" and isinstance(v, list):
                out[k] = [float(x) for x in v[:2]]
        except (TypeError, ValueError):
            continue
    return out

PORTA = 5757
PORTA_ANUNCIO = 5758   # UDP: o mestre anuncia a sessão e os jogadores a encontram sozinhos
PORTA_WEB = 5760       # HTTP: página para o celular (navegador) levantar a mão
# Celulares: o navegador pausa a página quando a tela bloqueia ou o app vai para segundo plano.
# Por isso o jogador só é marcado "sem sinal" depois de SEM_SINAL s e só sai da mesa (com a mão)
# depois de SAI_DA_MESA s sem nenhum contato.
SEM_SINAL = 20
SAI_DA_MESA = 600

PAGINA_WEB = """<!doctype html>
<html lang="pt-br"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>Prevalecentes — Sessão</title>
<style>
*{box-sizing:border-box}
body{margin:0;min-height:100vh;background:#1b2520;color:#e8dec5;font-family:Georgia,serif;
 display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px;text-align:center}
h1{color:#dcc387;margin:0 0 6px;font-size:26px}
p{color:#9fae9f;font-style:italic;margin:0 0 22px}
input{width:100%;max-width:340px;padding:14px;font-size:18px;border-radius:8px;border:1px solid #4b5d50;
 background:#fbf7ea;color:#2d2015;text-align:center;font-family:inherit}
button{width:100%;max-width:340px;border:0;border-radius:14px;font-family:inherit;font-weight:bold;cursor:pointer}
#entrar{margin-top:14px;padding:16px;font-size:18px;background:#b39552;color:#1b2520}
#mao{padding:44px 10px;font-size:24px;background:#b39552;color:#1b2520;margin:10px 0}
#mao.on{background:#4a6d33;color:#fff}
#msg{min-height:30px;font-size:20px;color:#dcc387;font-weight:bold;margin-top:12px}
#st{font-size:13px;color:#9fae9f;font-style:italic;margin-top:8px}
.oculto{display:none}
</style></head><body>
<div id="t1">
 <h1>&#9884; Prevalecentes</h1><p>Sess&atilde;o &mdash; levantar a m&atilde;o</p>
 <input id="nome" placeholder="Seu nome" maxlength="30" autocomplete="off">
 <button id="entrar">Entrar</button>
</div>
<div id="t2" class="oculto">
 <h1 id="quem"></h1>
 <button id="mao">&#9995; Levantar a m&atilde;o</button>
 <div id="msg"></div><div id="st"></div>
</div>
<script>
var id=localStorage.getItem('preva_id')||'', nome=localStorage.getItem('preva_nome')||'';
var $=function(x){return document.getElementById(x)};
var levantada=false, timer=null;
$('nome').value=nome;
function post(url,corpo){return fetch(url,{method:'POST',body:JSON.stringify(corpo)}).then(function(r){return r.json()})}
function entrar(){
  nome=$('nome').value.trim(); if(!nome){$('nome').focus();return}
  localStorage.setItem('preva_nome',nome);
  post('/api/oi',{nome:nome,id:id}).then(function(r){
    id=r.id; localStorage.setItem('preva_id',id);
    $('t1').classList.add('oculto'); $('t2').classList.remove('oculto');
    $('quem').textContent=id; if(!timer){timer=setInterval(consultar,1000)} consultar();
  }).catch(function(){alert('N\\u00e3o consegui falar com o mestre. Voc\\u00ea est\\u00e1 na mesma rede?')});
}
function pintar(){
  var b=$('mao'); b.className=levantada?'on':'';
  b.innerHTML=levantada?'&#9995; M&atilde;o levantada &mdash; toque para abaixar':'&#9995; Levantar a m&atilde;o';
}
function consultar(){
  fetch('/api/estado?id='+encodeURIComponent(id)).then(function(r){return r.json()}).then(function(r){
    if(!r.ok){ // o mestre reiniciou ou a conex\\u00e3o expirou: entra de novo
      post('/api/oi',{nome:nome,id:id}).then(function(x){id=x.id;localStorage.setItem('preva_id',id);$('quem').textContent=id});return}
    $('st').textContent='Conectado'; levantada=r.mao; pintar();
    if(r.palavra){$('msg').textContent='\\ud83c\\udfa4 O mestre te deu a palavra!';
      if(navigator.vibrate){navigator.vibrate([300,120,300])}
      setTimeout(function(){$('msg').textContent=''},8000)}
  }).catch(function(){$('st').textContent='Sem conex\\u00e3o com o mestre\\u2026'});
}
$('entrar').onclick=entrar;
$('nome').onkeydown=function(e){if(e.key==='Enter')entrar()};
$('mao').onclick=function(){
  post(levantada?'/api/abaixar':'/api/mao',{id:id}).then(consultar);
};
</script></body></html>
"""


class _Pagina(BaseHTTPRequestHandler):
    """Atende os celulares (navegador). `srv` é preenchido na criação (veja Servidor.iniciar)."""
    srv = None

    def log_message(self, *a):
        pass

    def _resp(self, corpo, tipo):
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corpo)

    def _json(self, obj):
        self._resp(json.dumps(obj).encode("utf-8"), "application/json")

    def do_GET(self):
        u = urlparse(self.path)
        try:
            if u.path == "/api/estado":
                self._json(self.srv.web_estado(parse_qs(u.query).get("id", [""])[0]))
            elif u.path == "/api/sessao":
                self._json({"sessao": True, "rodada": self.srv.rodada})
            elif u.path in ("/", "/index.html"):
                self._resp((PAGINA_FICHA or PAGINA_WEB).encode("utf-8"), "text/html; charset=utf-8")
            elif u.path == "/mao":
                self._resp(PAGINA_WEB.encode("utf-8"), "text/html; charset=utf-8")
            else:
                self.send_error(404)
        except OSError:
            pass

    def do_POST(self):
        try:
            n = min(int(self.headers.get("Content-Length") or 0), 20000)
            corpo = json.loads(self.rfile.read(n) or b"{}")
            if not isinstance(corpo, dict):
                corpo = {}
        except (ValueError, OSError):
            corpo = {}
        ident = str(corpo.get("id", ""))
        try:
            if self.path == "/api/oi":
                self._json({"id": self.srv.web_oi(str(corpo.get("nome", "")).strip()[:30], ident)})
            elif self.path == "/api/mao":
                self._json({"ok": self.srv.web_mao(ident, True)})
            elif self.path == "/api/abaixar":
                self._json({"ok": self.srv.web_mao(ident, False)})
            elif self.path == "/api/ficha":
                self._json({"ok": self.srv.receber_ficha(ident, corpo.get("dados"), web=True)})
            elif self.path == "/api/relato":
                self._json({"ok": self.srv.relato(ident, corpo.get("texto"), corpo.get("ativou"), web=True)})
            else:
                self.send_error(404)
        except OSError:
            pass


def procurar_mestre(fila, segundos=10):
    """Escuta o anúncio do mestre. Põe ("achou", ip, porta) ou ("nao_achou",) na fila."""
    def tarefa():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("", PORTA_ANUNCIO))
            s.settimeout(1)
            fim = time.time() + segundos
            while time.time() < fim:
                try:
                    dados, (ip, _) = s.recvfrom(512)
                    msg = json.loads(dados.decode("utf-8"))
                    if msg.get("preva") == 1:
                        fila.put(("achou", ip, int(msg["porta"])))
                        return
                except socket.timeout:
                    continue
                except (ValueError, KeyError, TypeError):
                    continue
        except OSError:
            pass
        finally:
            s.close()
        fila.put(("nao_achou",))
    threading.Thread(target=tarefa, daemon=True).start()


def ip_local():
    """IP da máquina na rede local (não envia nada; só descobre qual interface seria usada)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "127.0.0.1"
    finally:
        s.close()


def desenhar_qr(master, texto, tam=170):
    """Canvas com o QR code de `texto` (fundo branco e margem, para a câmera ler também no tema escuro)."""
    matriz = segno.make(texto, error="m", micro=False).matrix
    n, borda = len(matriz), 2
    mod = max(2, tam // (n + 2 * borda))
    lado = mod * (n + 2 * borda)
    cv = tk.Canvas(master, width=lado, height=lado, bg="white", highlightthickness=0)
    for y, linha in enumerate(matriz):
        for x, escuro in enumerate(linha):
            if escuro:
                x0, y0 = (x + borda) * mod, (y + borda) * mod
                cv.create_rectangle(x0, y0, x0 + mod, y0 + mod, fill="black", outline="")
    return cv


def _fechar(sock):
    """Fecha de verdade: sem o shutdown, o makefile() de quem está lendo mantém a conexão aberta
    e o outro lado nunca percebe que a sessão acabou."""
    if sock is None:
        return
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    try:
        sock.close()
    except OSError:
        pass


def _enviar(sock, msg):
    try:
        sock.sendall((json.dumps(msg, ensure_ascii=False) + "\n").encode("utf-8"))
        return True
    except OSError:
        return False


def _linhas(sock):
    """Gera as mensagens JSON recebidas até a conexão cair."""
    try:
        arq = sock.makefile("r", encoding="utf-8", newline="\n")
        for linha in arq:
            try:
                msg = json.loads(linha)
            except ValueError:
                continue
            if isinstance(msg, dict):
                yield msg
    except (OSError, ValueError):
        return


# ======================================================================= rede
class Servidor:
    """Lado do mestre. Os eventos para a interface vão em `fila`: ("mudou",) ou ("mao", nome)."""

    def __init__(self, porta, fila):
        self.porta = porta
        self.fila = fila
        self.lock = threading.Lock()
        self.clientes = {}     # nome -> socket
        self.maos = []         # nomes, na ordem em que levantaram a mão
        self.web = {}          # celulares (navegador): nome -> {"visto": hora, "palavra": bool}
        self.web_ok = False
        self.httpd = None
        self.sock = None
        self.ativo = False
        self.fichas = {}       # nome -> resumo da ficha (Vida, Mana, Vigor, CA...)
        self.efeitos = {}      # nome -> [{"id", "nome", "desc", "rodadas"}] aplicados pelo mestre
        self.pendentes = {}    # celulares: nome -> eventos ainda não entregues
        self.rodada = 1
        self.registro = []     # (hora, texto) para o painel do mestre
        self._seq = 0
        self.ordem = []        # [[nome, iniciativa, bônus]] em ordem de turno (vazia = fora de combate)
        self.vez = -1          # posição de quem age agora em self.ordem
        self.turno = 0         # conta os turnos passados (o celular usa para o desgaste de armas)

    def iniciar(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0", self.porta))
        self.sock.listen(16)
        self.ativo = True
        threading.Thread(target=self._aceitar, daemon=True).start()
        threading.Thread(target=self._anunciar, daemon=True).start()
        try:
            self.httpd = ThreadingHTTPServer(("0.0.0.0", PORTA_WEB), type("Pagina", (_Pagina,), {"srv": self}))
            self.httpd.daemon_threads = True
            threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
            self.web_ok = True
        except OSError:
            self.httpd = None   # porta ocupada: só os jogadores do app entram

    # --- celulares (a página HTTP chama estes métodos)
    def web_oi(self, nome, ident):
        with self.lock:
            if ident and ident in self.web:
                self.web[ident]["visto"] = time.time()
                return ident
            base, n = nome or "Jogador", 2
            nome = base
            while nome in self.clientes or nome in self.web:
                nome = f"{base} ({n})"
                n += 1
            self.web[nome] = {"visto": time.time(), "palavra": False}
        self.fila.put(("mudou",))
        return nome

    def web_mao(self, ident, levantar):
        with self.lock:
            w = self.web.get(ident)
            if w is None:
                return False
            w["visto"] = time.time()
            novo = levantar and ident not in self.maos
            if novo:
                self.maos.append(ident)
            elif not levantar and ident in self.maos:
                self.maos.remove(ident)
        self.fila.put(("mao", ident) if novo else ("mudou",))
        return True

    def web_estado(self, ident):
        with self.lock:
            w = self.web.get(ident)
            if w is None:
                return {"ok": False}
            w["visto"] = time.time()
            palavra, w["palavra"] = w["palavra"], False
            eventos, self.pendentes[ident] = self.pendentes.get(ident, []), []
            return {"ok": True, "mao": ident in self.maos, "palavra": palavra, "eventos": eventos,
                    "efeitos": list(self.efeitos.get(ident, [])), "rodada": self.rodada,
                    "vez": self._quem_age(), "turno": self.turno, "ordem": [o[0] for o in self.ordem]}

    def _varrer(self):
        """Tira da mesa os celulares que sumiram há muito tempo (fecharam a página ou saíram da rede).
        Tela bloqueada não conta: o jogador só fica "sem sinal" e a mão continua na fila."""
        agora = time.time()
        with self.lock:
            sumidos = [n for n, w in self.web.items() if agora - w["visto"] > SAI_DA_MESA]
            mudou_sinal = any((agora - w["visto"] > SEM_SINAL) != w.get("sem_sinal", False) for w in self.web.values())
            for w in self.web.values():
                w["sem_sinal"] = agora - w["visto"] > SEM_SINAL
            for n in sumidos:
                del self.web[n]
                if n in self.maos:
                    self.maos.remove(n)
        if sumidos or mudou_sinal:
            self.fila.put(("mudou",))

    def sem_sinal(self):
        """Celulares que não respondem há mais de SEM_SINAL segundos (provavelmente com a tela bloqueada)."""
        with self.lock:
            return {n for n, w in self.web.items() if w.get("sem_sinal")}

    def _anunciar(self):
        """Avisa a rede, a cada 1,5 s, que há uma sessão aberta (os jogadores a encontram sozinhos)."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        msg = json.dumps({"preva": 1, "porta": self.porta}).encode("utf-8")
        while self.ativo:
            ip = ip_local()
            destinos = {"255.255.255.255", ip.rsplit(".", 1)[0] + ".255"}
            for d in destinos:
                try:
                    s.sendto(msg, (d, PORTA_ANUNCIO))
                except OSError:
                    pass
            self._varrer()
            time.sleep(1.5)
        s.close()

    def _aceitar(self):
        while self.ativo:
            try:
                c, _ = self.sock.accept()
            except OSError:
                return
            c.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            threading.Thread(target=self._atender, args=(c,), daemon=True).start()

    def _atender(self, c):
        nome = None
        try:
            for msg in _linhas(c):
                t = msg.get("t")
                if nome is None:
                    if t != "oi":
                        continue
                    nome = self._registrar(c, str(msg.get("nome", "")).strip()[:30] or "Jogador")
                    _enviar(c, {"t": "ok", "nome": nome})
                    self._sincronizar(nome)
                    self.fila.put(("mudou",))
                elif t == "mao":
                    with self.lock:
                        novo = nome not in self.maos
                        if novo:
                            self.maos.append(nome)
                    if novo:
                        self.fila.put(("mao", nome))
                    self._avisar(nome)
                elif t == "abaixar":
                    with self.lock:
                        if nome in self.maos:
                            self.maos.remove(nome)
                    self.fila.put(("mudou",))
                    self._avisar(nome)
                elif t == "ficha":
                    self.receber_ficha(nome, msg.get("dados"))
                elif t == "relato":
                    self.relato(nome, msg.get("texto"), msg.get("ativou"))
        finally:
            if nome is not None:
                with self.lock:
                    if self.clientes.get(nome) is c:
                        del self.clientes[nome]
                    if nome in self.maos:
                        self.maos.remove(nome)
                self.fila.put(("mudou",))
            try:
                c.close()
            except OSError:
                pass

    def _registrar(self, c, nome):
        with self.lock:
            base, n = nome, 2
            while nome in self.clientes or nome in self.web:
                nome = f"{base} ({n})"
                n += 1
            self.clientes[nome] = c
        return nome

    def _avisar(self, nome):
        """Diz ao jogador se a mão dele está levantada (confirmação vinda do mestre)."""
        with self.lock:
            c = self.clientes.get(nome)
            lev = nome in self.maos
        if c:
            _enviar(c, {"t": "estado", "mao": lev})

    # --- fichas, dano, condições e rodadas
    def receber_ficha(self, nome, dados, web=False):
        with self.lock:
            if web:
                w = self.web.get(nome)
                if w is None:
                    return False
                w["visto"] = time.time()
            novo = limpar_ficha(dados)
            if self.fichas.get(nome) == novo:
                return True
            self.fichas[nome] = novo
        self.fila.put(("mudou",))
        return True

    def _anotar(self, texto):
        with self.lock:
            self.registro.insert(0, (time.strftime("%H:%M"), texto))
            del self.registro[200:]
        self.fila.put(("registro",))

    def _evento(self, nome, ev):
        """Entrega um evento ao jogador: na hora (PC) ou na próxima consulta (celular)."""
        with self.lock:
            c = self.clientes.get(nome)
            if c is None and nome in self.web:
                self.pendentes.setdefault(nome, []).append(ev)
        if c:
            _enviar(c, {"t": "evento", "ev": ev})

    def _sincronizar(self, nome):
        """Manda ao jogador do PC a lista atual de efeitos (o celular recebe na consulta)."""
        with self.lock:
            c = self.clientes.get(nome)
            lista, rod = list(self.efeitos.get(nome, [])), self.rodada
            vez, turno = self._quem_age(), self.turno
        if c:
            _enviar(c, {"t": "efeitos", "lista": lista, "rodada": rod, "vez": vez, "turno": turno})

    def jogadores(self):
        with self.lock:
            return list(self.clientes) + list(self.web)

    def enviar_dano(self, alvos, valor, tipo, desc):
        """valor > 0: dano; valor < 0: cura. A ficha do jogador aplica e devolve a Vida nova."""
        for n in alvos:
            self._evento(n, {"tipo": "dano", "valor": int(valor), "dano_tipo": tipo, "desc": desc})
        oque = f"{abs(valor)} de cura" if valor < 0 else f"{valor} de dano" + (f" ({tipo})" if tipo else "")
        self._anotar(f"{oque} → {', '.join(alvos)}" + (f": {desc}" if desc else ""))

    def adicionar_condicao(self, alvos, nome_cond, rodadas, desc, fim_combate=False, pct_turno=0, avisar=True):
        """rodadas: em combate (com ordem de turno) conta os turnos do afetado; fora dele, as rodadas."""
        for n in alvos:
            with self.lock:
                self._seq += 1
                self.efeitos.setdefault(n, []).append({"id": self._seq, "nome": nome_cond, "desc": desc, "rodadas": int(rodadas),
                                                       "fim_combate": bool(fim_combate), "pct_turno": int(pct_turno)})
            if avisar:
                self._evento(n, {"tipo": "condicao", "nome": nome_cond, "rodadas": int(rodadas), "desc": desc, "fim_combate": bool(fim_combate)})
            self._sincronizar(n)
        dur = f"{rodadas} turno(s)" if rodadas else "até o fim do combate" if fim_combate else "até o mestre remover"
        self._anotar(f"{nome_cond} ({dur}) → {', '.join(alvos)}" + (f": {desc}" if desc else ""))
        self.fila.put(("mudou",))

    def remover_condicao(self, nome, cid):
        with self.lock:
            lista = self.efeitos.get(nome, [])
            fim = [e for e in lista if e["id"] == cid]
            self.efeitos[nome] = [e for e in lista if e["id"] != cid]
        for e in fim:
            self._evento(nome, {"tipo": "fim", "nome": e["nome"]})
            self._anotar(f"{e['nome']} removido de {nome}")
        self._sincronizar(nome)
        self.fila.put(("mudou",))

    def proxima_rodada(self):
        """Avança a rodada: cada condição com duração perde 1; ao chegar a 0, termina e todos são avisados."""
        acabaram = []
        with self.lock:
            self.rodada += 1
            for nome, lista in self.efeitos.items():
                restam = []
                for e in lista:
                    if e["rodadas"] > 0:
                        e["rodadas"] -= 1
                        if e["rodadas"] == 0:
                            acabaram.append((nome, e["nome"]))
                            continue
                    restam.append(e)
                self.efeitos[nome] = restam
            rod = self.rodada
        for nome in self.jogadores():
            self._evento(nome, {"tipo": "rodada", "rodada": rod})
            self._sincronizar(nome)
        for nome, cond in acabaram:
            self._evento(nome, {"tipo": "fim", "nome": cond})
        self._anotar(f"Rodada {rod}" + (" — terminou: " + ", ".join(f"{c} ({n})" for n, c in acabaram) if acabaram else ""))
        self.fila.put(("mudou",))

    # --- itens, pontos de condição e relatos dos jogadores
    def dar_item(self, alvos, item, desc=""):
        it = {"item": str(item.get("item", ""))[:40], "carga": str(item.get("carga", ""))[:8], "qtd": max(1, int(item.get("qtd") or 1))}
        for n in alvos:
            self._evento(n, {"tipo": "item", "acao": "dar", "item": it, "desc": desc})
        self._anotar(f"Deu {it['qtd']}× {it['item']} → {', '.join(alvos)}" + (f": {desc}" if desc else ""))

    def tirar_item(self, nome, indice, nome_item, qtd=1, desc=""):
        self._evento(nome, {"tipo": "item", "acao": "tirar", "indice": int(indice), "nome": str(nome_item)[:40],
                            "qtd": max(1, int(qtd)), "desc": desc})
        self._anotar(f"Tirou {qtd}× {nome_item} de {nome}" + (f": {desc}" if desc else ""))

    def enviar_pontos_condicao(self, alvos, condicao, pontos, dt, desc=""):
        """Pontos de condição do livro (Veneno, Sangramento...). A ficha do jogador rola o teste
        (Fortitude ou Vontade contra a DT) e recebe metade num sucesso; o resultado volta como relato."""
        for n in alvos:
            self._evento(n, {"tipo": "cond_pontos", "condicao": condicao, "pontos": int(pontos), "dt": int(dt), "desc": desc})
        self._anotar(f"{pontos} de {condicao} (DT {dt}) → {', '.join(alvos)}" + (f": {desc}" if desc else ""))

    def relato(self, nome, texto, ativou=None, web=False):
        """O jogador conta o resultado (teste de condição, item usado...). Se uma condição ativou,
        o efeito do livro entra na lista dele com a duração certa."""
        with self.lock:
            if web and nome not in self.web:
                return False
        texto = str(texto or "")[:300]
        if texto:
            self._anotar(f"{nome}: {texto}")
        cond = str(ativou or "")
        info = R.CONDICAO_ATIVA.get(cond)
        if info:
            if cond == "Sono":
                self.adicionar_condicao([nome], "Inconsciente", 1, "Sono ativado: " + EFEITOS["Inconsciente"][1], avisar=False)
            elif cond == "Morte":
                self.adicionar_condicao([nome], "Morte", 0, info["desc"], avisar=False)
            elif "turnos" in info:
                self.adicionar_condicao([nome], cond, info["turnos"], info["desc"], fim_combate=info["turnos"] == 0,
                                        pct_turno=info.get("pct_turno", 0), avisar=False)
        self.fila.put(("mudou",))
        return True

    # --- ordem de turno (iniciativa)
    def _quem_age(self):
        return self.ordem[self.vez][0] if 0 <= self.vez < len(self.ordem) else ""

    def rolar_iniciativa(self, rng=None):
        """Rola a iniciativa de todos pela ficha (d20 por dado de iniciativa, fica o maior, + bônus) e começa o combate."""
        rng = rng or (lambda f: random.randint(1, f))
        with self.lock:
            ordem = []
            for n in list(self.clientes) + list(self.web):
                f = self.fichas.get(n, {})
                dados, bonus = max(1, int(f.get("iniciativa_dados", 1))), int(f.get("iniciativa", 0))
                rolos = [rng(20) for _ in range(dados)]
                ordem.append([n, max(rolos) + bonus, bonus])
            ordem.sort(key=lambda o: (-o[1], -o[2], o[0]))
            self.ordem, self.vez = ordem, -1
        self._anotar("Iniciativa: " + ", ".join(f"{n} {v}" for n, v, _ in ordem))
        for n in self.jogadores():
            self._evento(n, {"tipo": "combate", "fase": "inicio"})
        self.passar_turno(inicio=True)

    def definir_iniciativa(self, nome, valor):
        """Muda (ou inclui) a iniciativa de alguém sem perder de quem é a vez."""
        with self.lock:
            atual = self._quem_age()
            achou = False
            for o in self.ordem:
                if o[0] == nome:
                    o[1], achou = int(valor), True
            if not achou:
                self.ordem.append([nome, int(valor), int(self.fichas.get(nome, {}).get("iniciativa", 0))])
            self.ordem.sort(key=lambda o: (-o[1], -o[2], o[0]))
            self.vez = next((i for i, o in enumerate(self.ordem) if o[0] == atual), self.vez)
        self.fila.put(("mudou",))
        for n in self.jogadores():
            self._sincronizar(n)

    def tirar_da_ordem(self, nome):
        with self.lock:
            atual = self._quem_age()
            self.ordem = [o for o in self.ordem if o[0] != nome]
            self.vez = next((i for i, o in enumerate(self.ordem) if o[0] == atual), min(self.vez, len(self.ordem) - 1))
        self.fila.put(("mudou",))

    def passar_turno(self, inicio=False):
        """Termina o turno de quem age (as durações dele perdem 1), passa para o próximo da iniciativa e,
        depois do último, começa uma rodada nova. Sem ordem de iniciativa, passa a rodada."""
        if not self.ordem:
            self.proxima_rodada()
            return
        acabaram, dano = [], None
        with self.lock:
            anterior = "" if inicio else self._quem_age()
            if anterior:
                restam = []
                for e in self.efeitos.get(anterior, []):
                    if e["rodadas"] > 0:
                        e["rodadas"] -= 1
                        if e["rodadas"] == 0:
                            acabaram.append((anterior, e["nome"]))
                            continue
                    restam.append(e)
                self.efeitos[anterior] = restam
            self.vez += 1
            nova_rodada = self.vez >= len(self.ordem)
            if nova_rodada:
                self.vez = 0
                if not inicio:
                    self.rodada += 1
            self.turno += 1
            agora = self._quem_age()
            vmax = int(self.fichas.get(agora, {}).get("vida_max", 0))
            pct = [e for e in self.efeitos.get(agora, []) if e.get("pct_turno")]
            if pct and vmax:
                dano = [(e["nome"], max(1, vmax * e["pct_turno"] // 100)) for e in pct]
            rod = self.rodada
        for nome, cond in acabaram:
            self._evento(nome, {"tipo": "fim", "nome": cond})
        self._evento(agora, {"tipo": "vez", "rodada": rod})
        for n in self.jogadores():
            self._sincronizar(n)
        for cond, v in dano or []:
            self.enviar_dano([agora], v, "Direto", f"{cond} (início do turno)")
        self._anotar((f"Rodada {rod} — " if nova_rodada else "") + f"vez de {agora}"
                     + (" — terminou: " + ", ".join(f"{c} ({n})" for n, c in acabaram) if acabaram else ""))
        self.fila.put(("mudou",))

    def encerrar_combate(self):
        """Fim do combate: limpa a ordem e tira os efeitos que duram "até o fim do combate"."""
        fim = []
        with self.lock:
            self.ordem, self.vez = [], -1
            for n, lista in self.efeitos.items():
                fim += [(n, e["nome"]) for e in lista if e.get("fim_combate")]
                self.efeitos[n] = [e for e in lista if not e.get("fim_combate")]
        for n, c in fim:
            self._evento(n, {"tipo": "fim", "nome": c})
        for n in self.jogadores():
            self._evento(n, {"tipo": "combate", "fase": "fim"})
            self._sincronizar(n)
        self._anotar("Fim do combate" + (" — terminou: " + ", ".join(f"{c} ({n})" for n, c in fim) if fim else ""))
        self.fila.put(("mudou",))

    def painel(self):
        """Tudo que o painel do mestre desenha, numa leitura só."""
        with self.lock:
            agora = time.time()
            jog = []
            for n in list(self.clientes) + list(self.web):
                w = self.web.get(n)
                jog.append({"nome": n, "celular": w is not None, "sem_sinal": bool(w and agora - w["visto"] > SEM_SINAL),
                            "mao": n in self.maos, "ficha": dict(self.fichas.get(n, {})),
                            "efeitos": [dict(e) for e in self.efeitos.get(n, [])]})
            return {"jogadores": jog, "maos": list(self.maos), "rodada": self.rodada, "registro": list(self.registro[:60]),
                    "ordem": [list(o) for o in self.ordem], "vez": self._quem_age()}

    # --- ações do mestre
    def dar_palavra(self, nome):
        with self.lock:
            if nome in self.maos:
                self.maos.remove(nome)
            c = self.clientes.get(nome)
            if nome in self.web:
                self.web[nome]["palavra"] = True
        if c:
            _enviar(c, {"t": "palavra"})
            _enviar(c, {"t": "estado", "mao": False})

    def baixar(self, nome):
        with self.lock:
            if nome in self.maos:
                self.maos.remove(nome)
        self._avisar(nome)

    def baixar_todas(self):
        with self.lock:
            nomes = list(self.maos)
            self.maos.clear()
        for n in nomes:
            self._avisar(n)

    def estado(self):
        with self.lock:
            return list(self.clientes) + list(self.web), list(self.maos)

    def parar(self):
        self.ativo = False
        if self.httpd:
            threading.Thread(target=self.httpd.shutdown, daemon=True).start()
            self.httpd.server_close()
        with self.lock:
            socks = list(self.clientes.values())
        for c in socks:
            _fechar(c)
        try:
            if self.sock:
                self.sock.close()
        except OSError:
            pass


class Cliente:
    """Lado do jogador. Eventos: ("ok", nome), ("estado", bool), ("palavra",), ("caiu",)."""

    def __init__(self, fila):
        self.fila = fila
        self.sock = None

    def conectar(self, ip, porta, nome):
        self.sock = socket.create_connection((ip, porta), timeout=5)
        self.sock.settimeout(None)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        _enviar(self.sock, {"t": "oi", "nome": nome})
        threading.Thread(target=self._ouvir, daemon=True).start()

    def _ouvir(self):
        for msg in _linhas(self.sock):
            t = msg.get("t")
            if t == "ok":
                self.fila.put(("ok", msg.get("nome", "")))
            elif t == "estado":
                self.fila.put(("estado", bool(msg.get("mao"))))
            elif t == "palavra":
                self.fila.put(("palavra",))
            elif t == "evento" and isinstance(msg.get("ev"), dict):
                self.fila.put(("evento", msg["ev"]))
            elif t == "efeitos":
                self.fila.put(("efeitos", msg.get("lista") or [], int(msg.get("rodada") or 1),
                               str(msg.get("vez") or ""), int(msg.get("turno") or 0)))
        self.fila.put(("caiu",))

    def enviar(self, msg):
        return bool(self.sock) and _enviar(self.sock, msg)

    def parar(self):
        _fechar(self.sock)


# ======================================================================= interface
CORES_PADRAO = dict(FUNDO="#1b2520", CAMPO="#fbf7ea", PERG="#f2e9d3", PERG2="#e6d7b4", TINTA="#2d2015", TINTA2="#7d6a54",
                    VINHO="#7c2626", OURO="#b39552", OURO2="#dcc387", VERDE="#4a6d33", ALERTA="#f0a08c",
                    TINTA2_FUNDO="#9fae9f", FAIXA="#f6efdc", LINHA="#ddcda6", C_VIDA="#9a3d33", C_MANA="#3f6283",
                    C_VIGOR="#567a3b", FONTE="Georgia")


class JanelaSessao(tk.Toplevel):
    """Janela única com as três telas: escolha, painel do mestre e painel do jogador."""

    def __init__(self, app, cores, nome_padrao, ao_fechar, ponte=None):
        super().__init__(app)
        self.c = dict(CORES_PADRAO, **cores)
        self._avisos = []          # últimos avisos do mestre (jogador)
        self._vez = ""
        self._painel = {}
        self.meu_nome = ""
        self.ponte = ponte         # liga a sessão à ficha aberta (resumo, aplicar dano, mostrar efeitos)
        self.ao_fechar = ao_fechar
        self.nome_padrao = nome_padrao
        self.fonte = cores.get("FONTE", "Georgia")
        self.title("Sessão — Levantar a mão")
        self.geometry("460x560")
        self.minsize(400, 480)
        self.configure(background=self.c["FUNDO"])
        self.fila = queue.Queue()
        self.servidor = None
        self.cliente = None
        self.mao_levantada = False
        self.ultimo_ip = None      # IP do mestre da última conexão (salvo nas preferências ao fechar)
        self._maos_tela = []       # fila como está desenhada na tela do mestre
        self._btn_voltar = None
        self.selecionados = set()  # jogadores marcados no painel do mestre
        self._painel_agendado = False
        self._ultima_ficha = None
        self.efeitos = []          # efeitos recebidos do mestre (lado do jogador)
        self.protocol("WM_DELETE_WINDOW", self.fechar)
        self.tela = None
        self._escolha()
        self.after(150, self._bombear)

    # --- util
    def _trocar(self):
        if self.tela is not None:
            self.tela.destroy()
        self.tela = tk.Frame(self, bg=self.c["FUNDO"], padx=22, pady=18)
        self.tela.pack(fill="both", expand=True)
        return self.tela

    def _rot(self, master, txt, size=10, cor=None, bold=False, italic=False, **kw):
        estilo = ("bold " if bold else "") + ("italic" if italic else "")
        return tk.Label(master, text=txt, bg=master["bg"], fg=cor or self.c["TINTA2_FUNDO"],
                        font=(self.fonte, size, estilo.strip() or "normal"), **kw)

    def _aviso_sonoro(self):
        try:
            self.bell()
            self.after(180, self.bell)
        except tk.TclError:
            pass
        try:
            self.deiconify()
            self.lift()
            self.attributes("-topmost", True)
            self.after(1500, lambda: self.attributes("-topmost", False))
        except tk.TclError:
            pass

    # --- tela 1: escolher o papel
    def _escolha(self):
        t = self._trocar()
        self._rot(t, "✋ Sessão", 20, self.c["OURO2"], bold=True).pack(pady=(10, 4))
        self._rot(t, "Jogadores na mesma rede levantam a mão\npara o mestre, sem cortar o roleplay.\n"
                     "Só o mestre usa o botão \"Entrar como mestre\".",
                  10, italic=True, justify="center").pack(pady=(0, 18))

        mest = tk.LabelFrame(t, text=" Sou o mestre ", bg=self.c["FUNDO"], fg=self.c["OURO2"], padx=12, pady=10)
        mest.pack(fill="x", pady=6)
        self.v_porta = tk.StringVar(value=str(PORTA))
        ttk.Button(mest, text="Entrar como mestre", command=self._ser_mestre).pack(anchor="e")

        jog = tk.LabelFrame(t, text=" Sou jogador ", bg=self.c["FUNDO"], fg=self.c["OURO2"], padx=12, pady=10)
        jog.pack(fill="x", pady=6)
        g = tk.Frame(jog, bg=self.c["FUNDO"])
        g.pack(fill="x")
        self.v_nome = tk.StringVar(value=self.nome_padrao)
        self.v_ip = tk.StringVar()
        self.v_porta_j = tk.StringVar(value=str(PORTA))
        self._rot(g, "Seu nome").grid(row=0, column=0, sticky="w", pady=3)
        ttk.Entry(g, textvariable=self.v_nome, width=22).grid(row=0, column=1, sticky="w", padx=8, pady=3)
        self.btn_entrar = ttk.Button(jog, text="Entrar como jogador", command=self._ser_jogador)
        self.btn_entrar.pack(anchor="e", pady=(8, 0))
        self.lbl_busca = self._rot(jog, "", 10, self.c["ALERTA"], italic=True)
        self.lbl_busca.pack(anchor="w")
        av = tk.Frame(jog, bg=self.c["FUNDO"])
        av.pack(fill="x", pady=(8, 0))
        self._rot(av, "Só se não achar — IP do mestre:", 9, italic=True).pack(side="left")
        ttk.Entry(av, textvariable=self.v_ip, width=16).pack(side="left", padx=6)
        self._rot(t, "Se o Windows perguntar sobre o Firewall (no PC do mestre),\npermita o acesso em redes privadas.",
                  9, italic=True, justify="center").pack(pady=(14, 0))

    # --- tela 2: mestre
    def _ser_mestre(self):
        try:
            porta = int(self.v_porta.get())
            self.servidor = Servidor(porta, self.fila)
            self.servidor.iniciar()
        except (ValueError, OSError) as e:
            self.servidor = None
            messagebox.showerror("Sessão", f"Não foi possível abrir a sessão na porta {self.v_porta.get()}.\n{e}",
                                 parent=self)
            return
        self.title("Mesa do mestre")
        self.geometry("1180x760")
        self.minsize(980, 620)
        if self.tela is not None:
            self.tela.destroy()
        c = self.c
        self.tela = tk.Frame(self, bg=c["FUNDO"])
        self.tela.pack(fill="both", expand=True)

        # barra do topo
        topo = tk.Frame(self.tela, bg=c["FUNDO"], padx=18, pady=10)
        topo.pack(fill="x")
        self._rot(topo, "⚜ Mesa do mestre", 18, c["OURO2"], bold=True).pack(side="left")
        ip = ip_local()
        self.url_celular = f"http://{ip}:{PORTA_WEB}" if self.servidor.web_ok else ""
        info = f"PC: entram sozinhos (IP {ip})" + (f"   ·   Celular: {self.url_celular}" if self.url_celular else
                                                    f"   ·   celulares indisponíveis (porta {PORTA_WEB} ocupada)")
        self._rot(topo, info, 10, c["TINTA2_FUNDO"]).pack(side="left", padx=(18, 0))
        ttk.Button(topo, text="Passar turno ▶", command=self._passar_turno).pack(side="right")
        ttk.Button(topo, text="Fim do combate", command=lambda: self.servidor.encerrar_combate()).pack(side="right", padx=(0, 6))
        ttk.Button(topo, text="🎲 Iniciativa", command=self._iniciativa).pack(side="right", padx=(0, 6))
        self.lbl_rodada = self._rot(topo, "Rodada 1", 15, c["OURO2"], bold=True)
        self.lbl_rodada.pack(side="right", padx=14)
        if self.url_celular:
            ttk.Button(topo, text="QR code", command=self._mostrar_qr).pack(side="right", padx=(0, 6))
        tk.Frame(self.tela, height=1, bg=c["OURO"]).pack(fill="x")

        corpo = tk.Frame(self.tela, bg=c["PERG"])
        corpo.pack(fill="both", expand=True)
        corpo.columnconfigure(0, weight=1)
        corpo.rowconfigure(0, weight=1)

        # jogadores (rolagem)
        esq = tk.Frame(corpo, bg=c["PERG"])
        esq.grid(row=0, column=0, sticky="nsew", padx=(14, 6), pady=12)
        cab = tk.Frame(esq, bg=c["PERG"])
        cab.pack(fill="x")
        tk.Label(cab, text="JOGADORES", bg=c["PERG"], fg=c["VINHO"], font=(self.fonte, 10, "bold")).pack(side="left")
        self.lbl_sel = tk.Label(cab, text="", bg=c["PERG"], fg=c["TINTA2"], font=(self.fonte, 10, "italic"))
        self.lbl_sel.pack(side="left", padx=10)
        ttk.Button(cab, text="Item", command=lambda: self._dialogo_item(sorted(self.selecionados))).pack(side="right")
        ttk.Button(cab, text="Condição", command=lambda: self._dialogo_pontos(sorted(self.selecionados))).pack(side="right", padx=4)
        ttk.Button(cab, text="Efeito", command=lambda: self._dialogo_condicao(sorted(self.selecionados))).pack(side="right")
        ttk.Button(cab, text="Dano/Cura", command=lambda: self._dialogo_dano(sorted(self.selecionados))).pack(side="right", padx=4)
        tk.Label(cab, text="Aos marcados:", bg=c["PERG"], fg=c["TINTA2"], font=(self.fonte, 9, "italic")).pack(side="right")
        ttk.Button(cab, text="Marcar todos", command=self._marcar_todos).pack(side="right", padx=8)
        area = tk.Frame(esq, bg=c["PERG"])
        area.pack(fill="both", expand=True, pady=(8, 0))
        self.cv_jog = tk.Canvas(area, bg=c["PERG"], highlightthickness=0)
        sb = ttk.Scrollbar(area, orient="vertical", command=self.cv_jog.yview)
        self.cv_jog.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.cv_jog.pack(side="left", fill="both", expand=True)
        self.grade_jog = tk.Frame(self.cv_jog, bg=c["PERG"])
        self._win_jog = self.cv_jog.create_window((0, 0), window=self.grade_jog, anchor="nw")
        self.grade_jog.bind("<Configure>", lambda e: self.cv_jog.configure(scrollregion=self.cv_jog.bbox("all")))
        self.cv_jog.bind("<Configure>", lambda e: (self.cv_jog.itemconfigure(self._win_jog, width=e.width), self._agendar_painel()))

        # coluna da direita: mãos e registro
        dir_ = tk.Frame(corpo, bg=c["PERG"], width=330)
        dir_.grid(row=0, column=1, sticky="ns", padx=(6, 14), pady=12)
        dir_.grid_propagate(False)
        dir_.columnconfigure(0, weight=1)
        dir_.rowconfigure(7, weight=1)
        tk.Label(dir_, text="ORDEM DE TURNO", bg=c["PERG"], fg=c["VINHO"], font=(self.fonte, 10, "bold")).grid(row=0, column=0, sticky="w")
        self.lst_ordem = tk.Listbox(dir_, height=6, font=(self.fonte, 11), bg=c["CAMPO"], fg=c["TINTA"],
                                    selectbackground=c["OURO"], activestyle="none", exportselection=False,
                                    highlightthickness=1, highlightbackground=c["OURO"], relief="flat")
        self.lst_ordem.grid(row=1, column=0, sticky="we", pady=(4, 2))
        bo = tk.Frame(dir_, bg=c["PERG"])
        bo.grid(row=2, column=0, sticky="we", pady=(0, 8))
        ttk.Button(bo, text="Mudar valor", command=self._mudar_iniciativa).pack(side="left")
        ttk.Button(bo, text="Tirar da ordem", command=self._tirar_ordem).pack(side="left", padx=4)
        self._ordem_tela = []
        tk.Label(dir_, text="MÃOS LEVANTADAS (na ordem)", bg=c["PERG"], fg=c["VINHO"], font=(self.fonte, 10, "bold")).grid(row=3, column=0, sticky="w")
        self.lst_maos = tk.Listbox(dir_, height=5, font=(self.fonte, 13, "bold"), bg=c["CAMPO"], fg=c["VINHO"],
                                   selectbackground=c["OURO"], activestyle="none", exportselection=False,
                                   highlightthickness=1, highlightbackground=c["OURO"], relief="flat")
        self.lst_maos.grid(row=4, column=0, sticky="we", pady=(4, 4))
        self.lst_maos.bind("<Double-Button-1>", lambda e: self._dar_palavra())
        bt = tk.Frame(dir_, bg=c["PERG"])
        bt.grid(row=5, column=0, sticky="we")
        ttk.Button(bt, text="🎤 Dar a palavra", command=self._dar_palavra).pack(side="left")
        ttk.Button(bt, text="Baixar", command=self._baixar).pack(side="left", padx=4)
        ttk.Button(bt, text="Baixar todas", command=lambda: self.servidor.baixar_todas()).pack(side="right")
        self.lbl_aviso = tk.Label(dir_, text="", bg=c["PERG"], fg=c["VINHO"], font=(self.fonte, 11, "bold"), anchor="w")
        self.lbl_aviso.grid(row=6, column=0, sticky="we", pady=(6, 6))
        reg = tk.Frame(dir_, bg=c["PERG"])
        reg.grid(row=7, column=0, sticky="nsew")
        tk.Label(reg, text="REGISTRO", bg=c["PERG"], fg=c["VINHO"], font=(self.fonte, 10, "bold")).pack(anchor="w")
        self.txt_reg = tk.Text(reg, wrap="word", bg=c["CAMPO"], fg=c["TINTA"], font=(self.fonte, 10), relief="flat",
                               highlightthickness=1, highlightbackground=c["OURO"], padx=8, pady=6)
        self.txt_reg.pack(fill="both", expand=True, pady=(4, 0))
        self.txt_reg.configure(state="disabled")
        self._atualizar_mestre()

    def _mostrar_qr(self):
        w = tk.Toplevel(self)
        w.title("Celulares")
        w.configure(background="white")
        tk.Label(w, text="Aponte a câmera ou abra:\n" + self.url_celular, bg="white", fg="#222",
                 font=(self.fonte, 12, "bold")).pack(padx=16, pady=(14, 6))
        if segno:
            try:
                desenhar_qr(w, self.url_celular, 260).pack(padx=16, pady=(0, 16))
            except Exception:   # o QR é um extra: nunca derruba a mesa do mestre
                pass
        else:
            tk.Label(w, text="(instale o pacote segno para ver o QR code)", bg="white").pack(pady=(0, 14))

    def _proxima_rodada(self):
        self.servidor.proxima_rodada()

    def _passar_turno(self):
        self.servidor.passar_turno()

    def _iniciativa(self):
        if self.servidor.ordem and not messagebox.askyesno(
                "Iniciativa", "Já há um combate em andamento. Rolar a iniciativa de novo para todos?", parent=self):
            return
        if not self.servidor.jogadores():
            messagebox.showinfo("Iniciativa", "Ninguém conectado ainda.", parent=self)
            return
        self.servidor.rolar_iniciativa()

    def _ordem_selecionada(self):
        sel = self.lst_ordem.curselection()
        return self._ordem_tela[sel[0]] if sel and sel[0] < len(self._ordem_tela) else None

    def _mudar_iniciativa(self):
        from tkinter import simpledialog
        nome = self._ordem_selecionada()
        if not nome:
            messagebox.showinfo("Iniciativa", "Selecione alguém na ordem de turno.", parent=self)
            return
        v = simpledialog.askinteger("Iniciativa", f"Nova iniciativa de {nome}:", parent=self, minvalue=-20, maxvalue=200)
        if v is not None:
            self.servidor.definir_iniciativa(nome, v)

    def _tirar_ordem(self):
        nome = self._ordem_selecionada()
        if nome:
            self.servidor.tirar_da_ordem(nome)

    def _marcar_todos(self):
        todos = set(self.servidor.jogadores())
        self.selecionados = set() if self.selecionados >= todos and todos else todos
        self._atualizar_mestre()

    def _alternar_sel(self, nome):
        self.selecionados ^= {nome}
        self._atualizar_mestre()

    def _nome_selecionado(self):
        """Nome na linha selecionada, conforme a lista que está NA TELA (a fila pode ter mudado desde então)."""
        sel = self.lst_maos.curselection()
        idx = sel[0] if sel else 0
        maos = self._maos_tela
        return maos[idx] if idx < len(maos) else None

    def _dar_palavra(self):
        n = self._nome_selecionado()
        if n:
            self.servidor.dar_palavra(n)
            self.fila.put(("mudou",))

    def _baixar(self):
        n = self._nome_selecionado()
        if n:
            self.servidor.baixar(n)
            self.fila.put(("mudou",))

    def _agendar_painel(self):
        if not self._painel_agendado:
            self._painel_agendado = True
            self.after(250, self._atualizar_mestre)

    def _barra(self, master, rot, atual, maximo, cor):
        c = self.c
        f = tk.Frame(master, bg=c["CAMPO"])
        f.pack(fill="x", pady=1)
        tk.Label(f, text=rot, width=6, anchor="w", bg=c["CAMPO"], fg=c["TINTA2"], font=(self.fonte, 9, "bold")).pack(side="left")
        cv = tk.Canvas(f, height=16, bg=c["PERG2"], highlightthickness=0)
        cv.pack(side="left", fill="x", expand=True)
        frac = max(0.0, min(1.0, atual / maximo)) if maximo else 0.0

        def desenhar(e=None, cv=cv):
            cv.delete("all")
            w = cv.winfo_width() or 200
            cv.create_rectangle(0, 0, int(w * frac), 16, fill=cor, outline="")
            cv.create_text(w // 2, 8, text=f"{atual} / {maximo}", fill=c["TINTA"] if frac < .5 else c["FAIXA"],
                           font=(self.fonte, 9, "bold"))
        cv.bind("<Configure>", desenhar)
        desenhar()

    def _cartao(self, master, j):
        c = self.c
        fi, nome = j["ficha"], j["nome"]
        marcado = nome in self.selecionados
        vez = nome == self._vez
        card = tk.Frame(master, bg=c["CAMPO"], highlightthickness=3 if vez else 2 if marcado else 1,
                        highlightbackground=c["OURO2"] if vez else c["VINHO"] if marcado else c["OURO"], padx=10, pady=8)
        cab = tk.Frame(card, bg=c["CAMPO"])
        cab.pack(fill="x")
        v = tk.BooleanVar(value=marcado)
        tk.Checkbutton(cab, variable=v, bg=c["CAMPO"], activebackground=c["CAMPO"],
                       command=lambda n=nome: self._alternar_sel(n)).pack(side="left")
        tk.Label(cab, text=fi.get("personagem") or nome, bg=c["CAMPO"], fg=c["VINHO"], font=(self.fonte, 13, "bold")).pack(side="left")
        extra = nome if fi.get("personagem") and fi.get("personagem") != nome else ""
        extra += (" · " if extra else "") + ("celular" if j["celular"] else "PC")
        tk.Label(cab, text=extra, bg=c["CAMPO"], fg=c["TINTA2"], font=(self.fonte, 9, "italic")).pack(side="left", padx=6)
        if j["mao"]:
            tk.Label(cab, text="✋", bg=c["CAMPO"], fg=c["VINHO"], font=(self.fonte, 14, "bold")).pack(side="right")
        if vez:
            tk.Label(cab, text="⚔ VEZ", bg=c["OURO"], fg="#1b2520", font=(self.fonte, 9, "bold"), padx=4).pack(side="right", padx=4)
        if j["sem_sinal"]:
            tk.Label(cab, text="sem sinal", bg=c["CAMPO"], fg=c["TINTA2"], font=(self.fonte, 9, "italic")).pack(side="right", padx=4)
        if not fi:
            tk.Label(card, text="Aguardando a ficha… (o jogador entrou só para levantar a mão)", bg=c["CAMPO"], fg=c["TINTA2"],
                     font=(self.fonte, 9, "italic"), wraplength=320, justify="left").pack(anchor="w", pady=(4, 0))
        else:
            self._barra(card, "Vida", fi.get("vida", 0), fi.get("vida_max", 0), c["C_VIDA"])
            self._barra(card, "Mana", fi.get("mana", 0), fi.get("mana_max", 0), c["C_MANA"])
            self._barra(card, "Vigor", fi.get("vigor", 0), fi.get("vigor_max", 0), c["C_VIGOR"])
            linha = f"Nv {fi.get('nivel', 1)}  ·  CA {fi.get('ca', 10)}  ·  Mov {fi.get('movimento', 9)} m  ·  Ini +{fi.get('iniciativa', 0)}"
            tk.Label(card, text=linha, bg=c["CAMPO"], fg=c["TINTA"], font=(self.fonte, 10)).pack(anchor="w", pady=(4, 0))
            if fi.get("vida", 1) <= 0:
                p = fi.get("portao") or [0, 0]
                tk.Label(card, text=f"☠ Incapaz — Portão da Morte: {p[0]} sucesso(s), {p[1]} falha(s)", bg=c["CAMPO"],
                         fg=c["VINHO"], font=(self.fonte, 10, "bold")).pack(anchor="w")
            conds = [x for x in fi.get("condicoes", []) if x[1]]
            tk.Label(card, text=("Condições: " + ", ".join(f"{n} {a}/{m}" for n, a, m in conds)) if conds else "Condições: todas zeradas",
                     bg=c["CAMPO"], fg=c["VINHO"] if conds else c["TINTA2"], font=(self.fonte, 9, "bold" if conds else "normal"),
                     wraplength=320, justify="left").pack(anchor="w")
            inv = fi.get("inventario", [])
            carga = fi.get("carga") or []
            tk.Label(card, text=f"Bolsa: {sum(i['qtd'] for i in inv)} item(ns)"
                     + (f" · carga {carga[0]:g}/{carga[1]:g}" if len(carga) == 2 else "")
                     + (f" · {fi['dinheiro']}" if fi.get("dinheiro") else ""), bg=c["CAMPO"], fg=c["TINTA2"],
                     font=(self.fonte, 9)).pack(anchor="w")
        for e in j["efeitos"]:
            ln = tk.Frame(card, bg=c["PERG2"], padx=6, pady=2)
            ln.pack(fill="x", pady=(4, 0))
            dur = f"{e['rodadas']} turno(s)" if e["rodadas"] else "fim do combate" if e.get("fim_combate") else "sem fim"
            tk.Label(ln, text=f"⏳ {e['nome']} — {dur}", bg=c["PERG2"], fg=c["TINTA"], font=(self.fonte, 9, "bold")).pack(side="left")
            tk.Button(ln, text="✕", bg=c["PERG2"], fg=c["VINHO"], relief="flat", bd=0, cursor="hand2",
                      command=lambda n=nome, i=e["id"]: self.servidor.remover_condicao(n, i)).pack(side="right")
            if e.get("desc"):
                tk.Label(ln, text=e["desc"], bg=c["PERG2"], fg=c["TINTA2"], font=(self.fonte, 8, "italic"),
                         wraplength=300, justify="left").pack(side="bottom", anchor="w")
        bts = tk.Frame(card, bg=c["CAMPO"])
        bts.pack(fill="x", pady=(8, 0))
        ttk.Button(bts, text="Dano/Cura", command=lambda n=nome: self._dialogo_dano([n])).pack(side="left")
        ttk.Button(bts, text="Efeito", command=lambda n=nome: self._dialogo_condicao([n])).pack(side="left", padx=4)
        ttk.Button(bts, text="Condição", command=lambda n=nome: self._dialogo_pontos([n])).pack(side="left")
        if fi:
            ttk.Button(bts, text="Bolsa", command=lambda n=nome: self._dialogo_inventario(n)).pack(side="left", padx=4)
        return card

    def _atualizar_mestre(self):
        self._painel_agendado = False
        if not self.servidor:
            return
        p = self.servidor.painel()
        self._painel = p
        self._vez = p.get("vez", "")
        nomes = {j["nome"] for j in p["jogadores"]}
        self.selecionados &= nomes
        # fila de mãos
        sem = {j["nome"] for j in p["jogadores"] if j["sem_sinal"]}
        sel = self._nome_selecionado() if self._maos_tela else None
        self._maos_tela = list(p["maos"])
        self.lst_maos.delete(0, "end")
        for i, n in enumerate(p["maos"], 1):
            self.lst_maos.insert("end", f"  {i}.  ✋ {n}" + ("  (sem sinal)" if n in sem else ""))
        if p["maos"]:
            self.lst_maos.selection_set(p["maos"].index(sel) if sel in p["maos"] else 0)
        self.lbl_rodada.config(text=f"Rodada {p['rodada']}" + (f" · vez de {self._vez}" if self._vez else ""))
        sel_o = self._ordem_selecionada()
        self._ordem_tela = [o[0] for o in p["ordem"]]
        self.lst_ordem.delete(0, "end")
        for i, (n, v, _) in enumerate(p["ordem"]):
            self.lst_ordem.insert("end", f"{'⚔' if n == self._vez else '  '} {v:>3}  {n}")
            if n == self._vez:
                self.lst_ordem.itemconfigure(i, foreground=self.c["VINHO"])
        if not p["ordem"]:
            self.lst_ordem.insert("end", "  Fora de combate — 🎲 Iniciativa")
        elif sel_o in self._ordem_tela:
            self.lst_ordem.selection_set(self._ordem_tela.index(sel_o))
        self.lbl_sel.config(text=f"{len(self.selecionados)} marcado(s)" if self.selecionados else "marque cartões para agir em grupo")
        # cartões
        for w in self.grade_jog.winfo_children():
            w.destroy()
        largura = self.cv_jog.winfo_width() or 760
        cols = max(1, min(3, largura // 360))
        for i in range(3):
            self.grade_jog.columnconfigure(i, weight=1 if i < cols else 0, uniform="c" if i < cols else "")
        if not p["jogadores"]:
            tk.Label(self.grade_jog, text="Ninguém conectado ainda.\nNo PC: Sessão → Entrar como jogador.  No celular: abra o endereço ou o QR code.",
                     bg=self.c["PERG"], fg=self.c["TINTA2"], font=(self.fonte, 11, "italic"), justify="left").grid(row=0, column=0, sticky="w", pady=20)
        for i, j in enumerate(p["jogadores"]):
            self._cartao(self.grade_jog, j).grid(row=i // cols, column=i % cols, sticky="nsew", padx=5, pady=5)
        # registro
        self.txt_reg.configure(state="normal")
        self.txt_reg.delete("1.0", "end")
        for hora, texto in p["registro"]:
            self.txt_reg.insert("end", f"{hora}  {texto}\n")
        self.txt_reg.configure(state="disabled")
        self.title(f"✋ {len(p['maos'])} — Mesa do mestre" if p["maos"] else "Mesa do mestre")

    def _janela_acao(self, titulo, alvos):
        if not alvos:
            messagebox.showinfo("Sessão", "Marque pelo menos um jogador (caixinha no cartão).", parent=self)
            return None, None
        c = self.c
        w = tk.Toplevel(self)
        w.title(titulo)
        w.configure(background=c["PERG"])
        w.transient(self)
        w.resizable(False, False)
        f = tk.Frame(w, bg=c["PERG"], padx=20, pady=14)
        f.pack(fill="both", expand=True)
        tk.Label(f, text=titulo, bg=c["PERG"], fg=c["VINHO"], font=(self.fonte, 14, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        tk.Label(f, text="Para: " + ", ".join(alvos), bg=c["PERG"], fg=c["TINTA2"], font=(self.fonte, 10, "italic"),
                 wraplength=360, justify="left").grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 10))
        return w, f

    def _dialogo_dano(self, alvos):
        w, f = self._janela_acao("Dano ou cura", alvos)
        if not w:
            return
        c = self.c
        modo, valor, tipo = tk.StringVar(value="dano"), tk.StringVar(), tk.StringVar(value="")
        lin = tk.Frame(f, bg=c["PERG"])
        lin.grid(row=2, column=0, columnspan=2, sticky="w")
        ttk.Radiobutton(lin, text="Dano", value="dano", variable=modo).pack(side="left")
        ttk.Radiobutton(lin, text="Cura", value="cura", variable=modo).pack(side="left", padx=10)
        tk.Label(f, text="Valor", bg=c["PERG"], fg=c["TINTA"], font=(self.fonte, 11)).grid(row=3, column=0, sticky="w", pady=4)
        e = ttk.Entry(f, textvariable=valor, width=8, font=(self.fonte, 13))
        e.grid(row=3, column=1, sticky="w")
        e.focus_set()
        tk.Label(f, text="Tipo", bg=c["PERG"], fg=c["TINTA"], font=(self.fonte, 11)).grid(row=4, column=0, sticky="w", pady=4)
        ttk.Combobox(f, values=[""] + TIPOS_DANO, textvariable=tipo, width=16, state="readonly").grid(row=4, column=1, sticky="w")
        tk.Label(f, text="Descrição", bg=c["PERG"], fg=c["TINTA"], font=(self.fonte, 11)).grid(row=5, column=0, sticky="nw", pady=4)
        desc = tk.Text(f, width=36, height=3, wrap="word", font=(self.fonte, 10))
        desc.grid(row=5, column=1, sticky="w", pady=4)
        msg = tk.Label(f, text="A ficha de cada jogador desconta a RD (d4) e as resistências do tipo.\n"
                               "Magia Pura e Relâmpago ignoram RD; Direto ignora tudo.", bg=c["PERG"],
                       fg=c["TINTA2"], font=(self.fonte, 9, "italic"), justify="left")
        msg.grid(row=6, column=0, columnspan=2, sticky="w")

        def ok(*_):
            try:
                n = int(valor.get().strip())
                if n <= 0:
                    raise ValueError
            except ValueError:
                msg.config(text="Digite um número inteiro maior que zero.", fg=c["VINHO"])
                return
            n = -n if modo.get() == "cura" else n
            self.servidor.enviar_dano(alvos, n, tipo.get().strip() if n > 0 else "", desc.get("1.0", "end").strip())
            w.destroy()
        e.bind("<Return>", ok)
        bt = tk.Frame(f, bg=c["PERG"])
        bt.grid(row=7, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(bt, text="Cancelar", command=w.destroy).pack(side="right")
        ttk.Button(bt, text="Enviar", command=ok).pack(side="right", padx=6)
        w.grab_set()

    def _dialogo_condicao(self, alvos):
        w, f = self._janela_acao("Efeito", alvos)
        if not w:
            return
        c = self.c
        nome, rod = tk.StringVar(), tk.StringVar(value="1")
        tk.Label(f, text="Efeito", bg=c["PERG"], fg=c["TINTA"], font=(self.fonte, 11)).grid(row=2, column=0, sticky="w", pady=4)
        cb = ttk.Combobox(f, values=[f"{n} ({EFEITOS[n][0]})" for n in CONDICOES_SUGERIDAS], textvariable=nome, width=24)
        cb.grid(row=2, column=1, sticky="w")
        cb.focus_set()
        tk.Label(f, text="Turnos", bg=c["PERG"], fg=c["TINTA"], font=(self.fonte, 11)).grid(row=3, column=0, sticky="w", pady=4)
        ttk.Spinbox(f, from_=0, to=99, textvariable=rod, width=5).grid(row=3, column=1, sticky="w")
        tk.Label(f, text="Em combate conta os turnos do afetado; fora dele, as rodadas. 0 = até você remover.\n"
                         + R.NOTA_EFEITOS, bg=c["PERG"], fg=c["TINTA2"], font=(self.fonte, 9, "italic"),
                 wraplength=360, justify="left").grid(row=4, column=1, sticky="w")
        tk.Label(f, text="Descrição", bg=c["PERG"], fg=c["TINTA"], font=(self.fonte, 11)).grid(row=5, column=0, sticky="nw", pady=4)
        desc = tk.Text(f, width=36, height=3, wrap="word", font=(self.fonte, 10))
        desc.grid(row=5, column=1, sticky="w", pady=4)

        def escolheu(*_):
            n = nome.get().split(" (")[0]
            if n in EFEITOS:
                desc.delete("1.0", "end")
                desc.insert("1.0", EFEITOS[n][1])
        cb.bind("<<ComboboxSelected>>", escolheu)
        msg = tk.Label(f, text="", bg=c["PERG"], fg=c["VINHO"], font=(self.fonte, 9, "bold"))
        msg.grid(row=6, column=0, columnspan=2, sticky="w")

        def ok(*_):
            n = nome.get().strip()
            n = n.split(" (")[0] if n.split(" (")[0] in EFEITOS else n
            try:
                r = int(rod.get())
                if r < 0:
                    raise ValueError
            except ValueError:
                msg.config(text="Turnos: número inteiro (0 ou mais).")
                return
            if not n:
                msg.config(text="Escolha ou escreva um efeito.")
                return
            self.servidor.adicionar_condicao(alvos, n[:30], r, desc.get("1.0", "end").strip())
            w.destroy()
        bt = tk.Frame(f, bg=c["PERG"])
        bt.grid(row=7, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(bt, text="Cancelar", command=w.destroy).pack(side="right")
        ttk.Button(bt, text="Aplicar", command=ok).pack(side="right", padx=6)
        w.grab_set()

    def _dialogo_pontos(self, alvos):
        """Pontos de condição do livro, que enchem a barra de 100 de cada jogador."""
        w, f = self._janela_acao("Pontos de condição", alvos)
        if not w:
            return
        c = self.c
        cond, pts, dt = tk.StringVar(value="Sangramento"), tk.StringVar(), tk.StringVar(value="15")
        tk.Label(f, text="Condição", bg=c["PERG"], fg=c["TINTA"], font=(self.fonte, 11)).grid(row=2, column=0, sticky="w", pady=4)
        cb = ttk.Combobox(f, values=R.CONDICOES, textvariable=cond, width=16, state="readonly")
        cb.grid(row=2, column=1, sticky="w")
        tk.Label(f, text="Pontos", bg=c["PERG"], fg=c["TINTA"], font=(self.fonte, 11)).grid(row=3, column=0, sticky="w", pady=4)
        e = ttk.Entry(f, textvariable=pts, width=8, font=(self.fonte, 13))
        e.grid(row=3, column=1, sticky="w")
        e.focus_set()
        tk.Label(f, text="DT do inimigo", bg=c["PERG"], fg=c["TINTA"], font=(self.fonte, 11)).grid(row=4, column=0, sticky="w", pady=4)
        ttk.Entry(f, textvariable=dt, width=8).grid(row=4, column=1, sticky="w")
        tk.Label(f, text="Descrição", bg=c["PERG"], fg=c["TINTA"], font=(self.fonte, 11)).grid(row=5, column=0, sticky="nw", pady=4)
        desc = tk.Text(f, width=36, height=2, wrap="word", font=(self.fonte, 10))
        desc.grid(row=5, column=1, sticky="w", pady=4)
        info = tk.Label(f, text="", bg=c["PERG"], fg=c["TINTA2"], font=(self.fonte, 9, "italic"), wraplength=380, justify="left")
        info.grid(row=6, column=0, columnspan=2, sticky="w")
        msg = tk.Label(f, text="", bg=c["PERG"], fg=c["VINHO"], font=(self.fonte, 9, "bold"))
        msg.grid(row=7, column=0, columnspan=2, sticky="w")

        def mostra(*_):
            n = cond.get()
            info.config(text=f"A ficha rola {R.CONDICAO_TESTE[n]} contra a DT: sucesso recebe metade. "
                             f"Barra cheia: {R.CONDICAO_ATIVA[n]['desc']}")
        cb.bind("<<ComboboxSelected>>", mostra)
        mostra()

        def ok(*_):
            try:
                p, d = int(pts.get()), int(dt.get())
                if p <= 0 or d < 0:
                    raise ValueError
            except ValueError:
                msg.config(text="Pontos e DT: números inteiros (pontos maior que zero).")
                return
            self.servidor.enviar_pontos_condicao(alvos, cond.get(), p, d, desc.get("1.0", "end").strip())
            w.destroy()
        e.bind("<Return>", ok)
        bt = tk.Frame(f, bg=c["PERG"])
        bt.grid(row=8, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(bt, text="Cancelar", command=w.destroy).pack(side="right")
        ttk.Button(bt, text="Enviar", command=ok).pack(side="right", padx=6)
        w.grab_set()

    def _dialogo_item(self, alvos):
        """Dar um item: da lista do livro (peso já preenchido) ou personalizado."""
        w, f = self._janela_acao("Dar item", alvos)
        if not w:
            return
        c = self.c
        cats = ["Todos"] + sorted({i["categoria"] for i in ITENS_LIVRO})
        cat, nome, peso, qtd = tk.StringVar(value="Todos"), tk.StringVar(), tk.StringVar(value="1"), tk.StringVar(value="1")
        tk.Label(f, text="Categoria", bg=c["PERG"], fg=c["TINTA"], font=(self.fonte, 11)).grid(row=2, column=0, sticky="w", pady=4)
        cb_cat = ttk.Combobox(f, values=cats, textvariable=cat, width=30, state="readonly")
        cb_cat.grid(row=2, column=1, sticky="w")
        tk.Label(f, text="Item", bg=c["PERG"], fg=c["TINTA"], font=(self.fonte, 11)).grid(row=3, column=0, sticky="w", pady=4)
        cb = ttk.Combobox(f, textvariable=nome, width=30)
        cb.grid(row=3, column=1, sticky="w")
        cb.focus_set()
        tk.Label(f, text="Peso (cada)", bg=c["PERG"], fg=c["TINTA"], font=(self.fonte, 11)).grid(row=4, column=0, sticky="w", pady=4)
        ttk.Entry(f, textvariable=peso, width=8).grid(row=4, column=1, sticky="w")
        tk.Label(f, text="Quantidade", bg=c["PERG"], fg=c["TINTA"], font=(self.fonte, 11)).grid(row=5, column=0, sticky="w", pady=4)
        ttk.Spinbox(f, from_=1, to=99, textvariable=qtd, width=5).grid(row=5, column=1, sticky="w")
        info = tk.Label(f, text="Escolha da lista ou escreva um item personalizado.", bg=c["PERG"], fg=c["TINTA2"],
                        font=(self.fonte, 9, "italic"), wraplength=380, justify="left")
        info.grid(row=6, column=0, columnspan=2, sticky="w", pady=(4, 0))
        tk.Label(f, text="Nota", bg=c["PERG"], fg=c["TINTA"], font=(self.fonte, 11)).grid(row=7, column=0, sticky="w", pady=4)
        nota = tk.StringVar()
        ttk.Entry(f, textvariable=nota, width=32).grid(row=7, column=1, sticky="w")
        msg = tk.Label(f, text="", bg=c["PERG"], fg=c["VINHO"], font=(self.fonte, 9, "bold"))
        msg.grid(row=8, column=0, columnspan=2, sticky="w")
        por_nome = {i["nome"]: i for i in ITENS_LIVRO}

        def filtra(*_):
            cb.configure(values=[i["nome"] for i in ITENS_LIVRO if cat.get() in ("Todos", i["categoria"])])
        cb_cat.bind("<<ComboboxSelected>>", filtra)
        filtra()

        def escolheu(*_):
            it = por_nome.get(nome.get())
            if it:
                peso.set(f"{it['peso']:g}")
                info.config(text=f"{it['desc']}  ({it['preco']})")
        cb.bind("<<ComboboxSelected>>", escolheu)

        def ok(*_):
            n = nome.get().strip()
            try:
                q = int(qtd.get())
                pz = float(peso.get().replace(",", ".") or 0)
                if q < 1 or pz < 0:
                    raise ValueError
            except ValueError:
                msg.config(text="Peso e quantidade: números (quantidade 1 ou mais).")
                return
            if not n:
                msg.config(text="Escolha ou escreva o item.")
                return
            self.servidor.dar_item(alvos, {"item": n[:40], "carga": f"{pz:g}", "qtd": q}, nota.get().strip())
            w.destroy()
        bt = tk.Frame(f, bg=c["PERG"])
        bt.grid(row=9, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(bt, text="Cancelar", command=w.destroy).pack(side="right")
        ttk.Button(bt, text="Dar", command=ok).pack(side="right", padx=6)
        w.grab_set()

    def _dialogo_inventario(self, nome):
        """Bolsa do jogador: ver, tirar e dar itens."""
        j = next((x for x in self._painel.get("jogadores", []) if x["nome"] == nome), None)
        if not j:
            return
        fi, c = j["ficha"], self.c
        w = tk.Toplevel(self)
        w.title(f"Bolsa — {fi.get('personagem') or nome}")
        w.configure(background=c["PERG"])
        w.transient(self)
        f = tk.Frame(w, bg=c["PERG"], padx=18, pady=14)
        f.pack(fill="both", expand=True)
        carga = fi.get("carga") or []
        tk.Label(f, text=f"Bolsa de {fi.get('personagem') or nome}", bg=c["PERG"], fg=c["VINHO"],
                 font=(self.fonte, 14, "bold")).pack(anchor="w")
        tk.Label(f, text=(f"Carga {carga[0]:g}/{carga[1]:g}" if len(carga) == 2 else "")
                 + (f"  ·  Dinheiro: {fi['dinheiro']}" if fi.get("dinheiro") else ""), bg=c["PERG"], fg=c["TINTA2"],
                 font=(self.fonte, 10, "italic")).pack(anchor="w", pady=(0, 8))
        lista = tk.Frame(f, bg=c["CAMPO"], highlightthickness=1, highlightbackground=c["OURO"])
        lista.pack(fill="both", expand=True)
        inv = fi.get("inventario", [])
        if not inv:
            tk.Label(lista, text="A bolsa está vazia.", bg=c["CAMPO"], fg=c["TINTA2"], font=(self.fonte, 10, "italic"),
                     padx=10, pady=10).pack()
        for i, it in enumerate(inv):
            ln = tk.Frame(lista, bg=c["CAMPO"], padx=8, pady=2)
            ln.pack(fill="x")
            tk.Label(ln, text=f"{it['qtd']}× {it['item']}", bg=c["CAMPO"], fg=c["TINTA"], font=(self.fonte, 11), anchor="w").pack(side="left")
            tk.Label(ln, text=f"peso {it['carga'] or 0}", bg=c["CAMPO"], fg=c["TINTA2"], font=(self.fonte, 9)).pack(side="left", padx=8)
            ttk.Button(ln, text="Tirar tudo", command=lambda i=i, it=it: (self.servidor.tirar_item(nome, i, it["item"], it["qtd"]),
                                                                          w.destroy())).pack(side="right")
            if it["qtd"] > 1:
                ttk.Button(ln, text="Tirar 1", command=lambda i=i, it=it: (self.servidor.tirar_item(nome, i, it["item"], 1),
                                                                         w.destroy())).pack(side="right", padx=4)
        bt = tk.Frame(f, bg=c["PERG"])
        bt.pack(fill="x", pady=(10, 0))
        ttk.Button(bt, text="Fechar", command=w.destroy).pack(side="right")
        ttk.Button(bt, text="＋ Dar item", command=lambda: (w.destroy(), self._dialogo_item([nome]))).pack(side="right", padx=6)

    # --- tela 3: jogador
    def _ser_jogador(self):
        ip, nome = self.v_ip.get().strip(), self.v_nome.get().strip()
        if not nome:
            messagebox.showinfo("Sessão", "Preencha seu nome.", parent=self)
            return
        if ip:
            self._conectar(ip, PORTA, nome)
            return
        self.btn_entrar.config(state="disabled")
        self.lbl_busca.config(text="Procurando o mestre na rede…")
        procurar_mestre(self.fila)

    def _conectar(self, ip, porta, nome):
        try:
            self.cliente = Cliente(self.fila)
            self.cliente.conectar(ip, porta, nome)
        except (ValueError, OSError) as e:
            self.cliente = None
            self.btn_entrar.config(state="normal")
            self.lbl_busca.config(text="")
            messagebox.showerror("Sessão", f"Não consegui conectar em {ip}.\n"
                                           f"Confira se o mestre já entrou como mestre.\n{e}", parent=self)
            return
        self.ultimo_ip = ip
        t = self._trocar()
        self._rot(t, "✋ Sessão", 18, self.c["OURO2"], bold=True).pack()
        self.lbl_status = self._rot(t, "Conectado.", 10, italic=True)
        self.lbl_status.pack(pady=(2, 20))
        self.btn_mao = tk.Button(t, text="✋  Levantar a mão", font=(self.fonte, 18, "bold"), bg=self.c["OURO"],
                                 fg="#1b2520", activebackground=self.c["OURO2"], relief="flat", pady=26,
                                 command=self._alternar_mao)
        self.btn_mao.pack(fill="x", pady=10)
        self.lbl_palavra = self._rot(t, "", 14, self.c["OURO2"], bold=True)
        self.lbl_palavra.pack(pady=(12, 6))
        self.lbl_evento = self._rot(t, "", 11, self.c["ALERTA"], bold=True, wraplength=400, justify="center")
        self.lbl_evento.pack(pady=(0, 8))
        self.lbl_rodada_j = self._rot(t, "", 10, self.c["TINTA2_FUNDO"], italic=True)
        self.lbl_rodada_j.pack()
        self.lbl_efeitos = self._rot(t, "", 10, self.c["OURO2"], wraplength=400, justify="left")
        self.lbl_efeitos.pack(anchor="w", pady=(6, 0))
        if self.ponte:
            self._rot(t, "Sua Vida, Mana e Vigor aparecem para o mestre enquanto esta janela estiver aberta.",
                      9, italic=True, wraplength=400, justify="center").pack(side="bottom", pady=(10, 0))
            self.after(300, self._enviar_ficha)

    def _enviar_ficha(self):
        """Manda o resumo da ficha ao mestre sempre que muda (verifica a cada segundo)."""
        if not self.cliente or not self.ponte:
            return
        try:
            dados = self.ponte.resumo()
        except Exception:   # a ficha nunca derruba a sessão
            dados = None
        if dados and dados != self._ultima_ficha and self.cliente.enviar({"t": "ficha", "dados": dados}):
            self._ultima_ficha = dados
        self.after(1000, self._enviar_ficha)

    def _relatar(self, texto, ativou=None):
        if self.cliente and texto:
            self.cliente.enviar({"t": "relato", "texto": texto, "ativou": ativou})

    def _receber_evento(self, ev):
        tipo = ev.get("tipo")
        if tipo == "dano":
            valor, desc = int(ev.get("valor", 0)), str(ev.get("desc", ""))
            res, relato = self.ponte.aplicar_dano(valor, str(ev.get("dano_tipo", "")), desc) if self.ponte else ("", "")
            oque = f"Cura de {-valor}" if valor < 0 else f"{valor} de dano" + (f" ({ev.get('dano_tipo')})" if ev.get("dano_tipo") else "")
            texto = oque + (f" — {desc}" if desc else "") + (f"\n{res}" if res else "")
            self._relatar(relato)
            self._ultima_ficha = None
            self._aviso_sonoro()
        elif tipo == "condicao":
            dur = (f"{ev.get('rodadas')} turno(s)" if ev.get("rodadas")
                   else "até o fim do combate" if ev.get("fim_combate") else "até o mestre remover")
            texto = f"Efeito: {ev.get('nome')} ({dur})" + (f" — {ev.get('desc')}" if ev.get("desc") else "")
            self._aviso_sonoro()
        elif tipo == "cond_pontos" and self.ponte:
            texto, relato, ativou = self.ponte.pontos_condicao(str(ev.get("condicao", "")), int(ev.get("pontos", 0)),
                                                              int(ev.get("dt", 0)), str(ev.get("desc", "")))
            self._relatar(relato, ativou)
            self._ultima_ficha = None
            self._aviso_sonoro()
        elif tipo == "item" and self.ponte:
            texto = self.ponte.item(ev)
            self._ultima_ficha = None
        elif tipo == "vez":
            texto = "⚔ É a sua vez!"
            if self.ponte:
                self.ponte.minha_vez()
            self._aviso_sonoro()
        elif tipo == "combate":
            inicio = ev.get("fase") == "inicio"
            texto = ("⚔ Começou o combate: ações, contra-encantamentos e usos por combate renovados." if inicio
                     else "🏳 Fim do combate: usos por combate renovados.")
            if self.ponte and hasattr(self.ponte, "combate"):
                self.ponte.combate(inicio)
            self._ultima_ficha = None
        elif tipo == "fim":
            texto = f"Terminou: {ev.get('nome')}"
        else:
            return
        self._avisos = ([texto] + self._avisos)[:3]   # os três mais recentes, o novo em cima
        self.lbl_evento.config(text="\n".join(self._avisos))
        if self.ponte:
            self.ponte.aviso(texto)

    def _mostrar_efeitos(self, lista, rodada, vez="", turno=0):
        self.efeitos = lista
        self.lbl_rodada_j.config(text=f"Rodada {rodada}" + (f" · vez de {vez}" if vez else "")
                                 + ("  ⚔ SUA VEZ" if vez and vez == self.meu_nome else ""))
        self.lbl_efeitos.config(text="\n".join(f"⏳ {e['nome']} — " + (f"{e['rodadas']} turno(s)" if e["rodadas"] else
                                                                        "até o fim do combate" if e.get("fim_combate") else "sem fim")
                                               + (f": {e['desc']}" if e.get("desc") else "") for e in lista) or "Nenhum efeito ativo.")
        if self.ponte:
            self.ponte.efeitos(lista, rodada)

    def _voltar_escolha(self):
        if self.cliente:
            self.cliente.parar()
        self.cliente = None
        self._btn_voltar = None
        self.mao_levantada = False
        self._escolha()

    def _alternar_mao(self):
        if not self.cliente or not self.cliente.enviar({"t": "abaixar" if self.mao_levantada else "mao"}):
            self.lbl_status.config(text="Sem conexão com o mestre.")

    def _pintar_mao(self):
        if self.mao_levantada:
            self.btn_mao.config(text="✋  Mão levantada — toque para abaixar", bg=self.c["VERDE"], fg="#ffffff")
        else:
            self.btn_mao.config(text="✋  Levantar a mão", bg=self.c["OURO"], fg="#1b2520")

    # --- laço de eventos (thread de rede -> interface)
    def _bombear(self):
        try:
            while True:
                ev = self.fila.get_nowait()
                if ev[0] == "achou" and self.cliente is None and hasattr(self, "btn_entrar"):
                    self._conectar(ev[1], ev[2], self.v_nome.get().strip())
                elif ev[0] == "nao_achou" and self.cliente is None and hasattr(self, "btn_entrar"):
                    self.btn_entrar.config(state="normal")
                    ultimo = self.c.get("ULTIMO_IP", "")
                    if ultimo and not self.v_ip.get().strip():
                        self.v_ip.set(ultimo)
                        self.lbl_busca.config(text="Não encontrei o mestre. Preenchi o último IP usado; "
                                                   "confira e toque em Entrar de novo.")
                    else:
                        self.lbl_busca.config(text="Não encontrei o mestre. Ele já entrou como mestre? "
                                                   "Se sim, digite o IP dele abaixo.")
                elif ev[0] == "mao":
                    self._aviso_sonoro()
                    if hasattr(self, "lbl_aviso"):
                        self.lbl_aviso.config(text=f"✋ {ev[1]} levantou a mão")
                elif ev[0] == "ok" and hasattr(self, "lbl_status"):
                    self.meu_nome = ev[1]
                    self.lbl_status.config(text=f"Conectado como {ev[1]}")
                elif ev[0] == "estado" and self.cliente:
                    self.mao_levantada = ev[1]
                    self._pintar_mao()
                    if ev[1]:
                        self.lbl_palavra.config(text="")
                elif ev[0] == "palavra" and self.cliente:
                    self.lbl_palavra.config(text="🎤 O mestre te deu a palavra!")
                    self._aviso_sonoro()
                elif ev[0] == "evento" and self.cliente:
                    self._receber_evento(ev[1])
                elif ev[0] == "efeitos" and self.cliente:
                    self._mostrar_efeitos(*ev[1:])
                elif ev[0] == "caiu" and self.cliente:
                    self.lbl_status.config(text="Conexão perdida com o mestre.")
                    self.btn_mao.config(state="disabled")
                    if not self._btn_voltar:
                        self._btn_voltar = ttk.Button(self.tela, text="Conectar de novo", command=self._voltar_escolha)
                        self._btn_voltar.pack(pady=(4, 0))
                if self.servidor and ev[0] in ("mudou", "mao", "registro"):
                    self._agendar_painel()
        except queue.Empty:
            pass
        except tk.TclError:
            return
        self.after(150, self._bombear)

    def fechar(self):
        if self.ponte:
            try:
                self.ponte.efeitos([], 0)
            except Exception:
                pass
        for x in (self.servidor, self.cliente):
            if x:
                x.parar()
        self.ao_fechar(self.ultimo_ip)
        self.destroy()
