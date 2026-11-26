"""Abas Corpo (Perda de Membros, livro 3.4) e Crença (Cultos e Igrejas, livro 3.4) do app de PC.

As regras ficam em regras.py (penalidades_membros, poderes_culto…) e os textos do livro em dados_prevalecentes (DADOS["cultos"]).
Este módulo só monta a interface: é um mixin da janela principal (prevalecentes.App)."""
import random
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import regras as R

CULTO_VAZIO = {"papel": "", "crenca": "", "nome": "", "divindade": "", "profeta": "", "tema": "", "regra_faz": "", "regra_nunca": "",
               "grau": 1, "abalado": False, "local": "", "discipulos": "", "comunidades": "", "igreja": "", "na_igreja": False,
               "preces_usadas": 0, "milagres_usados": 0, "notas": ""}
PAPEIS = (("", "Sem culto"), ("fiel", "Fiel de um culto"), ("profeta", "Profeta (fundador)"))
CAMPOS_TEXTO = (("nome", "Nome do Culto"), ("divindade", "Divindade"), ("profeta", "Profeta"), ("regra_faz", "Os seguidores devem"),
                ("regra_nunca", "Os seguidores nunca podem"), ("comunidades", "Comunidades convertidas"), ("local", "Local sagrado"),
                ("discipulos", "Discípulos"), ("crenca", "No que acredita"), ("notas", "Anotações"))
ROT_TIPO = {"olhos": ("Olhos", "Olho"), "bracos": ("Braços e mãos", "Braço"), "pernas": ("Pernas", "Perna")}


def _int(v, padrao=0):
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return padrao


def normalizar(c):
    o = dict(CULTO_VAZIO)
    if isinstance(c, dict):
        o.update({k: c[k] for k in CULTO_VAZIO if k in c})
    for k, v in CULTO_VAZIO.items():
        if isinstance(v, str):
            o[k] = str(o[k] or "")
    if o["papel"] not in ("", "fiel", "profeta"):
        o["papel"] = ""
    o["grau"] = max(1, min(5, _int(o["grau"], 1)))
    o["abalado"], o["na_igreja"] = bool(o["abalado"]), bool(o["na_igreja"])
    o["preces_usadas"], o["milagres_usados"] = max(0, _int(o["preces_usadas"])), max(0, _int(o["milagres_usados"]))
    if o["igreja"] not in R.IGREJAS:
        o["igreja"] = ""
    return o


def poderes(c):
    ig = c["igreja"] in R.IGREJAS and c["na_igreja"] and c["grau"] >= 2
    return R.poderes_culto(c["grau"], ig and c["grau"] >= 5), ig


class CorpoCultoMixin:
    def _g(self, nome):
        """Cor/fonte atual do tema (os globais de prevalecentes mudam com o tema)."""
        return getattr(sys.modules[type(self).__module__], nome)

    # ============================================================ Corpo
    def _pag_corpo(self):
        G = self._g
        p = self._pagina("Corpo")
        p.columnconfigure(0, weight=1)
        p.columnconfigure(1, weight=1)
        c = self.secao(p, "Corpo  ·  Perda de Membros", row=0, column=0, columnspan=2)
        c.columnconfigure(0, weight=1)
        self.l_corpo_estado = tk.Label(c, text="", bg=G("PERG"), fg=G("VINHO"), font=(G("FONTE"), 12, "bold"), anchor="w", justify="left")
        self.l_corpo_estado.grid(row=0, column=0, sticky="we")
        self.l_corpo_notas = tk.Label(c, text="", bg=G("PERG"), fg=G("TINTA"), font=(G("FONTE"), 10), anchor="w", justify="left", wraplength=900)
        self.l_corpo_notas.grid(row=1, column=0, sticky="we", pady=(4, 0))
        self.l_corpo_regra = tk.Label(c, text="", bg=G("PERG"), fg=G("TINTA2"), font=(G("FONTE"), 9, "italic"), anchor="w", justify="left", wraplength=900)
        self.l_corpo_regra.grid(row=2, column=0, sticky="we", pady=(6, 0))
        bts = ttk.Frame(c)
        bts.grid(row=3, column=0, sticky="w", pady=(8, 0))
        ttk.Button(bts, text="🎲 Golpe forte: sortear o membro", command=self.membro_sortear).pack(side="left")
        self.ed(ttk.Button(bts, text="Corpo padrão (2 · 2 · 2)", command=self.membro_padrao)).pack(side="left", padx=8)
        self.fr_membros = {}
        for n, tipo in enumerate(("olhos", "bracos", "pernas")):
            s = self.secao(p, ROT_TIPO[tipo][0], row=1 + n // 2, column=n % 2)
            s.columnconfigure(0, weight=1)
            fr = ttk.Frame(s)
            fr.grid(row=0, column=0, sticky="we")
            self.fr_membros[tipo] = fr
            b = ttk.Frame(s)
            b.grid(row=1, column=0, sticky="w", pady=(6, 0))
            self.ed(ttk.Button(b, text=f"− {ROT_TIPO[tipo][1]}", command=lambda t=tipo: self.membro_qtd(t, -1))).pack(side="left")
            self.ed(ttk.Button(b, text=f"+ {ROT_TIPO[tipo][1]}", command=lambda t=tipo: self.membro_qtd(t, 1))).pack(side="left", padx=6)
        s = self.secao(p, "Outros membros da espécie", row=2, column=1)
        s.columnconfigure(0, weight=1)
        self.fr_membros["outros"] = ttk.Frame(s)
        self.fr_membros["outros"].grid(row=0, column=0, sticky="we")
        self.ed(ttk.Button(s, text="+ Outro membro", command=self.membro_outro)).grid(row=1, column=0, sticky="w", pady=(6, 0))
        tk.Label(p, text="Espécie com mais ou menos membros: no Modo Edição, use − e +. A penalidade conta quantos sobram: com 2 ou mais, "
                         "nenhuma; com 1, a de \"perdeu 1\"; com nenhum, a de \"perdeu os 2\". Membros que a espécie nunca teve não dão "
                         "penalidade. O braço inclui a mão.", bg=G("PERG"), fg=G("TINTA2"), font=(G("FONTE"), 9, "italic"),
                 justify="left", wraplength=900).grid(row=3, column=0, columnspan=2, sticky="w", padx=12, pady=(8, 12))
        self._sig_corpo = None

    def _pintar_corpo(self):
        if not hasattr(self, "fr_membros"):
            return
        G = self._g
        pm, c = self.pm, R.normalizar_corpo(self.corpo)
        limiar = -(-self.d.get("vida", 0) // 2)
        self.l_corpo_estado.configure(text=("Estado: " + " · ".join(pm["estados"])) if pm["estados"] else "Corpo inteiro: nenhum membro perdido.",
                                      fg=G("ALERTA") if pm["estados"] else G("VERDE"))
        self.l_corpo_notas.configure(text="\n".join(pm["notas"]) + ("\nJá aplicado na ficha: CA, deslocamento, Carga, Reflexo, Atletismo, "
                                                                    "Percepção e o acerto e o dano das armas." if pm["notas"] else ""))
        self.l_corpo_regra.configure(text=f"Um único golpe com dano final igual ou maior que a metade da Vida máxima ({limiar} para você) remove "
                                          "1 membro (role 1d8). Danos mentais (Psíquico, Êxtase, Melódico, Radiante), Veneno, Sangramento, "
                                          "Podridão e Congelamento não removem. A perda é permanente: nenhuma cura recupera um membro.")
        sig = (repr(c), self.modo)
        if sig == self._sig_corpo:
            return
        self._sig_corpo = sig
        for tipo, fr in self.fr_membros.items():
            for w in fr.winfo_children():
                w.destroy()
            lista = c[tipo]
            if not lista:
                tk.Label(fr, text="A espécie não tem." if tipo != "outros" else "Cauda, asas, antenas, chifres… o que a espécie tiver a mais.",
                         bg=G("PERG"), fg=G("TINTA2"), font=(G("FONTE"), 10, "italic")).grid(row=0, column=0, sticky="w")
            for i, m in enumerate(lista):
                cor = G("ALERTA") if m["perdido"] else G("TINTA")
                tk.Label(fr, text=("✗ " if m["perdido"] else "✓ ") + m["nome"], bg=G("PERG"), fg=cor, font=(G("FONTE"), 11, "bold"),
                         width=18, anchor="w").grid(row=i, column=0, sticky="w", pady=1)
                ttk.Button(fr, text="Recuperar" if m["perdido"] else "Perdeu", width=10,
                           command=lambda t=tipo, k=i: self.membro_alternar(t, k)).grid(row=i, column=1, padx=4)
                if tipo == "bracos" and not m["perdido"]:
                    ttk.Button(fr, text=f"{R.nome_mao(m['nome'])}: {'inteira' if m['mao'] else 'perdida'}", width=22,
                               command=lambda k=i: self.membro_mao(k)).grid(row=i, column=2, padx=4)
                if tipo == "outros" and self.modo == "edicao":
                    ttk.Button(fr, text="Remover", width=9, command=lambda k=i: self.membro_tirar(k)).grid(row=i, column=2, padx=4)

    def _mudou_corpo(self):
        self.corpo = R.normalizar_corpo(self.corpo)
        self.agendar()

    def _perder(self, tipo, i, mao=False):
        m = self.corpo[tipo][i]
        nome = R.nome_mao(m["nome"]) if mao else m["nome"]
        if mao:
            m["mao"] = False
        else:
            m["perdido"] = True
            if tipo == "bracos":
                m["mao"] = False
        self.corpo = R.normalizar_corpo(self.corpo)
        self.recalc()
        est = self.pm["estados"]
        self.registrar(f"✂ Membro perdido: {nome}", [f"Agora: {', '.join(est)}." if est else "Sem penalidade (a espécie tem membros de sobra)."], destaque=True)
        self.agendar()

    def membro_alternar(self, tipo, i):
        m = self.corpo[tipo][i]
        if m["perdido"]:
            if messagebox.askyesno("Recuperar membro", f"A perda de um membro é permanente: nenhuma cura recupera {m['nome']}.\n\n"
                                                       "Desmarcar só para corrigir um erro (ou se o Mestre permitir uma prótese)?"):
                m["perdido"] = False
                if tipo == "bracos":
                    m["mao"] = True
                self._mudou_corpo()
        elif messagebox.askyesno("Perda de membro", f"Perdeu {m['nome']}?" + (" O braço inclui a mão." if tipo == "bracos" else "")
                                 + "\n\nA perda é permanente e entra no Diário."):
            self._perder(tipo, i)

    def membro_mao(self, i):
        m = self.corpo["bracos"][i]
        if m["mao"]:
            if messagebox.askyesno("Perda de membro", f"Perdeu {R.nome_mao(m['nome'])}? (só a mão; o braço continua)"):
                self._perder("bracos", i, mao=True)
        else:
            m["mao"] = True
            self._mudou_corpo()

    def membro_qtd(self, tipo, d):
        if self._so_edicao("A quantidade de membros"):
            return
        lista = self.corpo[tipo]
        if d > 0 and len(lista) < 12:
            lista.append(dict({"nome": R.nome_membro(tipo, len(lista)), "perdido": False}, **({"mao": True} if tipo == "bracos" else {})))
        elif d < 0 and lista:
            lista.pop()
        self._mudou_corpo()

    def membro_outro(self):
        if self._so_edicao("Os membros da espécie"):
            return
        n = simpledialog.askstring("Outro membro", "Nome do membro (ex.: Cauda, Asa esquerda, Antena):", parent=self)
        if n and n.strip():
            self.corpo["outros"].append({"nome": n.strip(), "perdido": False})
            self._mudou_corpo()

    def membro_tirar(self, i):
        if self._so_edicao("Os membros da espécie"):
            return
        del self.corpo["outros"][i]
        self._mudou_corpo()

    def membro_padrao(self):
        if self._so_edicao("O corpo"):
            return
        if messagebox.askyesno("Corpo padrão", "Voltar a 2 olhos, 2 braços e 2 pernas, todos inteiros, e apagar os outros membros?"):
            self.corpo = R.corpo_padrao()
            self._mudou_corpo()

    def membro_sortear(self):
        G = self._g
        lista = R.membros_para_sortear(self.corpo)
        if not lista:
            messagebox.showinfo("Golpe forte", "Não sobrou membro para perder.")
            return
        n = len(lista)
        fis = self.fisico()
        sorteado = -1 if fis else random.randint(1, n) - 1
        w, f = self._janela(f"Qual membro (1d{n})")
        self._tit(f, f"Qual membro (1d{n})")
        self._txt(f, f"Role 1d{n} e clique no resultado." if fis else f"Resultado: {sorteado + 1} → {lista[sorteado][3]}", pady=(0, 6))
        for k, (t, i, mao, nome) in enumerate(lista):
            ttk.Button(f, text=f"{k + 1}.  {nome}" + ("   ◀" if k == sorteado else ""),
                       command=lambda t=t, i=i, mao=mao: (w.destroy(), self._perder(t, i, mao=bool(mao)))).pack(fill="x", pady=1)
        self._txt(f, "Clique no membro para confirmar a perda. Se o golpe deixa óbvio qual foi atingido, o Mestre pode escolher.", sub=True, pady=(6, 0))
        bf = tk.Frame(f, bg=G("PERG"))
        bf.pack(anchor="e", pady=(8, 0))
        if not fis:
            ttk.Button(bf, text="Rolar de novo", command=lambda: (w.destroy(), self.membro_sortear())).pack(side="left", padx=6)
        ttk.Button(bf, text="Cancelar", command=w.destroy).pack(side="left")

    # ============================================================ Crença e Culto
    def _pag_crenca(self):
        G = self._g
        L = self.dados.get("cultos") or {}
        p = self._pagina("Crença")
        p.columnconfigure(0, weight=1)
        p.columnconfigure(1, weight=1)
        self.cu_vars = {}
        c = self.secao(p, "Crença", row=0, column=0, columnspan=2)
        c.columnconfigure(1, weight=1)
        self.cu_papel = tk.StringVar(value="")
        rf = ttk.Frame(c)
        rf.grid(row=0, column=0, columnspan=2, sticky="w")
        for k, r in PAPEIS:
            ttk.Radiobutton(rf, text=r, value=k, variable=self.cu_papel).pack(side="left", padx=(0, 14))
        self.cu_papel.trace_add("write", lambda *a: self._culto_set("papel", self.cu_papel.get()))
        self._cu_campo(c, "crenca", "No que acredita", 1)
        self.l_cu_intro = tk.Label(c, text="", bg=G("PERG"), fg=G("TINTA2"), font=(G("FONTE"), 9, "italic"), justify="left", wraplength=900, anchor="w")
        self.l_cu_intro.grid(row=2, column=0, columnspan=2, sticky="we", pady=(6, 0))
        # o Culto
        self.fr_cu_culto = self.secao(p, "O Culto", row=1, column=0)
        cc = self.fr_cu_culto
        cc.columnconfigure(1, weight=1)
        self._cu_campo(cc, "nome", "Nome", 0)
        self._cu_campo(cc, "divindade", "Divindade", 1)
        self._cu_campo(cc, "profeta", "Profeta", 2)
        ttk.Label(cc, text="Tema", style="Rot.TLabel").grid(row=3, column=0, sticky="w", pady=2)
        self.cu_tema = tk.StringVar()
        cb = ttk.Combobox(cc, values=[""] + list((L.get("temas") or {}).keys()), textvariable=self.cu_tema, state="readonly", width=16)
        cb.grid(row=3, column=1, sticky="w", pady=2)
        self.cu_tema.trace_add("write", lambda *a: self._culto_set("tema", self.cu_tema.get()))
        self._cu_campo(cc, "regra_faz", "Os seguidores devem", 4)
        self._cu_campo(cc, "regra_nunca", "Os seguidores nunca podem", 5)
        self.cu_abalado = tk.BooleanVar()
        self.ck_cu_abalado = ttk.Checkbutton(cc, text="Abalado (quebrou uma regra: sem os poderes até se redimir diante dos seguidores)",
                                             variable=self.cu_abalado)
        self.ck_cu_abalado.grid(row=6, column=0, columnspan=2, sticky="w", pady=(6, 0))
        self.cu_abalado.trace_add("write", lambda *a: self._culto_set("abalado", self.cu_abalado.get()))
        self.l_cu_fe = tk.Label(cc, text="", bg=G("PERG"), fg=G("ALERTA"), font=(G("FONTE"), 10), anchor="w")
        self.l_cu_fe.grid(row=7, column=0, columnspan=2, sticky="w")
        # Grau
        self.fr_cu_grau = self.secao(p, "Grau do Culto", row=1, column=1)
        self.cu_grau = tk.IntVar(value=1)
        for g in (L.get("graus") or []):
            ttk.Radiobutton(self.fr_cu_grau, text=f"Grau {g['grau']} · {g['tamanho']}", value=g["grau"], variable=self.cu_grau).grid(
                row=2 * g["grau"], column=0, sticky="w")
            tk.Label(self.fr_cu_grau, text=f"{g['objetivo']} → {g['poderes']}", bg=G("PERG"), fg=G("TINTA2"), font=(G("FONTE"), 9),
                     justify="left", wraplength=420, anchor="w").grid(row=2 * g["grau"] + 1, column=0, sticky="w", padx=(22, 0))
        self.cu_grau.trace_add("write", lambda *a: self._culto_set("grau", self.cu_grau.get()))
        # Poderes
        self.fr_cu_pod = self.secao(p, "Poderes do Tema", row=2, column=0)
        self.fr_cu_pod.columnconfigure(0, weight=1)
        self.l_cu_pod = {}
        for r, k in enumerate(("bencao", "prece", "milagre")):
            self.l_cu_pod[k] = tk.Label(self.fr_cu_pod, text="", bg=G("PERG"), fg=G("TINTA"), font=(G("FONTE"), 10), justify="left",
                                        wraplength=440, anchor="w")
            self.l_cu_pod[k].grid(row=r, column=0, sticky="we", pady=2)
        bp = ttk.Frame(self.fr_cu_pod)
        bp.grid(row=3, column=0, sticky="w", pady=(6, 0))
        self.bt_cu_prece = ttk.Button(bp, text="🙏 Usar Prece", command=lambda: self.culto_usar("preces"))
        self.bt_cu_prece.pack(side="left")
        self.bt_cu_milagre = ttk.Button(bp, text="✨ Usar Milagre", command=lambda: self.culto_usar("milagres"))
        self.bt_cu_milagre.pack(side="left", padx=6)
        ttk.Button(bp, text="↺ Devolver usos", command=self.culto_recup).pack(side="left")
        tk.Label(self.fr_cu_pod, text=L.get("poderes_nota", "") + " A Prece volta sozinha no descanso longo.", bg=G("PERG"), fg=G("TINTA2"),
                 font=(G("FONTE"), 9, "italic"), justify="left", wraplength=440, anchor="w").grid(row=4, column=0, sticky="we", pady=(6, 0))
        # Seguidores e Igreja
        self.fr_cu_seg = self.secao(p, "Seguidores e Igreja", row=2, column=1)
        sg = self.fr_cu_seg
        sg.columnconfigure(1, weight=1)
        self._cu_campo(sg, "comunidades", "Comunidades convertidas", 0)
        self._cu_campo(sg, "local", "Local sagrado", 1)
        self.l_cu_disc = ttk.Label(sg, text="Discípulos", style="Rot.TLabel")
        self._cu_campo(sg, "discipulos", "Discípulos", 2, rotulo=self.l_cu_disc)
        ttk.Label(sg, text="Igreja", style="Rot.TLabel").grid(row=3, column=0, sticky="w", pady=2)
        self.cu_igreja = tk.StringVar()
        ttk.Combobox(sg, values=[""] + list(R.IGREJAS), textvariable=self.cu_igreja, state="readonly", width=12).grid(row=3, column=1, sticky="w")
        self.cu_igreja.trace_add("write", lambda *a: self._culto_set("igreja", self.cu_igreja.get()))
        self.cu_na_igreja = tk.BooleanVar()
        ttk.Checkbutton(sg, text="O Culto ocupa uma vaga da Igreja (Grau 2+, cerimônia com 1 Discípulo)", variable=self.cu_na_igreja).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(4, 0))
        self.cu_na_igreja.trace_add("write", lambda *a: self._culto_set("na_igreja", self.cu_na_igreja.get()))
        self.l_cu_igreja = tk.Label(sg, text="", bg=G("PERG"), fg=G("TINTA"), font=(G("FONTE"), 10), justify="left", wraplength=440, anchor="w")
        self.l_cu_igreja.grid(row=5, column=0, columnspan=2, sticky="we", pady=(4, 0))
        tk.Label(sg, text=L.get("conversao", ""), bg=G("PERG"), fg=G("TINTA2"), font=(G("FONTE"), 9, "italic"), justify="left",
                 wraplength=440, anchor="w").grid(row=6, column=0, columnspan=2, sticky="we", pady=(6, 0))
        self.fr_cu_notas = self.secao(p, "Anotações do Culto", row=3, column=0, columnspan=2)
        self.fr_cu_notas.columnconfigure(1, weight=1)
        self._cu_campo(self.fr_cu_notas, "notas", "Anotações", 0)
        self.ed(ttk.Button(self.fr_cu_notas, text="Subiu de Andar", command=self.culto_andar)).grid(row=1, column=0, sticky="w", pady=(6, 0))
        self._culto_para_ui()

    def _cu_campo(self, master, k, rot, row, rotulo=None):
        (rotulo or ttk.Label(master, text=rot, style="Rot.TLabel")).grid(row=row, column=0, sticky="w", pady=2, padx=(0, 8))
        v = tk.StringVar()
        ttk.Entry(master, textvariable=v, font=(self._g("FONTE"), 11)).grid(row=row, column=1, sticky="we", pady=2)
        v.trace_add("write", lambda *a, k=k, v=v: self._culto_set(k, v.get()))
        self.cu_vars[k] = v

    def _culto_set(self, k, valor):
        if getattr(self, "_cu_carregando", False) or self.culto.get(k) == valor:
            return
        if k == "na_igreja" and valor and self.culto["grau"] < 2:
            messagebox.showinfo("Igreja", "Para entrar na Igreja, o Culto precisa estar no Grau 2 ou mais.")
            self.cu_na_igreja.set(False)
            return
        self.culto[k] = valor
        self.culto = normalizar(self.culto)
        if k == "abalado":
            self.registrar("⚠ Culto Abalado" if valor else "✦ Culto restaurado",
                           ["O Profeta quebrou uma regra do Culto e perdeu os poderes." if valor else "O Profeta se redimiu diante dos seguidores."])
        self.agendar()

    def _culto_para_ui(self):
        """Copia self.culto para os controles (ao abrir uma ficha)."""
        if not hasattr(self, "cu_vars"):
            return
        self._cu_carregando = True
        try:
            c = self.culto
            for k, v in self.cu_vars.items():
                v.set(c.get(k, ""))
            self.cu_papel.set(c["papel"])
            self.cu_tema.set(c["tema"])
            self.cu_grau.set(c["grau"])
            self.cu_abalado.set(c["abalado"])
            self.cu_igreja.set(c["igreja"])
            self.cu_na_igreja.set(c["na_igreja"])
        finally:
            self._cu_carregando = False

    def _pintar_crenca(self):
        if not hasattr(self, "cu_vars"):
            return
        G = self._g
        L = self.dados.get("cultos") or {}
        c = self.culto
        papel, prof = c["papel"], c["papel"] == "profeta"
        fe = self.a.get("FE", 0)
        self.l_cu_intro.configure(text=("Cada povo, tribo e cidade criou suas próprias crenças. " + L.get("resumo", "")) if not papel else
                                  "Fiel: a Bênção do Tema vale perto do Profeta (ou até o próximo descanso longo, se descansou na Igreja do Culto)."
                                  if papel == "fiel" else "")
        for fr in (self.fr_cu_culto, self.fr_cu_grau, self.fr_cu_pod, self.fr_cu_notas):
            (fr.master.grid if papel else fr.master.grid_remove)()
        (self.fr_cu_seg.master.grid if prof else self.fr_cu_seg.master.grid_remove)()
        if prof:
            self.ck_cu_abalado.grid()
        else:
            self.ck_cu_abalado.grid_remove()
        self.l_cu_fe.configure(text=f"✗ Fundar um Culto exige {R.CULTO_FE_MIN} de Fé (você tem {fe})." if prof and fe < R.CULTO_FE_MIN else "")
        pod, ig = poderes(c)
        tema = (L.get("temas") or {}).get(c["tema"])
        ativo = not (prof and c["abalado"])
        if not tema:
            for lab in self.l_cu_pod.values():
                lab.configure(text="")
            self.l_cu_pod["bencao"].configure(text="Escolha o Tema para ver os poderes.")
        else:
            def linha(lab, nome, liberado, texto, req):
                lab.configure(text=f"{nome}{'' if liberado else f'  (a partir do {req})'}\n{texto}",
                              fg=G("TINTA") if liberado and ativo else G("TINTA2"))
            linha(self.l_cu_pod["bencao"], f"Bênção · sempre ativa, aliados a até {pod['bencao_alcance']} m", pod["bencao"], tema["bencao"], "Grau 2")
            linha(self.l_cu_pod["prece"], f"Prece · {max(0, pod['preces'] - c['preces_usadas'])}/{pod['preces']} por descanso longo" if pod["preces"]
                  else "Prece", pod["preces"] > 0, tema["prece"].replace("× o Grau", f"× o Grau ({5 * c['grau']})"), "Grau 3")
            linha(self.l_cu_pod["milagre"], f"Milagre · {max(0, pod['milagres'] - c['milagres_usados'])}/{pod['milagres']} neste Andar · "
                  f"DT {R.dt_milagre(self.a, self.nivel())}" if pod["milagres"] else "Milagre", pod["milagres"] > 0, tema["milagre"], "Grau 5")
        pode = prof and ativo and tema
        self.bt_cu_prece.state(["!disabled"] if pode and c["preces_usadas"] < pod["preces"] else ["disabled"])
        self.bt_cu_milagre.state(["!disabled"] if pode and c["milagres_usados"] < pod["milagres"] else ["disabled"])
        self.l_cu_disc.configure(text=f"Discípulos (até {pod['discipulos']})")
        info = next((x for x in L.get("igrejas") or [] if x["nome"] == c["igreja"]), None)
        txt = ""
        if info:
            txt = f"Base nível {info['base']} · {info['vagas']} vaga(s) para Cultos.\n"
            txt += "\n".join(("✓ " if ig and c["grau"] >= b["grau"] else "· ") + f"Grau {b['grau']} · {b['nome']}: {b['texto']}"
                             for b in L.get("igreja_beneficios") or [])
        self.l_cu_igreja.configure(text=(txt + "\n" if txt else "") + L.get("igreja_nota", ""))

    def culto_usar(self, k):
        c, L = self.culto, self.dados.get("cultos") or {}
        pod, _ = poderes(c)
        tema = (L.get("temas") or {}).get(c["tema"]) or {}
        mx, campo = (pod["preces"], "preces_usadas") if k == "preces" else (pod["milagres"], "milagres_usados")
        if c["abalado"]:
            messagebox.showinfo("Culto", "Culto Abalado: sem poderes até se redimir.")
            return
        if c[campo] >= mx:
            messagebox.showinfo("Culto", "Sem Preces até o próximo descanso longo." if k == "preces" else "Sem Milagres neste Andar.")
            return
        c[campo] += 1
        nome = "🙏 Prece" if k == "preces" else "✨ Milagre"
        self.registrar(f"{nome} · {c['tema']}", [tema.get("prece" if k == "preces" else "milagre", ""),
                                                 f"{mx - c[campo]}/{mx} restante(s)" + (f" neste Andar · DT {R.dt_milagre(self.a, self.nivel())} se pedir teste."
                                                                                       if k == "milagres" else " até o descanso longo.")])
        self.agendar()

    def culto_recup(self):
        self.culto["preces_usadas"] = self.culto["milagres_usados"] = 0
        self.agendar()

    def culto_andar(self):
        if self._so_edicao("O Culto"):
            return
        L = self.dados.get("cultos") or {}
        if not messagebox.askyesno("Subiu de Andar", L.get("andar", "") + "\n\nRecomeçar o Culto no Grau 1?"):
            return
        self.culto.update(grau=1, local="", discipulos="", comunidades="", igreja="", na_igreja=False, preces_usadas=0, milagres_usados=0)
        self._culto_para_ui()
        self.registrar("✦ Culto no Andar novo", ["O Culto recomeça no Grau 1; Tema e regras continuam."])
        self.agendar()
