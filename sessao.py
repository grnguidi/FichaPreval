# -*- coding: utf-8 -*-
"""Sessão de jogo em rede local: jogadores "levantam a mão" e o mestre recebe o aviso.

O mestre abre um servidor TCP (porta 5757 por padrão) e os jogadores se conectam pelo IP dele.
Só usa a biblioteca padrão do Python. Mensagens: JSON, uma por linha.
"""
import json
import queue
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

PORTA = 5757
PORTA_ANUNCIO = 5758   # UDP: o mestre anuncia a sessão e os jogadores a encontram sozinhos
PORTA_WEB = 5760       # HTTP: página para o celular (navegador) levantar a mão

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
            elif u.path in ("/", "/index.html"):
                self._resp(PAGINA_WEB.encode("utf-8"), "text/html; charset=utf-8")
            else:
                self.send_error(404)
        except OSError:
            pass

    def do_POST(self):
        try:
            n = min(int(self.headers.get("Content-Length") or 0), 2000)
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
            return {"ok": True, "mao": ident in self.maos, "palavra": palavra}

    def _varrer(self):
        """Tira da mesa os celulares que sumiram (fecharam a página ou saíram da rede)."""
        agora = time.time()
        with self.lock:
            sumidos = [n for n, w in self.web.items() if agora - w["visto"] > 8]
            for n in sumidos:
                del self.web[n]
                if n in self.maos:
                    self.maos.remove(n)
        if sumidos:
            self.fila.put(("mudou",))

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
        for c in socks + [self.sock]:
            try:
                if c:
                    c.close()
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
        self.fila.put(("caiu",))

    def enviar(self, msg):
        return bool(self.sock) and _enviar(self.sock, msg)

    def parar(self):
        try:
            if self.sock:
                self.sock.close()
        except OSError:
            pass


# ======================================================================= interface
class JanelaSessao(tk.Toplevel):
    """Janela única com as três telas: escolha, painel do mestre e painel do jogador."""

    def __init__(self, app, cores, nome_padrao, ao_fechar):
        super().__init__(app)
        self.c = cores
        self.ao_fechar = ao_fechar
        self.nome_padrao = nome_padrao
        self.fonte = cores.get("FONTE", "Georgia")
        self.title("Sessão — Levantar a mão")
        self.geometry("460x560")
        self.minsize(400, 480)
        self.configure(background=cores["FUNDO"])
        self.fila = queue.Queue()
        self.servidor = None
        self.cliente = None
        self.mao_levantada = False
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
        t = self._trocar()
        self._rot(t, "✋ Mesa do mestre", 18, self.c["OURO2"], bold=True).pack()
        ip = ip_local()
        self._rot(t, f"Jogadores no app: entram sozinhos (IP {ip})", 10, self.c["TINTA2_FUNDO"]).pack(pady=(2, 0))
        if self.servidor.web_ok:
            url = f"http://{ip}:{PORTA_WEB}"
            self._rot(t, f"Celulares: apontem a câmera para o QR\nou abram  {url}", 11, self.c["OURO2"],
                      bold=True, justify="center").pack(pady=(2, 6))
            if segno:
                try:
                    desenhar_qr(t, url).pack(pady=(0, 10))
                except Exception:   # o QR é um extra: nunca derruba a mesa do mestre
                    pass
            self.geometry("460x760")
        else:
            self._rot(t, f"Celulares indisponíveis (porta {PORTA_WEB} ocupada)", 10, self.c["ALERTA"]).pack(pady=(2, 12))

        self._rot(t, "MÃOS LEVANTADAS (na ordem)", 9, bold=True).pack(anchor="w")
        self.lst_maos = tk.Listbox(t, height=8, font=(self.fonte, 14, "bold"), bg=self.c["CAMPO"],
                                   fg=self.c["VINHO"], selectbackground=self.c["OURO"], activestyle="none",
                                   exportselection=False)
        self.lst_maos.pack(fill="both", expand=True, pady=(2, 6))
        self.lst_maos.bind("<Double-Button-1>", lambda e: self._dar_palavra())
        bt = tk.Frame(t, bg=self.c["FUNDO"])
        bt.pack(fill="x")
        ttk.Button(bt, text="🎤 Dar a palavra", command=self._dar_palavra).pack(side="left")
        ttk.Button(bt, text="Baixar mão", command=self._baixar).pack(side="left", padx=6)
        ttk.Button(bt, text="Baixar todas", command=lambda: self.servidor.baixar_todas()).pack(side="right")

        self._rot(t, "CONECTADOS", 9, bold=True).pack(anchor="w", pady=(14, 0))
        self.lbl_conectados = self._rot(t, "ninguém ainda", 10, justify="left", wraplength=400)
        self.lbl_conectados.pack(anchor="w")
        self.lbl_aviso = self._rot(t, "", 11, self.c["ALERTA"], bold=True)
        self.lbl_aviso.pack(anchor="w", pady=(10, 0))
        self._atualizar_mestre()

    def _nome_selecionado(self):
        sel = self.lst_maos.curselection()
        idx = sel[0] if sel else 0
        _, maos = self.servidor.estado()
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

    def _atualizar_mestre(self):
        conectados, maos = self.servidor.estado()
        self.lst_maos.delete(0, "end")
        for i, n in enumerate(maos, 1):
            self.lst_maos.insert("end", f"  {i}.  ✋ {n}")
        if maos:
            self.lst_maos.selection_set(0)
        self.lbl_conectados.config(text=", ".join(conectados) if conectados else "ninguém ainda")
        self.title(f"✋ {len(maos)} — Sessão" if maos else "Sessão — Mesa do mestre")

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
        t = self._trocar()
        self._rot(t, "✋ Sessão", 18, self.c["OURO2"], bold=True).pack()
        self.lbl_status = self._rot(t, "Conectado.", 10, italic=True)
        self.lbl_status.pack(pady=(2, 20))
        self.btn_mao = tk.Button(t, text="✋  Levantar a mão", font=(self.fonte, 18, "bold"), bg=self.c["OURO"],
                                 fg="#1b2520", activebackground=self.c["OURO2"], relief="flat", pady=26,
                                 command=self._alternar_mao)
        self.btn_mao.pack(fill="x", pady=10)
        self.lbl_palavra = self._rot(t, "", 14, self.c["OURO2"], bold=True)
        self.lbl_palavra.pack(pady=18)

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
                    self.lbl_busca.config(text="Não encontrei o mestre. Ele já entrou como mestre? "
                                               "Se sim, digite o IP dele abaixo.")
                elif ev[0] == "mao":
                    self._aviso_sonoro()
                    if hasattr(self, "lbl_aviso"):
                        self.lbl_aviso.config(text=f"✋ {ev[1]} levantou a mão")
                elif ev[0] == "ok" and hasattr(self, "lbl_status"):
                    self.lbl_status.config(text=f"Conectado como {ev[1]}")
                elif ev[0] == "estado" and self.cliente:
                    self.mao_levantada = ev[1]
                    self._pintar_mao()
                    if ev[1]:
                        self.lbl_palavra.config(text="")
                elif ev[0] == "palavra" and self.cliente:
                    self.lbl_palavra.config(text="🎤 O mestre te deu a palavra!")
                    self._aviso_sonoro()
                elif ev[0] == "caiu" and self.cliente:
                    self.lbl_status.config(text="Conexão perdida com o mestre.")
                    self.btn_mao.config(state="disabled")
                if self.servidor and ev[0] in ("mudou", "mao"):
                    self._atualizar_mestre()
        except queue.Empty:
            pass
        except tk.TclError:
            return
        self.after(150, self._bombear)

    def fechar(self):
        for x in (self.servidor, self.cliente):
            if x:
                x.parar()
        self.ao_fechar(getattr(self, "ultimo_ip", None))
        self.destroy()
