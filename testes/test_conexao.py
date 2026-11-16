# -*- coding: utf-8 -*-
"""Conexão: senha da mesa, chave por aparelho, consulta que espera, PC pelo endereço da página (o caminho do link
da internet), reconexão, mesa guardada e o túnel (com um cloudflared de mentira).
Rode com:  python testes/test_conexao.py"""
import json
import os
import queue
import sys
import tempfile
import threading
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import grupo    # noqa: E402
import sessao   # noqa: E402
import tunel    # noqa: E402

tmp = tempfile.mkdtemp()
grupo.Grupo.ARQ_GRUPO = os.path.join(tmp, "grupo.json")
sessao.Servidor.ARQ_SESSAO = os.path.join(tmp, "sessao.json")
sessao.PORTA_WEB, sessao.PORTA_ANUNCIO = 5791, 5792
BASE = "http://127.0.0.1:5791"


def http(caminho, corpo=None, espera=30):
    dados = None if corpo is None else json.dumps(corpo).encode()
    with urllib.request.urlopen(urllib.request.Request(BASE + caminho, data=dados), timeout=espera) as r:
        return json.loads(r.read().decode())


def colher(fila, tipo, segundos=6):
    fim = time.time() + segundos
    while time.time() < fim:
        try:
            ev = fila.get(timeout=0.2)
        except queue.Empty:
            continue
        if ev[0] == tipo:
            return ev
    raise AssertionError("não chegou: " + tipo)


s = sessao.Servidor(5790, queue.Queue())
s.senha = "4321"
s.iniciar()
assert s.web_ok

# senha da mesa
assert http("/api/sessao")["senha"] is True
assert http("/api/oi", {"nome": "Ana", "senha": "0000"}) == {"erro": "senha"}
ana = http("/api/oi", {"nome": "Ana", "senha": "4321"})
assert ana["id"] == "Ana" and len(ana["chave"]) == 32

# chave por aparelho: sem ela ninguém lê nem age como a Ana
assert http("/api/estado?id=Ana&k=errada")["ok"] is False
assert http("/api/mao", {"id": "Ana", "chave": "errada"})["ok"] is False and "Ana" not in s.maos
assert http("/api/mao", {"id": "Ana", "chave": ana["chave"]})["ok"] is True and "Ana" in s.maos
# quem tenta entrar com o nome dela, sem a chave, vira outro jogador
assert http("/api/oi", {"nome": "Ana", "id": "Ana", "senha": "4321"})["id"] == "Ana (2)"
# ela mesma volta sem precisar da senha
assert http("/api/oi", {"nome": "Ana", "id": "Ana", "chave": ana["chave"]})["id"] == "Ana"

# consulta que espera: volta na hora quando chega dano; sem novidade, segura
r0 = http(f"/api/estado?id=Ana&k={ana['chave']}&ack=0&gv=0")
t0 = time.time()
r1 = http(f"/api/estado?id=Ana&k={ana['chave']}&ack=0&gv={r0['gv']}&sig={r0['sig']}&espera=1")
assert 0.9 < time.time() - t0 < 2.5 and r1["eventos"] == []
threading.Timer(0.5, lambda: s.enviar_dano(["Ana"], 7, "Fogo", "teste")).start()
t0 = time.time()
r2 = http(f"/api/estado?id=Ana&k={ana['chave']}&ack=0&gv={r0['gv']}&sig={r0['sig']}&espera=20")
assert time.time() - t0 < 2 and r2["eventos"][0]["valor"] == 7

# PC pelo endereço da página (é o caminho do link da internet)
assert sessao.separar_link("https://abc-def.trycloudflare.com/#s=4321") == ("https://abc-def.trycloudflare.com", "", "4321")
assert sessao.separar_link("abc-def.trycloudflare.com") == ("https://abc-def.trycloudflare.com", "", "")
assert sessao.separar_link("192.168.0.7") == ("", "192.168.0.7", "")
assert sessao.separar_link("192.168.0.7:5760") == ("http://192.168.0.7:5760", "", "")
fb = queue.Queue()
try:
    sessao.ClienteWeb(fb).conectar(BASE, "Beto", "errada")
    raise AssertionError("entrou sem a senha")
except sessao.SenhaErrada:
    pass
beto = sessao.ClienteWeb(fb)
beto.ESPERA = 3
beto.conectar(BASE, "Beto", "4321")
assert colher(fb, "ok")[1] == "Beto"
assert {j["nome"]: j["celular"] for j in s.painel()["jogadores"]}["Beto"] is False
beto.enviar({"t": "mao"})
ev = colher(fb, "estado")
while ev[1] is not True:
    ev = colher(fb, "estado")
assert "Beto" in s.maos
s.enviar_dano(["Beto"], 5, "Gelo", "")
t0 = time.time()
assert colher(fb, "evento")[1]["valor"] == 5 and time.time() - t0 < 1.5
s.dar_palavra("Beto")
colher(fb, "palavra")
beto.enviar({"t": "ficha", "dados": {"personagem": "Bardo", "vida": 9, "vida_max": 10}})
beto.enviar({"t": "grupo", "m": {"acao": "sinal", "sinal": "Preciso de cura"}})
assert colher(fb, "grupo_resp")[1]["ok"]
time.sleep(0.4)
assert s.fichas["Beto"]["personagem"] == "Bardo" and s.sinais["Beto"]["sinal"] == "Preciso de cura"

# PC direto na rede local: senha e reconexão com o mesmo nome
fc = queue.Queue()
caio = sessao.Cliente(fc)
caio.conectar("127.0.0.1", 5790, "Caio", "errada")
assert colher(fc, "recusado")[1] is caio
caio = sessao.Cliente(fc)
caio.conectar("127.0.0.1", 5790, "Caio", "4321")
assert colher(fc, "ok")[1] == "Caio"
caio.parar()
assert colher(fc, "caiu")[1] is caio
time.sleep(0.3)
caio = sessao.Cliente(fc)
caio.conectar("127.0.0.1", 5790, "Caio", "4321")
assert colher(fc, "ok")[1] == "Caio"

# mesa guardada: o mestre fecha e reabre; todos continuam de onde pararam
s.rolar_iniciativa()
s.adicionar_condicao(["Ana"], "Lento", 3, "")
s.enviar_dano(["Ana"], 11, "Fogo", "antes de cair")
assert s.salvar_sessao() and not s.salvar_sessao()
rodada, ordem, token = s.rodada, [o[0] for o in s.ordem], s.token
s.parar()
caio.parar()
time.sleep(1.0)
guardada = sessao.Servidor.sessao_salva()
assert guardada and "Ana" in guardada["mesa"]["web"]
s = sessao.Servidor(5790, queue.Queue())
assert s.retomar(guardada["mesa"])
s.iniciar()
assert s.web_ok and s.token == token and s.senha == "4321" and [o[0] for o in s.ordem] == ordem and s.rodada == rodada
r = http(f"/api/estado?id=Ana&k={ana['chave']}&ack={r2['eventos'][-1]['seq']}&gv=0")
assert r["ok"] and [e["valor"] for e in r["eventos"] if e["tipo"] == "dano"] == [11] and r["efeitos"][0]["nome"] == "Lento"
s.enviar_dano(["Beto"], 3, "Raio", "depois de voltar")     # o PC por link reconecta sozinho
ev = colher(fb, "evento", 15)
while ev[1].get("valor") != 3:
    ev = colher(fb, "evento", 15)
beto.parar()

# túnel: lê o link que o cloudflared escreve
falso = os.path.join(tmp, "cloudflared_falso.py")
with open(falso, "w") as f:
    f.write("import sys,time\nprint('INF Requesting new quick Tunnel on trycloudflare.com...',file=sys.stderr)\n"
            "print('INF |  https://mesa-de-teste-abc.trycloudflare.com  |',file=sys.stderr);sys.stderr.flush()\ntime.sleep(4)\n")
ft = queue.Queue()
if sys.platform.startswith("win"):
    lancador = os.path.join(tmp, "cf.bat")
    with open(lancador, "w") as f:
        f.write(f'@echo off\r\n"{sys.executable}" "{falso}"\r\n')
else:
    lancador = os.path.join(tmp, "cf.sh")
    with open(lancador, "w") as f:
        f.write(f"#!/bin/sh\nexec {sys.executable} {falso}\n")
    os.chmod(lancador, 0o755)
t = tunel.Tunel(5791, ft, programa=lancador)
assert not t.precisa_baixar()
t.abrir()
ev = colher(ft, "tunel")
while ev[1] != "ok":
    ev = colher(ft, "tunel")
assert ev[2] == "https://mesa-de-teste-abc.trycloudflare.com" == t.url
t.fechar()
ev = colher(ft, "tunel")
assert ev[1] == "fechado" and t.url == ""
s.parar()
print("ok")
