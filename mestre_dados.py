# -*- coding: utf-8 -*-
"""Dados e regras do painel do mestre: biblioteca de inimigos, anotações e o combate em andamento.

Fica numa pasta `mestre/` ao lado do programa (inimigos.json, anotacoes.json, combate.json). Nada aqui usa interface:
o painel (mestre_web.py) chama estes métodos e a sessão (sessao.py) é opcional: sem sessão aberta, dá para preparar
inimigos e anotações e até testar um combate só com os inimigos."""
import json
import math
import os
import random
import re
import threading
import time

import bestiario as B
import regras as R
from fichas_mesa import _base

PASTA = os.path.join(_base(), "mestre")
TIPOS_DANO_LISTA = []   # preenchido por mestre_web (nomes do livro)


def _id():
    return "%08x" % random.getrandbits(32)


def _num(v, padrao=0):
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return padrao


class Mestre:
    def __init__(self, pasta=None, rng=None):
        self.pasta = pasta or PASTA
        self.lock = threading.RLock()
        self.rng = rng or random.randint
        self._inimigos = None
        self._notas = None
        self._combate = None
        self.servidor = lambda: None          # função que devolve a sessão aberta (ou None)

    # ------------------------------------------------------------ arquivos
    def _arq(self, nome):
        return os.path.join(self.pasta, nome)

    def _ler(self, nome, padrao):
        try:
            with open(self._arq(nome), encoding="utf-8-sig") as f:
                d = json.load(f)
            return d if isinstance(d, type(padrao)) else padrao
        except (OSError, ValueError):
            return padrao

    def _gravar(self, nome, dados):
        os.makedirs(self.pasta, exist_ok=True)
        tmp = self._arq(nome) + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            json.dump(dados, f, ensure_ascii=False, indent=1)
            f.write("\n")
        os.replace(tmp, self._arq(nome))

    # ------------------------------------------------------------ biblioteca de inimigos
    def inimigos(self):
        with self.lock:
            if self._inimigos is None:
                self._inimigos = self._ler("inimigos.json", {"itens": []}).get("itens", [])
            return self._inimigos

    def inimigo(self, iid):
        return next((x for x in self.inimigos() if x["id"] == iid), None)

    def salvar_inimigo(self, d):
        """Cria ou troca um inimigo da biblioteca. Só guarda campos conhecidos."""
        if not isinstance(d, dict):
            return None
        tier = d.get("tier") if d.get("tier") in B.TIERS else "Comum"
        listas = ("golpes", "habilidades", "pontos_chave")
        item = {
            "id": str(d.get("id") or _id()), "nome": str(d.get("nome") or "Inimigo sem nome")[:60], "tier": tier,
            "nmp": max(1, min(30, _num(d.get("nmp"), 1))), "jogadores": max(1, min(12, _num(d.get("jogadores"), 4))),
            "vida": max(1, _num(d.get("vida"), 1)), "ca": _num(d.get("ca")), "ataque": _num(d.get("ataque")), "dt": _num(d.get("dt")),
            "ini_dados": max(1, min(10, _num(d.get("ini_dados"), 1))), "ini_bonus": _num(d.get("ini_bonus")),
            "postura": max(0, _num(d.get("postura"))), "vida_condicao": max(0, _num(d.get("vida_condicao"))),
            "cond_por_golpe": max(0, _num(d.get("cond_por_golpe"))),
            "atencao": str(d.get("atencao") or "")[:300], "descricao": str(d.get("descricao") or "")[:3000],
            "set_drops": str(d.get("set_drops") or "")[:3000], "loot": str(d.get("loot") or "")[:1000], "notas": str(d.get("notas") or "")[:5000],
            "resistencias": [str(x)[:20] for x in (d.get("resistencias") or [])][:20],
            "imunidades": [str(x)[:20] for x in (d.get("imunidades") or [])][:20],
            "vulnerabilidades": [str(x)[:20] for x in (d.get("vulnerabilidades") or [])][:20],
            "afinidades": {c: a for c, a in (d.get("afinidades") or {}).items() if c in B.CONDICOES and a in B.AFINIDADES},
        }
        for k in listas:
            item[k] = [x for x in (d.get(k) or []) if isinstance(x, dict)][:30]
        item["golpes"] = [{"nome": str(g.get("nome") or "Golpe")[:60], "tipo": str(g.get("tipo") or "")[:20],
                           "bonus": _num(g.get("bonus"), item["ataque"]), "dano": _num(g.get("dano")),
                           "alcance": str(g.get("alcance") or "")[:30], "efeito": str(g.get("efeito") or "")[:500],
                           "cond": g.get("cond") if g.get("cond") in B.CONDICOES else "", "cond_pts": _num(g.get("cond_pts"))} for g in item["golpes"]]
        item["habilidades"] = [{"nome": str(h.get("nome") or "")[:60], "acao": str(h.get("acao") or "")[:20], "texto": str(h.get("texto") or "")[:1500]}
                               for h in item["habilidades"]]
        item["pontos_chave"] = [{"nome": str(p.get("nome") or "")[:60], "efeito": str(p.get("efeito") or "")[:500]} for p in item["pontos_chave"]][:3]
        with self.lock:
            lista = self.inimigos()
            for i, x in enumerate(lista):
                if x["id"] == item["id"]:
                    lista[i] = item
                    break
            else:
                lista.append(item)
            self._gravar("inimigos.json", {"itens": lista})
        return item

    def excluir_inimigo(self, iid):
        with self.lock:
            lista = self.inimigos()
            n = len(lista)
            lista[:] = [x for x in lista if x["id"] != iid]
            if len(lista) != n:
                self._gravar("inimigos.json", {"itens": lista})
            return len(lista) != n

    # ------------------------------------------------------------ anotações
    def notas(self):
        with self.lock:
            if self._notas is None:
                self._notas = self._ler("anotacoes.json", {"itens": []}).get("itens", [])
            return self._notas

    def salvar_nota(self, d):
        if not isinstance(d, dict):
            return None
        item = {"id": str(d.get("id") or _id()), "titulo": str(d.get("titulo") or "Sem título")[:120], "etiqueta": str(d.get("etiqueta") or "")[:30],
                "texto": str(d.get("texto") or "")[:200000], "fixa": bool(d.get("fixa")), "em": int(time.time())}
        with self.lock:
            lista = self.notas()
            for i, x in enumerate(lista):
                if x["id"] == item["id"]:
                    lista[i] = item
                    break
            else:
                lista.append(item)
            self._gravar("anotacoes.json", {"itens": lista})
        return item

    def excluir_nota(self, nid):
        with self.lock:
            lista = self.notas()
            n = len(lista)
            lista[:] = [x for x in lista if x["id"] != nid]
            if len(lista) != n:
                self._gravar("anotacoes.json", {"itens": lista})
            return len(lista) != n

    # ------------------------------------------------------------ combate
    def combate(self):
        with self.lock:
            if self._combate is None:
                c = self._ler("combate.json", {})
                self._combate = {"inimigos": c.get("inimigos", []), "log": c.get("log", []), "ordem": c.get("ordem", []), "vez": c.get("vez", -1),
                                 "rodada": c.get("rodada", 1), "abertura": c.get("abertura", ""), "detalhe": c.get("detalhe", {})}
            return self._combate

    def _salvar_combate(self):
        self._gravar("combate.json", self.combate())

    def _log(self, texto):
        c = self.combate()
        c["log"].insert(0, [time.strftime("%H:%M"), texto])
        del c["log"][150:]

    def _achar(self, iid):
        return next((x for x in self.combate()["inimigos"] if x["iid"] == iid), None)

    def _cond_inicial(self, base, tier):
        """Barras de condição de um inimigo novo: o valor da tabela, trocado pelas afinidades."""
        out = {}
        for c in B.CONDICOES:
            af = (base.get("afinidades") or {}).get(c, "")
            mx = int(round(base["vida_condicao"] * (B.AFINIDADES[af] if af and af != "imune" else 1)))
            out[c] = {"max": mx, "atual": mx, "base": mx, "ativacoes": 0, "afinidade": af}
        return out

    def adicionar_ao_combate(self, itens):
        """itens: [{id, qtd}]. Cria uma instância por criatura, com Vida, Postura e barras de condição próprias."""
        novos = []
        with self.lock:
            c = self.combate()
            for it in itens or []:
                base = self.inimigo(str(it.get("id")))
                if not base:
                    continue
                qtd = max(1, min(30, _num(it.get("qtd"), 1)))
                existentes = [x for x in c["inimigos"] if x["base_id"] == base["id"]]
                for k in range(qtd):
                    n = len(existentes) + k + 1
                    nome = base["nome"] if qtd == 1 and not existentes else f"{base['nome']} {n}"
                    inst = {"iid": _id(), "base_id": base["id"], "nome": nome, "tier": base["tier"], "nmp": base["nmp"],
                            "vida_max": base["vida"], "vida": base["vida"], "ca": base["ca"], "ataque": base["ataque"], "dt": base["dt"],
                            "postura_max": base["postura"], "postura": base["postura"], "exposto": False,
                            "cond": self._cond_inicial(base, base["tier"]), "dots": [], "efeitos": [], "notas": "",
                            "golpes": base["golpes"], "habilidades": base["habilidades"], "resistencias": base["resistencias"],
                            "imunidades": base["imunidades"], "vulnerabilidades": base["vulnerabilidades"],
                            "pontos_chave": [dict(p, revelado=False) for p in base["pontos_chave"]], "cond_por_golpe": base["cond_por_golpe"],
                            "ini": None, "caido": False, "ini_dados": base.get("ini_dados", 1), "ini_bonus": base.get("ini_bonus", 0)}
                    c["inimigos"].append(inst)
                    novos.append(inst)
            if novos:
                self._log("Entraram: " + ", ".join(x["nome"] for x in novos))
                self._salvar_combate()
        return novos

    def remover_do_combate(self, iid):
        with self.lock:
            c = self.combate()
            x = self._achar(iid)
            if not x:
                return False
            c["inimigos"].remove(x)
            c["ordem"] = [o for o in c["ordem"] if o[0] != x["nome"]]
            self._log(f"{x['nome']} saiu do combate")
            self._salvar_combate()
            return True

    def limpar_inimigos(self):
        """Tira todos os inimigos (e a ordem local) antes de começar um combate novo."""
        with self.lock:
            c = self.combate()
            c.update(inimigos=[], ordem=[], vez=-1, rodada=1, abertura="", detalhe={})
            self._salvar_combate()

    def limpar_combate(self):
        with self.lock:
            c = self.combate()
            c.update(inimigos=[], ordem=[], vez=-1, rodada=1, abertura="", detalhe={})
            self._log("Combate encerrado")
            self._salvar_combate()

    # --- o que acontece com um inimigo
    def aplicar_dano(self, iid, valor, tipo="", corpo=False, direto=False):
        """Dano num inimigo: imunidade zera, vulnerabilidade soma metade, resistência corta pela metade (Direto ignora tudo).
        Golpe corpo a corpo que acerta também reduz a Postura; ao zerar, ela quebra (Exposto) e recarrega."""
        with self.lock:
            x = self._achar(iid)
            if not x:
                return {"ok": False, "erro": "inimigo não está no combate"}
            valor = max(0, _num(valor))
            notas = []
            final = valor
            if not direto and tipo:
                if tipo in x["imunidades"]:
                    final = 0
                    notas.append(f"imune a {tipo}")
                elif tipo in x["vulnerabilidades"]:
                    final = valor + valor // 2
                    notas.append(f"vulnerável a {tipo}: +50%")
                elif tipo in x["resistencias"]:
                    final = valor // 2
                    notas.append(f"resistente a {tipo}: metade")
            antes = x["vida"]
            x["vida"] = max(0, x["vida"] - final)
            if corpo and final > 0 and x["postura_max"] > 0 and not x["exposto"]:
                x["postura"] = max(0, x["postura"] - final)
                if x["postura"] == 0:
                    x["exposto"] = True
                    x["postura"] = x["postura_max"]
                    notas.append("POSTURA QUEBRADA: Exposto e sem a próxima Reação até o fim do próximo turno")
            if x["vida"] == 0 and antes > 0:
                x["caido"] = True
                notas.append("derrotado")
            self._log(f"{x['nome']}: −{final} de Vida ({antes} → {x['vida']})" + (" · " + "; ".join(notas) if notas else ""))
            self._salvar_combate()
            return {"ok": True, "dano": final, "vida": x["vida"], "notas": notas}

    def curar(self, iid, valor):
        with self.lock:
            x = self._achar(iid)
            if not x:
                return {"ok": False}
            antes = x["vida"]
            x["vida"] = min(x["vida_max"], x["vida"] + max(0, _num(valor)))
            if x["vida"] > 0:
                x["caido"] = False
            self._log(f"{x['nome']}: +{x['vida'] - antes} de Vida ({antes} → {x['vida']})")
            self._salvar_combate()
            return {"ok": True, "vida": x["vida"]}

    def aplicar_condicao(self, iid, cond, pontos):
        """Tira pontos da barra da condição. Ao zerar, o efeito dispara e a barra recarrega (máximo +50%, na 3ª ativação +100%)."""
        with self.lock:
            x = self._achar(iid)
            if not x or cond not in B.CONDICOES:
                return {"ok": False}
            b = x["cond"][cond]
            if b["afinidade"] == "imune":
                self._log(f"{x['nome']} é imune a {cond}")
                self._salvar_combate()
                return {"ok": True, "ativou": False, "notas": ["imune"]}
            pontos = max(0, _num(pontos))
            antes = b["atual"]
            b["atual"] -= pontos
            notas = []
            ativou = b["atual"] <= 0
            if ativou:
                b["ativacoes"] += 1
                notas += self._efeito_condicao(x, cond)
                novo = B.recarga_apos_ativar(b["base"], b["ativacoes"])
                b["max"] = b["atual"] = novo
            self._log(f"{x['nome']}: −{pontos} de {cond} ({antes} → {max(0, b['atual'])})" + (" · ATIVOU: " + "; ".join(notas) if ativou else ""))
            self._salvar_combate()
            return {"ok": True, "ativou": ativou, "atual": b["atual"], "max": b["max"], "notas": notas}

    def _efeito_condicao(self, x, cond):
        ef = B.EFEITO_CONDICAO[cond]
        metade = x["tier"] in B.MEIA_PCT_TIERS
        notas = [f"{cond} ATIVOU: " + ef["txt"]]
        if cond == "Morte":
            pct = 25 if x["tier"] == "Deus" else 50
            if x["tier"] in B.MEIA_PCT_TIERS:
                perda = max(1, x["vida_max"] * pct // 100)
                x["vida"] = max(0, x["vida"] - perda)
                notas.append(f"perde {perda} de Vida ({pct}% da máxima)")
            else:
                x["vida"] = 0
                x["caido"] = True
                notas.append("morre")
            return notas
        pct_ja = ef.get("pct_ja")
        if pct_ja:
            pct = pct_ja / 2 if metade else pct_ja
            perda = max(1, int(x["vida_max"] * pct / 100))
            x["vida"] = max(0, x["vida"] - perda)
            notas.append(f"perde {perda} de Vida na hora")
            if x["vida"] == 0:
                x["caido"] = True
        if ef.get("pct_turno"):
            pct = ef["pct_turno"] / 2 if metade else ef["pct_turno"]
            x["dots"].append({"cond": cond, "pct": pct, "turnos": ef.get("turnos", 0)})
            notas.append(f"sofre {pct:g}% da Vida máxima por turno" + (f" por {ef['turnos']} turnos" if ef.get("turnos") else " até o fim do combate"))
        if cond in ("Sono", "Congelamento", "Loucura"):
            x["efeitos"].append({"nome": {"Sono": "Inconsciente", "Congelamento": "CA pela metade", "Loucura": "Loucura (dano mental ×2)"}[cond],
                                 "turnos": ef.get("turnos", 0)})
        return notas

    def ponto_chave(self, iid, idx, revelado):
        with self.lock:
            x = self._achar(iid)
            if not x or not (0 <= int(idx) < len(x["pontos_chave"])):
                return False
            x["pontos_chave"][int(idx)]["revelado"] = bool(revelado)
            self._salvar_combate()
            return True

    def editar(self, iid, campos):
        """Troca valores à mão: nome, Vida, Vida máxima, Postura, CA, notas, iniciativa, efeitos e barras de condição."""
        with self.lock:
            x = self._achar(iid)
            if not x:
                return False
            for k in ("nome", "notas"):
                if k in campos:
                    x[k] = str(campos[k])[:300 if k == "nome" else 3000]
            for k in ("vida_max", "vida", "postura_max", "postura", "ca", "ataque", "dt"):
                if k in campos:
                    x[k] = max(0, _num(campos[k]))
            x["vida"] = min(x["vida"], x["vida_max"])
            if "exposto" in campos:
                x["exposto"] = bool(campos["exposto"])
            if "caido" in campos:
                x["caido"] = bool(campos["caido"])
            if "ini" in campos:
                x["ini"] = None if campos["ini"] in (None, "") else _num(campos["ini"])
            if isinstance(campos.get("efeitos"), list):
                x["efeitos"] = [{"nome": str(e.get("nome", ""))[:40], "turnos": max(0, _num(e.get("turnos")))} for e in campos["efeitos"] if isinstance(e, dict)][:20]
            for c, v in (campos.get("cond") or {}).items():
                if c in x["cond"] and isinstance(v, dict):
                    b = x["cond"][c]
                    for k in ("atual", "max"):
                        if k in v:
                            b[k] = _num(v[k])
            self._salvar_combate()
            return True

    # --- iniciativa e turnos (com a sessão aberta, a ordem é a da sessão; sem ela, é local)
    def ao_vez(self, nome):
        """Chamado a cada turno novo (sessão ou local): aplica o que acontece no começo do turno de um inimigo."""
        with self.lock:
            x = next((i for i in self.combate()["inimigos"] if i["nome"] == nome), None)
            if not x:
                return
            notas = []
            for d in list(x["dots"]):
                perda = max(1, int(x["vida_max"] * d["pct"] / 100))
                x["vida"] = max(0, x["vida"] - perda)
                notas.append(f"{d['cond']}: −{perda}")
                if d["turnos"]:
                    d["turnos"] -= 1
                    if d["turnos"] <= 0:
                        x["dots"].remove(d)
            resto = []
            for e in x["efeitos"]:
                if e.get("turnos"):
                    e["turnos"] -= 1
                    if e["turnos"] <= 0:
                        continue
                resto.append(e)
            x["efeitos"] = resto
            if x["exposto"]:
                x["exposto"] = False
            if x["vida"] == 0:
                x["caido"] = True
            if notas:
                self._log(f"Início do turno de {x['nome']}: " + ", ".join(notas) + f" (Vida {x['vida']})")
            self._salvar_combate()

    def ordem_local(self):
        c = self.combate()
        return c["ordem"], c["vez"], c["rodada"]

    def participantes_inimigos(self):
        """Quem dos inimigos entra na iniciativa (os que não caíram), com dados e bônus de cada um."""
        return [{"nome": x["nome"], "dados": x.get("ini_dados", 1), "bonus": x.get("ini_bonus", 0)} for x in self.combate()["inimigos"] if not x["caido"]]

    def _gravar_iniciativa(self, ordem, det):
        for x in self.combate()["inimigos"]:
            x["ini"] = next((o[1] for o in ordem if o[0] == x["nome"]), None)

    def local_iniciativa(self, jogadores=(), primeiro=""):
        """Sem sessão aberta: rola os inimigos (e quem for passado em `jogadores`) e monta a ordem."""
        with self.lock:
            c = self.combate()
            parts = self.participantes_inimigos() + [dict(j) for j in jogadores]
            ordem, det = R.rolar_ordem_iniciativa(parts, lambda f: self.rng(1, f), primeiro)
            c["ordem"], c["vez"], c["rodada"], c["detalhe"] = ordem, -1, 1, det
            c["abertura"] = primeiro if any(o[0] == primeiro for o in ordem) else ""
            self._gravar_iniciativa(ordem, det)
            self._log("Iniciativa: " + ", ".join(f"{n} {v}" for n, v, _ in ordem) + (f" — {c['abertura']} abre o combate" if c["abertura"] else ""))
            self._salvar_combate()
        if c["abertura"]:
            self.ao_vez(c["abertura"])
        else:
            self.local_passar()

    def local_passar(self):
        with self.lock:
            c = self.combate()
            if not c["ordem"]:
                c["rodada"] += 1
            else:
                c["vez"] += 1
                if c["vez"] >= len(c["ordem"]):
                    c["vez"] = 0
                    c["rodada"] += 1
            nome = c["ordem"][c["vez"]][0] if 0 <= c["vez"] < len(c["ordem"]) else ""
            self._log(f"Rodada {c['rodada']} — vez de {nome}" if nome else f"Rodada {c['rodada']}")
            self._salvar_combate()
        if nome:
            self.ao_vez(nome)
