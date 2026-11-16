# -*- coding: utf-8 -*-
"""Sessão de jogo em rede local: jogadores "levantam a mão" e o mestre recebe o aviso.

O mestre abre um servidor TCP (porta 5757 por padrão) e os jogadores se conectam pelo IP dele.
Só usa a biblioteca padrão do Python. Mensagens: JSON, uma por linha.
"""
import hashlib
import json
import os
import queue
import random
import socket
import threading
import time
import tkinter as tk
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from tkinter import ttk, messagebox
import urllib.error
import urllib.request
from urllib.parse import parse_qs, quote, urlparse

try:
    import segno   # QR code (pip install segno); sem ele o app funciona, só não mostra o QR
except ImportError:
    segno = None
try:
    from pagina_celular import HTML as PAGINA_FICHA   # ficha completa do celular (gerada por celular/build.py)
except ImportError:
    PAGINA_FICHA = None

import regras as R
from grupo import Grupo, CFG_ROTULOS, SUSSURRO_MODOS, REACOES
from tunel import Tunel
from fichas_mesa import Fichas, slug as slug_ficha, LIMITE_BYTES as LIMITE_FICHA
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
SERVIDOR_ATIVO = None   # a sessão do mestre aberta agora (o painel do mestre, mestre_web.py, usa)
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
var id=localStorage.getItem('preva_id')||'', nome=localStorage.getItem('preva_nome')||'', chave=localStorage.getItem('preva_chave')||'';
var senha=(location.hash.match(/s=([^&]+)/)||[])[1]||localStorage.getItem('preva_senha')||'';
var $=function(x){return document.getElementById(x)};
var levantada=false, timer=null;
$('nome').value=nome;
function post(url,corpo){return fetch(url,{method:'POST',body:JSON.stringify(corpo)}).then(function(r){return r.json()})}
function entrar(){
  nome=$('nome').value.trim(); if(!nome){$('nome').focus();return}
  localStorage.setItem('preva_nome',nome);
  post('/api/oi',{nome:nome,id:id,chave:chave,senha:senha}).then(function(r){
    if(r.erro){senha=prompt('Senha da mesa:')||'';localStorage.setItem('preva_senha',senha);if(senha){entrar()}return}
    id=r.id; chave=r.chave||''; localStorage.setItem('preva_id',id); localStorage.setItem('preva_chave',chave);
    $('t1').classList.add('oculto'); $('t2').classList.remove('oculto');
    $('quem').textContent=id; if(!timer){timer=setInterval(consultar,1000)} consultar();
  }).catch(function(){alert('N\\u00e3o consegui falar com o mestre. Voc\\u00ea est\\u00e1 na mesma rede?')});
}
function pintar(){
  var b=$('mao'); b.className=levantada?'on':'';
  b.innerHTML=levantada?'&#9995; M&atilde;o levantada &mdash; toque para abaixar':'&#9995; Levantar a m&atilde;o';
}
function consultar(){
  fetch('/api/estado?id='+encodeURIComponent(id)+'&k='+chave).then(function(r){return r.json()}).then(function(r){
    if(!r.ok){ // o mestre reiniciou ou a conex\\u00e3o expirou: entra de novo
      post('/api/oi',{nome:nome,id:id,chave:chave,senha:senha}).then(function(x){if(x.erro){return}id=x.id;chave=x.chave||'';localStorage.setItem('preva_id',id);localStorage.setItem('preva_chave',chave);$('quem').textContent=id});return}
    $('st').textContent='Conectado'; levantada=r.mao; pintar();
    if(r.palavra){$('msg').textContent='\\ud83c\\udfa4 O mestre te deu a palavra!';
      if(navigator.vibrate){navigator.vibrate([300,120,300])}
      setTimeout(function(){$('msg').textContent=''},8000)}
  }).catch(function(){$('st').textContent='Sem conex\\u00e3o com o mestre\\u2026'});
}
$('entrar').onclick=entrar;
$('nome').onkeydown=function(e){if(e.key==='Enter')entrar()};
$('mao').onclick=function(){
  post(levantada?'/api/abaixar':'/api/mao',{id:id,chave:chave}).then(consultar);
};
</script></body></html>
"""


class _Pagina(BaseHTTPRequestHandler):
    """Atende os celulares (navegador). `srv` é preenchido na criação (veja Servidor.iniciar)."""
    srv = None
    protocol_version = "HTTP/1.1"   # mantém a conexão (o túnel da internet reaproveita)
    timeout = 75

    def log_message(self, *a):
        pass

    def _resp(self, corpo, tipo):
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        if not self.srv.ativo:   # mesa fechada: não segura a conexão (senão o aparelho fica falando com a mesa antiga)
            self.send_header("Connection", "close")
            self.close_connection = True
        self.end_headers()
        self.wfile.write(corpo)

    def _json(self, obj):
        self._resp(json.dumps(obj).encode("utf-8"), "application/json")

    def _fechada(self):
        if self.srv.ativo:
            return False
        self.close_connection = True
        try:
            self.send_error(503)
        except OSError:
            pass
        return True

    def do_GET(self):
        if self._fechada():
            return
        u = urlparse(self.path)
        try:
            if u.path == "/api/estado":
                q = parse_qs(u.query)
                try:
                    ack = int(q["ack"][0]) if "ack" in q else None
                except ValueError:
                    ack = None
                try:
                    gv = int(q["gv"][0]) if "gv" in q else None
                except ValueError:
                    gv = None
                try:
                    espera = float(q["espera"][0]) if "espera" in q else 0
                except ValueError:
                    espera = 0
                ident = q.get("id", [""])[0]
                if not self.srv.web_confere(ident, q.get("k", [""])[0]):
                    self._json({"ok": False})
                else:
                    self._json(self.srv.web_espera(ident, ack, gv, q.get("sig", [""])[0], espera))
            elif u.path == "/api/sessao":
                self._json({"sessao": True, "rodada": self.srv.rodada, "senha": bool(self.srv.senha),
                            "fichas": self.srv.fichas_lista(parse_qs(u.query).get("id", [""])[0])})
            elif u.path == "/api/foto":          # foto do personagem de uma ficha da mesa (o ?v= muda quando a foto muda)
                dados, tipo = self.srv.fichas_arq.foto(slug_ficha(parse_qs(u.query).get("f", [""])[0]))
                if dados is None:
                    self.send_error(404)
                else:
                    self.send_response(200)
                    self.send_header("Content-Type", tipo)
                    self.send_header("Content-Length", str(len(dados)))
                    self.send_header("Cache-Control", "max-age=86400")
                    self.end_headers()
                    self.wfile.write(dados)
            elif u.path == "/api/ficha-arq":
                q = parse_qs(u.query)
                self._json(self.srv.ficha_baixar(q.get("id", [""])[0], q.get("k", [""])[0]))
            elif u.path in ("/", "/index.html"):
                self._resp((PAGINA_FICHA or PAGINA_WEB).encode("utf-8"), "text/html; charset=utf-8")
            elif u.path == "/mao":
                self._resp(PAGINA_WEB.encode("utf-8"), "text/html; charset=utf-8")
            else:
                self.send_error(404)
        except OSError:
            pass

    def do_POST(self):
        if self._fechada():
            return
        try:
            limite = LIMITE_FICHA if self.path in ("/api/ficha-salvar", "/api/fichas-pc") else 20000
            n = min(int(self.headers.get("Content-Length") or 0), limite)
            corpo = json.loads(self.rfile.read(n) or b"{}")
            if not isinstance(corpo, dict):
                corpo = {}
        except (ValueError, OSError):
            corpo = {}
        ident = str(corpo.get("id", ""))
        try:
            if self.path == "/api/oi":
                self._json(self.srv.web_entrar(str(corpo.get("nome", "")).strip()[:30], ident,
                                               str(corpo.get("senha", "")), str(corpo.get("chave", "")), bool(corpo.get("pc")),
                                               str(corpo.get("ficha", ""))[:40], str(corpo.get("codigo", ""))[:12]))
            elif not self.srv.web_confere(ident, str(corpo.get("chave", ""))):
                self._json({"ok": False, "erro": "Você não está na mesa."})
            elif self.path == "/api/mao":
                self._json({"ok": self.srv.web_mao(ident, True)})
            elif self.path == "/api/abaixar":
                self._json({"ok": self.srv.web_mao(ident, False)})
            elif self.path == "/api/ficha":
                self._json({"ok": self.srv.receber_ficha(ident, corpo.get("dados"), web=True)})
            elif self.path == "/api/ficha-salvar":
                self._json(self.srv.ficha_salvar(ident, corpo.get("estado"), corpo.get("base"), bool(corpo.get("forcar"))))
            elif self.path == "/api/fichas-pc":
                self._json(self.srv.ficha_acao(ident, corpo.get("m")))
            elif self.path == "/api/grupo":
                with self.srv.lock:
                    na_mesa = ident in self.srv.web
                    if na_mesa:
                        self.srv.web[ident]["visto"] = time.time()
                self._json(self.srv.grupo_acao(ident, corpo) if na_mesa else {"ok": False, "erro": "Você não está na mesa."})
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
class Servidor(Grupo):
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
        self.pendentes = {}    # celulares: nome -> eventos (com "seq") ainda não confirmados pelo celular
        self._seq_ev = 0       # numera os eventos dos celulares, para a confirmação (ack)
        self.token = "%08x" % random.getrandbits(32)   # muda quando o mestre reinicia: o celular zera a contagem
        self.rodada = 1
        self.registro = []     # (hora, texto) para o painel do mestre
        self._seq = 0
        self.ordem = []        # [[nome, iniciativa, bônus]] em ordem de turno (vazia = fora de combate)
        self.vez = -1          # posição de quem age agora em self.ordem
        self.abertura = ""     # primeiro atacante: age antes de a tabela de iniciativa começar a rodar
        self.ini_detalhe = {}  # nome -> {rolos, bonus, total, rodadas} da última iniciativa rolada
        self.turno = 0         # conta os turnos passados (o celular usa para o desgaste de armas)
        self.senha = ""        # senha da mesa (vazia = entra quem souber o endereço)
        self._erros_senha = []
        self._salvo = ""
        self.fichas_arq = Fichas()   # pasta fichas/: um .json por jogador
        self.ficha_pc = {}           # jogador do PC (conexão direta) -> ficha da mesa que ele escolheu
        self._grupo_init()     # interação entre jogadores (grupo.py)

    # --- mesa guardada: se o PC do mestre fechar, dá para retomar de onde parou
    ARQ_SESSAO = os.path.join(os.path.expanduser("~"), ".prevalecentes", "sessao.json")
    VALE_HORAS = 12

    def _retrato(self):
        if True:
            return {"token": self.token, "senha": self.senha, "rodada": self.rodada, "ordem": self.ordem, "vez": self.vez,
                    "turno": self.turno, "efeitos": self.efeitos, "fichas": self.fichas, "pendentes": self.pendentes,
                    "seq_ev": self._seq_ev, "seq": self._seq, "registro": self.registro[:200], "maos": self.maos,
                    "web": {n: w.get("chave", "") for n, w in self.web.items()}, "pc": list(self.clientes)}

    def salvar_sessao(self):
        """Grava a mesa em disco quando algo mudou (chamado a cada 1,5 s pelo laço do anúncio)."""
        try:
            with self.lock:
                txt = json.dumps(self._retrato(), ensure_ascii=False, sort_keys=True)
            if txt == self._salvo:
                return False
            os.makedirs(os.path.dirname(self.ARQ_SESSAO), exist_ok=True)
            tmp = self.ARQ_SESSAO + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write('{"hora": %r, "mesa": %s}' % (time.time(), txt))
            os.replace(tmp, self.ARQ_SESSAO)
            self._salvo = txt
            return True
        except (OSError, TypeError, ValueError):
            return False

    @classmethod
    def sessao_salva(cls):
        """A mesa guardada, se houver uma recente com jogadores: {"hora", "mesa"}; senão None."""
        try:
            with open(cls.ARQ_SESSAO, encoding="utf-8") as f:
                d = json.load(f)
            m = d["mesa"]
            if time.time() - float(d["hora"]) > cls.VALE_HORAS * 3600 or not (m.get("web") or m.get("pc")):
                return None
            return d
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def retomar(self, mesa):
        """Volta a mesa guardada: rodada, ordem de turno, efeitos, fichas e os eventos que ainda não chegaram.
        Os celulares e os PCs por link continuam com o mesmo nome; os PCs da rede local entram de novo sozinhos."""
        try:
            with self.lock:
                self.token = str(mesa.get("token") or self.token)
                self.senha = str(mesa.get("senha") or "")
                self.rodada = int(mesa.get("rodada") or 1)
                self.ordem = [list(o) for o in mesa.get("ordem") or []]
                self.vez = int(mesa.get("vez", -1))
                self.turno = int(mesa.get("turno") or 0)
                self.efeitos = {str(k): list(v) for k, v in (mesa.get("efeitos") or {}).items()}
                self.fichas = {str(k): dict(v) for k, v in (mesa.get("fichas") or {}).items()}
                self.pendentes = {str(k): list(v) for k, v in (mesa.get("pendentes") or {}).items()}
                self._seq_ev = int(mesa.get("seq_ev") or 0)
                self._seq = int(mesa.get("seq") or 0)
                self.registro = [tuple(r) for r in mesa.get("registro") or []]
                agora = time.time()
                self.web = {str(n): {"visto": agora - SEM_SINAL - 1, "palavra": False, "chave": str(k), "sem_sinal": True}
                            for n, k in (mesa.get("web") or {}).items()}
                self.maos = [n for n in mesa.get("maos") or [] if n in self.web]
        except (TypeError, ValueError, AttributeError):
            return False
        self._anotar("Mesa retomada de onde parou.")
        self._gmudou()
        self.fila.put(("mudou",))
        return True

    def iniciar(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0", self.porta))
        self.sock.listen(16)
        self.ativo = True
        global SERVIDOR_ATIVO
        SERVIDOR_ATIVO = self
        self.fichas_arq.iniciar()   # cria fichas/ (Bruno, Carol, Kauã, Enrico e Guidi) e guarda uma cópia datada
        threading.Thread(target=self._aceitar, daemon=True).start()
        threading.Thread(target=self._anunciar, daemon=True).start()
        try:
            self.httpd = ThreadingHTTPServer(("0.0.0.0", PORTA_WEB), type("Pagina", (_Pagina,), {"srv": self}))
            self.httpd.daemon_threads = True
            threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
            self.web_ok = True
        except OSError:
            self.httpd = None   # porta ocupada: só os jogadores do app entram

    # --- celulares e PCs por link (a página HTTP chama estes métodos)
    def senha_confere(self, senha):
        """True se a senha bate (ou a mesa não tem senha). Muitas tentativas erradas travam a entrada por 1 minuto."""
        if not self.senha:
            return True
        agora = time.time()
        with self.lock:
            self._erros_senha = [t for t in self._erros_senha if agora - t < 60]
            if len(self._erros_senha) >= 20:
                return False
            if str(senha).strip() == self.senha:
                return True
            self._erros_senha.append(agora)
        time.sleep(0.4)
        return False

    def web_entrar(self, nome, ident, senha="", chave="", pc=False, ficha="", codigo=""):
        """Entrada pela página: confere a senha da mesa e devolve o nome e uma chave só deste aparelho
        (sem a chave ninguém age em nome de outro jogador)."""
        with self.lock:
            w = self.web.get(ident) if ident else None
            volta = w is not None and w.get("chave") and w["chave"] == chave
        if not volta and not self.senha_confere(senha):
            return {"erro": "senha"}
        if not volta:
            ident = ""
        if ficha:
            sl = slug_ficha(ficha)
            erro = self.ficha_pode(sl, ident, codigo)
            if erro:
                return erro
            if not ident:        # o dono voltou por outro aparelho: retoma o mesmo lugar na mesa (o antigo estava sem sinal)
                with self.lock:
                    velho = next((n for n, w in self.web.items() if w.get("ficha") == sl), "")
                    if velho:
                        self.web[velho]["chave"] = ""
                        ident = velho
        nome = self.web_oi(nome, ident)
        with self.lock:
            w = self.web.get(nome)
            if w is None:
                return {"erro": "mesa"}
            w["pc"] = bool(pc)
            if ficha:                       # a ficha da pasta fichas/ que este celular está jogando
                w["ficha"] = slug_ficha(ficha)
            if not w.get("chave"):
                w["chave"] = "%032x" % random.SystemRandom().getrandbits(128)
            return {"id": nome, "chave": w["chave"], "ficha": w.get("ficha", "")}

    def web_confere(self, ident, chave):
        """A chave do aparelho bate com a do nome? (Entradas antigas ou de teste, sem chave, passam.)"""
        with self.lock:
            w = self.web.get(ident)
            return w is None or not w.get("chave") or w["chave"] == chave

    def web_espera(self, ident, ack=None, gv=None, sig="", espera=0):
        """Consulta que espera: segura a resposta até haver novidade para este jogador (ou `espera` segundos).
        Assim o dano e a vez chegam na hora, sem o aparelho perguntar o tempo todo."""
        fim = time.time() + max(0.0, min(float(espera or 0), 25.0))
        while True:
            r = self.web_estado(ident, ack, gv)
            if (not r.get("ok") or r["eventos"] or r["palavra"] or "grupo" in r or r["sig"] != sig
                    or time.time() >= fim or not self.ativo):
                return r
            time.sleep(0.2)

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

    def web_estado(self, ident, ack=None, gv=None):
        r = self._web_estado(ident, ack)
        if r.get("ok") and gv is not None:   # página com a aba Grupo: manda o grupo só quando mudou
            r["gv"] = self.gv
            if gv != self.gv:
                r["grupo"] = self.grupo_estado(ident)
        return r

    def _web_estado(self, ident, ack=None):
        """Estado para o celular. Os eventos só saem da fila quando o celular confirma (ack = último seq que
        ele processou): se a resposta se perder (tela bloqueada, Wi-Fi caindo), o dano chega na próxima consulta.
        Sem ack (página antiga, só com a mão), a fila é esvaziada ao entregar."""
        with self.lock:
            w = self.web.get(ident)
            if w is None:
                return {"ok": False}
            w["visto"] = time.time()
            palavra, w["palavra"] = w["palavra"], False
            fila = self.pendentes.get(ident, [])
            if ack is None:
                eventos, self.pendentes[ident] = fila, []
            else:
                eventos = self.pendentes[ident] = [e for e in fila if e["seq"] > ack]
            r = {"ok": True, "token": self.token, "mao": ident in self.maos, "fv": self.fichas_arq.ver(w.get("ficha", "")), "efeitos": list(self.efeitos.get(ident, [])),
                 "rodada": self.rodada, "vez": self._quem_age(), "turno": self.turno, "ordem": [o[0] for o in self.ordem]}
            r["sig"] = hashlib.md5(json.dumps(r, sort_keys=True).encode("utf-8")).hexdigest()[:12]
            r.update(palavra=palavra, eventos=eventos)
            return r

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
                # quem saiu da mesa não deixa rastro: eventos, efeitos, resumo e lugar na iniciativa
                self.pendentes.pop(n, None)
                self.efeitos.pop(n, None)
                self.fichas.pop(n, None)
                if any(o[0] == n for o in self.ordem):
                    atual = self._quem_age()
                    self.ordem = [o for o in self.ordem if o[0] != n]
                    self.vez = next((i for i, o in enumerate(self.ordem) if o[0] == atual), min(self.vez, len(self.ordem) - 1))
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
            self.salvar_sessao()
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
                    if not self.senha_confere(msg.get("senha", "")):
                        _enviar(c, {"t": "recusado", "motivo": "senha"})
                        break
                    nome = self._registrar(c, str(msg.get("nome", "")).strip()[:30] or "Jogador")
                    _enviar(c, {"t": "ok", "nome": nome})
                    self._sincronizar(nome)
                    self._gmudou()
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
                elif t == "grupo":
                    r = self.grupo_acao(nome, msg.get("m"))
                    _enviar(c, {"t": "grupo_resp", "r": r, "ref": msg.get("ref")})
                elif t == "fichas":
                    _enviar(c, {"t": "fichas_resp", "r": self.ficha_acao(nome, msg.get("m"))})
        finally:
            if nome is not None:
                with self.lock:
                    if self.clientes.get(nome) is c:
                        del self.clientes[nome]
                        self.ficha_pc.pop(nome, None)
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
        self._gmudou()
        return True

    # --- fichas completas na pasta fichas/
    def _ficha_de(self, ident):
        with self.lock:
            w = self.web.get(ident)
            if w is not None:
                w["visto"] = time.time()
                return w.get("ficha", "")
            return self.ficha_pc.get(ident, "")

    def ficha_pode(self, s, ident, codigo):
        """None se `ident` pode entrar na ficha `s`; senão o erro: ficha que não existe, em uso agora, presa a outro
        jogador, ou livre e ainda sem o código que o novo dono precisa criar."""
        if not any(f["slug"] == s for f in self.fichas_arq.lista()):
            return {"erro": "ficha_inexistente"}
        por = self.ficha_em_uso(s, ident)
        if por:
            return {"erro": "ficha_em_uso", "por": por}
        r = self.fichas_arq.conferir_dono(s, codigo)
        if r == "presa":
            time.sleep(0.4)      # freia quem tenta adivinhar o código
            return {"erro": "ficha_presa"}
        if r == "codigo":
            return {"erro": "ficha_codigo"}
        return None

    def ficha_em_uso(self, s, exceto=""):
        """Nome do jogador conectado que está com a ficha `s` (sem contar `exceto`), ou ''."""
        if not s:
            return ""
        agora = time.time()
        with self.lock:
            for n, w in self.web.items():
                if n != exceto and w.get("ficha") == s and agora - w.get("visto", 0) < SEM_SINAL:
                    return n
            for n, f in self.ficha_pc.items():
                if n != exceto and f == s and n in self.clientes:
                    return n
        return ""

    def fichas_lista(self, ident=""):
        """A lista das fichas da mesa com quem está usando cada uma agora ('uso') e qual é a de `ident` ('minha')."""
        minha = self._ficha_de(ident) if ident else ""
        out = self.fichas_arq.lista()
        for f in out:
            f["uso"] = self.ficha_em_uso(f["slug"], ident)
            f["minha"] = bool(minha) and f["slug"] == minha
        return out

    def ficha_acao(self, ident, m):
        """Fichas da mesa para o jogador do PC (conexão direta ou por link): listar, escolher, baixar, salvar, ver, soltar."""
        if not isinstance(m, dict):
            return {"ok": False}
        acao = m.get("acao")
        with self.lock:
            web, pc = ident in self.web, ident in self.clientes
        if not (web or pc):
            return {"ok": False, "erro": "Você não está na mesa."}
        if acao == "listar":
            return {"ok": True, "acao": acao, "fichas": self.fichas_lista(ident), "minha": self._ficha_de(ident)}
        if acao == "escolher":
            s = slug_ficha(m.get("slug"))
            e = self.ficha_pode(s, ident, m.get("codigo"))
            if e:
                txt = {"ficha_inexistente": "Essa ficha não existe mais na mesa.", "ficha_em_uso": f"Essa ficha está em uso por {e.get('por', 'outro jogador')}.",
                       "ficha_presa": "Essa ficha é de outro jogador (código errado). Peça ao mestre para liberar.",
                       "ficha_codigo": "Crie um código de 3 a 12 caracteres para esta ficha."}[e["erro"]]
                return {"ok": False, "acao": acao, "slug": s, "motivo": e["erro"], "erro": txt}
            with self.lock:
                if web:
                    self.web[ident]["ficha"] = s
                else:
                    self.ficha_pc[ident] = s
            self._anotar(f"{ident} escolheu a ficha “{self.fichas_arq.nome(s)}”.")
            ficha, ver, mt = self.fichas_arq.ler(s)
            return {"ok": True, "acao": acao, "slug": s, "nome": self.fichas_arq.nome(s), "existe": ficha is not None, "ficha": ficha, "ver": ver}
        s = self._ficha_de(ident)
        if acao == "soltar":
            with self.lock:
                if web:
                    self.web[ident].pop("ficha", None)
                else:
                    self.ficha_pc.pop(ident, None)
            self.fila.put(("mudou",))
            return {"ok": True, "acao": acao}
        if not s:
            return {"ok": False, "acao": acao, "erro": "escolha uma ficha"}
        if acao == "ver":
            return {"ok": True, "acao": acao, "ver": self.fichas_arq.ver(s)}
        if acao == "baixar":
            ficha, ver, mt = self.fichas_arq.ler(s)
            return {"ok": True, "acao": acao, "existe": ficha is not None, "ficha": ficha, "ver": ver}
        if acao == "salvar":
            r = self.ficha_salvar(ident, m.get("estado"), m.get("base"), bool(m.get("forcar")))
            r["acao"] = acao
            return r
        return {"ok": False}

    def ficha_baixar(self, ident, chave):
        """Entrega ao celular a ficha dele (a que está no .json) e a versão atual."""
        if not self.web_confere(ident, chave):
            return {"ok": False}
        s = self._ficha_de(ident)
        if not s:
            return {"ok": False, "erro": "escolha uma ficha"}
        ficha, ver, mt = self.fichas_arq.ler(s)
        return {"ok": True, "existe": ficha is not None, "ficha": ficha, "ver": ver, "mtime": mt, "agora": int(time.time() * 1000)}

    def ficha_salvar(self, ident, estado, base=None, forcar=False):
        """O celular devolve a ficha depois de cada mudança. Conflito = o .json mudou por outro caminho."""
        s = self._ficha_de(ident)
        if not s:
            return {"ok": False, "erro": "escolha uma ficha"}
        r = self.fichas_arq.gravar(s, estado, base if isinstance(base, str) else None, forcar)
        if r.get("ok"):
            self.fila.put(("mudou",))
        return r

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
                self._seq_ev += 1
                fila = self.pendentes.setdefault(nome, [])
                fila.append(dict(ev, seq=self._seq_ev))
                del fila[:-200]   # celular sumido não faz a fila crescer sem fim
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
        if self.vez == -1 and self.abertura:
            return self.abertura
        return self.ordem[self.vez][0] if 0 <= self.vez < len(self.ordem) else ""

    def rolar_iniciativa(self, rng=None, extras=(), apenas=None, primeiro=""):
        """Rola a iniciativa pela regra do livro (1d20 + 1d20 a cada 20 de Destreza, o maior, + Bônus de Combate de Destreza;
        empates rolam de novo) e começa o combate.
        extras: [{"nome", "dados", "bonus"}] de quem entra sem ser jogador (os inimigos do painel do mestre).
        apenas: nomes dos jogadores que entram (todos, se vazio). primeiro: quem deu o golpe que começou o combate."""
        rng = rng or (lambda f: random.randint(1, f))
        with self.lock:
            parts = []
            for n in list(self.clientes) + list(self.web):
                if apenas is not None and n not in apenas:
                    continue
                f = self.fichas.get(n, {})
                parts.append({"nome": n, "dados": max(1, int(f.get("iniciativa_dados", 1))), "bonus": int(f.get("iniciativa", 0))})
            parts += [{"nome": str(e["nome"]), "dados": int(e.get("dados", 1)), "bonus": int(e.get("bonus", 0))} for e in extras]
            ordem, det = R.rolar_ordem_iniciativa(parts, rng, primeiro)
            self.ordem, self.vez, self.ini_detalhe = ordem, -1, det
            self.abertura = primeiro if any(o[0] == primeiro for o in ordem) else ""
        self._anotar("Iniciativa: " + ", ".join(f"{n} {v}" for n, v, _ in ordem) + (f" — {self.abertura} abre o combate" if self.abertura else ""))
        for n in self.jogadores():
            self._evento(n, {"tipo": "combate", "fase": "inicio"})
        if self.abertura:       # o primeiro atacante age antes de a tabela começar; "Passar turno" leva ao primeiro da ordem
            self._evento(self.abertura, {"tipo": "vez", "rodada": self.rodada})
            for n in self.jogadores():
                self._sincronizar(n)
            if getattr(self, "gancho_vez", None):
                try:
                    self.gancho_vez(self.abertura)
                except Exception:
                    pass
            self.fila.put(("mudou",))
        else:
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
            if self.vez != -1:
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
        if anterior:
            self._grupo_fim_turno(anterior)
        self._evento(agora, {"tipo": "vez", "rodada": rod})
        for n in self.jogadores():
            self._sincronizar(n)
        if getattr(self, "gancho_vez", None):      # o painel do mestre aplica o que acontece no turno de um inimigo
            try:
                self.gancho_vez(agora)
            except Exception:
                pass
        for cond, v in dano or []:
            self.enviar_dano([agora], v, "Direto", f"{cond} (início do turno)")
        self._anotar((f"Rodada {rod} — " if nova_rodada else "") + f"vez de {agora}"
                     + (" — terminou: " + ", ".join(f"{c} ({n})" for n, c in acabaram) if acabaram else ""))
        self.fila.put(("mudou",))

    def encerrar_combate(self):
        """Fim do combate: limpa a ordem e tira os efeitos que duram "até o fim do combate"."""
        fim = []
        with self.lock:
            self.ordem, self.vez, self.abertura, self.ini_detalhe = [], -1, "", {}
            for n, lista in self.efeitos.items():
                fim += [(n, e["nome"]) for e in lista if e.get("fim_combate")]
                self.efeitos[n] = [e for e in lista if not e.get("fim_combate")]
        for n, c in fim:
            self._evento(n, {"tipo": "fim", "nome": c})
        for n in self.jogadores():
            self._evento(n, {"tipo": "combate", "fase": "fim"})
            self._sincronizar(n)
        self._grupo_fim_combate()
        self._anotar("Fim do combate" + (" — terminou: " + ", ".join(f"{c} ({n})" for n, c in fim) if fim else ""))
        self.fila.put(("mudou",))

    def painel(self):
        """Tudo que o painel do mestre desenha, numa leitura só."""
        with self.lock:
            agora = time.time()
            jog = []
            for n in list(self.clientes) + list(self.web):
                w = self.web.get(n)
                jog.append({"nome": n, "celular": w is not None and not w.get("pc"), "sem_sinal": bool(w and agora - w["visto"] > SEM_SINAL),
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
        global SERVIDOR_ATIVO
        if SERVIDOR_ATIVO is self:
            SERVIDOR_ATIVO = None
        if self.httpd:
            threading.Thread(target=self.httpd.shutdown, daemon=True).start()
            self.httpd.server_close()
        with self.lock:
            socks = list(self.clientes.values())
        for c in socks:
            _fechar(c)
        _fechar(self.sock)   # o shutdown solta o accept(): a porta fica livre para reabrir a mesa


class Cliente:
    """Lado do jogador. Eventos: ("ok", nome), ("estado", bool), ("palavra",), ("caiu",)."""

    def __init__(self, fila):
        self.fila = fila
        self.sock = None

    def conectar(self, ip, porta, nome, senha=""):
        self.sock = socket.create_connection((ip, porta), timeout=5)
        self.sock.settimeout(None)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        _enviar(self.sock, {"t": "oi", "nome": nome, "senha": senha})
        threading.Thread(target=self._ouvir, daemon=True).start()

    def _ouvir(self):
        for msg in _linhas(self.sock):
            t = msg.get("t")
            if t == "ok":
                self.fila.put(("ok", msg.get("nome", "")))
            elif t == "recusado":
                self.fila.put(("recusado", self))
                return
            elif t == "estado":
                self.fila.put(("estado", bool(msg.get("mao"))))
            elif t == "palavra":
                self.fila.put(("palavra",))
            elif t == "evento" and isinstance(msg.get("ev"), dict):
                self.fila.put(("evento", msg["ev"]))
            elif t == "grupo" and isinstance(msg.get("estado"), dict):
                self.fila.put(("grupo", msg["estado"]))
            elif t == "grupo_resp" and isinstance(msg.get("r"), dict):
                self.fila.put(("grupo_resp", msg["r"]))
            elif t == "fichas_resp" and isinstance(msg.get("r"), dict):
                self.fila.put(("fichas_resp", msg["r"]))
            elif t == "efeitos":
                self.fila.put(("efeitos", msg.get("lista") or [], int(msg.get("rodada") or 1),
                               str(msg.get("vez") or ""), int(msg.get("turno") or 0)))
        self.fila.put(("caiu", self))

    def enviar(self, msg):
        return bool(self.sock) and _enviar(self.sock, msg)

    def parar(self):
        _fechar(self.sock)


class SenhaErrada(Exception):
    pass


def separar_link(texto):
    """Do que o jogador colou, tira o endereço e a senha: aceita "https://x.trycloudflare.com/#s=1234",
    "x.trycloudflare.com", "192.168.0.5:5760" (página) e devolve (base_http ou "", ip ou "", senha)."""
    t, senha = str(texto or "").strip(), ""
    if "#" in t:
        t, frag = t.split("#", 1)
        for parte in frag.split("&"):
            if parte.startswith("s="):
                senha = parte[2:]
    t = t.rstrip("/")
    if not t:
        return "", "", senha
    if t.lower().startswith(("http://", "https://")):
        return t, "", senha
    so_ip = all(p.isdigit() for p in t.split(":")[0].split("."))
    if so_ip and ":" not in t:
        return "", t, senha                      # IP puro: conexão direta na rede local
    return ("http://" if so_ip else "https://") + t, "", senha


class ClienteWeb:
    """Jogador do PC ligado pelo endereço da página (link da internet ou http://IP:5760): usa o mesmo caminho
    dos celulares, então atravessa o túnel. Põe na fila os mesmos eventos do Cliente e reconecta sozinho;
    ("sinal", bool) avisa quando perde e quando recupera o contato."""
    ESPERA = 20

    def __init__(self, fila):
        self.fila = fila
        self.base = self.id = self.chave = self.senha = self.nome = ""
        self.ativo = False
        self.ack = self.gv = 0
        self.sig = self.token = ""
        self._mao = None
        self._efe = None
        self._saida = queue.Queue()

    def _req(self, caminho, corpo=None, espera=8):
        dados = None if corpo is None else json.dumps(corpo).encode("utf-8")
        req = urllib.request.Request(self.base + caminho, data=dados, headers={"User-Agent": "FichaPrevalecentes"})
        with urllib.request.urlopen(req, timeout=espera) as r:
            return json.loads(r.read().decode("utf-8"))

    def _oi(self):
        r = self._req("/api/oi", {"nome": self.nome, "id": self.id, "chave": self.chave, "senha": self.senha, "pc": True})
        if r.get("erro") == "senha":
            raise SenhaErrada()
        if not r.get("id"):
            raise OSError("resposta inesperada do mestre")
        self.id, self.chave = r["id"], r.get("chave", "")

    def conectar(self, base, nome, senha=""):
        self.base, self.nome, self.senha = base.rstrip("/"), nome, senha
        try:
            self._oi()
        except (urllib.error.URLError, ValueError) as e:
            raise OSError(str(e))
        self.ativo = True
        self.fila.put(("ok", self.id))
        threading.Thread(target=self._ouvir, daemon=True).start()
        threading.Thread(target=self._mandar, daemon=True).start()

    def _ouvir(self):
        falhas = 0
        while self.ativo:
            try:
                r = self._req("/api/estado?id=%s&k=%s&ack=%d&gv=%d&sig=%s&espera=%d" % (
                    quote(self.id), self.chave, self.ack, self.gv, self.sig, self.ESPERA), espera=self.ESPERA + 15)
                if not r.get("ok"):          # o mestre reabriu a mesa: entra de novo com o mesmo nome
                    self._oi()
                    self.fila.put(("ok", self.id))
                    continue
            except SenhaErrada:
                self.fila.put(("recusado", self))
                return
            except (OSError, ValueError):
                falhas += 1
                if falhas == 2 and self.ativo:
                    self.fila.put(("sinal", False))
                time.sleep(min(2 + falhas, 8))
                continue
            if falhas >= 2:
                self.fila.put(("sinal", True))
            falhas = 0
            if not self.ativo:
                return
            self._entregar(r)

    def _entregar(self, r):
        if r.get("token") and r["token"] != self.token:
            self.token, self.ack, self.gv = r["token"], 0, 0
        self.sig = r.get("sig", "")
        for ev in r.get("eventos") or []:
            if isinstance(ev, dict) and int(ev.get("seq") or 0) > self.ack:
                self.ack = int(ev.get("seq") or 0)
                self.fila.put(("evento", ev))
        if bool(r.get("mao")) != self._mao:
            self._mao = bool(r.get("mao"))
            self.fila.put(("estado", self._mao))
        if r.get("palavra"):
            self.fila.put(("palavra",))
        efe = (r.get("efeitos") or [], int(r.get("rodada") or 1), str(r.get("vez") or ""), int(r.get("turno") or 0))
        if efe != self._efe:
            self._efe = efe
            self.fila.put(("efeitos",) + efe)
        if isinstance(r.get("grupo"), dict):
            self.gv = int(r.get("gv") or 0)
            self.fila.put(("grupo", r["grupo"]))

    def _mandar(self):
        rotas = {"mao": "/api/mao", "abaixar": "/api/abaixar", "ficha": "/api/ficha", "relato": "/api/relato", "grupo": "/api/grupo",
                 "fichas": "/api/fichas-pc"}
        while self.ativo:
            try:
                msg = self._saida.get(timeout=1)
            except queue.Empty:
                continue
            t = msg.get("t")
            corpo = dict(msg.get("m") or {}) if t == "grupo" else {k: v for k, v in msg.items() if k != "t"}   # "fichas" leva o "m" inteiro
            corpo.update(id=self.id, chave=self.chave)
            for tentativa in range(4):
                try:
                    r = self._req(rotas[t], corpo, 30 if t == "fichas" else 8)
                    if t == "grupo" and isinstance(r, dict):
                        self.fila.put(("grupo_resp", r))
                    elif t == "fichas" and isinstance(r, dict):
                        self.fila.put(("fichas_resp", r))
                    break
                except (OSError, ValueError):
                    if not self.ativo:
                        return
                    time.sleep(1.5)

    def enviar(self, msg):
        if not self.ativo or msg.get("t") not in ("mao", "abaixar", "ficha", "relato", "grupo", "fichas"):
            return False
        self._saida.put(msg)
        return True

    def parar(self):
        self.ativo = False


# ======================================================================= interface
CORES_PADRAO = dict(FUNDO="#1b2520", CAMPO="#fbf7ea", PERG="#f2e9d3", PERG2="#e6d7b4", TINTA="#2d2015", TINTA2="#7d6a54",
                    VINHO="#7c2626", OURO="#b39552", OURO2="#dcc387", VERDE="#4a6d33", ALERTA="#f0a08c",
                    TINTA2_FUNDO="#9fae9f", FAIXA="#f6efdc", LINHA="#ddcda6", C_VIDA="#9a3d33", C_MANA="#3f6283",
                    C_VIGOR="#567a3b", FONTE="Georgia")


from fichas_ui import FichasJogador, JanelaFichasMestre   # noqa: E402


class JanelaSessao(tk.Toplevel, FichasJogador):
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
        self.geometry("480x640")
        self.minsize(420, 560)
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
        self.grupo = None          # estado do grupo (lado do jogador)
        self.win_grupo = None      # janela do Grupo aberta (jogador ou mestre)
        self.compartilha = True    # minhas rolagens aparecem para o grupo
        self.auto_ajuda = False    # aceitar ajudas (Medicina, cura, efeitos...) sem perguntar
        self._auto_ok = set()
        self._fichas_init()        # ficha da mesa escolhida pelo jogador (fichas_ui.py)
        self.win_fichas_mestre = None
        self.tunel = None          # mesa pela internet (mestre)
        self.win_convite = None
        self._destino = None       # (endereço, porta, senha) da conexão atual do jogador, para reconectar
        self._reconectando = False
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
        self._rot(t, "Na mesma rede os jogadores entram sozinhos.\nDe longe, o mestre abre a mesa para a internet e manda o link.\n"
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
        self._rot(av, "De longe, ou se não achar — link ou IP do mestre:", 9, italic=True).pack(anchor="w")
        ttk.Entry(av, textvariable=self.v_ip).pack(fill="x", pady=(2, 4))
        sv = tk.Frame(jog, bg=self.c["FUNDO"])
        sv.pack(fill="x")
        self.v_senha = tk.StringVar()
        self._rot(sv, "Senha da mesa (se houver):", 9, italic=True).pack(side="left")
        ttk.Entry(sv, textvariable=self.v_senha, width=10).pack(side="left", padx=6)
        self._rot(t, "Se o Windows perguntar sobre o Firewall (no PC do mestre),\npermita o acesso em redes privadas.",
                  9, italic=True, justify="center").pack(pady=(14, 0))

    # --- tela 2: mestre
    def _ser_mestre(self):
        try:
            porta = int(self.v_porta.get())
            self.servidor = Servidor(porta, self.fila)
            salva = Servidor.sessao_salva()
            if salva:
                m = salva["mesa"]
                quem = ", ".join(list(m.get("web") or {}) + list(m.get("pc") or [])) or "ninguém"
                if messagebox.askyesno("Sessão", f"Há uma mesa guardada de {time.strftime('%d/%m %H:%M', time.localtime(salva['hora']))} "
                                                 f"(rodada {m.get('rodada', 1)}; {quem}).\n\nRetomar de onde parou?", parent=self):
                    self.servidor.retomar(m)
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
        ttk.Button(topo, text="👥 Grupo", command=self.abrir_grupo).pack(side="right", padx=(0, 6))
        ttk.Button(topo, text="👹 Inimigos e anotações", command=self._abrir_painel_mestre).pack(side="right", padx=(0, 6))
        ttk.Button(topo, text="📜 Fichas", command=self._abrir_fichas_mestre).pack(side="right", padx=(0, 6))
        self.lbl_rodada = self._rot(topo, "Rodada 1", 15, c["OURO2"], bold=True)
        self.lbl_rodada.pack(side="right", padx=14)
        ttk.Button(topo, text="🌐 Convidar", command=self._mostrar_qr).pack(side="right", padx=(0, 6))
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

    # --- convidar: endereço da rede, senha da mesa e mesa pela internet
    def link_internet(self):
        """Link para quem está longe (com a senha embutida), ou "" se a mesa não está aberta para a internet."""
        if not (self.tunel and self.tunel.url):
            return ""
        return self.tunel.url + ("/#s=" + self.servidor.senha if self.servidor.senha else "")

    def _mostrar_qr(self):
        if self.win_convite is not None:
            try:
                self.win_convite.destroy()
            except tk.TclError:
                pass
        w = self.win_convite = tk.Toplevel(self)
        w.title("Convidar jogadores")
        w.configure(background="white", padx=18, pady=14)
        f = self.fonte

        def titulo(txt):
            tk.Label(w, text=txt, bg="white", fg="#7c2626", font=(f, 11, "bold")).pack(anchor="w", pady=(10, 2))

        def nota(txt):
            tk.Label(w, text=txt, bg="white", fg="#555", font=(f, 9, "italic"), justify="left", wraplength=420).pack(anchor="w")

        def copiar(txt):
            self.clipboard_clear()
            self.clipboard_append(txt)

        def qr(txt, tam=200):
            if segno:
                try:
                    desenhar_qr(w, txt, tam).pack(pady=(6, 0))
                except Exception:   # o QR é um extra: nunca derruba a mesa do mestre
                    pass

        titulo("Senha da mesa")
        ls = tk.Frame(w, bg="white")
        ls.pack(anchor="w")
        v = tk.StringVar(value=self.servidor.senha)
        ttk.Entry(ls, textvariable=v, width=12).pack(side="left")

        def aplicar():
            self.servidor.senha = v.get().strip()[:20]
            self._mostrar_qr()
        ttk.Button(ls, text="Aplicar", command=aplicar).pack(side="left", padx=6)
        nota("Vazia = entra quem tiver o endereço. O link da internet já leva a senha junto. Quem já está na mesa continua.")

        titulo("Na mesma rede (Wi-Fi)")
        if self.url_celular:
            tk.Label(w, text="Celular: " + self.url_celular, bg="white", fg="#222", font=(f, 12, "bold")).pack(anchor="w")
            nota("No PC, o jogador toca em \"Entrar como jogador\" e o programa acha a mesa sozinho.")
        else:
            nota(f"Celulares indisponíveis (porta {PORTA_WEB} ocupada). Os PCs da rede entram sozinhos.")

        titulo("De longe (internet)")
        link, est = self.link_internet(), self.tunel.estado if self.tunel else "fechado"
        if not self.servidor.web_ok:
            nota(f"Indisponível: a porta {PORTA_WEB} está ocupada neste PC.")
        elif link:
            e = ttk.Entry(w, width=58)
            e.insert(0, link)
            e.configure(state="readonly")
            e.pack(anchor="w", fill="x")
            lb = tk.Frame(w, bg="white")
            lb.pack(anchor="w", pady=4)
            ttk.Button(lb, text="Copiar link", command=lambda: copiar(link)).pack(side="left")
            ttk.Button(lb, text="Fechar a internet", command=self._fechar_tunel).pack(side="left", padx=6)
            nota("Mande o link aos jogadores. No celular é só abrir; no PC, colar em \"link ou IP do mestre\" "
                 "e tocar em Entrar como jogador. O link vale até você fechar a mesa e muda a cada sessão.")
            qr(link)
        elif est in ("baixando", "abrindo"):
            self.lbl_tunel = tk.Label(w, text="Abrindo…", bg="white", fg="#222", font=(f, 11, "bold"))
            self.lbl_tunel.pack(anchor="w")
        else:
            ttk.Button(w, text="🌐 Abrir a mesa para a internet", command=self._abrir_tunel).pack(anchor="w", pady=2)
            nota("Usa o cloudflared (Cloudflare): não precisa de conta nem de mexer no roteador. "
                 "Só entra quem tiver o link" + (" e a senha." if self.servidor.senha else "; uma senha é criada junto."))
        if link == "" and self.url_celular:
            qr(self.url_celular, 170)

    def _abrir_tunel(self):
        self.tunel = self.tunel or Tunel(PORTA_WEB, self.fila)
        if self.tunel.precisa_baixar() and not messagebox.askyesno(
                "Mesa pela internet", "Para abrir a mesa para a internet, o programa precisa baixar o cloudflared "
                "(da Cloudflare, cerca de 65 MB, uma vez só) para a pasta .prevalecentes do seu usuário.\n\nBaixar agora?",
                parent=self.win_convite or self):
            return
        if not self.servidor.senha:
            self.servidor.senha = "%04d" % random.SystemRandom().randrange(10000)
        self.tunel.estado = "abrindo"
        self.tunel.abrir()
        self._mostrar_qr()

    def _fechar_tunel(self):
        if self.tunel:
            self.tunel.fechar()
        self._mostrar_qr()

    def _tunel_mudou(self, estado, texto):
        viva = False
        try:
            viva = bool(self.win_convite and self.win_convite.winfo_exists())
        except tk.TclError:
            pass
        if estado == "baixando" and viva and hasattr(self, "lbl_tunel"):
            try:
                self.lbl_tunel.config(text=f"Baixando o cloudflared… {texto}")
            except tk.TclError:
                pass
            return
        if estado == "ok":
            self.servidor._anotar("Mesa aberta para a internet.")
        elif estado == "erro":
            messagebox.showwarning("Mesa pela internet", texto, parent=self)
        if viva and estado in ("ok", "erro", "fechado"):
            self._mostrar_qr()

    def _abrir_fichas_mestre(self):
        try:
            if self.win_fichas_mestre is not None and self.win_fichas_mestre.winfo_exists():
                self.win_fichas_mestre.lift()
                self.win_fichas_mestre.atualizar(True)
                return
        except tk.TclError:
            pass
        self.win_fichas_mestre = JanelaFichasMestre(self)

    def _abrir_painel_mestre(self):
        """Abre o painel do mestre (inimigos, anotações e combate) no navegador deste computador."""
        import mestre_web
        try:
            mestre_web.abrir_no_navegador()
        except OSError as e:
            messagebox.showerror("Painel do mestre", f"Não consegui abrir o painel (porta {mestre_web.PORTA} ocupada?).\n{e}", parent=self)

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

    def _foto_do_jogador(self, nome):
        """Miniatura da foto do personagem (da ficha da mesa do jogador), guardada enquanto a ficha não muda."""
        try:
            sl = self.servidor._ficha_de(nome)
            ver = self.servidor.fichas_arq.resumo(sl)["foto"] if sl else ""
            if not ver:
                return None
            guard = self.__dict__.setdefault("_fotos_painel", {})
            if guard.get(nome, ("", None))[0] != ver:
                import foto as F
                guard[nome] = (ver, F.para_tk((self.servidor.fichas_arq.ler(sl)[0] or {}).get("foto"), 52))
            return guard[nome][1]
        except Exception:      # a foto é enfeite: nunca derruba o painel
            return None

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
        img = self._foto_do_jogador(nome)
        if img is not None:
            tk.Label(cab, image=img, bg=c["CAMPO"]).pack(side="left", padx=(0, 6))
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
            base, ip_puro, senha = separar_link(ip)
            if senha:
                self.v_senha.set(senha)
            self._conectar(base or ip_puro, PORTA, nome)
            return
        self.btn_entrar.config(state="disabled")
        self.lbl_busca.config(text="Procurando o mestre na rede…")
        procurar_mestre(self.fila)

    def _novo_cliente(self, ip, porta, nome, senha):
        """Cliente já conectado: pela página (link ou http://IP:porta) ou direto na rede local."""
        if str(ip).lower().startswith("http"):
            c = ClienteWeb(self.fila)
            c.conectar(ip, nome, senha)
        else:
            c = Cliente(self.fila)
            c.conectar(ip, porta, nome, senha)
        return c

    def _conectar(self, ip, porta, nome):
        senha = self.v_senha.get().strip() if hasattr(self, "v_senha") else ""
        try:
            self.cliente = self._novo_cliente(ip, porta, nome, senha)
        except SenhaErrada:
            self.cliente = None
            self.btn_entrar.config(state="normal")
            self.lbl_busca.config(text="A mesa tem senha: peça ao mestre e preencha em \"Senha da mesa\".")
            return
        except (ValueError, OSError) as e:
            self.cliente = None
            self.btn_entrar.config(state="normal")
            self.lbl_busca.config(text="")
            messagebox.showerror("Sessão", f"Não consegui conectar em {ip}.\n"
                                           f"Confira o endereço e se o mestre já abriu a mesa.\n{e}", parent=self)
            return
        self._destino = (ip, porta, senha)
        self._reconectando = False
        self._btn_voltar = None
        if not str(ip).lower().startswith("http"):
            self.ultimo_ip = ip
        t = self._trocar()
        self._rot(t, "✋ Sessão", 18, self.c["OURO2"], bold=True).pack()
        self.lbl_status = self._rot(t, "Conectado.", 10, italic=True)
        self.lbl_status.pack(pady=(2, 20))
        self.btn_mao = tk.Button(t, text="✋  Levantar a mão", font=(self.fonte, 18, "bold"), bg=self.c["OURO"],
                                 fg="#1b2520", activebackground=self.c["OURO2"], relief="flat", pady=26,
                                 command=self._alternar_mao)
        self.btn_mao.pack(fill="x", pady=10)
        self.btn_grupo = ttk.Button(t, text="👥 Grupo", command=self.abrir_grupo)
        self.btn_grupo.pack(fill="x")
        lf = tk.Frame(t, bg=t["bg"])
        lf.pack(fill="x", pady=(8, 0))
        self.lbl_ficha_mesa = self._rot(lf, "Sem ficha da mesa", 9, italic=True)
        self.lbl_ficha_mesa.pack(side="left")
        ttk.Button(lf, text="Trocar ficha", command=self.ficha_trocar).pack(side="right")
        self._ficha_rotulo()
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

    # --- grupo (interação entre jogadores)
    def itens_livro(self):
        return ITENS_LIVRO

    def abrir_grupo(self):
        from grupo_ui import JanelaGrupo, JanelaGrupoMestre
        w = self.win_grupo
        try:
            if w is not None and w.winfo_exists():
                w.lift()
                return w
        except tk.TclError:
            pass
        self.win_grupo = JanelaGrupoMestre(self) if self.servidor else JanelaGrupo(self)
        return self.win_grupo

    def _win_grupo_viva(self):
        w = self.win_grupo
        try:
            return w if w is not None and w.winfo_exists() else None
        except tk.TclError:
            return None

    def enviar_grupo(self, m):
        if not self.cliente or not self.cliente.enviar({"t": "grupo", "m": m}):
            self._mostrar_aviso("Sem conexão com o mestre.")

    def compartilhar(self, titulo, linhas, destaque=False):
        """A ficha chama a cada rolagem: aparece nas Rolagens do grupo (se o jogador deixar e o mestre permitir)."""
        g = self.grupo
        if not self.cliente or not g or not g["cfg"].get("feed") or not self.compartilha:
            return
        if not any("d20" in str(x) or "Dano" in str(x) for x in linhas):
            return   # só rolagens, não avisos e anotações
        self.cliente.enviar({"t": "grupo", "m": {"acao": "rolagem", "titulo": str(titulo), "linhas": [str(x) for x in linhas[:4]],
                                                 "destaque": bool(destaque)}})

    def _grupo_chegou(self, g):
        self.grupo = g
        para = [p for p in g["propostas"] if p["para"] == self.meu_nome]
        if self.auto_ajuda:
            for p in para:
                if p["tipo"] in ("medicina", "incentivo", "cura", "buff", "refeicao") and p["id"] not in self._auto_ok:
                    self._auto_ok.add(p["id"])
                    self.enviar_grupo({"acao": "responder", "num": p["id"], "aceitar": True})
        pend = len(para) + (1 if g.get("teste") and g["teste"]["aberto"] and not g["teste"]["ja"] else 0)
        if hasattr(self, "btn_grupo"):
            self.btn_grupo.config(text="👥 Grupo" + (f"  ({pend} esperando você)" if pend else ""))
        w = self._win_grupo_viva()
        if w:
            w.atualizar(g)

    def _mostrar_aviso(self, texto):
        self._avisos = ([texto] + self._avisos)[:3]
        if hasattr(self, "lbl_evento"):
            self.lbl_evento.config(text="\n".join(self._avisos))

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
        self._tique_ficha += 1
        if self._tique_ficha % 2 == 0:
            try:
                self._ficha_sincronizar()        # ficha da mesa: devolve as mudanças ao .json do mestre
            except Exception:
                pass
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
        elif tipo == "aviso":
            texto = "👥 " + str(ev.get("texto", ""))
            if self.ponte:
                self.ponte.registrar("👥 Grupo", [str(ev.get("texto", ""))])
        elif tipo == "pedido":
            texto = f"👥 {ev.get('de')} quer te dar: {ev.get('texto')} — abra o Grupo para responder."
            if not self.auto_ajuda:
                self._aviso_sonoro()
        elif tipo == "portao" and self.ponte:
            texto = self.ponte.portao_sucesso(str(ev.get("de", "")))
            self._relatar(texto)
            self._ultima_ficha = None
            self._aviso_sonoro()
        elif tipo == "dinheiro" and self.ponte:
            texto = self.ponte.dinheiro(int(ev.get("delta", 0)), str(ev.get("desc", "")))
            self._ultima_ficha = None
        elif tipo == "sussurro":
            texto = f"🤫 {ev.get('de')}: {ev.get('texto')}"
            if self.ponte:
                self.ponte.registrar(f"🤫 Sussurro de {ev.get('de')}", [str(ev.get("texto", ""))])
            self._aviso_sonoro()
        elif tipo == "teste":
            texto = f"🎲 O mestre pediu {ev.get('pericia')}" + (f" (DT {ev.get('dt')})" if ev.get("dt") else "") + " de todos — abra o Grupo para rolar."
            self._aviso_sonoro()
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

    def _tentar_reconectar(self):
        """Conexão direta caiu: tenta de novo a cada 3 s, com o mesmo nome, até voltar ou o jogador desistir."""
        if not self._reconectando or self._destino is None:
            return
        ip, porta, senha = self._destino
        nome, fila = self.meu_nome or self.nome_padrao or "Jogador", self.fila

        def tarefa():
            try:
                c = Cliente(fila)
                c.conectar(ip, porta, nome, senha)
                fila.put(("reconectou", c))
            except (ValueError, OSError):
                fila.put(("reconexao_falhou",))
        threading.Thread(target=tarefa, daemon=True).start()

    def _voltar_escolha(self):
        self._reconectando = False
        if self.cliente:
            self.cliente.parar()
        self.cliente = None
        self._btn_voltar = None
        self.mao_levantada = False
        self._fichas_init()
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
                    self.fichas_pedir_lista()        # fichas da mesa: escolhe ao entrar; retoma ao reconectar
                elif ev[0] == "fichas_resp" and self.cliente:
                    self._fichas_resp(ev[1])
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
                elif ev[0] == "grupo" and len(ev) > 1 and self.cliente:
                    self._grupo_chegou(ev[1])
                elif ev[0] == "grupo_resp" and self.cliente:
                    if ev[1].get("erro") or ev[1].get("msg"):
                        self._mostrar_aviso("👥 " + (ev[1].get("erro") or ev[1].get("msg")))
                elif ev[0] == "grupo" and self.servidor:
                    w = self._win_grupo_viva()
                    if w:
                        w.atualizar()
                elif ev[0] == "tunel" and self.servidor:
                    self._tunel_mudou(ev[1], ev[2])
                elif ev[0] == "recusado" and self.cliente is not None and ev[1] is self.cliente:
                    self._reconectando = False
                    antes = (self.meu_nome or self.nome_padrao, self._destino[0] if self._destino else "")
                    self._voltar_escolha()
                    self.v_nome.set(antes[0])
                    self.v_ip.set(antes[1])
                    self.lbl_busca.config(text="A mesa tem senha: peça ao mestre e preencha em \"Senha da mesa\".")
                elif ev[0] == "sinal" and self.cliente:
                    self.lbl_status.config(text=f"Conectado como {self.meu_nome}" if ev[1] else "Sem sinal — tentando reconectar…")
                    self.btn_mao.config(state="normal" if ev[1] else "disabled")
                    if ev[1]:
                        self._ultima_ficha = None
                elif ev[0] == "caiu" and self.cliente is not None and (len(ev) < 2 or ev[1] is self.cliente):
                    self.lbl_status.config(text="Conexão perdida — tentando reconectar…")
                    self.btn_mao.config(state="disabled")
                    if not self._btn_voltar:
                        self._btn_voltar = ttk.Button(self.tela, text="Desistir e voltar", command=self._voltar_escolha)
                        self._btn_voltar.pack(pady=(4, 0))
                    if not self._reconectando:
                        self._reconectando = True
                        self.after(1500, self._tentar_reconectar)
                elif ev[0] == "reconexao_falhou" and self._reconectando:
                    self.after(3000, self._tentar_reconectar)
                elif ev[0] == "reconectou":
                    if self._reconectando and self.cliente is not None:
                        self._reconectando = False
                        self.cliente = ev[1]
                        self.mao_levantada = False
                        self._pintar_mao()
                        self.btn_mao.config(state="normal")
                        if self._btn_voltar:
                            self._btn_voltar.destroy()
                            self._btn_voltar = None
                        self._ultima_ficha = None
                    else:
                        ev[1].parar()
                if self.servidor and ev[0] in ("mudou", "mao", "registro"):
                    self._agendar_painel()
                    try:
                        if self.win_fichas_mestre is not None and self.win_fichas_mestre.winfo_exists():
                            self.win_fichas_mestre.atualizar()
                    except tk.TclError:
                        pass
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
        self._reconectando = False
        if self.tunel:
            self.tunel.fechar()
        for x in (self.servidor, self.cliente):
            if x:
                x.parar()
        self.ao_fechar(self.ultimo_ip)
        self.destroy()
