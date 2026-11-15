# -*- coding: utf-8 -*-
"""Janelas do Grupo no PC: a do jogador (aliados, pedidos, trocas, rolagens…) e a do mestre (liga/desliga, espólio,
teste em grupo, aprovar pedidos). A lógica fica no mestre (grupo.py); aqui é só a interface."""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import regras as R
from grupo import CFG_ROTULOS, SUSSURRO_MODOS, REACOES, DT_MEDICINA

SINAIS = ["Preciso de cura", "Vou focar este alvo", "Recuem!", "Guardem a Reação", "Sem Mana", "Pronto para o combo"]
PERICIAS_TESTE = [p[0] for p in R.PERICIAS] + [p[0] for p in R.PERICIAS_DEFESA]


class _Base(tk.Toplevel):
    """Janela com área rolável que é redesenhada quando o estado do grupo muda."""

    def __init__(self, pai, titulo, tamanho):
        super().__init__(pai)
        self.pai, self.c, self.fonte = pai, pai.c, pai.fonte
        self.title(titulo)
        self.geometry(tamanho)
        self.configure(background=self.c["PERG"])
        self._ultimo = None
        cv = tk.Canvas(self, bg=self.c["PERG"], highlightthickness=0)
        sb = ttk.Scrollbar(self, orient="vertical", command=cv.yview)
        cv.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        cv.pack(side="left", fill="both", expand=True)
        self.corpo = tk.Frame(cv, bg=self.c["PERG"], padx=16, pady=12)
        jan = cv.create_window((0, 0), window=self.corpo, anchor="nw")
        self.corpo.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>", lambda e: cv.itemconfigure(jan, width=e.width))

    def _limpar(self):
        for w in self.corpo.winfo_children():
            w.destroy()

    def _sec(self, txt, extra=""):
        f = tk.Frame(self.corpo, bg=self.c["PERG"])
        f.pack(fill="x", pady=(12, 4))
        tk.Label(f, text="❧ " + txt.upper(), bg=self.c["PERG"], fg=self.c["VINHO"], font=(self.fonte, 10, "bold")).pack(side="left")
        if extra:
            tk.Label(f, text=extra, bg=self.c["PERG"], fg=self.c["TINTA2"], font=(self.fonte, 9, "italic")).pack(side="left", padx=8)
        return f

    def _txt(self, master, txt, bold=False, sub=False, cor=None, **kw):
        lb = tk.Label(master, text=txt, bg=master["bg"], fg=cor or (self.c["TINTA2"] if sub else self.c["TINTA"]),
                      font=(self.fonte, 9 if sub else 10, "bold" if bold else "italic" if sub else "normal"),
                      justify="left", anchor="w", wraplength=kw.pop("wrap", 520))
        lb.pack(**dict({"anchor": "w"}, **kw))
        return lb

    def _cartao(self, cor=None):
        f = tk.Frame(self.corpo, bg=cor or self.c["CAMPO"], padx=10, pady=8, highlightbackground=self.c["OURO"], highlightthickness=1)
        f.pack(fill="x", pady=3)
        return f

    def _linha(self, master):
        f = tk.Frame(master, bg=master["bg"])
        f.pack(fill="x", pady=(4, 0))
        return f


class JanelaGrupo(_Base):
    """O grupo visto pelo jogador do PC."""

    def __init__(self, pai):
        super().__init__(pai, "Grupo", "600x720")
        self.atualizar(pai.grupo)

    def acao(self, **m):
        self.pai.enviar_grupo(m)

    def _pedir(self, tipo, para, **m):
        self.acao(acao="propor", tipo=tipo, para=para, **m)

    def atualizar(self, g):
        chave = repr({k: v for k, v in (g or {}).items() if k != "v"})
        if chave == self._ultimo:
            return
        self._ultimo = chave
        self._limpar()
        if not g:
            self._txt(self.corpo, "Aguardando o mestre…", sub=True)
            return
        self.g, eu, c = g, self.pai.meu_nome, self.c
        para = [p for p in g["propostas"] if p["para"] == eu]
        meus = [p for p in g["propostas"] if p["de"] == eu]
        if para or meus:
            self._sec("Pedidos")
            for p in para:
                f = self._cartao()
                self._txt(f, f"{p['de']} quer te dar", bold=True)
                self._txt(f, p["texto"], sub=True)
                ln = self._linha(f)
                ttk.Button(ln, text="Aceitar", command=lambda i=p["id"]: self.acao(acao="responder", num=i, aceitar=True)).pack(side="left")
                ttk.Button(ln, text="Recusar", command=lambda i=p["id"]: self.acao(acao="responder", num=i, aceitar=False)).pack(side="left", padx=6)
            for p in meus:
                f = self._cartao()
                self._txt(f, f"Aguardando {p['para']}: {p['texto']}", sub=True)
                ttk.Button(f, text="Cancelar", command=lambda i=p["id"]: self.acao(acao="cancelar", num=i)).pack(anchor="w")
        t = g.get("teste")
        if t:
            self._sec("Teste em grupo")
            f = self._cartao()
            self._txt(f, t["pericia"] + (f"  (DT {t['dt']})" if t["dt"] else ""), bold=True)
            if t["aberto"]:
                self._txt(f, ("Já rolaram: " + ", ".join(t["rolaram"]) + ". " if t["rolaram"] else "")
                          + ("Faltam: " + ", ".join(t["faltam"]) + ". " if t["faltam"] else "") + "O resultado aparece quando todos rolarem.", sub=True)
                if t["ja"]:
                    self._txt(f, f"Você rolou {t['res'][0]['total'] if t['res'] else ''}.", cor=c["VERDE"])
                else:
                    ttk.Button(f, text=f"🎲 Rolar {t['pericia']}", command=self._teste).pack(anchor="w", pady=(4, 0))
            else:
                for r in t["res"]:
                    self._txt(f, f"{r['nome']}: {r['total']}" + ((" — passou" if r["total"] >= t["dt"] else " — falhou") if t["dt"] else ""))
        self._sec("Aliados", "em combate" if g["ordem"] else "")
        for m in sorted(g["membros"], key=lambda x: not x["eu"]):
            f = self._cartao(c["PERG2"] if m.get("incapaz") else None)
            cab = m["nome"] + (" (você)" if m["eu"] else "") + (f"  ·  {m['personagem']}" if m.get("personagem") else "") \
                + (f" · Nv {m['nivel']}" if m.get("nivel") else "") + ("  ⚔ vez" if m["vez"] else "") + ("  · sem sinal" if m.get("sem_sinal") else "")
            self._txt(f, cab, bold=True, cor=c["VINHO"] if m["vez"] else None)
            if m.get("vida"):
                self._txt(f, f"Vida {m['vida'][0]}/{m['vida'][1]}  " + "█" * (m["pct"] // 10) + "░" * (10 - m["pct"] // 10))
            elif m.get("pct") is not None:
                self._txt(f, f"Vida {m['pct']}%  " + "█" * (m["pct"] // 10) + "░" * (10 - m["pct"] // 10))
            if m.get("incapaz"):
                pt = m.get("portao") or [0, 0]
                self._txt(f, f"INCAPAZ — Portão da Morte: {pt[0]} sucesso(s), {pt[1]} falha(s)", bold=True, cor=c["C_VIDA"])
            extras = [f"{x[0]} {x[1]}/{x[2]}" for x in m.get("cond", [])] + ["⏳ " + e for e in m.get("efeitos", [])]
            if extras:
                self._txt(f, " · ".join(extras), sub=True)
            if m.get("sinal"):
                self._txt(f, "⚑ " + m["sinal"], bold=True, cor=c["VINHO"])
            if m.get("intencao"):
                self._txt(f, "Pretende: " + m["intencao"], sub=True)
            if m.get("vinculo"):
                self._txt(f, "Vínculo: " + m["vinculo"], sub=True)
            ln = self._linha(f)
            if m["eu"]:
                ttk.Button(ln, text="⚑ Sinal e intenção", command=self._sinal).pack(side="left")
                tk.Label(ln, text="  Mostrar aos aliados:", bg=ln["bg"], fg=c["TINTA2"], font=(self.fonte, 9, "italic")).pack(side="left")
                for v, r in (("tudo", "tudo"), ("barra", "só a barra"), ("nada", "nada")):
                    ttk.Button(ln, text=("● " if g["vis"] == v else "") + r, command=lambda v=v: self.acao(acao="vis", modo=v)).pack(side="left", padx=2)
            else:
                n = m["nome"]
                if g["cfg"]["ajuda"]:
                    if m.get("incapaz"):
                        ttk.Button(ln, text="✚ Medicina", command=lambda n=n: self._medicina(n)).pack(side="left")
                    ttk.Button(ln, text="Incentivar", command=lambda n=n: self._incentivo(n)).pack(side="left", padx=2)
                    ttk.Button(ln, text="Curar", command=lambda n=n: self._cura(n)).pack(side="left")
                    ttk.Button(ln, text="Efeito", command=lambda n=n: self._buff(n)).pack(side="left", padx=2)
                ln2 = self._linha(f)
                if g["cfg"]["trocas"]:
                    ttk.Button(ln2, text="Dar item", command=lambda n=n: self._item(n)).pack(side="left")
                    ttk.Button(ln2, text="Dar dinheiro", command=lambda n=n: self._dinheiro(n)).pack(side="left", padx=2)
                if g["cfg"]["sussurro"] != "off":
                    ttk.Button(ln2, text="Sussurrar", command=lambda n=n: self._sussurro(n)).pack(side="left")
                if g["cfg"]["diario"]:
                    ttk.Button(ln2, text="Vínculo", command=lambda n=n, v=m.get("vinculo", ""): self._vinculo(n, v)).pack(side="left", padx=2)
        if g["cfg"]["ajuda"] and len(g["membros"]) > 1:
            ttk.Button(self.corpo, text="🍲 Cozinhar para o grupo", command=self._refeicao).pack(anchor="w", pady=(6, 0))
        esp = g.get("espolio")
        if esp:
            self._sec("Espólio", "marque o que você quer; o mestre divide e o empate vai no d20")
            for it in esp["itens"]:
                f = self._cartao()
                quero = eu in it["quer"]
                self._txt(f, f"{it['qtd']}× {it['item']}", bold=True)
                self._txt(f, "Querem: " + ", ".join(it["quer"]) if it["quer"] else "Ninguém marcou", sub=True)
                ttk.Button(f, text="✓ Quero" if quero else "Quero",
                           command=lambda i=it["id"], q=not quero: self.acao(acao="espolio_quero", num=i, quer=q)).pack(anchor="w")
            if esp["contos"]:
                self._txt(self.corpo, f"Dinheiro a dividir: {esp['contos_txt']}.", sub=True)
        if g.get("caixa"):
            self._sec("Caixa do grupo")
            f = self._cartao()
            self._txt(f, g["caixa"]["txt"], bold=True)
            ln = self._linha(f)
            ttk.Button(ln, text="Pôr", command=lambda: self._caixa(1)).pack(side="left")
            ttk.Button(ln, text="Tirar", command=lambda: self._caixa(-1)).pack(side="left", padx=4)
            if g["caixa"]["log"]:
                self._txt(f, "\n".join(g["caixa"]["log"][:4]), sub=True)
        if g["cfg"]["feed"]:
            sec = self._sec("Rolagens do grupo")
            ttk.Button(sec, text="minhas: visíveis" if self.pai.compartilha else "minhas: ocultas", command=self._alternar_feed).pack(side="right")
            if not g["feed"]:
                self._txt(self.corpo, "Nenhuma rolagem ainda.", sub=True)
            for e in g["feed"][:15]:
                f = self._cartao(c["PERG2"] if e["destaque"] else None)
                self._txt(f, f"{e['quem']} · {e['titulo']}   {e['hora']}", bold=True)
                self._txt(f, "\n".join(e["linhas"]), sub=True)
                ln = self._linha(f)
                for r in REACOES:
                    q = e["reacoes"].get(r, [])
                    ttk.Button(ln, text=r + (f" {len(q)}" if q else ""), width=5,
                               command=lambda s=e["seq"], r=r: self.acao(acao="reagir", seq=s, r=r)).pack(side="left", padx=1)
        if g["cfg"]["diario"]:
            self._sec("Diário do grupo")
            ttk.Button(self.corpo, text="＋ Anotar", command=self._nota).pack(anchor="w")
            for n in g["notas"][:30]:
                f = self._cartao()
                self._txt(f, f"{n['quem']}   {n['hora']}", bold=True)
                self._txt(f, n["texto"])
                if n["quem"] == eu:
                    ttk.Button(f, text="Apagar", command=lambda i=n["id"]: self.acao(acao="nota_del", num=i)).pack(anchor="w")
        ln = tk.Frame(self.corpo, bg=c["PERG"])
        ln.pack(fill="x", pady=(14, 0))
        ttk.Button(ln, text=("✓ " if self.pai.auto_ajuda else "") + "Aceitar ajudas sem perguntar", command=self._alternar_auto).pack(side="left")
        self._txt(self.corpo, "Trocas de item e dinheiro sempre perguntam. O mestre vê tudo e pode desligar cada recurso.", sub=True)

    # --- ações
    def _ponte(self):
        if not self.pai.ponte or not self.pai.ponte.app.inicializado:
            messagebox.showinfo("Grupo", "Abra uma ficha primeiro.", parent=self)
            return None
        return self.pai.ponte

    def _alternar_feed(self):
        self.pai.compartilha = not self.pai.compartilha
        self._ultimo = None
        self.atualizar(self.g)

    def _alternar_auto(self):
        self.pai.auto_ajuda = not self.pai.auto_ajuda
        self._ultimo = None
        self.atualizar(self.g)

    def _teste(self):
        p = self._ponte()
        if p:
            total, txt = p.rolar_pericia(self.g["teste"]["pericia"])
            p.registrar(f"🎲 Teste em grupo: {self.g['teste']['pericia']}", [txt])
            self.acao(acao="teste_rolar", total=total, txt=txt)

    def _medicina(self, n):
        p = self._ponte()
        if p:
            total, txt = p.rolar_pericia("Medicina")
            p.registrar(f"✚ Medicina em {n}", [txt, f"DT {DT_MEDICINA}: " + ("sucesso" if total >= DT_MEDICINA else "falhou")])
            self._pedir("medicina", n, total=total, txt=txt)

    def _incentivo(self, n):
        if self.pai.ponte:
            self.pai.ponte.marcar_acao("Reação")
        self._pedir("incentivo", n)

    def _cura(self, n):
        v = simpledialog.askinteger("Curar", f"Quanto de Vida para {n}? (role a cura na sua ficha e mande o total)", parent=self, minvalue=1, maxvalue=9999)
        if v:
            d = simpledialog.askstring("Curar", "De onde vem a cura? (opcional)", parent=self) or ""
            self._pedir("cura", n, valor=v, desc=d)

    def _buff(self, n):
        nome = simpledialog.askstring("Efeito", f"Nome do efeito em {n} (ex.: Bênção):", parent=self)
        if not nome:
            return
        t = simpledialog.askinteger("Efeito", "Dura quantos turnos dele? (0 = até o mestre tirar)", parent=self, minvalue=0, maxvalue=99, initialvalue=1)
        d = simpledialog.askstring("Efeito", "O que faz? (ex.: +2 de acerto)", parent=self) or ""
        self._pedir("buff", n, nome=nome, turnos=t or 0, desc=d)

    def _escolher(self, titulo, opcoes):
        """Lista simples de escolha; devolve o índice ou None."""
        w = tk.Toplevel(self)
        w.title(titulo)
        w.configure(background=self.c["PERG"])
        w.transient(self)
        f = tk.Frame(w, bg=self.c["PERG"], padx=16, pady=12)
        f.pack(fill="both", expand=True)
        tk.Label(f, text=titulo, bg=self.c["PERG"], fg=self.c["VINHO"], font=(self.fonte, 12, "bold")).pack(anchor="w", pady=(0, 6))
        res = {"i": None}
        for i, o in enumerate(opcoes):
            ttk.Button(f, text=o, command=lambda i=i: (res.update(i=i), w.destroy())).pack(fill="x", pady=1)
        self._esc_win, self._esc_res = w, res
        try:
            w.grab_set()
            self.wait_window(w)
        except tk.TclError:
            pass
        return res["i"]

    def _item(self, n):
        p = self._ponte()
        if not p:
            return
        itens = [i for i in p.itens() if i["item"].strip()]
        if not itens:
            messagebox.showinfo("Grupo", "Sua bolsa está vazia.", parent=self)
            return
        i = self._escolher(f"Dar a {n}", [f"{x['item']}  (você tem {x['qtd']})" for x in itens])
        if i is None:
            return
        it = itens[i]
        q = simpledialog.askinteger("Dar item", f"Quantos {it['item']}? (você tem {it['qtd']})", parent=self, minvalue=1,
                                    maxvalue=max(1, it["qtd"]), initialvalue=1)
        if q:
            self._pedir("item", n, item={"item": it["item"], "carga": it["carga"], "qtd": q})

    def _valor(self, titulo, pergunta, limite=None):
        s = simpledialog.askstring(titulo, pergunta, parent=self)
        if not s:
            return None
        v = R.ler_dinheiro(s)
        if not v or v < 1:
            messagebox.showinfo("Grupo", "Não entendi o valor. Ex.: 35 prata.", parent=self)
            return None
        if limite is not None and v > limite:
            messagebox.showinfo("Grupo", f"Você só tem {R.formatar_dinheiro(limite)}.", parent=self)
            return None
        return v

    def _dinheiro(self, n):
        p = self._ponte()
        if p:
            v = self._valor("Dar dinheiro", f"Quanto para {n}? Você tem {R.formatar_dinheiro(p.dinheiro_atual())}. Ex.: 35 prata", p.dinheiro_atual())
            if v:
                self._pedir("dinheiro", n, contos=v)

    def _caixa(self, sinal):
        p = self._ponte()
        if p:
            v = self._valor("Caixa do grupo", ("Pôr" if sinal > 0 else "Tirar") + f" quanto? A caixa tem {self.g['caixa']['txt']}; você tem "
                            f"{R.formatar_dinheiro(p.dinheiro_atual())}.", p.dinheiro_atual() if sinal > 0 else None)
            if v:
                self.acao(acao="caixa", delta=sinal * v)

    def _sussurro(self, n):
        t = simpledialog.askstring("Sussurrar", f"Mensagem para {n}" + (" (o mestre também lê):" if self.g["cfg"]["sussurro"] == "tudo" else ":"), parent=self)
        if t:
            self.acao(acao="sussurro", para=n, texto=t)

    def _vinculo(self, n, atual):
        t = simpledialog.askstring("Vínculo", f"O que liga você e {n}? (os dois veem)", parent=self, initialvalue=atual)
        if t is not None:
            self.acao(acao="vinculo", com=n, texto=t)

    def _sinal(self):
        i = self._escolher("Sinal para o grupo", SINAIS + ["Escrever outro…", "Limpar sinal e intenção"])
        if i is None:
            return
        if i == len(SINAIS) + 1:
            self.acao(acao="sinal", sinal="", intencao="")
            return
        s = SINAIS[i] if i < len(SINAIS) else (simpledialog.askstring("Sinal", "Sinal (até 40 letras):", parent=self) or "")
        it = simpledialog.askstring("Intenção", "O que você pretende fazer no seu turno? (opcional)", parent=self) or ""
        self.acao(acao="sinal", sinal=s, intencao=it)

    def _nota(self):
        t = simpledialog.askstring("Diário do grupo", "Nota (todos do grupo leem):", parent=self)
        if t:
            self.acao(acao="nota_add", texto=t)

    def _refeicao(self):
        p = self._ponte()
        if not p:
            return
        i = self._escolher("Nível da refeição", [f"Nível {n} — DT {R.REFEICOES[n][0]}: {R.REFEICOES[n][1]}" for n in (1, 2, 3, 4)])
        if i is None:
            return
        nivel = i + 1
        total, txt = p.rolar_pericia("Gastronomia")
        dt = R.REFEICOES[nivel][0]
        p.registrar(f"🍲 Refeição de nível {nivel}", [txt, "Deu certo." if total >= dt else f"Falhou (DT {dt})."])
        self.acao(acao="propor", tipo="refeicao", nivel=nivel, total=total, txt=txt, eu=True,
                  alvos=[m["nome"] for m in self.g["membros"] if not m["eu"]])


class JanelaGrupoMestre(_Base):
    """O grupo visto pelo mestre: liga e desliga recursos, aprova pedidos, pede testes e solta o espólio."""

    def __init__(self, pai):
        super().__init__(pai, "Grupo — mestre", "640x760")
        self.srv = pai.servidor
        self.atualizar()

    def atualizar(self):
        g = self.srv.grupo_mestre()
        chave = repr(g)
        if chave == self._ultimo:
            return
        self._ultimo = chave
        self._limpar()
        self.g, c = g, self.c
        self._sec("O que os jogadores podem fazer entre si")
        for k, r in CFG_ROTULOS:
            ttk.Button(self.corpo, text=("☑ " if g["cfg"][k] else "☐ ") + r, command=lambda k=k: self.srv.grupo_config(k, not self.g["cfg"][k])).pack(anchor="w", pady=1)
        ln = tk.Frame(self.corpo, bg=c["PERG"])
        ln.pack(anchor="w", pady=(4, 0))
        for k, r in SUSSURRO_MODOS:
            ttk.Button(ln, text=("● " if g["cfg"]["sussurro"] == k else "○ ") + r, command=lambda k=k: self.srv.grupo_config("sussurro", k)).pack(anchor="w", pady=1)
        self._sec("Pedidos em aberto", "o jogador que recebe aceita; você também pode decidir")
        if not g["propostas"]:
            self._txt(self.corpo, "Nenhum pedido aguardando.", sub=True)
        for p in g["propostas"]:
            f = self._cartao()
            self._txt(f, f"{p['de']} → {p['para']}: {p['texto']}")
            ln = self._linha(f)
            ttk.Button(ln, text="Aceitar por ele", command=lambda i=p["id"]: self.srv.mestre_resolver(i, True)).pack(side="left")
            ttk.Button(ln, text="Recusar", command=lambda i=p["id"]: self.srv.mestre_resolver(i, False)).pack(side="left", padx=6)
        self._sec("Teste em grupo")
        t = g["teste"]
        ln = tk.Frame(self.corpo, bg=c["PERG"])
        ln.pack(anchor="w")
        ttk.Button(ln, text="🎲 Pedir teste…", command=self._pedir_teste).pack(side="left")
        if t:
            if t["aberto"]:
                ttk.Button(ln, text="Revelar agora", command=self.srv.revelar_teste).pack(side="left", padx=6)
            ttk.Button(ln, text="Encerrar", command=self.srv.encerrar_teste).pack(side="left")
            self._txt(self.corpo, t["pericia"] + (f" (DT {t['dt']})" if t["dt"] else "") + (" — aberto" if t["aberto"] else " — revelado"), bold=True)
            for n, r in sorted(t["res"].items(), key=lambda x: -x[1]["total"]):
                self._txt(self.corpo, f"{n}: {r['total']}" + ((" — passou" if r["total"] >= t["dt"] else " — falhou") if t["dt"] else ""))
        self._sec("Espólio")
        ln = tk.Frame(self.corpo, bg=c["PERG"])
        ln.pack(anchor="w")
        ttk.Button(ln, text="＋ Item…", command=self._espolio_item).pack(side="left")
        ttk.Button(ln, text="＋ Dinheiro…", command=self._espolio_dinheiro).pack(side="left", padx=6)
        e = g["espolio"]
        if e:
            ttk.Button(ln, text="Dividir entre os jogadores", command=self.srv.distribuir_espolio).pack(side="left")
            ttk.Button(ln, text="Descartar", command=self.srv.descartar_espolio).pack(side="left", padx=6)
            for it in e["itens"]:
                self._txt(self.corpo, f"{it['qtd']}× {it['item']} — " + ("querem: " + ", ".join(it["quer"]) if it["quer"] else "ninguém marcou"))
            if e["contos"]:
                self._txt(self.corpo, "Dinheiro: " + R.formatar_dinheiro(e["contos"]))
        else:
            self._txt(self.corpo, "Nada solto. Itens com um interessado vão para ele; com vários, o d20 decide. O dinheiro é dividido por igual.", sub=True)
        self._sec("Caixa do grupo")
        self._txt(self.corpo, g["caixa"]["txt"], bold=True)
        if g["caixa"]["log"]:
            self._txt(self.corpo, "\n".join(g["caixa"]["log"][:8]), sub=True)
        if g["sinais"]:
            self._sec("Sinais e intenções")
            for n, s in g["sinais"].items():
                self._txt(self.corpo, f"{n}: " + " · ".join(x for x in (s.get("sinal"), s.get("intencao")) if x))
        self._sec("Rolagens do grupo")
        for x in g["feed"][:20]:
            self._txt(self.corpo, f"{x['hora']}  {x['quem']} · {x['titulo']}: " + " | ".join(x["linhas"])
                      + ("   " + " ".join(f"{r}{len(q)}" for r, q in x["reacoes"].items()) if x["reacoes"] else ""), sub=not x["destaque"])
        if not g["feed"]:
            self._txt(self.corpo, "Nenhuma rolagem ainda.", sub=True)
        self._sec("Diário do grupo")
        ttk.Button(self.corpo, text="＋ Anotar como mestre", command=self._nota).pack(anchor="w")
        for n in g["notas"][:40]:
            f = self._cartao()
            self._txt(f, f"{n['quem']}   {n['hora']}", bold=True)
            self._txt(f, n["texto"])
            ttk.Button(f, text="Apagar", command=lambda i=n["id"]: self.srv.apagar_nota(i)).pack(anchor="w")

    def _pedir_teste(self):
        w = tk.Toplevel(self)
        w.title("Teste em grupo")
        w.configure(background=self.c["PERG"])
        w.transient(self)
        f = tk.Frame(w, bg=self.c["PERG"], padx=16, pady=12)
        f.pack()
        vp, vd = tk.StringVar(value="Furtividade"), tk.StringVar(value="15")
        tk.Label(f, text="Perícia", bg=self.c["PERG"], fg=self.c["TINTA"]).grid(row=0, column=0, sticky="w")
        ttk.Combobox(f, values=PERICIAS_TESTE, textvariable=vp, width=22).grid(row=0, column=1, padx=6, pady=2)
        tk.Label(f, text="DT (0 = sem DT)", bg=self.c["PERG"], fg=self.c["TINTA"]).grid(row=1, column=0, sticky="w")
        ttk.Entry(f, textvariable=vd, width=6).grid(row=1, column=1, sticky="w", padx=6, pady=2)

        def ok():
            try:
                dt = int(vd.get() or 0)
            except ValueError:
                dt = 0
            self.srv.pedir_teste(vp.get().strip() or "Teste", dt)
            w.destroy()
        ttk.Button(f, text="Pedir a todos", command=ok).grid(row=2, column=1, sticky="e", pady=(8, 0))
        self._teste_ok = ok

    def _espolio_item(self):
        nome = simpledialog.askstring("Espólio", "Item (nome do livro ou outro):", parent=self)
        if not nome:
            return
        q = simpledialog.askinteger("Espólio", f"Quantos {nome}?", parent=self, minvalue=1, maxvalue=999, initialvalue=1) or 1
        livro = next((x for x in self.pai.itens_livro() if x["nome"].lower() == nome.strip().lower()), None)
        self.srv.soltar_espolio([{"item": livro["nome"] if livro else nome, "carga": f"{livro.get('peso', 0):g}" if livro else "", "qtd": q}])

    def _espolio_dinheiro(self):
        s = simpledialog.askstring("Espólio", "Quanto dinheiro? Ex.: 3 ouro, 20 prata", parent=self)
        v = R.ler_dinheiro(s or "")
        if v:
            self.srv.soltar_espolio([], v)
        elif s:
            messagebox.showinfo("Grupo", "Não entendi o valor.", parent=self)

    def _nota(self):
        t = simpledialog.askstring("Diário do grupo", "Nota do mestre:", parent=self)
        if t:
            self.srv.nota_do_mestre(t)
