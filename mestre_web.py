# -*- coding: utf-8 -*-
"""Painel do mestre (inimigos, anotações e combate) servido só neste computador.

Abre em http://127.0.0.1:5761 e escuta apenas o endereço local: os jogadores (porta 5760) e o túnel da internet não chegam aqui.
Funciona sem sessão (para preparar inimigos e anotações). Com a sessão aberta, mostra os jogadores e deixa mandar dano,
condições e efeitos, e passar o turno."""
import json
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import bestiario as B
import regras as R
from mestre_dados import Mestre

PORTA = 5761
_unico = {"srv": None, "httpd": None, "mestre": None}
_trava = threading.Lock()


def servidor_da_sessao():
    """A sessão do mestre aberta agora (ou None)."""
    try:
        import sessao
        return getattr(sessao, "SERVIDOR_ATIVO", None)
    except Exception:
        return None


def _jogadores(srv):
    """Cartões dos jogadores a partir do que cada celular manda ao mestre (resumo da ficha)."""
    out = []
    if not srv:
        return out
    with srv.lock:
        nomes = list(srv.clientes) + list(srv.web)
        for n in nomes:
            f = dict(srv.fichas.get(n, {}))
            w = srv.web.get(n, {})
            out.append({"nome": n, "ficha": f, "efeitos": [dict(e) for e in srv.efeitos.get(n, [])], "mao": n in srv.maos,
                        "sem_sinal": bool(w.get("sem_sinal")), "celular": n in srv.web})
    return out


def estado(m):
    srv = servidor_da_sessao()
    c = m.combate()
    if srv and getattr(srv, "gancho_vez", None) is None:
        srv.gancho_vez = m.ao_vez
    if srv:
        with srv.lock:
            ordem = [list(o) for o in srv.ordem]
            vez, rodada = srv.vez, srv.rodada
            registro = list(srv.registro[:25])
            abertura, detalhe = getattr(srv, "abertura", ""), dict(getattr(srv, "ini_detalhe", {}))
        sessao_ativa = True
    else:
        ordem, vez, rodada = m.ordem_local()
        registro = []
        sessao_ativa = False
        abertura, detalhe = c.get("abertura", ""), c.get("detalhe", {})
    jogs = _jogadores(srv)
    niveis = [int(j["ficha"].get("nivel", 0)) for j in jogs if j["ficha"].get("nivel")]
    return {"sessao": sessao_ativa, "jogadores": jogs, "ordem": ordem, "vez": vez, "rodada": rodada,
            "abertura": abertura, "detalhe": detalhe,
            "nmp": (sum(niveis) // len(niveis)) if niveis else 0, "inimigos": c["inimigos"], "log": c["log"][:60], "registro": registro}


class _Painel(BaseHTTPRequestHandler):
    m = None
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _resp(self, corpo, tipo="application/json", codigo=200):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corpo)

    def _json(self, obj, codigo=200):
        self._resp(json.dumps(obj, ensure_ascii=False).encode("utf-8"), codigo=codigo)

    def _local(self):
        """Só aceita quem fala com 127.0.0.1/localhost (a porta já escuta só no endereço local; a conferência do Host evita ataques de páginas de fora)."""
        host = (self.headers.get("Host") or "").split(":")[0].lower()
        if host not in ("127.0.0.1", "localhost", "[::1]"):
            self._json({"erro": "só neste computador"}, 403)
            return False
        return True

    def do_GET(self):
        if not self._local():
            return
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        m = self.m
        try:
            if u.path in ("/", "/index.html"):
                from pagina_mestre import HTML
                self._resp(HTML.encode("utf-8"), "text/html; charset=utf-8")
            elif u.path == "/api/config":
                self._json({"tiers": B.TIERS, "condicoes": B.CONDICOES, "tipos_dano": R.NOMES_DANO, "ajustes": B.AJUSTES,
                            "efeitos": [n for n, _, _ in R.EFEITOS_LIVRO], "afinidades": list(B.AFINIDADES)})
            elif u.path == "/api/calcular":
                self._json(B.calcular(q.get("tier", "Comum"), int(q.get("nmp", 1)), int(q.get("jog", 4))))
            elif u.path == "/api/inimigos":
                self._json({"itens": m.inimigos()})
            elif u.path == "/api/notas":
                self._json({"itens": m.notas()})
            elif u.path == "/api/estado":
                self._json(estado(m))
            else:
                self._json({"erro": "não existe"}, 404)
        except (ValueError, KeyError) as e:
            self._json({"erro": str(e)}, 400)
        except OSError:
            pass

    def do_POST(self):
        if not self._local():
            return
        try:
            n = min(int(self.headers.get("Content-Length") or 0), 2_000_000)
            d = json.loads(self.rfile.read(n) or b"{}")
            if not isinstance(d, dict):
                d = {}
        except (ValueError, OSError):
            d = {}
        try:
            self._json(self.acao(self.path, d))
        except (ValueError, KeyError, TypeError) as e:
            self._json({"ok": False, "erro": f"pedido inválido ({e})"}, 400)
        except OSError:
            pass

    # --- rotas de escrita
    def acao(self, caminho, d):
        m, srv = self.m, servidor_da_sessao()
        if caminho == "/api/inimigos":
            return {"ok": True, "item": m.salvar_inimigo(d)}
        if caminho == "/api/inimigos/excluir":
            return {"ok": m.excluir_inimigo(str(d.get("id")))}
        if caminho == "/api/notas":
            return {"ok": True, "item": m.salvar_nota(d)}
        if caminho == "/api/notas/excluir":
            return {"ok": m.excluir_nota(str(d.get("id")))}
        if caminho == "/api/combate/adicionar":
            novos = m.adicionar_ao_combate(d.get("itens"))
            ordem_ativa = bool(srv.ordem) if srv else bool(m.combate()["ordem"])
            for x in novos:      # combate já rolando: quem chega depois rola a iniciativa na hora e entra na ordem
                if ordem_ativa:
                    _, det = R.rolar_ordem_iniciativa([{"nome": x["nome"], "dados": x.get("ini_dados", 1), "bonus": x.get("ini_bonus", 0)}], lambda f: m.rng(1, f))
                    self._definir_ini(m, srv, x["nome"], det[x["nome"]]["total"], x.get("ini_bonus", 0), det[x["nome"]])
            return {"ok": True, "novos": [x["nome"] for x in novos]}
        if caminho == "/api/combate/tirar":
            nome = str(d.get("nome"))
            if srv:
                srv.tirar_da_ordem(nome)
            else:
                c = m.combate()
                c["ordem"] = [o for o in c["ordem"] if o[0] != nome]
                m._salvar_combate()
            return {"ok": True}
        if caminho == "/api/combate/remover":
            return {"ok": m.remover_do_combate(str(d.get("iid")))}
        if caminho == "/api/combate/dano":
            return m.aplicar_dano(str(d.get("iid")), d.get("valor"), str(d.get("tipo") or ""), bool(d.get("corpo")), bool(d.get("direto")))
        if caminho == "/api/combate/cura":
            return m.curar(str(d.get("iid")), d.get("valor"))
        if caminho == "/api/combate/condicao":
            return m.aplicar_condicao(str(d.get("iid")), str(d.get("cond")), d.get("pontos"))
        if caminho == "/api/combate/ponto-chave":
            return {"ok": m.ponto_chave(str(d.get("iid")), d.get("idx"), d.get("revelado"))}
        if caminho == "/api/combate/editar":
            return {"ok": m.editar(str(d.get("iid")), d.get("campos") or {})}
        if caminho == "/api/combate/iniciar":
            # começar um combate: escolhe os inimigos, quem entra da mesa e quem deu o primeiro golpe; a iniciativa é rolada e a tabela montada
            if d.get("limpar", True):
                m.limpar_inimigos()
            novos = m.adicionar_ao_combate(d.get("itens"))
            if not m.combate()["inimigos"]:
                return {"ok": False, "erro": "Escolha pelo menos um inimigo."}
            self._iniciativa(m, srv, d.get("jogadores"), str(d.get("primeiro") or ""))
            return {"ok": True, "novos": [x["nome"] for x in novos]}
        if caminho == "/api/combate/iniciativa":
            return self._iniciativa(m, srv, d.get("jogadores"), str(d.get("primeiro") or ""))
        if caminho == "/api/combate/ini":
            nome, valor = str(d.get("nome")), int(d.get("valor"))
            x = next((i for i in m.combate()["inimigos"] if i["nome"] == nome), None)
            if x:
                m.editar(x["iid"], {"ini": valor})
            if srv:
                srv.definir_iniciativa(nome, valor)
            else:
                c = m.combate()
                for o in c["ordem"]:
                    if o[0] == nome:
                        o[1] = valor
                c["ordem"].sort(key=lambda o: (-o[1], o[0]))
            return {"ok": True}
        if caminho == "/api/combate/passar":
            self._passar(m, srv)
            return {"ok": True}
        if caminho == "/api/combate/encerrar":
            m.limpar_combate()
            if srv:
                srv.encerrar_combate()
            return {"ok": True}
        # --- jogadores (precisa da sessão)
        if caminho.startswith("/api/jogador/"):
            if not srv:
                return {"ok": False, "erro": "Abra a sessão como mestre para falar com os jogadores."}
            alvos = [str(a) for a in (d.get("alvos") or []) if str(a) in srv.jogadores()]
            if not alvos and caminho != "/api/jogador/remover-efeito":
                return {"ok": False, "erro": "Nenhum jogador escolhido."}
            if caminho == "/api/jogador/dano":
                valor = int(d.get("valor"))
                srv.enviar_dano(alvos, valor, str(d.get("tipo") or ""), str(d.get("desc") or ""))
                return {"ok": True}
            if caminho == "/api/jogador/pontos":
                srv.enviar_pontos_condicao(alvos, str(d.get("cond")), int(d.get("pontos")), int(d.get("dt") or 10), str(d.get("desc") or ""))
                return {"ok": True}
            if caminho == "/api/jogador/efeito":
                srv.adicionar_condicao(alvos, str(d.get("nome")), int(d.get("rodadas") or 0), str(d.get("desc") or ""), bool(d.get("fim_combate")))
                return {"ok": True}
            if caminho == "/api/jogador/remover-efeito":
                srv.remover_condicao(str(d.get("nome")), d.get("cid"))
                return {"ok": True}
        return {"ok": False, "erro": "ação desconhecida"}

    def _definir_ini(self, m, srv, nome, valor, bonus, detalhe):
        x = next((i for i in m.combate()["inimigos"] if i["nome"] == nome), None)
        if x:
            x["ini"] = valor
        if srv:
            srv.definir_iniciativa(nome, valor)
            with srv.lock:
                srv.ini_detalhe[nome] = detalhe
        else:
            c = m.combate()
            c["ordem"].append([nome, valor, bonus])
            c["ordem"].sort(key=lambda o: (-o[1], -o[2], o[0]))
            c["detalhe"][nome] = detalhe
        m._salvar_combate()

    def _passar(self, m, srv):
        """Passa o turno e pula os inimigos já derrotados (no máximo uma volta inteira)."""
        voltas = 0
        while True:
            if srv:
                srv.passar_turno()
                with srv.lock:
                    nome = srv._quem_age()
            else:
                m.local_passar()
                o, v, _ = m.ordem_local()
                nome = o[v][0] if 0 <= v < len(o) else ""
            voltas += 1
            x = next((i for i in m.combate()["inimigos"] if i["nome"] == nome), None)
            if not (x and x["caido"]) or voltas > 60:
                break

    def _iniciativa(self, m, srv, jogadores=None, primeiro=""):
        """Rola a iniciativa pela regra do livro (jogadores pela ficha, inimigos pelos dados e bônus deles) e começa o combate."""
        inimigos = m.participantes_inimigos()
        if srv:
            escolhidos = [str(j) for j in jogadores] if isinstance(jogadores, list) else None
            srv.rolar_iniciativa(extras=inimigos, apenas=escolhidos, primeiro=primeiro)
            with srv.lock:
                m._gravar_iniciativa(srv.ordem, srv.ini_detalhe)
            m._salvar_combate()
        else:
            m.local_iniciativa(primeiro=primeiro)
        return {"ok": True}


def iniciar():
    """Abre o painel (uma vez só) e devolve o endereço. Chamado pelos menus do programa."""
    with _trava:
        if _unico["httpd"] is None:
            m = Mestre()
            m.servidor = servidor_da_sessao
            _unico["mestre"] = m
            h = type("Painel", (_Painel,), {"m": m})
            httpd = ThreadingHTTPServer(("127.0.0.1", PORTA), h)
            httpd.daemon_threads = True
            threading.Thread(target=httpd.serve_forever, daemon=True).start()
            _unico["httpd"] = httpd
    return f"http://127.0.0.1:{PORTA}/"


def _navegador_app():
    """Caminho do Edge ou do Chrome (o Edge já vem no Windows), para abrir o painel numa janela própria, sem abas nem barra de endereço."""
    import os
    import shutil
    pastas = [os.environ.get(v, "") for v in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")]
    candidatos = [os.path.join(p, r) for p in pastas if p for r in (r"Microsoft\Edge\Application\msedge.exe", r"Google\Chrome\Application\chrome.exe")]
    candidatos += [shutil.which(n) or "" for n in ("msedge", "chrome", "google-chrome", "chromium")]
    return next((c for c in candidatos if c and os.path.exists(c)), "")


def abrir_no_navegador():
    """Abre o painel numa janela de aplicativo (Edge ou Chrome em modo --app: sem abas nem barra de endereço). Sem eles, abre no navegador comum."""
    url = iniciar()
    exe = _navegador_app()
    if exe:
        try:
            import subprocess
            subprocess.Popen([exe, f"--app={url}", "--window-size=1500,950"], close_fds=True)
            return url
        except OSError:
            pass
    webbrowser.open(url)
    return url
