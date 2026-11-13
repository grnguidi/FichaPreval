# -*- coding: utf-8 -*-
"""Ponte entre a ficha do PC aberta e a sessão em rede (resumo para o mestre; dano, condições, itens e vez do mestre)."""
import regras as R


def to_int(s, default=0):
    try:
        return int(str(s).strip().replace("+", ""))
    except Exception:
        return default


class PonteSessao:
    """Liga a ficha aberta à sessão: manda o resumo ao mestre e recebe dano, condições, itens e a vez."""

    def __init__(self, app):
        self.app = app

    def resumo(self):
        a = self.app
        if not a.inicializado:
            return None
        d, aa, n3 = a.d, a.a, a.nivel() // 3
        tal = a.talentos_escolhidos()
        defesas = {n: [d["bc"][k] + n3 + (2 if tn in tal else 0), R.vantagem(aa[k])] for n, k, tn in R.PERICIAS_DEFESA}
        return {"personagem": a.v_nome.get().strip(), "especie": a.v_especie.get().strip(), "nivel": a.nivel(),
                "vida": a._atual(a.v_vida_atual, d["vida"]), "vida_max": d["vida"],
                "mana": a._atual(a.v_mana_atual, d["mana"]), "mana_max": d["mana"],
                "vigor": a._atual(a.v_vigor_atual, d["vigor"]), "vigor_max": d["vigor"],
                "ca": d["ca"], "movimento": d["movimento"], "iniciativa": d["iniciativa_bonus"],
                "iniciativa_dados": d["iniciativa_dados"], "rd": d["rd"], "resistencias": list(d["resistencias"]),
                "defesas": defesas,
                "portao": [sum(v.get() for v in a.portao["Sucessos"]), sum(v.get() for v in a.portao["Falhas"])],
                "condicoes": [[n, to_int(c["atual"].get()), a.cond_max(n)] for n, c in a.cond.items()],
                "inventario": [{"item": i["item"], "carga": i["carga"], "qtd": to_int(i["qtd"], 1) or 1} for i in a._inventario()],
                "dinheiro": a.v_dinheiro.get().strip(), "carga": [round(a._carga_atual(), 1), d["carga"]],
                "sem_alma": a.sem_alma}

    def _nomes_efeitos(self):
        return {e.get("nome") for e in self.app.efeitos_mestre}

    def aplicar_dano(self, valor, tipo, desc):
        """valor > 0: dano, descontando RD e resistências da ficha; valor < 0: cura (sem passar do máximo).
        Devolve (texto para o jogador, relato para o mestre)."""
        a = self.app
        a.recalc()
        maximo = a.d["vida"]
        antes = a._atual(a.v_vida_atual, maximo)
        notas = []
        final = valor
        if valor > 0:
            ef = self._nomes_efeitos()
            final, notas = R.defesas_contra_dano(valor, tipo, a.d, a._rng, "Fragilizado" in ef, "Loucura" in ef)
        depois = max(0, min(maximo, antes - final))
        a.v_vida_atual.set(str(depois))
        txt = (f"Recebeu {final}" + (f" ({'; '.join(notas)})" if notas else "") + ". " if valor > 0 else "") + f"Vida: {antes} → {depois}"
        if depois == 0 and antes > 0:
            txt += "  — INCAPAZ: role o Portão da Morte no início do seu turno."
            if final > maximo // 2:
                txt += " Dano maior que metade da Vida: 1 falha automática."
        oque = f"Cura de {-valor}" if valor < 0 else f"{valor} de dano" + (f" ({tipo})" if tipo else "")
        a.registrar("📣 Do mestre", [oque + (f" — {desc}" if desc else ""), txt])
        relato = (f"recebeu {final} de {valor} ({'; '.join(notas)}), Vida {depois}/{maximo}" if valor > 0 and notas else
                  f"Vida {depois}/{maximo}" + (" — INCAPAZ" if depois == 0 and antes > 0 else ""))
        return txt, relato

    def pontos_condicao(self, cond, pontos, dt, desc):
        """Rola Fortitude/Vontade contra a DT; sucesso recebe metade. Se a barra encher, aplica o efeito do livro.
        Devolve (texto, relato, condição ativada ou None)."""
        a = self.app
        if cond not in a.cond:
            return "", "", None
        a.recalc()
        defesa = R.CONDICAO_TESTE.get(cond, "Fortitude")
        k = next(k for n, k, _ in R.PERICIAS_DEFESA if n == defesa)
        tn = next(tn for n, _, tn in R.PERICIAS_DEFESA if n == defesa)
        bonus = a.d["bc"][k] + a.nivel() // 3 + (2 if tn in a.talentos_escolhidos() else 0)
        auto_falha = defesa == "Vontade" and "Loucura" in self._nomes_efeitos()
        t = R.rolar_defesa(bonus, R.vantagem(a.a[k]), a._rng)
        sucesso = not auto_falha and t["total"] >= dt
        c = a.cond[cond]
        mx = a.cond_max(cond)
        antes = to_int(c["atual"].get())
        rec, novo, ativou = R.receber_condicao(antes, mx, pontos, sucesso)
        c["atual"].set(str(novo) if novo else "")
        teste = (f"{defesa} {t['total']} [d20 {', '.join(map(str, t['d20']))} +{bonus}] contra DT {dt}: "
                 + ("falha automática (Loucura)" if auto_falha else "SUCESSO, metade" if sucesso else "falhou"))
        linhas = [f"{pontos} de {cond}" + (f" — {desc}" if desc else ""), teste, f"{cond}: {antes} → {min(antes + rec, mx)}/{mx} (+{rec})"]
        relato = f"{teste}; {cond} +{rec} → {min(antes + rec, mx)}/{mx}"
        if ativou:
            info = R.CONDICAO_ATIVA[cond]
            linhas.append(f"⚠ {cond.upper()} ATIVOU: {info['desc']} A barra volta a zero.")
            relato += f" — {cond.upper()} ATIVOU"
            if info.get("pct_ja"):
                perda = max(1, a.d["vida"] * info["pct_ja"] // 100)
                vida = a._atual(a.v_vida_atual, a.d["vida"])
                a.v_vida_atual.set(str(max(0, vida - perda)))
                linhas.append(f"Vida: {vida} → {max(0, vida - perda)} (−{perda})")
                relato += f", perdeu {perda} de Vida"
        a.registrar(f"📣 {cond}", linhas, destaque=ativou)
        a.recalc()
        return "\n".join(linhas[1:]), relato, cond if ativou else None

    def item(self, ev):
        """O mestre dá ou tira um item da bolsa."""
        a = self.app
        if ev.get("acao") == "dar":
            it = ev.get("item") or {}
            nome, q = str(it.get("item", ""))[:40], max(1, to_int(it.get("qtd"), 1))
            linha = next((x for x in a.inv if x["item"].get().strip().lower() == nome.lower()), None)
            if linha:
                linha["qtd"].set(str((to_int(linha["qtd"].get(), 1) or 1) + q))
            else:
                linha = next((x for x in a.inv if not x["item"].get().strip() and not x["carga"].get().strip()), None)
                if linha is None:
                    a.registrar("📣 Do mestre", [f"Recebeu {q}× {nome}, mas a bolsa está cheia (30 linhas): anote à mão."])
                    return f"Bolsa cheia: {q}× {nome} não coube."
                linha["item"].set(nome)
                linha["carga"].set(str(it.get("carga", "")))
                linha["qtd"].set(str(q))
            txt = f"Recebeu {q}× {nome}" + (f" — {ev.get('desc')}" if ev.get("desc") else "")
        else:
            nome, q = str(ev.get("nome", "")), max(1, to_int(ev.get("qtd"), 1))
            linha = next((x for x in a.inv if x["item"].get().strip().lower() == nome.lower()), None)
            if not linha:
                return f"O mestre tirou {nome}, mas o item não está mais na bolsa."
            resto = (to_int(linha["qtd"].get(), 1) or 1) - q
            if resto > 0:
                linha["qtd"].set(str(resto))
            else:
                for k in ("item", "carga", "qtd"):
                    linha[k].set("")
            txt = f"O mestre tirou {q}× {nome}" + (f" — {ev.get('desc')}" if ev.get("desc") else "")
        a.registrar("📣 Bolsa", [txt])
        a.recalc()
        return txt

    def minha_vez(self):
        """Começo do meu turno: conta para o desgaste (a arma desgastada volta depois de um turno parada)."""
        a = self.app
        a.meus_turnos += 1
        for dg in a.desgaste.values():
            if dg.get("desgastada") and a.meus_turnos >= dg.get("em", 0) + 2:
                dg.update(usados=0, desgastada=False, contado=-1)
        a.novo_turno(silencioso=True)   # ações e usos por turno renovados
        a.recalc()

    def combate(self, inicio):
        """O mestre começou (iniciativa) ou encerrou o combate: renova ações, contra-encantamentos e usos por combate."""
        self.app.novo_combate(silencioso=True)
        self.app.recalc()

    def efeitos(self, lista, rodada):
        self.app.efeitos_mestre = list(lista)
        self.app.recalc()

    def aviso(self, texto):
        pass   # o próprio diário já registra; efeitos aparecem na aba Combate
