# -*- coding: utf-8 -*-
"""Interação entre jogadores na sessão (o lado do mestre guarda e repassa tudo).

É misturado ao Servidor de sessao.py. O que os jogadores fazem entre si passa por aqui:
painel do grupo, ajudas pelas regras do livro (Medicina no Portão da Morte, Incentivar, cura, efeitos,
refeição), trocas de item e dinheiro, caixa do grupo, espólio, rolagens compartilhadas, teste em grupo,
sinais, sussurros, vínculos e o diário do grupo.

Cuidados: tudo que mexe na ficha de outro jogador vira um PEDIDO que o destinatário (ou o mestre) aceita;
o mestre liga e desliga cada recurso e vê tudo; texto vindo da rede é limpo antes de ser guardado.
"""
import html
import json
import os
import random
import re
import threading
import time

import regras as R

CFG_PADRAO = {"painel": True, "ajuda": True, "trocas": True, "feed": True, "sinais": True, "sussurro": "aviso",
              "diario": True}
CFG_ROTULOS = [("painel", "Painel do grupo (Vida e condições dos aliados)"), ("ajuda", "Ajudas: Medicina, Incentivar, cura, efeitos, refeição"),
               ("trocas", "Trocas de item e dinheiro, caixa do grupo"), ("feed", "Rolagens compartilhadas e reações"),
               ("sinais", "Sinais e intenções de turno"), ("diario", "Diário e vínculos do grupo")]
SUSSURRO_MODOS = [("aviso", "Sussurros: o mestre só vê que houve"), ("tudo", "Sussurros: o mestre lê tudo"), ("off", "Sussurros desligados")]
VISIBILIDADE = ("tudo", "barra", "nada")
REACOES = ("🎉", "👏", "😱", "💀")
TIPOS_AJUDA = ("medicina", "incentivo", "cura", "buff", "refeicao")
TIPOS_TROCA = ("item", "dinheiro")
DT_MEDICINA = 15


def texto_limpo(s, n=200):
    """Texto simples e curto: tira marcação HTML e caracteres de controle (o que vem da rede não é confiável)."""
    s = html.unescape(re.sub(r"<[^>]*>", "", str(s if s is not None else "")))
    return re.sub(r"[\x00-\x08\x0b-\x1f]", "", s).strip()[:n]


def _int(v, padrao=0, lo=None, hi=None):
    try:
        v = int(v)
    except (TypeError, ValueError):
        return padrao
    if lo is not None:
        v = max(lo, v)
    if hi is not None:
        v = min(hi, v)
    return v


class Grupo:
    """Estado e ações do grupo. Usa self.glock (nunca junto com self.lock: os efeitos colaterais rodam depois)."""
    ARQ_GRUPO = None   # onde caixa, diário e vínculos ficam guardados entre as sessões (None = pasta do usuário)

    def _grupo_init(self):
        self.glock = threading.RLock()
        self.gv = 1
        self.cfg = dict(CFG_PADRAO)
        self.vis = {}          # nome -> "tudo" | "barra" | "nada"
        self.propostas = {}    # id -> {"id", "de", "para", "tipo", "dados", "texto", "hora"}
        self._pid = 0
        self.feed = []         # [{"seq", "hora", "quem", "titulo", "linhas", "destaque", "reacoes": {r: [nomes]}}]
        self._fseq = 0
        self.sinais = {}       # nome -> {"sinal": str, "intencao": str}
        self.teste = None      # {"id", "pericia", "dt", "res": {nome: {"total", "txt"}}, "aberto": bool}
        self.espolio = None    # {"itens": [{"id", "item", "carga", "qtd", "quer": [nomes]}], "contos": int}
        self.caixa = {"contos": 0, "log": []}
        self.notas = []        # [{"id", "hora", "quem", "texto"}]
        self.vinculos = {}     # "A|B" (nomes em ordem) -> texto
        self._nid = 0
        self._carregar_grupo()

    # --- guardar entre sessões
    def _arq_grupo(self):
        if self.ARQ_GRUPO:
            return self.ARQ_GRUPO
        return os.path.join(os.path.expanduser("~"), ".prevalecentes", "grupo.json")

    def _carregar_grupo(self):
        try:
            with open(self._arq_grupo(), encoding="utf-8") as f:
                d = json.load(f)
            self.caixa = {"contos": _int(d.get("caixa", {}).get("contos"), 0, 0), "log": list(d.get("caixa", {}).get("log", []))[:30]}
            self.notas = [n for n in d.get("notas", []) if isinstance(n, dict)][:200]
            self.vinculos = {str(k): str(v)[:200] for k, v in dict(d.get("vinculos", {})).items()}
            self._nid = max([_int(n.get("id")) for n in self.notas] + [0])
            for k, v in dict(d.get("cfg", {})).items():
                if k in self.cfg:
                    self.cfg[k] = v
        except (OSError, ValueError, AttributeError, TypeError):
            pass

    def _salvar_grupo(self):
        with self.glock:
            d = {"caixa": self.caixa, "notas": self.notas, "vinculos": self.vinculos, "cfg": self.cfg}
        try:
            arq = self._arq_grupo()
            os.makedirs(os.path.dirname(arq), exist_ok=True)
            with open(arq + ".tmp", "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False)
            os.replace(arq + ".tmp", arq)
        except OSError:
            pass

    # --- avisar quem está na mesa
    def _gmudou(self, salvar=False):
        with self.glock:
            self.gv += 1
        if salvar:
            self._salvar_grupo()
        self.fila.put(("grupo",))
        with self.lock:
            pcs = dict(self.clientes)
        for nome, c in pcs.items():
            self._enviar_grupo(nome, c)

    def _enviar_grupo(self, nome, c):
        from sessao import _enviar
        _enviar(c, {"t": "grupo", "estado": self.grupo_estado(nome)})

    def _aviso(self, nome, texto):
        self._evento(nome, {"tipo": "aviso", "texto": texto})

    def _hora(self):
        return time.strftime("%H:%M")

    @staticmethod
    def _chave_vinculo(a, b):
        return "|".join(sorted([a, b]))

    # --- o que cada jogador vê
    def grupo_estado(self, nome):
        with self.lock:
            agora = time.time()
            nomes = list(self.clientes) + list(self.web)
            fichas = {n: dict(self.fichas.get(n, {})) for n in nomes}
            efeitos = {n: [e["nome"] for e in self.efeitos.get(n, [])] for n in nomes}
            sem_sinal = {n for n, w in self.web.items() if agora - w["visto"] > 12}
            vez = self._quem_age()
            ordem = [o[0] for o in self.ordem]
            de_quem = {n: (self.web[n].get("ficha", "") if n in self.web else getattr(self, "ficha_pc", {}).get(n, "")) for n in nomes}
        fotos = {}      # foto do personagem (da ficha da mesa de cada um): "slug?v=versão", para a página buscar em /api/foto
        arq = getattr(self, "fichas_arq", None)
        for n, sl in de_quem.items():
            if sl and arq is not None:
                try:
                    v = arq.resumo(sl)["foto"]
                except (OSError, ValueError, KeyError):
                    v = ""
                if v:
                    fotos[n] = f"{sl}&v={v}"
        with self.glock:
            cfg = dict(self.cfg)
            membros = []
            for n in nomes:
                f, vis = fichas[n], self.vis.get(n, "tudo")
                m = {"nome": n, "personagem": f.get("personagem", ""), "nivel": f.get("nivel", 0), "vis": vis, "vez": n == vez,
                     "sem_sinal": n in sem_sinal, "eu": n == nome, "foto": fotos.get(n, "")}
                vmax = f.get("vida_max", 0)
                ver = cfg["painel"] and (vis != "nada" or n == nome) and vmax
                if ver:
                    vida = f.get("vida", 0)
                    m["pct"] = max(0, min(100, round(100 * vida / vmax)))
                    m["incapaz"] = vida <= 0
                    if m["incapaz"]:
                        m["portao"] = list(f.get("portao", [0, 0]))[:2]
                    if vis == "tudo" or n == nome:
                        m["vida"] = [vida, vmax]
                        m["cond"] = [[c[0], c[1], c[2]] for c in f.get("condicoes", []) if c[1] > 0]
                        m["efeitos"] = efeitos[n]
                if cfg["sinais"]:
                    s = self.sinais.get(n, {})
                    m["sinal"], m["intencao"] = s.get("sinal", ""), s.get("intencao", "")
                if cfg["diario"] and n != nome:
                    m["vinculo"] = self.vinculos.get(self._chave_vinculo(nome, n), "")
                membros.append(m)
            props = [{k: p[k] for k in ("id", "de", "para", "tipo", "texto", "hora")} for p in self.propostas.values()
                     if (p["de"] == nome or p["para"] == nome) and p["de"] in nomes and p["para"] in nomes]
            teste = None
            if self.teste:
                t = self.teste
                revelar = not t["aberto"]
                teste = {"id": t["id"], "pericia": t["pericia"], "dt": t["dt"], "aberto": t["aberto"], "ja": nome in t["res"],
                         "rolaram": sorted(t["res"]), "faltam": [n for n in nomes if n not in t["res"]],
                         "res": [{"nome": n, **r} for n, r in sorted(t["res"].items(), key=lambda x: -x[1]["total"])
                                 if revelar or n == nome]}
            esp = None
            if self.espolio:
                esp = {"contos": self.espolio["contos"], "contos_txt": R.formatar_dinheiro(self.espolio["contos"]),
                       "itens": [dict(i, quer=list(i["quer"])) for i in self.espolio["itens"]]}
            return {"v": self.gv, "cfg": cfg, "vis": self.vis.get(nome, "tudo"), "membros": membros, "ordem": ordem,
                    "propostas": props, "feed": self.feed[:30] if cfg["feed"] else [], "teste": teste, "espolio": esp,
                    "caixa": {"contos": self.caixa["contos"], "txt": R.formatar_dinheiro(self.caixa["contos"]),
                              "log": self.caixa["log"][:8]} if cfg["trocas"] else None,
                    "notas": self.notas[:40] if cfg["diario"] else []}

    def grupo_mestre(self):
        """Tudo, para a janela do mestre."""
        with self.glock:
            return {"cfg": dict(self.cfg), "propostas": [dict(p) for p in self.propostas.values()], "feed": self.feed[:60],
                    "teste": json.loads(json.dumps(self.teste)) if self.teste else None,
                    "espolio": json.loads(json.dumps(self.espolio)) if self.espolio else None,
                    "caixa": {"contos": self.caixa["contos"], "txt": R.formatar_dinheiro(self.caixa["contos"]), "log": self.caixa["log"][:30]},
                    "notas": self.notas[:100], "vis": dict(self.vis),
                    "sinais": {n: dict(s) for n, s in self.sinais.items() if s.get("sinal") or s.get("intencao")}}

    def _na_mesa(self, nome):
        with self.lock:
            return nome in self.clientes or nome in self.web

    def _ficha(self, nome):
        with self.lock:
            return dict(self.fichas.get(nome, {}))

    # --- ações dos jogadores
    def grupo_acao(self, nome, m):
        """Uma ação de jogador. Devolve {"ok": bool, "erro": str, "msg": str}."""
        if not isinstance(m, dict) or not self._na_mesa(nome):
            return {"ok": False, "erro": "Você não está na mesa."}
        f = getattr(self, "_g_" + re.sub(r"[^a-z_]", "", str(m.get("acao", ""))), None)
        if f is None:
            return {"ok": False, "erro": "Ação desconhecida."}
        try:
            r = f(nome, m)
        except (TypeError, ValueError, KeyError, AttributeError):
            return {"ok": False, "erro": "Pedido inválido."}
        if isinstance(r, str):
            return {"ok": False, "erro": r}
        return {"ok": True, "msg": r[1] if isinstance(r, tuple) else ""}

    def _g_vis(self, nome, m):
        modo = m.get("modo")
        if modo not in VISIBILIDADE:
            return "Escolha tudo, barra ou nada."
        with self.glock:
            self.vis[nome] = modo
        self._gmudou()

    # pedidos: tudo que mexe na ficha de outro jogador
    def _g_propor(self, nome, m):
        tipo = m.get("tipo")
        alvos = m.get("alvos") if isinstance(m.get("alvos"), list) else [m.get("para")]
        alvos = [str(a) for a in alvos if a and str(a) != nome and self._na_mesa(str(a))][:12]
        if tipo == "refeicao" and m.get("eu"):
            alvos.append(nome)   # quem cozinha também come
        if not alvos:
            return "Escolha um aliado que esteja na mesa."
        with self.glock:
            cfg = dict(self.cfg)
        if tipo in TIPOS_AJUDA and not cfg["ajuda"]:
            return "O mestre desligou as ajudas entre jogadores."
        if tipo in TIPOS_TROCA and not cfg["trocas"]:
            return "O mestre desligou as trocas."
        dados, msg = {}, ""
        if tipo == "medicina":
            alvo = alvos[0]
            fa = self._ficha(alvo)
            if not fa.get("vida_max") or fa.get("vida", 1) > 0:
                return f"{alvo} não está Incapaz."
            total = _int(m.get("total"), 0, 0, 999)
            ok = total >= DT_MEDICINA
            self._publicar(nome, "Medicina em " + alvo, [texto_limpo(m.get("txt"), 120) or f"Medicina: {total}",
                                                          f"DT {DT_MEDICINA}: " + ("sucesso" if ok else "falhou")], ok)
            self._anotar(f"{nome} fez Medicina ({total}) em {alvo}: " + ("sucesso" if ok else "falhou"))
            if not ok:
                return None, f"Medicina {total} contra DT {DT_MEDICINA}: falhou."
            texto, alvos = f"Medicina {total} (DT {DT_MEDICINA}): 1 sucesso no Portão da Morte", [alvo]
        elif tipo == "incentivo":
            texto = "Incentivar (Reação): você age logo antes dele neste turno"
        elif tipo == "cura":
            dados["valor"] = _int(m.get("valor"), 0, 1, 9999)
            dados["desc"] = texto_limpo(m.get("desc"), 60)
            texto = f"Cura de {dados['valor']}" + (f" ({dados['desc']})" if dados["desc"] else "")
        elif tipo == "buff":
            dados["nome"] = texto_limpo(m.get("nome"), 30)
            if not dados["nome"]:
                return "Dê um nome ao efeito."
            dados["turnos"] = _int(m.get("turnos"), 0, 0, 99)
            dados["desc"] = texto_limpo(m.get("desc"), 120)
            texto = f"Efeito {dados['nome']}" + (f" por {dados['turnos']} turno(s)" if dados["turnos"] else "") \
                    + (f": {dados['desc']}" if dados["desc"] else "")
        elif tipo == "refeicao":
            nivel = _int(m.get("nivel"), 1, 1, 4)
            dt, beneficio = R.REFEICOES[nivel]
            total = _int(m.get("total"), 0, 0, 999)
            ok = total >= dt
            self._publicar(nome, f"Refeição de nível {nivel}", [texto_limpo(m.get("txt"), 120) or f"Gastronomia: {total}",
                                                                 f"DT {dt}: " + ("sucesso" if ok else "falhou")], ok)
            self._anotar(f"{nome} cozinhou uma refeição de nível {nivel} ({total} contra DT {dt}): " + ("sucesso" if ok else "falhou"))
            if not ok:
                return None, f"Gastronomia {total} contra DT {dt}: a refeição não deu certo."
            dados.update(nivel=nivel, beneficio=beneficio)
            texto = f"Refeição de nível {nivel}: {beneficio}"
        elif tipo == "item":
            it = m.get("item") if isinstance(m.get("item"), dict) else {}
            dados["item"] = {"item": texto_limpo(it.get("item"), 40), "carga": texto_limpo(it.get("carga"), 8),
                             "qtd": _int(it.get("qtd"), 1, 1, 999)}
            if not dados["item"]["item"]:
                return "Escolha o item."
            texto = f"{dados['item']['qtd']}× {dados['item']['item']}"
        elif tipo == "dinheiro":
            dados["contos"] = _int(m.get("contos"), 0, 1, 10 ** 9)
            texto = R.formatar_dinheiro(dados["contos"])
        else:
            return "Tipo de pedido desconhecido."
        with self.glock:
            for a in alvos:
                self._pid += 1
                self.propostas[self._pid] = {"id": self._pid, "de": nome, "para": a, "tipo": tipo, "dados": dict(dados),
                                             "texto": texto, "hora": self._hora()}
        resolver_ja = [p for p in list(self.propostas.values()) if p["de"] == p["para"]]
        for p in resolver_ja:   # a própria refeição não precisa de confirmação
            self._resolver(p["id"], True, por="")
        for a in alvos:
            if a != nome:
                self._evento(a, {"tipo": "pedido", "de": nome, "texto": texto})
        self._anotar(f"{nome} → {', '.join(alvos)}: {texto} (aguardando resposta)")
        self._gmudou()
        return None, msg or "Pedido enviado: aguardando " + ", ".join(a for a in alvos if a != nome) + "."

    def _g_responder(self, nome, m):
        pid = _int(m.get("num"))
        with self.glock:
            p = self.propostas.get(pid)
            if not p or p["para"] != nome:
                return "Esse pedido não está mais aberto."
        self._resolver(pid, bool(m.get("aceitar")), por="")

    def _g_cancelar(self, nome, m):
        pid = _int(m.get("num"))
        with self.glock:
            p = self.propostas.get(pid)
            if not p or p["de"] != nome:
                return "Esse pedido não é seu."
            del self.propostas[pid]
        self._aviso(p["para"], f"{nome} cancelou: {p['texto']}.")
        self._gmudou()

    def mestre_resolver(self, pid, aceitar):
        self._resolver(_int(pid), bool(aceitar), por=" (pelo mestre)")

    def _resolver(self, pid, aceitar, por=""):
        with self.glock:
            p = self.propostas.pop(pid, None)
        if not p:
            return
        de, para, tipo, d = p["de"], p["para"], p["tipo"], p["dados"]
        if not aceitar:
            self._aviso(de, f"{para} recusou{por}: {p['texto']}.")
            self._anotar(f"{para} recusou{por} o pedido de {de}: {p['texto']}")
            self._gmudou()
            return
        if tipo == "medicina":
            self._evento(para, {"tipo": "portao", "sucesso": 1, "de": de})
        elif tipo == "incentivo":
            self.adicionar_condicao([para], "Incentivado", 1, f"Age logo antes de {de} neste turno.")
        elif tipo == "cura":
            self.enviar_dano([para], -d["valor"], "", f"cura de {de}" + (f" ({d['desc']})" if d.get("desc") else ""))
        elif tipo == "buff":
            self.adicionar_condicao([para], d["nome"], d["turnos"], (d.get("desc") or "") + f" (de {de})")
        elif tipo == "refeicao":
            self.adicionar_condicao([para], f"Refeição nível {d['nivel']}", 0,
                                    f"{d['beneficio']} Até o próximo descanso longo." + ("" if de == para else f" (preparada por {de})"))
        elif tipo == "item":
            self.tirar_item(de, -1, d["item"]["item"], d["item"]["qtd"], f"entregue a {para}")
            self.dar_item([para], d["item"], f"de {de}")
        elif tipo == "dinheiro":
            self._evento(de, {"tipo": "dinheiro", "delta": -d["contos"], "desc": f"entregue a {para}"})
            self._evento(para, {"tipo": "dinheiro", "delta": d["contos"], "desc": f"de {de}"})
        if de != para:
            self._aviso(de, f"{para} aceitou{por}: {p['texto']}.")
        self._anotar(f"{para} aceitou{por} de {de}: {p['texto']}")
        self._gmudou()

    # rolagens compartilhadas
    def _publicar(self, nome, titulo, linhas, destaque=False):
        with self.glock:
            if not self.cfg["feed"]:
                return
            self._fseq += 1
            self.feed.insert(0, {"seq": self._fseq, "hora": self._hora(), "quem": nome, "titulo": texto_limpo(titulo, 80),
                                 "linhas": [texto_limpo(x, 200) for x in list(linhas)[:6] if texto_limpo(x)],
                                 "destaque": bool(destaque), "reacoes": {}})
            del self.feed[60:]

    def _g_rolagem(self, nome, m):
        with self.glock:
            if not self.cfg["feed"]:
                return "O mestre desligou as rolagens compartilhadas."
        linhas = m.get("linhas") if isinstance(m.get("linhas"), list) else []
        self._publicar(nome, m.get("titulo"), linhas, m.get("destaque"))
        self._gmudou()

    def _g_reagir(self, nome, m):
        r, seq = m.get("r"), _int(m.get("seq"))
        if r not in REACOES:
            return "Reação desconhecida."
        with self.glock:
            e = next((x for x in self.feed if x["seq"] == seq), None)
            if not e:
                return "Essa rolagem já saiu da lista."
            quem = e["reacoes"].setdefault(r, [])
            if nome in quem:
                quem.remove(nome)
                if not quem:
                    del e["reacoes"][r]
            else:
                quem.append(nome)
        self._gmudou()

    # teste em grupo
    def _g_teste_rolar(self, nome, m):
        with self.glock:
            t = self.teste
            if not t or not t["aberto"]:
                return "Não há teste em grupo aberto."
            if nome in t["res"]:
                return "Você já rolou este teste."
            t["res"][nome] = {"total": _int(m.get("total"), 0, 0, 999), "txt": texto_limpo(m.get("txt"), 120)}
        nomes = self.jogadores()
        with self.glock:
            completo = all(n in t["res"] for n in nomes)
        if completo:
            self.revelar_teste()
        else:
            self._gmudou()

    # sinais e intenções
    def _g_sinal(self, nome, m):
        with self.glock:
            if not self.cfg["sinais"]:
                return "O mestre desligou os sinais."
            s = self.sinais.setdefault(nome, {"sinal": "", "intencao": ""})
            if "sinal" in m:
                s["sinal"] = texto_limpo(m.get("sinal"), 40)
            if "intencao" in m:
                s["intencao"] = texto_limpo(m.get("intencao"), 80)
        self._gmudou()

    def _g_sussurro(self, nome, m):
        para, texto = str(m.get("para", "")), texto_limpo(m.get("texto"), 300)
        with self.glock:
            modo = self.cfg["sussurro"]
        if modo == "off":
            return "O mestre desligou os sussurros."
        if not texto or para == nome or not self._na_mesa(para):
            return "Escolha um aliado e escreva a mensagem."
        self._evento(para, {"tipo": "sussurro", "de": nome, "texto": texto})
        self._anotar(f"{nome} sussurrou para {para}" + (f": {texto}" if modo == "tudo" else ""))
        return None, f"Sussurro enviado a {para}."

    # caixa do grupo
    def _g_caixa(self, nome, m):
        delta = _int(m.get("delta"), 0, -10 ** 9, 10 ** 9)
        if not delta:
            return "Informe o valor."
        with self.glock:
            if not self.cfg["trocas"]:
                return "O mestre desligou as trocas."
            if delta < 0 and -delta > self.caixa["contos"]:
                return f"A caixa só tem {R.formatar_dinheiro(self.caixa['contos'])}."
            self.caixa["contos"] += delta
            oque = f"{nome} {'pôs' if delta > 0 else 'tirou'} {R.formatar_dinheiro(abs(delta))}"
            self.caixa["log"].insert(0, f"{self._hora()} {oque}")
            del self.caixa["log"][30:]
        self._evento(nome, {"tipo": "dinheiro", "delta": -delta, "desc": "caixa do grupo"})
        self._anotar(f"Caixa do grupo: {oque}")
        self._gmudou(salvar=True)

    # espólio
    def _g_espolio_quero(self, nome, m):
        iid = _int(m.get("num"))
        with self.glock:
            it = next((i for i in (self.espolio or {}).get("itens", []) if i["id"] == iid), None)
            if not it:
                return "Esse item não está mais no espólio."
            if m.get("quer") and nome not in it["quer"]:
                it["quer"].append(nome)
            elif not m.get("quer") and nome in it["quer"]:
                it["quer"].remove(nome)
        self._gmudou()

    # vínculos e diário
    def _g_vinculo(self, nome, m):
        com = str(m.get("com", ""))
        if com == nome or not self._na_mesa(com):
            return "Escolha um aliado."
        with self.glock:
            if not self.cfg["diario"]:
                return "O mestre desligou o diário do grupo."
            k, t = self._chave_vinculo(nome, com), texto_limpo(m.get("texto"), 200)
            if t:
                self.vinculos[k] = t
            else:
                self.vinculos.pop(k, None)
        self._aviso(com, f"{nome} anotou o vínculo de vocês: {t or '(apagado)'}")
        self._gmudou(salvar=True)

    def _g_nota_add(self, nome, m):
        t = texto_limpo(m.get("texto"), 400)
        if not t:
            return "Escreva a nota."
        with self.glock:
            if not self.cfg["diario"]:
                return "O mestre desligou o diário do grupo."
            self._nid += 1
            self.notas.insert(0, {"id": self._nid, "hora": time.strftime("%d/%m %H:%M"), "quem": nome, "texto": t})
            del self.notas[200:]
        self._gmudou(salvar=True)

    def _g_nota_del(self, nome, m):
        nid = _int(m.get("num"))
        with self.glock:
            n = next((x for x in self.notas if x["id"] == nid), None)
            if not n or n["quem"] != nome:
                return "Só quem escreveu a nota pode apagar."
            self.notas.remove(n)
        self._gmudou(salvar=True)

    # --- ações do mestre
    def grupo_config(self, chave, valor):
        with self.glock:
            if chave not in self.cfg:
                return
            self.cfg[chave] = valor if chave == "sussurro" else bool(valor)
        self._anotar(f"Grupo: {chave} = {valor}")
        self._gmudou(salvar=True)

    def pedir_teste(self, pericia, dt=0):
        with self.glock:
            self._pid += 1
            self.teste = {"id": self._pid, "pericia": texto_limpo(pericia, 30), "dt": _int(dt, 0, 0, 999), "res": {}, "aberto": True}
        for n in self.jogadores():
            self._evento(n, {"tipo": "teste", "pericia": self.teste["pericia"], "dt": self.teste["dt"]})
        self._anotar(f"Teste em grupo: {self.teste['pericia']}" + (f" (DT {self.teste['dt']})" if self.teste["dt"] else ""))
        self._gmudou()

    def revelar_teste(self):
        with self.glock:
            t = self.teste
            if not t or not t["aberto"]:
                return
            t["aberto"] = False
            res = sorted(t["res"].items(), key=lambda x: -x[1]["total"])
            linhas = [f"{n}: {r['total']}" + (" (passou)" if t["dt"] and r["total"] >= t["dt"] else " (falhou)" if t["dt"] else "")
                      for n, r in res]
            titulo = f"Teste em grupo: {t['pericia']}" + (f" (DT {t['dt']})" if t["dt"] else "")
        self._publicar("Grupo", titulo, linhas or ["Ninguém rolou."])
        self._anotar(titulo + " — " + ", ".join(linhas))
        self._gmudou()

    def encerrar_teste(self):
        with self.glock:
            self.teste = None
        self._gmudou()

    def soltar_espolio(self, itens, contos=0):
        with self.glock:
            esp = self.espolio or {"itens": [], "contos": 0}
            for it in itens:
                self._pid += 1
                esp["itens"].append({"id": self._pid, "item": texto_limpo(it.get("item"), 40), "carga": texto_limpo(it.get("carga"), 8),
                                     "qtd": _int(it.get("qtd"), 1, 1, 999), "quer": []})
            esp["contos"] += _int(contos, 0, 0, 10 ** 9)
            self.espolio = esp
        for n in self.jogadores():
            self._aviso(n, "O mestre soltou o espólio: marque o que você quer na aba Grupo.")
        self._anotar("Espólio solto: " + ", ".join(f"{i['qtd']}× {i['item']}" for i in itens)
                     + (f" e {R.formatar_dinheiro(contos)}" if contos else ""))
        self._gmudou()

    def distribuir_espolio(self, rng=None):
        """Item com um interessado vai para ele; com vários, cada um rola 1d20 e leva o maior; sem ninguém, fica.
        O dinheiro é dividido igualmente e o resto vai para a caixa do grupo."""
        rng = rng or (lambda f: random.randint(1, f))
        nomes = self.jogadores()
        with self.glock:
            esp = self.espolio
            if not esp:
                return []
            entregas, linhas, sobram = [], [], []
            for it in esp["itens"]:
                quer = [n for n in it["quer"] if n in nomes]
                if not quer:
                    sobram.append(it)
                    continue
                if len(quer) == 1:
                    ganhou, como = quer[0], ""
                else:
                    while True:
                        rolos = {n: rng(20) for n in quer}
                        mx = max(rolos.values())
                        if list(rolos.values()).count(mx) == 1:
                            break
                    ganhou = next(n for n, v in rolos.items() if v == mx)
                    como = " (disputa: " + ", ".join(f"{n} {v}" for n, v in rolos.items()) + ")"
                entregas.append((ganhou, it))
                linhas.append(f"{it['qtd']}× {it['item']} → {ganhou}{como}")
            parte, resto = (divmod(esp["contos"], len(nomes)) if nomes else (0, esp["contos"]))
            if esp["contos"]:
                linhas.append(f"{R.formatar_dinheiro(esp['contos'])}: {R.formatar_dinheiro(parte)} para cada"
                              + (f", {R.formatar_dinheiro(resto)} para a caixa" if resto else ""))
                if resto:
                    self.caixa["contos"] += resto
                    self.caixa["log"].insert(0, f"{self._hora()} resto do espólio: {R.formatar_dinheiro(resto)}")
            self.espolio = {"itens": sobram, "contos": 0} if sobram else None
        for ganhou, it in entregas:
            self.dar_item([ganhou], it, "espólio")
        if parte:
            for n in nomes:
                self._evento(n, {"tipo": "dinheiro", "delta": parte, "desc": "espólio"})
        self._publicar("Grupo", "Espólio dividido", linhas or ["Ninguém quis nada."])
        self._gmudou(salvar=True)
        return linhas

    def descartar_espolio(self):
        with self.glock:
            self.espolio = None
        self._gmudou()

    def nota_do_mestre(self, texto):
        t = texto_limpo(texto, 400)
        if not t:
            return
        with self.glock:
            self._nid += 1
            self.notas.insert(0, {"id": self._nid, "hora": time.strftime("%d/%m %H:%M"), "quem": "Mestre", "texto": t})
        self._gmudou(salvar=True)

    def apagar_nota(self, nid):
        with self.glock:
            self.notas = [n for n in self.notas if n["id"] != nid]
        self._gmudou(salvar=True)

    # --- ganchos do combate
    def _grupo_fim_turno(self, nome):
        with self.glock:
            s = self.sinais.get(nome)
            if not s or not (s.get("sinal") or s.get("intencao")):
                return
            self.sinais[nome] = {"sinal": "", "intencao": ""}
        self._gmudou()

    def _grupo_fim_combate(self):
        with self.glock:
            self.sinais = {}
        self._gmudou()
