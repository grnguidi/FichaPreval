# -*- coding: utf-8 -*-
"""Assistente passo a passo de criação de personagem (capítulo "Criando seu Personagem")."""
import tkinter as tk
from tkinter import ttk, messagebox

import regras as R

PASSOS = [
    ("Seu Sonho", "Antes de qualquer número, decida por que este personagem busca a Intérprete. O Sonho é o motor "
                  "de tudo: define as escolhas, dá sentido às Metas de Vida e determina o que o personagem está "
                  "disposto a sacrificar."),
    ("A Alma", "Quando um ser vivo perece, sua essência se transforma em uma Alma, que vaga pelo mundo em busca de "
               "um propósito. Escolha a Alma que seu personagem carrega: ela define seus poderes iniciais e boa parte "
               "da sua identidade. Se preferir, é possível começar sem Alma alguma, e então o corpo e a mente crescem "
               "mais fortes: +2 pontos de atributo a cada nível."),
    ("A Espécie", "Crie ou escolha a espécie do personagem: duas vantagens e duas desvantagens, um par numérico e um "
                  "par descritivo. O par numérico é um bônus em um atributo e um prejuízo de mesmo valor (1 a 5) em outro."),
    ("Atributos", "Distribua os valores iniciais (16, 14, 12, 11, 10, 9, 8 e 7) entre os atributos, pensando no que o "
                  "personagem faz, não no que ele é. Um conjurador precisa de Inteligência para aprender e Mente para "
                  "conjurar; um guerreiro precisa de Força e Tenacidade para o Vigor, e Destreza para as ações."),
    ("Perícias e equipamento", "Você começa treinado em 1 perícia de ataque e 5 fora de combate, mais uma a cada 10 pontos "
                               "em Inteligência ou Mente. Escolha sua arma inicial respeitando os requisitos do nível 1. "
                               "Quem começa com cajado ou selo recebe três encantamentos iniciais."),
    ("Talentos", "Talentos são habilidades que o personagem adquire a cada nível par. Ficam ativos o tempo todo e não "
                 "podem ser trocados depois de obtidos."),
    ("Vínculos", "Antes da primeira sessão, defina uma ligação com outro personagem do grupo e uma pessoa no mundo que "
                 "importa para você. Vínculos sobem os Andares junto com o aventureiro e dão ao mestre os ganchos de que ele precisa."),
    ("Resumo", "Confira tudo antes de criar a ficha. Você pode voltar a qualquer passo."),
]


class Assistente(tk.Toplevel):
    def __init__(self, app, cores):
        super().__init__(app)
        self.app, self.c = app, cores
        c = cores
        self.title("Novo personagem — passo a passo")
        self.configure(background=c["FUNDO"])
        self.geometry("980x680")
        self.minsize(900, 600)
        self.transient(app)
        self.passo = 0
        self.feitos = set()
        self._texto_ativo = None
        self._lista_enc = []
        sv, bv = tk.StringVar, tk.BooleanVar
        self.v = {
            "nome": sv(), "player": sv(), "sonho": sv(),
            "sem_alma": bv(value=False), "alma_nome": sv(), "alma_atr": sv(value="INT"),
            "alma_hist": "", "pas_nome": sv(), "pas_ef": sv(), "atv_nome": sv(), "atv_ef": sv(),
            "especie": sv(), "esp_bon": sv(), "esp_pre": sv(), "esp_val": sv(value="0"), "esp_notas": "",
            "ini": {k: sv() for k in R.ATRIBUTOS},
            "per": {n: bv(value=False) for n, _, _ in R.PERICIAS}, "per_atk": sv(value="Luta"), "prev_attr": sv(value="ARC"),
            "arma": sv(), "arma_disp": sv(), "encs": [],
            "vinc_grupo": sv(), "vinc_mundo": sv(), "metas": sv(),
        }
        self._montar()
        self._mostrar()
        self.grab_set()
        self.focus_set()

    # ------------------------------------------------------------ estrutura
    def _montar(self):
        c = self.c
        lado = tk.Frame(self, bg=c["FUNDO"], width=230, padx=18, pady=20)
        lado.pack(side="left", fill="y")
        lado.pack_propagate(False)
        tk.Label(lado, text="⚜ Criando seu\nPersonagem", bg=c["FUNDO"], fg=c["OURO2"], font=(c["FONTE_TIT"], 15, "bold"),
                 justify="left").pack(anchor="w", pady=(0, 18))
        self.rot_passos = []
        for i, (t, _) in enumerate(PASSOS):
            lab = tk.Label(lado, text="", bg=c["FUNDO"], anchor="w", font=(c["FONTE"], 11), cursor="hand2")
            lab.pack(fill="x", pady=4)
            lab.bind("<Button-1>", lambda e, i=i: self._ir(i))
            self.rot_passos.append(lab)

        dir_ = tk.Frame(self, bg=c["PERG"])
        dir_.pack(side="left", fill="both", expand=True)
        cab = tk.Frame(dir_, bg=c["PERG"], padx=28, pady=18)
        cab.pack(fill="x")
        self.l_num = tk.Label(cab, bg=c["PERG"], fg=c["TINTA2"], font=(c["FONTE"], 10, "italic"))
        self.l_num.pack(anchor="w")
        self.l_tit = tk.Label(cab, bg=c["PERG"], fg=c["VINHO"], font=(c["FONTE_TIT"], 20, "bold"))
        self.l_tit.pack(anchor="w")
        self.l_txt = tk.Label(cab, bg=c["PERG"], fg=c["TINTA2"], font=(c["FONTE"], 10, "italic"), wraplength=660, justify="left")
        self.l_txt.pack(anchor="w", pady=(6, 0))
        tk.Frame(dir_, height=1, bg=c["OURO"]).pack(fill="x", padx=28)
        self.corpo = tk.Frame(dir_, bg=c["PERG"], padx=28, pady=16)
        self.corpo.pack(fill="both", expand=True)
        rod = tk.Frame(dir_, bg=c["PERG"], padx=28, pady=14)
        rod.pack(fill="x", side="bottom")
        self.l_erro = tk.Label(rod, bg=c["PERG"], fg=c["VINHO"], font=(c["FONTE"], 10, "bold"), wraplength=420, justify="left")
        self.l_erro.pack(side="left")
        self.b_prox = ttk.Button(rod, text="Próximo →", command=self._proximo)
        self.b_prox.pack(side="right")
        self.b_volta = ttk.Button(rod, text="← Voltar", command=lambda: self._ir(self.passo - 1))
        self.b_volta.pack(side="right", padx=8)
        ttk.Button(rod, text="Cancelar", command=self._cancelar, style="Peq.TButton").pack(side="right", padx=(0, 18))

    def _cancelar(self):
        if messagebox.askyesno("Novo personagem", "Cancelar a criação? Nada será salvo.", parent=self):
            self.destroy()

    def _ir(self, i):
        if i < 0 or i >= len(PASSOS) or i == self.passo:
            return
        if i > self.passo:
            for j in range(self.passo, i):  # não pula passos com erro
                erro = self._validar(j)
                if erro:
                    self.passo = j
                    self._mostrar()
                    self.l_erro.configure(text=erro)
                    return
                self.feitos.add(j)
        self._guardar_textos()
        self.passo = i
        self._mostrar()

    def _proximo(self):
        erro = self._validar(self.passo)
        if erro:
            self.l_erro.configure(text=erro)
            return
        self.feitos.add(self.passo)
        if self.passo == len(PASSOS) - 1:
            self._concluir()
        else:
            self._ir(self.passo + 1)

    def _mostrar(self):
        c = self.c
        for i, lab in enumerate(self.rot_passos):
            atual = i == self.passo
            marca = "▸" if atual else ("✓" if i in self.feitos else "·")
            pre = f"{i + 1}." if i < len(PASSOS) - 1 else "★"
            lab.configure(text=f"{marca}  {pre} {PASSOS[i][0]}", fg=c["OURO2"] if atual else (c["MESA_TXT"] if i in self.feitos else "#7f8d80"),
                          font=(c["FONTE"], 11, "bold" if atual else "normal"))
        t, txt = PASSOS[self.passo]
        self.l_num.configure(text=f"Passo {self.passo + 1} de {len(PASSOS) - 1}" if self.passo < len(PASSOS) - 1 else "Último passo")
        self.l_tit.configure(text=t)
        self.l_txt.configure(text=txt)
        self.l_erro.configure(text="")
        for w in self.corpo.winfo_children():
            w.destroy()
        [self._p_sonho, self._p_alma, self._p_especie, self._p_atributos, self._p_pericias,
         self._p_talentos, self._p_vinculos, self._p_resumo][self.passo]()
        self.b_volta.state(["disabled"] if self.passo == 0 else ["!disabled"])
        self.b_prox.configure(text="⚜  Criar e salvar ficha" if self.passo == len(PASSOS) - 1 else "Próximo →")

    # ------------------------------------------------------------ helpers de tela
    def _rot(self, master, txt, r, col=0, **kw):
        tk.Label(master, text=txt, bg=self.c["PERG"], fg=self.c["TINTA"], font=(self.c["FONTE"], 11), anchor="w").grid(
            row=r, column=col, sticky="w", pady=4, padx=(0, 10), **kw)

    def _dica(self, master, txt, r, cols=4):
        tk.Label(master, text=txt, bg=self.c["PERG"], fg=self.c["TINTA2"], font=(self.c["FONTE"], 9, "italic"),
                 wraplength=640, justify="left").grid(row=r, column=0, columnspan=cols, sticky="w", pady=(2, 8))

    def _texto(self, master, chave, r, h=4):
        t = tk.Text(master, height=h, width=70, wrap="word")
        t.insert("1.0", self.v[chave])
        t.grid(row=r, column=0, columnspan=4, sticky="we", pady=4)
        self._texto_ativo = (chave, t)

    def _guardar_textos(self):
        ta = self._texto_ativo
        if ta:
            chave, t = ta
            try:
                self.v[chave] = t.get("1.0", "end-1c")
            except tk.TclError:
                pass
            self._texto_ativo = None

    def atributos(self):
        a = {}
        val = R.ATR_POR_NOME
        bon, pre = val.get(self.v["esp_bon"].get()), val.get(self.v["esp_pre"].get())
        n = max(0, min(5, _int(self.v["esp_val"].get())))
        for k in R.ATRIBUTOS:
            a[k] = _int(self.v["ini"][k].get()) + (n if k == bon else -n if k == pre else 0)
        return a

    def max_pericias(self):
        a = self.atributos()
        return 5 + max(R.cap(a["INT"]), R.cap(a["MEN"])) // 10

    # ------------------------------------------------------------ passos
    def _p_sonho(self):
        f = self.corpo
        self._rot(f, "Nome do personagem", 0)
        ttk.Entry(f, textvariable=self.v["nome"], width=40).grid(row=0, column=1, sticky="w")
        self._rot(f, "Player", 1)
        ttk.Entry(f, textvariable=self.v["player"], width=30).grid(row=1, column=1, sticky="w")
        self._rot(f, "Sonho", 2)
        ttk.Entry(f, textvariable=self.v["sonho"], width=60).grid(row=2, column=1, sticky="w")
        self._dica(f, "Ex.: \"Encontrar a Intérprete para trazer meu irmão de volta\", \"Provar que minha espécie não é amaldiçoada\".", 3)

    def _p_alma(self):
        c, f = self.c, self.corpo
        sel = tk.Frame(f, bg=c["PERG"])
        sel.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 12))
        for txt, val in (("✧  Com alma", False), ("☠  Sem alma", True)):
            ttk.Radiobutton(sel, text=txt, value=val, variable=self.v["sem_alma"],
                            command=lambda: (self._guardar_textos(), self._mostrar())).pack(side="left", padx=(0, 18))
        if self.v["sem_alma"].get():
            self._dica(f, "Sem alma: a ficha não terá a aba Alma e você recebe 12 pontos por nível em vez de 10 "
                          "(continua ganhando +5 nos níveis múltiplos de 3).", 1)
            return
        self._rot(f, "Nome da Alma", 1)
        ttk.Entry(f, textvariable=self.v["alma_nome"], width=36).grid(row=1, column=1, sticky="w")
        self._rot(f, "DT da Alma usa", 1, col=2)
        ttk.Combobox(f, values=["INT", "FE"], textvariable=self.v["alma_atr"], width=5, state="readonly").grid(row=1, column=3, sticky="w")
        self._rot(f, "Quem foi, por que está com você, que habilidade tinha em vida:", 2, columnspan=4)
        self._texto(f, "alma_hist", 3, h=4)
        self._rot(f, "Habilidade passiva", 4)
        ttk.Entry(f, textvariable=self.v["pas_nome"], width=24).grid(row=4, column=1, sticky="w")
        ttk.Entry(f, textvariable=self.v["pas_ef"], width=40).grid(row=4, column=2, columnspan=2, sticky="we")
        self._rot(f, "Habilidade ativa", 5)
        ttk.Entry(f, textvariable=self.v["atv_nome"], width=24).grid(row=5, column=1, sticky="w")
        ttk.Entry(f, textvariable=self.v["atv_ef"], width=40).grid(row=5, column=2, columnspan=2, sticky="we")
        self._dica(f, "Combine com o mestre os poderes da Alma (capítulo Almas). Ela começa com 1 habilidade passiva e 1 ativa; "
                      "novas ativas surgem nos níveis 10, 20 e 30.", 6)

    def _p_especie(self):
        f = self.corpo
        nomes = [""] + [R.NOMES_ATR[k] for k in R.ATRIBUTOS]
        self._rot(f, "Espécie", 0)
        ttk.Entry(f, textvariable=self.v["especie"], width=30).grid(row=0, column=1, columnspan=3, sticky="w")
        self._rot(f, "Bônus em", 1)
        ttk.Combobox(f, values=nomes, textvariable=self.v["esp_bon"], width=14, state="readonly").grid(row=1, column=1, sticky="w")
        self._rot(f, "Valor (1 a 5)", 1, col=2)
        ttk.Spinbox(f, from_=0, to=5, textvariable=self.v["esp_val"], width=4).grid(row=1, column=3, sticky="w")
        self._rot(f, "Prejuízo em", 2)
        ttk.Combobox(f, values=nomes, textvariable=self.v["esp_pre"], width=14, state="readonly").grid(row=2, column=1, sticky="w")
        self._dica(f, "Deixe o valor em 0 se a espécie não tiver par numérico.", 3)
        self._rot(f, "Vantagens e desvantagens descritivas (anotações):", 4, columnspan=4)
        self._texto(f, "esp_notas", 5, h=4)

    def _p_atributos(self):
        c, f = self.c, self.corpo
        vars_ini = self.v["ini"]

        def livres(k):
            usados = {v.get() for kk, v in vars_ini.items() if kk != k and v.get()}
            return [""] + [str(x) for x in R.VALORES_INICIAIS if str(x) not in usados]

        grade = tk.Frame(f, bg=c["PERG"])
        grade.grid(row=0, column=0, sticky="nw")
        for i, k in enumerate(R.ATRIBUTOS):
            r, col = i % 4, (i // 4) * 2
            self._rot(grade, R.NOMES_ATR[k], r, col=col)
            cb = ttk.Combobox(grade, textvariable=vars_ini[k], width=5, state="readonly")
            cb.configure(postcommand=lambda cb=cb, k=k: cb.configure(values=livres(k)))
            cb.grid(row=r, column=col + 1, sticky="w", padx=(0, 30))
        ttk.Button(grade, text="Limpar", style="Peq.TButton",
                   command=lambda: [v.set("") for v in vars_ini.values()]).grid(row=4, column=0, sticky="w", pady=(8, 0))

        prev = tk.Frame(f, bg=c["CAMPO"], highlightbackground=c["OURO"], highlightthickness=1, padx=14, pady=10)
        prev.grid(row=0, column=1, sticky="ne", padx=(30, 0))
        tk.Label(prev, text="PRÉVIA (com a espécie)", bg=c["CAMPO"], fg=c["VINHO"], font=(c["FONTE"], 9, "bold")).pack(anchor="w")
        self.l_prev = tk.Label(prev, bg=c["CAMPO"], fg=c["TINTA"], font=(c["FONTE"], 10), justify="left")
        self.l_prev.pack(anchor="w", pady=(6, 0))

        def atualizar(*_):
            try:
                a = self.atributos()
                d = R.derivadas(a, 1, set(), 7 * R.curva(a["VIT"]))
                linhas = [f"{R.NOMES_ATR[k]:<13} {a[k]:>3}" for k in R.ATRIBUTOS]
                linhas += ["", f"Vida {d['vida']}   Mana {d['mana']}   Vigor {d['vigor']}",
                           f"CA {d['ca']}   Carga {d['carga']}   Mov. {d['movimento']} m",
                           f"Perícias treinadas: {5 + max(R.cap(a['INT']), R.cap(a['MEN'])) // 10}",
                           f"Espaços de encantamento: {d['espacos_encant']}"]
                self.l_prev.configure(text="\n".join(linhas))
            except tk.TclError:
                pass
        for v in vars_ini.values():
            v.trace_add("write", atualizar)
        atualizar()
        self._dica(f, "Cada valor só pode ser usado uma vez. A prévia já soma o par numérico da espécie.", 1, cols=2)

    def _p_pericias(self):
        c, f = self.c, self.corpo
        a = self.atributos()
        mx = self.max_pericias()
        topo = tk.Frame(f, bg=c["PERG"])
        topo.grid(row=0, column=0, columnspan=2, sticky="w")
        tk.Label(topo, text="Perícia de ataque treinada:", bg=c["PERG"], fg=c["TINTA"], font=(c["FONTE"], 11)).pack(side="left")
        for n, _ in R.PERICIAS_ATAQUE:
            ttk.Radiobutton(topo, text=n, value=n, variable=self.v["per_atk"]).pack(side="left", padx=6)

        pf = tk.Frame(f, bg=c["PERG"])
        pf.grid(row=1, column=0, sticky="nw", pady=(10, 0))
        self.l_cont_per = tk.Label(pf, bg=c["PERG"], fg=c["VINHO"], font=(c["FONTE"], 10, "bold"))
        self.l_cont_per.grid(row=0, column=0, columnspan=3, sticky="w")

        def contar(*_):
            n = sum(v.get() for v in self.v["per"].values())
            try:
                self.l_cont_per.configure(text=f"Fora de combate: {n} de {mx}", fg=self.c["VINHO"] if n != mx else self.c["VERDE"])
            except tk.TclError:
                pass
        metade = (len(R.PERICIAS) + 1) // 2
        for i, (n, atrs, req) in enumerate(R.PERICIAS):
            r, col = (i % metade) + 1, i // metade
            ttk.Checkbutton(pf, text=n + (" •" if req else ""), variable=self.v["per"][n], command=contar).grid(row=r, column=col, sticky="w", padx=(0, 14))
        contar()

        eq = tk.Frame(f, bg=c["PERG"])
        eq.grid(row=1, column=1, sticky="nw", padx=(30, 0), pady=(10, 0))
        tk.Label(eq, text="Arma inicial (nível 1)", bg=c["PERG"], fg=c["VINHO"], font=(c["FONTE"], 10, "bold")).grid(row=0, column=0, sticky="w")
        cb = ttk.Combobox(eq, textvariable=self.v["arma_disp"], width=46, state="readonly")
        vals = ["— nenhuma —"]
        oks, bloq = [], []
        for arma in self.app.dados["armas"]:
            m = R.req_falta(R.req_arma(arma, 1), a)
            (bloq if m else oks).append(f"✗ {arma['nome']}  — falta: {', '.join(m)}" if m else f"✓ {arma['nome']}")
        cb.configure(values=vals + oks + bloq)
        cb.grid(row=1, column=0, sticky="w", pady=4)

        def escolher_arma(e=None):
            t = self.v["arma_disp"].get()
            if t.startswith("✗"):
                messagebox.showinfo("Arma inicial", "Seus atributos ainda não cumprem os requisitos dessa arma.", parent=self)
                self.v["arma_disp"].set(self.v["arma"].get())
                return
            self.v["arma"].set("" if t.startswith("—") else t[2:].strip())
            self._mostrar()
        cb.bind("<<ComboboxSelected>>", escolher_arma)
        if self.v["arma"].get():
            self.v["arma_disp"].set(self.v["arma"].get())

        arma = self.v["arma"].get()
        if arma in ("Cajado", "Selo"):
            dom = "Magia" if arma == "Cajado" else "Feitiço"
            tk.Label(eq, text=f"Encantamentos iniciais ({'Magias' if dom == 'Magia' else 'Feitiços'}, até 3)", bg=c["PERG"],
                     fg=c["VINHO"], font=(c["FONTE"], 10, "bold")).grid(row=2, column=0, sticky="w", pady=(12, 0))
            lb = tk.Listbox(eq, selectmode="multiple", height=12, width=50, exportselection=False, bg=c["CAMPO"], fg=c["TINTA"],
                            selectbackground=c["VINHO"], selectforeground=c["FAIXA"], font=(c["FONTE"], 10), highlightthickness=1,
                            highlightbackground=c["OURO"], relief="flat")
            lb.grid(row=3, column=0, sticky="we")
            itens, bloqs = [], []
            for e in self.app.dados["encantamentos"]:
                if e["dominio"] != dom:
                    continue
                m = R.status_versao(e["versoes"][0], dom, a, 1, tem_impl_inicial=True)
                (bloqs if m else itens).append((e["nome"], m))
            self._lista_enc = itens + bloqs
            for i, (nome, m) in enumerate(self._lista_enc):
                lb.insert("end", f"✓ {nome}" if not m else f"✗ {nome}  — {', '.join(m)}")
                if m:
                    lb.itemconfigure(i, foreground=c["TINTA2"])
                if nome in self.v["encs"]:
                    lb.selection_set(i)
            l_enc = tk.Label(eq, bg=c["PERG"], fg=c["TINTA2"], font=(c["FONTE"], 9, "italic"))
            l_enc.grid(row=4, column=0, sticky="w")

            def sel_enc(e=None):
                escolhidos = []
                for i in lb.curselection():
                    nome, m = self._lista_enc[i]
                    if m or len(escolhidos) >= 3:
                        lb.selection_clear(i)
                    else:
                        escolhidos.append(nome)
                self.v["encs"] = escolhidos
                l_enc.configure(text=f"{len(escolhidos)} de 3 escolhidos")
            lb.bind("<<ListboxSelect>>", sel_enc)
            sel_enc()
        else:
            self.v["encs"] = []
            tk.Label(eq, text="Escolha Cajado (Magias) ou Selo (Feitiços) para\nreceber 3 encantamentos iniciais.", bg=c["PERG"],
                     fg=c["TINTA2"], font=(c["FONTE"], 9, "italic"), justify="left").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self._dica(f, "•  perícia que exige treino para ser usada.", 2, cols=2)

    def _p_talentos(self):
        f = self.corpo
        self._dica(f, "No nível 1 ainda não há talento para escolher: o primeiro chega no nível 2. "
                      "Quando subir de nível, use a aba Talentos da ficha; ela mostra primeiro os talentos que você pode pegar "
                      "e explica o que falta nos outros.", 0)
        a = self.atributos()
        livres = [t for t in self.app.dados["talentos"] if t["nivel"] <= 2 and not R.status_talento(t, 2, set(), a, set(), [], set())]
        tk.Label(f, text=f"Com estes atributos, {len(livres)} talentos já estarão disponíveis no nível 2, por exemplo:",
                 bg=self.c["PERG"], fg=self.c["TINTA"], font=(self.c["FONTE"], 10)).grid(row=1, column=0, sticky="w", pady=(6, 4))
        for i, t in enumerate(livres[:8]):
            tk.Label(f, text=f"✦ {t['nome']} — {t['descricao'][:110]}{'…' if len(t['descricao']) > 110 else ''}", bg=self.c["PERG"],
                     fg=self.c["TINTA2"], font=(self.c["FONTE"], 9), wraplength=640, justify="left").grid(row=2 + i, column=0, sticky="w", pady=1)

    def _p_vinculos(self):
        f = self.corpo
        self._rot(f, "Vínculo com o grupo", 0)
        ttk.Entry(f, textvariable=self.v["vinc_grupo"], width=60).grid(row=0, column=1, sticky="we")
        self._rot(f, "Vínculo com o mundo", 1)
        ttk.Entry(f, textvariable=self.v["vinc_mundo"], width=60).grid(row=1, column=1, sticky="we")
        self._rot(f, "Metas de vida", 2)
        ttk.Entry(f, textvariable=self.v["metas"], width=60).grid(row=2, column=1, sticky="we")
        self._dica(f, "Pode deixar em branco e preencher depois na aba Talentos (seção Vínculos e metas).", 3, cols=2)

    def _p_resumo(self):
        c, f = self.c, self.corpo
        a = self.atributos()
        d = R.derivadas(a, 1, set(), 7 * R.curva(a["VIT"]))
        per = [n for n, v in self.v["per"].items() if v.get()]
        linhas = [
            ("Personagem", f"{self.v['nome'].get() or '—'}  (player: {self.v['player'].get() or '—'})"),
            ("Sonho", self.v["sonho"].get() or "—"),
            ("Alma", "sem alma (+2 pontos por nível)" if self.v["sem_alma"].get() else (self.v["alma_nome"].get() or "com alma, sem nome")),
            ("Espécie", (self.v["especie"].get() or "—") + (f"  (+{self.v['esp_val'].get()} {self.v['esp_bon'].get()}, "
                                                            f"−{self.v['esp_val'].get()} {self.v['esp_pre'].get()})" if _int(self.v["esp_val"].get()) else "")),
            ("Atributos", "  ".join(f"{k} {a[k]}" for k in R.ATRIBUTOS)),
            ("Características", f"Vida {d['vida']} · Mana {d['mana']} · Vigor {d['vigor']} · CA {d['ca']} · Carga {d['carga']} · Mov. {d['movimento']} m"),
            ("Perícias", f"{self.v['per_atk'].get()} (ataque); " + (", ".join(per) or "nenhuma fora de combate")),
            ("Arma", self.v["arma"].get() or "nenhuma"),
            ("Encantamentos", ", ".join(self.v["encs"]) or "nenhum"),
            ("Vínculos", " / ".join(x for x in (self.v["vinc_grupo"].get(), self.v["vinc_mundo"].get()) if x) or "—"),
        ]
        for r, (k, v) in enumerate(linhas):
            tk.Label(f, text=k, bg=c["PERG"], fg=c["VINHO"], font=(c["FONTE"], 10, "bold"), anchor="nw").grid(row=r, column=0, sticky="nw", pady=3, padx=(0, 14))
            tk.Label(f, text=v, bg=c["PERG"], fg=c["TINTA"], font=(c["FONTE"], 10), anchor="w", justify="left", wraplength=540).grid(row=r, column=1, sticky="w", pady=3)
        self._dica(f, "Ao criar, o programa pergunta onde salvar o arquivo da ficha.", len(linhas), cols=2)

    # ------------------------------------------------------------ validação
    def _validar(self, i):
        self._guardar_textos()
        if i == 0 and not self.v["nome"].get().strip():
            return "Dê um nome ao personagem."
        if i == 2:
            n = _int(self.v["esp_val"].get())
            b, p = self.v["esp_bon"].get(), self.v["esp_pre"].get()
            if n and (not b or not p or b == p):
                return "Escolha atributos diferentes para o bônus e o prejuízo da espécie (ou deixe o valor em 0)."
        if i == 3:
            vals = [v.get() for v in self.v["ini"].values()]
            if "" in vals or len(set(vals)) != 8:
                return "Atribua os oito valores (16, 14, 12, 11, 10, 9, 8 e 7), cada um uma vez."
        if i == 4:
            n = sum(v.get() for v in self.v["per"].values())
            if n > self.max_pericias():
                return f"Você marcou {n} perícias; o máximo é {self.max_pericias()}."
            arma = self.app.armas_por_nome.get(self.v["arma"].get())
            if arma and R.req_falta(R.req_arma(arma, 1), self.atributos()):
                return "Seus atributos não cumprem os requisitos da arma escolhida."
        return None

    # ------------------------------------------------------------ concluir
    def _concluir(self):
        for j in range(len(PASSOS) - 1):
            erro = self._validar(j)
            if erro:
                self.passo = j
                self._mostrar()
                self.l_erro.configure(text=erro)
                return
        v = self.v
        n = max(0, min(5, _int(v["esp_val"].get())))
        kb, kp = R.ATR_POR_NOME.get(v["esp_bon"].get()), R.ATR_POR_NOME.get(v["esp_pre"].get())
        a = self.atributos()
        espacos = 1 + (R.cap(a["INT"]) + R.cap(a["FE"])) // 6
        encs, usados = [], 0
        for nome in v["encs"]:
            e = self.app.enc_por_nome[nome]
            eq = usados + e["espaco"] <= espacos
            usados += e["espaco"] if eq else 0
            encs.append({"familia": nome, "versoes": [e["versoes"][0]["nivel"]], "equipado": eq})
        hab = []
        if not v["sem_alma"].get():
            if v["pas_nome"].get():
                hab.append({"nome": v["pas_nome"].get(), "efeito": v["pas_ef"].get(), "tipo": "Passivo"})
            if v["atv_nome"].get():
                hab.append({"nome": v["atv_nome"].get(), "efeito": v["atv_ef"].get(), "tipo": "Ativo"})
        especie = v["especie"].get().strip()
        estado = {
            "inicializado": True, "sem_alma": v["sem_alma"].get(),
            "identidade": {"nome": v["nome"].get().strip(), "player": v["player"].get().strip(), "nivel": 1,
                           "especie": especie, "sonho": v["sonho"].get().strip(), "guilda": ""},
            "atributos": {k: {"inicial": v["ini"][k].get(), "niveis": "0", "especie": str(n if k == kb else -n if k == kp else 0) if n else "0",
                              "bonus": "0"} for k in R.ATRIBUTOS},
            "pericias": [p for p, b in v["per"].items() if b.get()], "pericia_ataque": v["per_atk"].get(), "prevalencia_attr": "ARC",
            "armas": [{"grupo": v["arma"].get(), "nivel": "1", "props": ""}, {}],
            "encantamentos": encs,
            "alma": {"nome": v["alma_nome"].get(), "atr": v["alma_atr"].get(), "historia": v["alma_hist"], "habilidades": hab},
            "vinculos": {"grupo": v["vinc_grupo"].get(), "mundo": v["vinc_mundo"].get(), "metas": v["metas"].get()},
            "especie_notas": v["esp_notas"].strip(),
        }
        self.grab_release()
        self.destroy()
        self.app.criar_de_assistente(estado)


def _int(s, d=0):
    try:
        return int(str(s).strip())
    except (TypeError, ValueError):
        return d
