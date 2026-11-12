# -*- coding: utf-8 -*-
"""Ficha de Personagem — Prevalecentes (PREVA 3.1)
Calcula características derivadas, controla pontos por nível e oferece menus
de armas, encantamentos e talentos marcando o que pode ou não ser aprendido.
Layout segue a ficha oficial (páginas I a VII).
"""
import json
import os
import random
import re
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font as tkfont

import regras as R
import sessao
from dados_prevalecentes import DADOS as _DADOS_EMBUTIDOS

APP_NOME = "Ficha Prevalecentes 3.1"
OK, NO = "✓", "✗"

# ---------------------------------------------------------------- paletas
# "Biblioteca élfica": verde-floresta profundo, pergaminho, couro e ouro velho.
TEMAS = {
    "diurno": dict(
        FUNDO="#1b2520", FUNDO2="#26342c", PERG="#f2e9d3", PERG2="#e6d7b4", CAMPO="#fbf7ea",
        TINTA="#2d2015", TINTA2="#7d6a54", OURO="#b39552", OURO2="#dcc387", VINHO="#7c2626", VERDE="#4a6d33",
        FAIXA="#f6efdc", LINHA="#ddcda6", ROSA="#f1dcd6", AGUA="#d7e7e3",
        MESA_CAMPO="#2f3f35", MESA_BORDA="#4b5d50", MESA_ATIVO="#34463b", MESA_TXT="#9fae9f", ALERTA="#f0a08c",
        C_VIDA="#9a3d33", C_MANA="#3f6283", C_VIGOR="#567a3b", C_MOV="#3d7471", C_CA="#6f675a", C_ATK="#a2463e",
        C_DEF="#4a6893", C_PER="#b07a3c", C_TAL="#3d7471", C_DIN="#567a3b", C_ATR="#3b4a3f"),
    "noturno": dict(
        FUNDO="#0d120f", FUNDO2="#18211b", PERG="#1b231e", PERG2="#2a342d", CAMPO="#232c26",
        TINTA="#e8dec5", TINTA2="#a3977f", OURO="#8f7542", OURO2="#d6bd82", VINHO="#b85a50", VERDE="#8dbb68",
        FAIXA="#f3ead4", LINHA="#36423a", ROSA="#33262a", AGUA="#1f302c",
        MESA_CAMPO="#1d2721", MESA_BORDA="#36463b", MESA_ATIVO="#243128", MESA_TXT="#8a998a", ALERTA="#e8907c",
        C_VIDA="#80352d", C_MANA="#34516e", C_VIGOR="#476532", C_MOV="#33605e", C_CA="#5b554a", C_ATK="#86403a",
        C_DEF="#3d5679", C_PER="#8c6232", C_TAL="#33605e", C_DIN="#476532", C_ATR="#2f3d33"),
}
NOTURNO = False


def aplicar_tema(nome):
    global NOTURNO
    NOTURNO = nome == "noturno"
    globals().update(TEMAS[nome])


aplicar_tema("diurno")
ARQ_PREF = os.path.join(os.path.expanduser("~"), ".ficha_prevalecentes.json")


def ler_pref():
    try:
        with open(ARQ_PREF, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def gravar_pref(**kw):
    p = ler_pref()
    p.update(kw)
    try:
        with open(ARQ_PREF, "w", encoding="utf-8") as f:
            json.dump(p, f)
    except Exception:
        pass


FONTE = "Georgia"
FONTE_TIT = "Georgia"



def pasta_app():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def carregar_dados():
    ext = os.path.join(pasta_app(), "dados_prevalecentes.json")
    if os.path.exists(ext):
        try:
            with open(ext, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:  # noqa
            messagebox.showwarning(APP_NOME, f"Não consegui ler dados_prevalecentes.json ({e}).\nUsando os dados embutidos.")
    return _DADOS_EMBUTIDOS


def to_int(s, default=0):
    try:
        return int(str(s).strip().replace("+", ""))
    except Exception:
        return default


def ordenar(vals):
    """Itens permitidos (✓) primeiro, bloqueados (✗) por último; mantém a ordem do livro dentro de cada grupo."""
    return [v for v in vals if not v.startswith(NO)] + [v for v in vals if v.startswith(NO)]


def versalete(txt):
    """Imita versalete com espaçamento: 'Atributos' -> 'A T R I B U T O S'."""
    return " ".join(txt.upper())


class Rot(tk.Label):
    """Rótulo de valor. Aceita style='Erro.TLabel'/'Ok.TLabel' (muda a cor do texto)."""

    def __init__(self, master, fg=None, bg=None, size=10, bold=True, italic=False, **kw):
        self._fg0 = fg or TINTA
        estilo = ("bold" if bold else "normal") + (" italic" if italic else "")
        super().__init__(master, fg=self._fg0, bg=bg or PERG, font=(FONTE, size, estilo), anchor=kw.pop("anchor", "w"), **kw)

    def configure(self, cnf=None, **kw):
        st = kw.pop("style", None)
        if st is not None:
            kw.setdefault("fg", {"Erro.TLabel": VINHO, "Ok.TLabel": VERDE}.get(st, self._fg0))
        return super().configure(cnf, **kw)

    config = configure


class ScrollFrame(ttk.Frame):
    """Página com rolagem vertical."""

    def __init__(self, master):
        super().__init__(master, style="Pagina.TFrame")
        self.canvas = tk.Canvas(self, highlightthickness=0, background=PERG, borderwidth=0, yscrollincrement=20)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas, style="Pagina.TFrame", padding=(22, 14, 22, 22))
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._win, width=e.width))
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def rolar(self, passos):
        if self.canvas.yview() != (0.0, 1.0):
            self.canvas.yview_scroll(passos, "units")


class Dica:
    """Janela de descrição que aparece ao parar o mouse sobre uma linha de uma Treeview."""

    def __init__(self, raiz, tree, texto_de):
        self.raiz, self.tree, self.texto_de = raiz, tree, texto_de
        self.janela, self.linha, self._agendado = None, None, None
        tree.bind("<Motion>", self._mover, add="+")
        tree.bind("<Leave>", lambda e: self._esconder(), add="+")
        tree.bind("<ButtonPress>", lambda e: self._esconder(), add="+")

    def _mover(self, e):
        linha = self.tree.identify_row(e.y)
        if linha == self.linha:
            if self.janela is not None:
                self._posicionar(e.x_root, e.y_root)
            return
        self._esconder()
        self.linha = linha
        if linha:
            self._agendado = self.raiz.after(350, lambda: self._mostrar(e.x_root, e.y_root))

    def _mostrar(self, x, y):
        info = self.texto_de(self.linha) if self.linha else None
        if not info:
            return
        titulo, corpo = info
        w = tk.Toplevel(self.raiz)
        w.wm_overrideredirect(True)
        try:
            w.attributes("-topmost", True)
        except tk.TclError:
            pass
        f = tk.Frame(w, bg=CAMPO, highlightbackground=OURO, highlightthickness=1, padx=12, pady=10)
        f.pack()
        tk.Label(f, text=titulo, bg=CAMPO, fg=VINHO, font=(FONTE, 11, "bold"), anchor="w", justify="left").pack(anchor="w")
        tk.Frame(f, height=1, bg=OURO).pack(fill="x", pady=5)
        tk.Label(f, text=corpo, bg=CAMPO, fg=TINTA, font=(FONTE, 9), wraplength=440, justify="left", anchor="w").pack(anchor="w")
        self.janela = w
        self._posicionar(x, y)

    def _posicionar(self, x, y):
        w = self.janela
        w.update_idletasks()
        larg, alt = w.winfo_reqwidth(), w.winfo_reqheight()
        tela_l, tela_a = w.winfo_screenwidth(), w.winfo_screenheight()
        px = x + 18 if x + 18 + larg < tela_l else x - larg - 12
        py = y + 14 if y + 14 + alt < tela_a else max(0, y - alt - 10)
        w.geometry(f"+{px}+{py}")

    def _esconder(self):
        if self._agendado:
            self.raiz.after_cancel(self._agendado)
            self._agendado = None
        if self.janela is not None:
            self.janela.destroy()
            self.janela = None
        self.linha = None


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NOME)
        self.geometry("1240x860")
        self.minsize(1040, 680)
        self.dados = carregar_dados()
        self.armas_por_nome = {a["nome"]: a for a in self.dados["armas"]}
        self.enc_por_nome = {e["nome"]: e for e in self.dados["encantamentos"]}
        self.tal_por_nome = {t["nome"]: t for t in self.dados["talentos"]}
        self.tal_info = {t["nome"]: t for t in self.dados.get("talismas", [])}
        self.categorias_tal = sorted({t["categoria"] for t in self.dados["talentos"]})
        self.categorias_enc = []
        for e in self.dados["encantamentos"]:
            if e["categoria"] not in self.categorias_enc:
                self.categorias_enc.append(e["categoria"])
        self.arquivo = None
        self._recalc_agendado = False
        self._carregando = False
        self.nivel_anterior = 1
        self.vida_rolagens = []
        self.sem_alma = False
        self.manual = {}          # valores digitados que substituem o cálculo: atributos, "vida", "mana"
        self.desfazer = []        # custos descontados pelas rolagens: [(var, valor_antigo, descrição)]
        self.diario = None
        self._receitas_salvas = ""
        self.encantamentos = []
        self.d = {}
        self.caixas = {}
        self.so_edicao = []
        self.modo = "jogo"
        self.efeitos_mestre = []
        self.janela_sessao = None
        aplicar_tema(ler_pref().get("tema", "diurno"))
        self._estilo()
        self._menu()
        self._montar()
        self._aplicar_modo()
        self.novo(perguntar=False)
        self.bind_all("<MouseWheel>", lambda e: self._roda(e, -1 if e.delta > 0 else 1, abs(e.delta)))
        self.bind_all("<Button-4>", lambda e: self._roda(e, -1, 120))
        self.bind_all("<Button-5>", lambda e: self._roda(e, 1, 120))
        self.protocol("WM_DELETE_WINDOW", self.fechar)

    # ============================================================ estilo
    def _estilo(self):
        global FONTE, FONTE_TIT
        fams = set(tkfont.families(self))
        for f in ("Palatino Linotype", "Book Antiqua", "Constantia", "Georgia", "Garamond", "Cambria", "Times New Roman"):
            if f in fams:
                FONTE = f
                break
        FONTE_TIT = FONTE
        for f in ("Cinzel", "Trajan Pro", "Perpetua Titling MT", "Castellar", "Felix Titling"):
            if f in fams:
                FONTE_TIT = f
                break
        self.configure(background=FUNDO)
        for nome in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
            try:
                tkfont.nametofont(nome).configure(family=FONTE, size=10)
            except tk.TclError:
                pass
        for k, v in {"*Text.background": CAMPO, "*Text.foreground": TINTA, "*Text.font": (FONTE, 10), "*Text.relief": "flat",
                     "*Text.highlightThickness": 1, "*Text.highlightBackground": OURO, "*Text.highlightColor": VINHO,
                     "*Text.selectBackground": VINHO, "*Text.padX": 10, "*Text.padY": 8,
                     "*TCombobox*Listbox.background": CAMPO, "*TCombobox*Listbox.foreground": TINTA,
                     "*TCombobox*Listbox.selectBackground": VINHO, "*TCombobox*Listbox.selectForeground": FAIXA,
                     "*TCombobox*Listbox.font": (FONTE, 10), "*Menu.background": PERG, "*Menu.foreground": TINTA,
                     "*Menu.activeBackground": VINHO, "*Menu.activeForeground": FAIXA}.items():
            self.option_add(k, v)

        st = ttk.Style(self)
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        st.configure(".", background=PERG, foreground=TINTA, font=(FONTE, 10), bordercolor=OURO,
                     lightcolor=PERG, darkcolor=PERG, troughcolor=PERG2, focuscolor=OURO,
                     selectbackground=VINHO, selectforeground=FAIXA, fieldbackground=CAMPO, insertcolor=TINTA)
        st.configure("TFrame", background=PERG)
        st.configure("Pagina.TFrame", background=PERG)
        st.configure("Mesa.TFrame", background=FUNDO)
        st.configure("TLabel", background=PERG, foreground=TINTA)
        st.configure("Sub.TLabel", foreground=TINTA2, font=(FONTE, 9, "italic"))
        st.configure("Rot.TLabel", foreground=TINTA2, font=(FONTE, 9))
        st.configure("Mesa.TLabel", background=FUNDO, foreground=OURO2, font=(FONTE, 9))

        st.configure("TNotebook", background=FUNDO, borderwidth=0, tabmargins=(14, 8, 14, 0))
        st.configure("TNotebook.Tab", background=FUNDO2, foreground=OURO2, padding=(16, 7), font=(FONTE, 10),
                     bordercolor=FUNDO, lightcolor=FUNDO2, darkcolor=FUNDO2)
        st.map("TNotebook.Tab", background=[("selected", PERG), ("active", MESA_ATIVO)],
               foreground=[("selected", VINHO)], font=[("selected", (FONTE, 10, "bold"))],
               lightcolor=[("selected", PERG)], expand=[("selected", (1, 2, 1, 0))])

        st.configure("TButton", background=FUNDO2, foreground=OURO2, bordercolor=OURO, lightcolor=FUNDO2, darkcolor=FUNDO2,
                     padding=(12, 4), font=(FONTE, 10), relief="flat")
        st.map("TButton", background=[("disabled", PERG2), ("active", VINHO)], foreground=[("disabled", TINTA2), ("active", FAIXA)])
        st.configure("Peq.TButton", padding=(4, 1))
        st.configure("Alternar.TCheckbutton", background=PERG2, foreground=TINTA, padding=(12, 6), font=(FONTE, 11, "bold"),
                     indicatorsize=0, indicatormargin=0, bordercolor=OURO, relief="raised")
        st.layout("Alternar.TCheckbutton", [("Checkbutton.border", {"sticky": "nswe", "children": [
            ("Checkbutton.padding", {"sticky": "nswe", "children": [("Checkbutton.label", {"sticky": "nswe"})]})]})])
        st.map("Alternar.TCheckbutton", background=[("selected", VINHO), ("active", PERG2)], foreground=[("selected", FAIXA)])

        for w in ("TEntry", "TSpinbox", "TCombobox"):
            st.configure(w, fieldbackground=CAMPO, background=PERG2, foreground=TINTA, bordercolor=OURO,
                         lightcolor=CAMPO, darkcolor=CAMPO, arrowcolor=VINHO, padding=(4, 2))
            st.map(w, fieldbackground=[("readonly", CAMPO), ("disabled", PERG2)], foreground=[("disabled", TINTA2)],
                   bordercolor=[("focus", VINHO)], selectbackground=[("readonly", CAMPO)], selectforeground=[("readonly", TINTA)])
        st.configure("Mesa.TEntry", fieldbackground=MESA_CAMPO, foreground=FAIXA, bordercolor=MESA_BORDA, lightcolor=MESA_CAMPO,
                     darkcolor=MESA_CAMPO, insertcolor=OURO2)
        st.configure("Mesa.TSpinbox", fieldbackground=MESA_CAMPO, foreground=FAIXA, bordercolor=MESA_BORDA, lightcolor=MESA_CAMPO,
                     darkcolor=MESA_CAMPO, insertcolor=OURO2, arrowcolor=OURO2, background=FUNDO2)
        for w in ("TCheckbutton", "TRadiobutton"):
            st.configure(w, background=PERG, foreground=TINTA, indicatorbackground=CAMPO, indicatorforeground=VINHO, bordercolor=OURO)
            st.map(w, background=[("active", PERG)], indicatorbackground=[("selected", CAMPO)])
        st.configure("Treeview", background=CAMPO, fieldbackground=CAMPO, foreground=TINTA, rowheight=26, bordercolor=OURO, font=(FONTE, 10))
        st.configure("Treeview.Heading", background=C_ATR, foreground=FAIXA, font=(FONTE, 10, "bold"), relief="flat", bordercolor=OURO)
        st.map("Treeview", background=[("selected", VINHO)], foreground=[("selected", FAIXA)])
        st.map("Treeview.Heading", background=[("active", C_ATR)])
        st.configure("Vertical.TScrollbar", background=PERG2, troughcolor=PERG, bordercolor=PERG, arrowcolor=VINHO,
                     lightcolor=PERG2, darkcolor=PERG2, gripcount=0)

    # ============================================================ helpers
    def var(self, valor="", tipo=tk.StringVar):
        v = tipo(value=valor)
        v.trace_add("write", lambda *a: self.agendar())
        return v

    def agendar(self):
        if self._carregando:
            return
        if not getattr(self, "alterado", True) and getattr(self, "inicializado", False):
            self.alterado = True
            self._titulo()
        if self._recalc_agendado:
            return
        self._recalc_agendado = True
        self.after_idle(self.recalc)

    def ed(self, w):
        """Marca um controle como "só no Modo Edição" (desabilitado no Modo Jogo)."""
        self.so_edicao.append(w)
        return w

    def secao(self, master, titulo, row=0, column=0, columnspan=1, rowspan=1, sticky="nsew", pady=(10, 4)):
        """Cabeçalho de seção: título em versalete + filete dourado. Retorna o corpo."""
        box = ttk.Frame(master)
        box.grid(row=row, column=column, columnspan=columnspan, rowspan=rowspan, sticky=sticky, padx=10, pady=pady)
        box.columnconfigure(0, weight=1)
        cab = ttk.Frame(box)
        cab.grid(row=0, column=0, sticky="we")
        tk.Label(cab, text="❧", fg=OURO, bg=PERG, font=(FONTE, 12)).pack(side="left")
        tk.Label(cab, text=versalete(titulo), fg=VINHO, bg=PERG, font=(FONTE_TIT, 10, "bold")).pack(side="left", padx=(4, 8))
        tk.Frame(cab, height=1, bg=OURO).pack(side="left", fill="x", expand=True, pady=(4, 0))
        corpo = ttk.Frame(box)
        corpo.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        box.rowconfigure(1, weight=1)
        return corpo

    def cabecalho(self, master, cols, cor, row=0, col0=0, larguras=None):
        """Linha de cabeçalho de tabela colorida (como na ficha)."""
        for i, c in enumerate(cols):
            tk.Label(master, text=c, bg=cor, fg=FAIXA if cor not in (PERG2,) else TINTA, font=(FONTE, 9, "bold"),
                     anchor="w", padx=6, pady=3, width=(larguras[i] if larguras else 0) or None
                     ).grid(row=row, column=col0 + i, sticky="nsew", padx=(0, 1))

    def linha(self, master, row, ncols, col0=0):
        tk.Frame(master, height=1, bg=LINHA).grid(row=row, column=col0, columnspan=ncols, sticky="we")

    def caixa(self, master, titulo, cor, row, column, sub=True, larg=12, big=18, **grid):
        """Caixa estilo D&D: faixa colorida com o nome, número grande, legenda pequena."""
        f = tk.Frame(master, bg=CAMPO, highlightbackground=OURO, highlightthickness=1)
        f.grid(row=row, column=column, padx=4, pady=4, sticky="nsew", **grid)
        rotulo = versalete(titulo) if len(titulo) < 12 else titulo.upper()
        tk.Label(f, text=rotulo, bg=cor, fg=FAIXA, font=(FONTE, 8, "bold"), pady=2,
                 width=max(larg, int(len(titulo) * 1.6) + 2)).pack(fill="x")
        v = Rot(f, bg=CAMPO, size=big, anchor="center")
        v.pack(fill="x", padx=6, pady=(4, 0 if sub else 6))
        s = None
        if sub:
            s = Rot(f, bg=CAMPO, fg=TINTA2, size=8, bold=False, italic=True, anchor="center")
            s.pack(fill="x", padx=4, pady=(0, 5))
        return v, s

    def campo(self, master, r, c, texto, var, w=18, estilo=None, **kw):
        ttk.Label(master, text=texto, style=estilo + ".TLabel" if estilo else "Rot.TLabel").grid(row=r, column=c, sticky="w", padx=(0, 4), pady=2)
        e = ttk.Entry(master, textvariable=var, width=w, style=estilo + ".TEntry" if estilo else "TEntry", **kw)
        e.grid(row=r, column=c + 1, sticky="we", padx=(0, 12), pady=2)
        return e

    def val(self, master, r, c, texto, **kw):
        ttk.Label(master, text=texto, style="Rot.TLabel").grid(row=r, column=c, sticky="w", padx=(0, 4), pady=2)
        lab = Rot(master, **kw)
        lab.grid(row=r, column=c + 1, sticky="w", padx=(0, 16), pady=2)
        return lab

    def texto(self, master, **kw):
        return tk.Text(master, wrap="word", **kw)

    # ============================================================ menu
    def _menu(self):
        m = tk.Menu(self)
        arq = tk.Menu(m, tearoff=0)
        arq.add_command(label="Nova ficha", command=self.novo, accelerator="Ctrl+N")
        arq.add_command(label="Abrir…", command=self.abrir, accelerator="Ctrl+O")
        arq.add_command(label="Salvar", command=self.salvar, accelerator="Ctrl+S")
        arq.add_command(label="Salvar como…", command=lambda: self.salvar(como=True))
        arq.add_separator()
        arq.add_command(label="Exportar ficha em PDF…", command=self.exportar_pdf, accelerator="Ctrl+P")
        arq.add_separator()
        arq.add_command(label="Sair", command=self.fechar)
        m.add_cascade(label="Arquivo", menu=arq)
        fi = tk.Menu(m, tearoff=0)
        fi.add_command(label="Refazer distribuição inicial…",
                       command=lambda: (self.novo() if not self.inicializado else None if self._so_edicao("A distribuição inicial") else self.inicializar()))
        fi.add_command(label="Comparar duas fichas…", command=self.comparar)
        m.add_cascade(label="Ficha", menu=fi)
        se = tk.Menu(m, tearoff=0)
        se.add_command(label="Levantar a mão / Mesa do mestre…", command=self.abrir_sessao)
        m.add_cascade(label="Sessão", menu=se)
        ex = tk.Menu(m, tearoff=0)
        ex.add_command(label="Alternar modo noturno", command=self.alternar_tema, accelerator="Ctrl+T")
        m.add_cascade(label="Exibir", menu=ex)
        self.bind("<Control-t>", lambda e: self.alternar_tema())
        aj = tk.Menu(m, tearoff=0)
        aj.add_command(label="Criar personagem passo a passo…", command=self.novo)
        aj.add_command(label="Regras usadas nos cálculos", command=self.mostrar_regras)
        m.add_cascade(label="Ajuda", menu=aj)
        self.config(menu=m)
        self.bind("<Control-n>", lambda e: self.novo())
        self.bind("<Control-o>", lambda e: self.abrir())
        self.bind("<Control-s>", lambda e: self.salvar())
        self.bind("<Control-p>", lambda e: self.exportar_pdf())

    # ============================================================ montagem
    def _montar(self):
        # --- cabeçalho da ficha (como no topo da página 1)
        ban = tk.Frame(self, bg=FUNDO, padx=22, pady=12)
        ban.pack(fill="x")
        tit = tk.Frame(ban, bg=FUNDO)
        tit.pack(side="left", anchor="n")
        tk.Label(tit, text="⚜ Prevalecentes", bg=FUNDO, fg=OURO2, font=(FONTE_TIT, 22, "bold")).pack(anchor="w")
        tk.Label(tit, text="Ficha do Sonhador  ·  edição 3.1", bg=FUNDO, fg=MESA_TXT, font=(FONTE, 9, "italic")).pack(anchor="w")
        self.lbl_modo = tk.Label(tit, text="", bg=FUNDO, fg=OURO2, font=(FONTE, 9, "bold"))
        self.lbl_modo.pack(anchor="w", pady=(4, 0))

        idf = ttk.Frame(ban, style="Mesa.TFrame")
        idf.pack(side="left", padx=(36, 0), anchor="n")
        self.v_nome, self.v_player, self.v_nivel = self.var(), self.var(), self.var("1")
        self.v_especie, self.v_sonho, self.v_guilda = self.var(), self.var(), self.var()
        self.ed(self.campo(idf, 0, 0, "Nome", self.v_nome, 24, estilo="Mesa"))
        self.ed(self.campo(idf, 0, 2, "Player", self.v_player, 16, estilo="Mesa"))
        ttk.Label(idf, text="Nível", style="Mesa.TLabel").grid(row=0, column=4, sticky="w", padx=(0, 4))
        self.ed(ttk.Spinbox(idf, from_=1, to=R.NIVEL_MAX, textvariable=self.v_nivel, width=4, style="Mesa.TSpinbox")).grid(row=0, column=5, sticky="w")
        self.ed(self.campo(idf, 1, 0, "Espécie", self.v_especie, 24, estilo="Mesa"))
        self.ed(self.campo(idf, 1, 2, "Sonho", self.v_sonho, 16, estilo="Mesa"))
        self.ed(self.campo(idf, 1, 4, "Guilda", self.v_guilda, 4, estilo="Mesa"))

        arq = tk.Frame(ban, bg=FUNDO)
        arq.pack(side="right", anchor="n", padx=(22, 0), pady=(4, 0))
        ttk.Button(arq, text="✦ Nova ficha", command=self.novo).pack(fill="x", pady=1)
        ttk.Button(arq, text="Abrir", command=self.abrir).pack(fill="x", pady=1)
        ttk.Button(arq, text="Salvar", command=self.salvar).pack(fill="x", pady=1)
        ext = tk.Frame(ban, bg=FUNDO)
        ext.pack(side="right", anchor="n", padx=(12, 0), pady=(4, 0))
        self.bt_modo = ttk.Button(ext, text="✎ Modo Edição", command=self.alternar_modo)
        self.bt_modo.pack(fill="x", pady=1)
        ttk.Button(ext, text="☀ Modo diurno" if NOTURNO else "☾ Modo noturno", command=self.alternar_tema).pack(fill="x", pady=1)
        ttk.Button(ext, text="⚖ Comparar fichas", command=self.comparar).pack(fill="x", pady=1)
        ttk.Button(ext, text="📜 Exportar PDF", command=self.exportar_pdf).pack(fill="x", pady=1)
        ttk.Button(ext, text="✋ Sessão", command=self.abrir_sessao).pack(fill="x", pady=1)
        pts = tk.Frame(ban, bg=FUNDO)
        pts.pack(side="right", anchor="n")
        tk.Label(pts, text="PONTOS DE ATRIBUTO", bg=FUNDO, fg=MESA_TXT, font=(FONTE, 8, "bold")).pack(anchor="e")
        self.lbl_pontos_topo = Rot(pts, bg=FUNDO, fg=OURO2, size=16, anchor="e")
        self.lbl_pontos_topo.pack(anchor="e")
        self.lbl_pontos_topo_sub = Rot(pts, bg=FUNDO, fg=MESA_TXT, size=9, bold=False, italic=True, anchor="e")
        self.lbl_pontos_topo_sub.pack(anchor="e")
        tk.Frame(self, height=1, bg=OURO).pack(fill="x")

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        self._pag_ficha()
        self._pag_combate()
        self._pag_alma()
        self._pag_inventario()
        self._pag_encantamentos()
        self._pag_talentos()
        self.abas_nomes = []
        for w in (self.nb.tabs() or ()):
            try:
                txt = self.nb.tab(w, "text")
                self.abas_nomes.append((self.nametowidget(w), txt.split(" · ", 1)[-1]))
            except (tk.TclError, AttributeError, TypeError, KeyError):
                pass
        self._renumerar_abas()

        # capa que bloqueia a ficha até a inicialização
        self.capa = tk.Frame(self, bg=PERG, highlightbackground=OURO, highlightthickness=1)
        miolo = tk.Frame(self.capa, bg=PERG)
        miolo.place(relx=0.5, rely=0.42, anchor="center")
        tk.Label(miolo, text="❦", bg=PERG, fg=OURO, font=(FONTE, 30)).pack()
        tk.Label(miolo, text="Bem-vindo, Sonhador", bg=PERG, fg=VINHO, font=(FONTE_TIT, 20, "bold")).pack(pady=(4, 6))
        tk.Label(miolo, text="Crie uma ficha nova ou abra uma ficha salva.\n"
                             "A ficha nova abre um passo a passo que segue o livro, do Sonho aos Vínculos.",
                 bg=PERG, fg=TINTA2, font=(FONTE, 11, "italic"), justify="center").pack(pady=(0, 14))
        bts = tk.Frame(miolo, bg=PERG)
        bts.pack()
        ttk.Button(bts, text="✦  Nova ficha", command=self.novo).pack(side="left", padx=6)
        ttk.Button(bts, text="Abrir ficha salva", command=self.abrir).pack(side="left", padx=6)
        self.alterado = False
        self.inicializado = False

    def _pagina(self, titulo):
        sf = ScrollFrame(self.nb)
        self.nb.add(sf, text=titulo)
        self._ultima_pagina = sf
        return sf.inner

    def _renumerar_abas(self):
        """Mostra/esconde a aba Alma e renumera as abas visíveis (I, II, III…)."""
        if not hasattr(self, "aba_alma"):
            return
        sem = getattr(self, "sem_alma", False)
        try:
            if sem:
                self.nb.hide(self.aba_alma)
            else:
                self.nb.add(self.aba_alma)
        except tk.TclError:
            pass
        romanos = ["I", "II", "III", "IV", "V", "VI", "VII"]
        i = 0
        for w, nome in self.abas_nomes:
            if w is self.aba_alma and sem:
                continue
            try:
                self.nb.tab(w, text=f"{romanos[i]} · {nome}")
            except tk.TclError:
                pass
            i += 1

    # ------------------------------------------------------------ I · Ficha
    def _pag_ficha(self):
        p = self._pagina("I · Ficha")
        p.columnconfigure(0, weight=3)
        p.columnconfigure(1, weight=2)

        # Vida / Mana / Vigor + Movimento + CA (bloco da ficha)
        c = self.secao(p, "Vigor do corpo", row=0, column=0)
        vm = ttk.Frame(c)
        vm.grid(row=0, column=0, sticky="nw")
        self.v_vida_atual, self.v_mana_atual, self.v_vigor_atual = self.var(), self.var(), self.var()
        self.l_vida = self.l_mana = self.l_vigor = None
        for r, (nome, cor, attr, var) in enumerate([("Vida", C_VIDA, "l_vida", self.v_vida_atual),
                                                     ("Mana", C_MANA, "l_mana", self.v_mana_atual),
                                                     ("Vigor", C_VIGOR, "l_vigor", self.v_vigor_atual)]):
            tk.Label(vm, text=nome, bg=cor, fg=FAIXA, font=(FONTE, 10, "bold"), width=7, pady=4).grid(row=r, column=0, sticky="nsew", pady=1)
            ttk.Label(vm, text="Máx", style="Rot.TLabel").grid(row=r, column=1, padx=(10, 4))
            lab = Rot(vm, size=14, width=5)
            lab.grid(row=r, column=2, sticky="w")
            setattr(self, attr, lab)
            if nome in ("Vida", "Mana"):
                lab.configure(cursor="hand2")
                lab.bind("<Button-1>", lambda e, ch=nome.lower(): self.editar_manual(ch))
                ttk.Button(vm, text="✎", width=2, style="Peq.TButton",
                           command=lambda ch=nome.lower(): self.editar_manual(ch)).grid(row=r, column=5, padx=(8, 0))
            ttk.Label(vm, text="Atual", style="Rot.TLabel").grid(row=r, column=3, padx=(10, 4))
            ttk.Entry(vm, textvariable=var, width=6).grid(row=r, column=4)
        self.l_vigor_regen = Rot(vm, fg=TINTA2, size=9, bold=False, italic=True)
        self.l_vigor_regen.grid(row=3, column=0, columnspan=5, sticky="w", pady=(4, 0))
        bx = ttk.Frame(c)
        bx.grid(row=0, column=1, sticky="ne", padx=(24, 0))
        self.caixas["mov1"] = self.caixa(bx, "Movimento", C_MOV, 0, 0)
        self.caixas["ca1"] = self.caixa(bx, "CA", C_CA, 0, 1)
        c.columnconfigure(1, weight=1)

        dv = ttk.Frame(c)
        dv.grid(row=1, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.v_vida_modo = self.var("media")
        ttk.Label(dv, text="Dados de vida (1d12 por ponto de Curva da VIT):", style="Rot.TLabel").pack(side="left")
        self.ed(ttk.Radiobutton(dv, text="média fixa (7)", value="media", variable=self.v_vida_modo)).pack(side="left", padx=6)
        self.ed(ttk.Radiobutton(dv, text="rolar", value="rolar", variable=self.v_vida_modo)).pack(side="left", padx=6)
        self.btn_rolar = ttk.Button(dv, text="🎲 Rolar dados novos", command=self.rolar_vida)
        self.btn_rolar.pack(side="left", padx=6)
        ttk.Button(dv, text="Zerar", command=self.zerar_rolagens, style="Peq.TButton").pack(side="left")
        self.l_vida_dados = Rot(c, fg=TINTA2, size=9, bold=False, italic=True, wraplength=640, justify="left")
        self.l_vida_dados.grid(row=2, column=0, columnspan=2, sticky="w", pady=(2, 0))

        # Avisos (coluna direita)
        c = self.secao(p, "Avisos do escriba", row=0, column=1, rowspan=2)
        c.rowconfigure(0, weight=1)
        c.columnconfigure(0, weight=1)
        self.txt_avisos = self.texto(c, width=44, height=16, spacing1=3, spacing3=3)
        self.txt_avisos.grid(row=0, column=0, sticky="nsew")
        self.txt_avisos.tag_configure("ok", foreground=VERDE)
        self.txt_avisos.tag_configure("erro", foreground=VINHO)

        # Atributos (cartões)
        c = self.secao(p, "Atributos", row=1, column=0)
        grade = ttk.Frame(c)
        grade.grid(row=0, column=0, sticky="w")
        self.atr = {}
        iniciais = [""] + [str(x) for x in R.VALORES_INICIAIS]
        for i, k in enumerate(R.ATRIBUTOS):
            row = {"inicial": self.var(), "niveis": self.var("0"), "especie": self.var("0"), "bonus": self.var("0")}
            f = tk.Frame(grade, bg=CAMPO, highlightbackground=OURO, highlightthickness=1)
            f.grid(row=i // 4, column=i % 4, padx=4, pady=4, sticky="nsew")
            tk.Label(f, text=versalete(R.NOMES_ATR[k]), bg=C_ATR, fg=OURO2, font=(FONTE, 8, "bold"), pady=3).pack(fill="x")
            row["l_total"] = Rot(f, bg=CAMPO, size=22, anchor="center", cursor="hand2")
            row["l_total"].pack(fill="x", pady=(2, 0))
            row["l_total"].bind("<Button-1>", lambda e, k=k: self.editar_manual(k))
            linha1 = tk.Frame(f, bg=CAMPO)
            linha1.pack()
            row["l_curva"] = Rot(linha1, bg=CAMPO, fg=TINTA2, size=9, bold=False)
            row["l_curva"].pack(side="left")
            tk.Label(linha1, text=" · ", bg=CAMPO, fg=OURO, font=(FONTE, 9)).pack(side="left")
            row["l_bc"] = Rot(linha1, bg=CAMPO, fg=TINTA2, size=9, bold=False)
            row["l_bc"].pack(side="left")
            linha2 = tk.Frame(f, bg=CAMPO)
            linha2.pack()
            row["l_dados"] = Rot(linha2, bg=CAMPO, fg=TINTA2, size=9, bold=False)
            row["l_dados"].pack(side="left")
            row["l_vant"] = Rot(linha2, bg=CAMPO, fg=VERDE, size=9)
            row["l_vant"].pack(side="left", padx=(4, 0))
            tk.Frame(f, height=1, bg=LINHA).pack(fill="x", padx=8, pady=(5, 3))
            ent = tk.Frame(f, bg=CAMPO)
            ent.pack(padx=6, pady=(0, 6))
            for j, (rot, chave) in enumerate([("ini", "inicial"), ("nív", "niveis"), ("esp", "especie"), ("bôn", "bonus")]):
                tk.Label(ent, text=rot, bg=CAMPO, fg=TINTA2, font=(FONTE, 7)).grid(row=0, column=j)
                if chave in ("inicial", "especie"):
                    w = tk.Label(ent, textvariable=row[chave], bg=PERG2, fg=TINTA, font=(FONTE, 10, "bold"), width=4, pady=1)
                elif chave == "niveis":
                    w = self.ed(ttk.Spinbox(ent, from_=0, to=99, textvariable=row[chave], width=3))
                else:
                    w = self.ed(ttk.Spinbox(ent, from_=-50 if chave == "bonus" else -5, to=50 if chave == "bonus" else 5, textvariable=row[chave], width=3))
                w.grid(row=1, column=j, padx=1)
            self.atr[k] = row
        self.lbl_pontos = Rot(c, size=10)
        self.lbl_pontos.grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Label(c, text="Clique no número grande para digitar um valor rolado fora da ficha  ·  ini e esp são definidos ao criar a ficha (menu Ficha → Refazer distribuição inicial)  ·  ini = valor inicial (16, 14, 12, 11, 10, 9, 8, 7)  ·  nív = pontos de nível (+10 por nível, +5 nos múltiplos de 3)  ·  "
                          "esp = espécie (± 1 a 5)  ·  bôn = talismãs e efeitos", style="Sub.TLabel", wraplength=700).grid(row=2, column=0, sticky="w")

        # Régua da Curva
        rg = ttk.Frame(c)
        rg.grid(row=3, column=0, sticky="w", pady=(8, 0))
        marcos = list(range(5, 100, 5)) + [99]
        tk.Label(rg, text="Pts", bg=C_ATR, fg=OURO2, font=(FONTE, 8, "bold"), width=5).grid(row=0, column=0, sticky="nsew")
        tk.Label(rg, text="Curva", bg=PERG2, fg=TINTA, font=(FONTE, 8, "bold"), width=5).grid(row=1, column=0, sticky="nsew")
        for j, m in enumerate(marcos, start=1):
            tk.Label(rg, text=str(m), bg=C_ATR, fg=FAIXA, font=(FONTE, 8), width=3).grid(row=0, column=j, sticky="nsew")
            tk.Label(rg, text=str(R.curva(m)), bg=CAMPO, fg=TINTA, font=(FONTE, 8), width=3).grid(row=1, column=j, sticky="nsew")

        # Perícias (duas colunas, como na ficha)
        c = self.secao(p, "Perícias", row=2, column=0, columnspan=2)
        self.per = {}
        self.v_prev_attr = self.var("ARC")
        metade = (len(R.PERICIAS) + 1) // 2
        for bloco in range(2):
            col0 = bloco * 6
            self.cabecalho(c, ["T", "Perícia", "Atributo", "Bônus", "Dados"], C_PER, row=0, col0=col0)
            if bloco == 0:
                tk.Frame(c, width=24, bg=PERG).grid(row=0, column=5)
        for i, (nome, atrs, req) in enumerate(R.PERICIAS):
            bloco, r = (0, i + 1) if i < metade else (1, i - metade + 1)
            col0 = bloco * 6
            v = self.var(False, tk.BooleanVar)
            self.ed(ttk.Checkbutton(c, variable=v)).grid(row=r, column=col0, padx=(4, 0))
            tk.Label(c, text=nome + ("  •" if req else ""), bg=PERG, fg=TINTA, font=(FONTE, 10), anchor="w").grid(row=r, column=col0 + 1, sticky="w", padx=6, pady=1)
            if atrs is None:
                self.ed(ttk.Combobox(c, values=R.ATRIBUTOS, textvariable=self.v_prev_attr, width=5, state="readonly")).grid(row=r, column=col0 + 2, sticky="w", padx=6)
            else:
                tk.Label(c, text="/".join(atrs), bg=PERG, fg=TINTA2, font=(FONTE, 9)).grid(row=r, column=col0 + 2, sticky="w", padx=6)
            lb = Rot(c, size=10)
            lb.grid(row=r, column=col0 + 3, sticky="w", padx=6)
            ld = Rot(c, fg=TINTA2, size=9, bold=False)
            ld.grid(row=r, column=col0 + 4, sticky="w", padx=6)
            self.per[nome] = {"var": v, "bonus": lb, "dados": ld, "attrs": atrs}
        for j in (1, 7):
            c.columnconfigure(j, weight=1)
        rod = ttk.Frame(c)
        rod.grid(row=metade + 2, column=0, columnspan=11, sticky="w", pady=(8, 0))
        self.l_per_cont = Rot(rod, size=10)
        self.l_per_cont.pack(side="left")
        ttk.Label(rod, text="   ·   Perícia de ataque treinada inicial:", style="Rot.TLabel").pack(side="left")
        self.v_per_ataque = self.var("Luta")
        for n, _ in R.PERICIAS_ATAQUE:
            self.ed(ttk.Radiobutton(rod, text=n, value=n, variable=self.v_per_ataque)).pack(side="left", padx=4)
        ttk.Label(c, text="•  requer treino.  Bônus = nível ÷ 2, mais a Curva do atributo se treinada  ·  +1d20 a cada 20 pontos no atributo  ·  "
                          "treinadas: 5 + 1 a cada 10 em INT ou MEN (o maior)", style="Sub.TLabel").grid(row=metade + 3, column=0, columnspan=11, sticky="w")

    # ------------------------------------------------------------ II · Combate
    def _pag_combate(self):
        p = self._pagina("II · Combate")
        p.columnconfigure(0, weight=1)
        p.columnconfigure(1, weight=1)
        c = self.secao(p, "Características", row=0, column=0, columnspan=2)
        for i, (k, t, cor) in enumerate([("ca", "CA", C_CA), ("carga", "Carga máx.", C_ATR), ("mov", "Movimento", C_MOV),
                                         ("ini", "Iniciativa", C_ATR), ("acoes", "Ações extras", C_ATR), ("rd", "Red. de dano", C_ATR),
                                         ("desc", "Descoberta", C_ATR), ("talism", "Talismãs", C_TAL)]):
            self.caixas[k] = self.caixa(c, t, cor, 0, i, larg=11, big=16)
        rs = ttk.Frame(c)
        rs.grid(row=1, column=0, columnspan=8, sticky="w", pady=(8, 0))
        ttk.Label(rs, text="Resistências (Tenacidade):", style="Rot.TLabel").pack(side="left", padx=(4, 8))
        self.res_labels = {}
        for lim, nome in R.RESISTENCIAS:
            l = tk.Label(rs, text=f"☐ {nome} {lim}", bg=PERG, fg=TINTA2, font=(FONTE, 9))
            l.pack(side="left", padx=5)
            self.res_labels[nome] = (l, lim)

        c = self.secao(p, "Perícias de ataque", row=1, column=0)
        self.cabecalho(c, ["Perícia", "Bônus"], C_ATK)
        c.columnconfigure(1, weight=1)
        self.l_atk = {}
        for i, (n, atrs) in enumerate(R.PERICIAS_ATAQUE, start=1):
            tk.Label(c, text=f"{n} ({' ou '.join(atrs)})", bg=PERG, fg=TINTA, font=(FONTE, 10), anchor="w").grid(row=2 * i - 1, column=0, sticky="w", padx=6, pady=3)
            self.l_atk[n] = Rot(c, size=10)
            self.l_atk[n].grid(row=2 * i - 1, column=1, sticky="w", padx=6)
            self.linha(c, 2 * i, 2)
        ttk.Label(c, text="1d20 + BC + nível ÷ 3 + acerto da arma", style="Sub.TLabel").grid(row=10, column=0, columnspan=2, sticky="w", pady=(4, 0))

        c = self.secao(p, "Perícias de defesa", row=1, column=1)
        self.cabecalho(c, ["Perícia", "Bônus"], C_DEF)
        c.columnconfigure(1, weight=1)
        self.l_def = {}
        for i, (n, k, _) in enumerate(R.PERICIAS_DEFESA, start=1):
            tk.Label(c, text=f"{n} ({k})", bg=PERG, fg=TINTA, font=(FONTE, 10), anchor="w").grid(row=2 * i - 1, column=0, sticky="w", padx=6, pady=3)
            self.l_def[n] = Rot(c, size=10)
            self.l_def[n].grid(row=2 * i - 1, column=1, sticky="w", padx=6)
            self.linha(c, 2 * i, 2)
        ttk.Label(c, text="1d20 + BC + nível ÷ 3", style="Sub.TLabel").grid(row=10, column=0, columnspan=2, sticky="w", pady=(4, 0))
        self.l_dts = Rot(c, fg=TINTA2, size=9, bold=False, italic=True)
        self.l_dts.grid(row=11, column=0, columnspan=2, sticky="w")

        c = self.secao(p, "Rolar", row=2, column=0, columnspan=2)
        self.bt_rolar_arma = []
        for i in range(2):
            b = ttk.Button(c, text=f"🎲 Arma {i + 1}", command=lambda i=i: self.rolar_arma(i))
            b.grid(row=0, column=i, padx=(0, 6), sticky="w")
            self.bt_rolar_arma.append(b)
        ttk.Button(c, text="🎲 Iniciativa", command=self.rolar_iniciativa).grid(row=0, column=2, padx=(0, 6), sticky="w")
        ttk.Button(c, text="✧ Conjurar…", command=self.conjurar_menu).grid(row=0, column=3, padx=(0, 6), sticky="w")
        ttk.Button(c, text="📜 Diário de rolagens", command=self.abrir_diario).grid(row=0, column=4, padx=(0, 6), sticky="w")
        self.l_ef_ativos = Rot(c, size=9, bold=False, wraplength=980, justify="left")
        self.l_ef_ativos.grid(row=1, column=0, columnspan=6, sticky="w", pady=(6, 0))
        self.l_ef_mestre = Rot(c, size=10, wraplength=980, justify="left", fg=VINHO)
        self.l_ef_mestre.grid(row=3, column=0, columnspan=6, sticky="w", pady=(4, 0))
        ttk.Label(c, text="Ataques descontam o Vigor das armas pesadas e encantamentos descontam Mana; o Diário tem \"Desfazer custo\".",
                  style="Sub.TLabel").grid(row=2, column=0, columnspan=6, sticky="w")

        c = self.secao(p, "Condições", row=3, column=0)
        self.cabecalho(c, ["Condição", "Máx.", "Atual", "Notas"], PERG2)
        c.columnconfigure(3, weight=1)
        self.cond = {}
        for r, n in enumerate(R.CONDICOES, start=1):
            cv = {"max": self.var("100"), "atual": self.var(), "notas": self.var()}
            tk.Label(c, text=n, bg=PERG, fg=TINTA, font=(FONTE, 10, "bold"), anchor="w").grid(row=r, column=0, sticky="w", padx=6)
            ttk.Entry(c, textvariable=cv["max"], width=5).grid(row=r, column=1, padx=2, pady=1)
            ttk.Entry(c, textvariable=cv["atual"], width=5).grid(row=r, column=2, padx=2, pady=1)
            ttk.Entry(c, textvariable=cv["notas"]).grid(row=r, column=3, padx=2, pady=1, sticky="we")
            self.cond[n] = cv

        c = self.secao(p, "Portão da Morte", row=3, column=1)
        ttk.Label(c, text="Vida 0 = Incapaz. d20 no início do turno: 11+ é sucesso.\n5 sucessos: volta com 1 de Vida e 1 cicatriz. 5 falhas: morte.",
                  style="Sub.TLabel").grid(row=0, column=0, columnspan=7, sticky="w", pady=(0, 6))
        self.portao = {}
        for r, (n, cor) in enumerate([("Sucessos", C_VIGOR), ("Falhas", C_VIDA)], start=1):
            tk.Label(c, text=n, bg=cor, fg=FAIXA, font=(FONTE, 9, "bold"), width=10, pady=3).grid(row=r, column=0, sticky="w", pady=2)
            vs = []
            for i in range(5):
                v = self.var(False, tk.BooleanVar)
                ttk.Checkbutton(c, variable=v).grid(row=r, column=1 + i, padx=3)
                vs.append(v)
            self.portao[n] = vs
        self.v_cicatrizes = self.var()
        tk.Label(c, text="Cicatrizes", bg=PERG2, fg=TINTA, font=(FONTE, 9, "bold"), width=10, pady=3).grid(row=3, column=0, sticky="w", pady=2)
        ttk.Entry(c, textvariable=self.v_cicatrizes, width=34).grid(row=3, column=1, columnspan=6, sticky="we", padx=3)
        ttk.Button(c, text="Limpar marcas", command=self._limpar_portao, style="Peq.TButton").grid(row=4, column=0, columnspan=3, sticky="w", pady=6)

    def _limpar_portao(self):
        for vs in self.portao.values():
            for v in vs:
                v.set(False)

    # ------------------------------------------------------------ III · Alma
    def _pag_alma(self):
        p = self._pagina("III · Alma")
        self.aba_alma = self._ultima_pagina
        p.columnconfigure(0, weight=1)
        c = self.secao(p, "A Alma", row=0, column=0)
        self.alma = {"nome": self.var(), "atr": self.var("INT"), "restantes": self.var()}
        topo = ttk.Frame(c)
        topo.grid(row=0, column=0, sticky="w")
        ttk.Label(topo, text="Nome da Alma", style="Rot.TLabel").pack(side="left")
        self.ed(ttk.Entry(topo, textvariable=self.alma["nome"], width=34, font=(FONTE, 12))).pack(side="left", padx=8)
        cx = ttk.Frame(c)
        cx.grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.l_alma_nivel, _ = self.caixa(cx, "Nível da Alma", C_ATR, 0, 0, sub=False, larg=14, big=16)
        self.l_alma_dt, self.l_alma_dt_sub = self.caixa(cx, "DT da Alma", C_ATR, 0, 1, larg=14, big=16)
        self.l_alma_usos, _ = self.caixa(cx, "Usos / descanso", C_ATR, 0, 2, sub=False, larg=14, big=16)
        self.l_alma_ativas, _ = self.caixa(cx, "Ativas liberadas", C_ATR, 0, 3, sub=False, larg=14, big=16)
        op = ttk.Frame(cx)
        op.grid(row=0, column=4, sticky="nw", padx=(16, 0))
        ttk.Label(op, text="DT usa", style="Rot.TLabel").grid(row=0, column=0, sticky="w")
        self.ed(ttk.Combobox(op, values=["INT", "FE"], textvariable=self.alma["atr"], width=5, state="readonly")).grid(row=0, column=1, padx=6)
        ttk.Label(op, text="Usos restantes", style="Rot.TLabel").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Entry(op, textvariable=self.alma["restantes"], width=6).grid(row=1, column=1, padx=6)
        ttk.Label(c, text="Quem foi, por que está com você, que habilidade tinha em vida:", style="Rot.TLabel").grid(row=2, column=0, sticky="w", pady=(10, 2))
        self.txt_alma = self.texto(c, height=4)
        self.txt_alma.grid(row=3, column=0, sticky="we")
        self.ed(self.txt_alma)
        self.txt_alma.bind("<<Modified>>", self._txt_mod)
        c.columnconfigure(0, weight=1)

        c = self.secao(p, "Habilidades", row=1, column=0)
        self.cabecalho(c, ["Habilidade", "Efeito", "Passivo ou Ativo"], C_ATR)
        c.columnconfigure(1, weight=1)
        self.alma_hab = []
        for r in range(1, 7):
            h = {"nome": self.var(), "efeito": self.var(), "tipo": self.var()}
            self.ed(ttk.Entry(c, textvariable=h["nome"], width=24)).grid(row=r, column=0, padx=(0, 2), pady=2, sticky="we")
            self.ed(ttk.Entry(c, textvariable=h["efeito"])).grid(row=r, column=1, padx=2, pady=2, sticky="we")
            self.ed(ttk.Combobox(c, values=["", "Passivo", "Ativo"], textvariable=h["tipo"], width=12, state="readonly")).grid(row=r, column=2, padx=2)
            self.alma_hab.append(h)

    # ------------------------------------------------------------ IV · Inventário
    def _pag_inventario(self):
        p = self._pagina("IV · Inventário")
        p.columnconfigure(0, weight=1)
        p.columnconfigure(1, weight=1)
        c = self.secao(p, "Armas equipadas", row=0, column=0, columnspan=2)
        c.columnconfigure(0, weight=1)
        self.armas_ui = []
        for idx, cor in enumerate([ROSA, AGUA]):
            f = tk.Frame(c, bg=cor, highlightbackground=OURO, highlightthickness=1, padx=10, pady=8)
            f.grid(row=idx, column=0, sticky="we", pady=4)
            ui = {"grupo": self.var(), "nivel": self.var("1"), "props": self.var(), "disp_grupo": tk.StringVar(), "disp_nivel": tk.StringVar()}
            lin = tk.Frame(f, bg=cor)
            lin.pack(fill="x")
            tk.Label(lin, text=f"{'I' if idx == 0 else 'II'}", bg=cor, fg=VINHO, font=(FONTE_TIT, 14, "bold"), width=2).pack(side="left")
            cg = self.ed(ttk.Combobox(lin, textvariable=ui["disp_grupo"], width=44, state="readonly"))
            cg.configure(postcommand=lambda cb=cg, i=idx: self._valores_armas(cb, i))
            cg.bind("<<ComboboxSelected>>", lambda e, i=idx: self._escolher_arma(i))
            cg.pack(side="left", padx=4)
            cn = self.ed(ttk.Combobox(lin, textvariable=ui["disp_nivel"], width=44, state="readonly"))
            cn.configure(postcommand=lambda cb=cn, i=idx: self._valores_nivel_arma(cb, i))
            cn.bind("<<ComboboxSelected>>", lambda e, i=idx: self._escolher_nivel_arma(i))
            cn.pack(side="left", padx=4)
            self.ed(ttk.Button(lin, text="✕", width=3, command=lambda i=idx: self._remover_arma(i), style="Peq.TButton")).pack(side="left", padx=4)
            ttk.Button(lin, text="📖 Ações", command=lambda i=idx: self.mostrar_acoes_arma(self.armas_ui[i]["grupo"].get()),
                       style="Peq.TButton").pack(side="left", padx=4)
            ttk.Button(lin, text="🎲 Atacar", command=lambda i=idx: self.rolar_arma(i), style="Peq.TButton").pack(side="left", padx=4)
            g = tk.Frame(f, bg=cor)
            g.pack(fill="x", pady=(6, 0))
            for j, (k, t) in enumerate([("l_dano", "Dano"), ("l_crit", "Crítico"), ("l_acerto", "Ataque"), ("l_peso", "Peso"),
                                        ("l_tipo", "Tipo"), ("l_props_max", "Propriedades"), ("l_vigor", "Vigor/atk"), ("l_dt", "DT")]):
                tk.Label(g, text=t.upper(), bg=cor, fg=TINTA2, font=(FONTE, 7, "bold")).grid(row=0, column=j, sticky="w", padx=(0, 18))
                ui[k] = Rot(g, bg=cor, size=10)
                ui[k].grid(row=1, column=j, sticky="w", padx=(0, 18))
            ui["l_req"] = Rot(f, bg=cor, size=9, wraplength=900, justify="left")
            ui["l_req"].pack(anchor="w", pady=(4, 0))
            pr = tk.Frame(f, bg=cor)
            pr.pack(fill="x", pady=(2, 0))
            tk.Label(pr, text="Propriedades:", bg=cor, fg=TINTA2, font=(FONTE, 9)).pack(side="left")
            self.ed(ttk.Entry(pr, textvariable=ui["props"], width=60)).pack(side="left", padx=6)
            self.armas_ui.append(ui)
        self.l_duplo = Rot(c, size=9, bold=False, wraplength=980, justify="left")
        self.l_duplo.grid(row=2, column=0, sticky="w", pady=(4, 0))

        c = self.secao(p, "Armadura e escudo", row=1, column=0, columnspan=2)
        self.arm = {"armadura": self.var(), "escudo": self.var(), "ca_extra": self.var(), "peitoral_set": self.var(False, tk.BooleanVar)}
        self.arm_ui = {}
        self.cabecalho(c, ["", "Equipamento", "CA", "Peso", "Requisito", ""], C_CA)
        c.columnconfigure(4, weight=1)
        for r, (n, chave) in enumerate([("Armadura", "armadura"), ("Escudo", "escudo")], start=1):
            tk.Label(c, text=n, bg=PERG, fg=TINTA, font=(FONTE, 10, "bold")).grid(row=r, column=0, sticky="w", padx=6)
            disp = tk.StringVar()
            cb = self.ed(ttk.Combobox(c, textvariable=disp, width=46, state="readonly"))
            cb.configure(postcommand=lambda cb=cb, k=chave: self._valores_protecao(cb, k))
            cb.bind("<<ComboboxSelected>>", lambda e, k=chave: self._escolher_protecao(k))
            cb.grid(row=r, column=1, padx=2, pady=3, sticky="w")
            ui = {"disp": disp, "l_ca": Rot(c, size=12), "l_peso": Rot(c, size=10), "l_req": Rot(c, size=9, bold=False, wraplength=380, justify="left")}
            ui["l_ca"].grid(row=r, column=2, padx=8)
            ui["l_peso"].grid(row=r, column=3, padx=8)
            ui["l_req"].grid(row=r, column=4, sticky="w", padx=6)
            self.arm_ui[chave] = ui
        self.ed(ttk.Checkbutton(c, text="Peitoral de set (não exige o nível de jogador)", variable=self.arm["peitoral_set"])).grid(row=1, column=5, sticky="w", padx=6)
        ttk.Label(c, text="Outros bônus de CA", style="Rot.TLabel").grid(row=3, column=0, sticky="w", padx=6, pady=(6, 0))
        self.ed(ttk.Spinbox(c, from_=-10, to=10, textvariable=self.arm["ca_extra"], width=4)).grid(row=3, column=1, sticky="w", padx=2, pady=(6, 0))
        self.l_ca_total = Rot(c, size=10)
        self.l_ca_total.grid(row=3, column=2, columnspan=4, sticky="w", pady=(6, 0))

        c = self.secao(p, "Talismãs", row=2, column=0)
        self.cabecalho(c, ["", "Talismã", "Efeito"], C_TAL)
        c.columnconfigure(2, weight=1)
        self.talismas = []
        for r in range(7):
            t = {"nome": self.var(), "efeito": self.var(), "disp": tk.StringVar()}
            tk.Label(c, text="✦", bg=PERG, fg=OURO, font=(FONTE, 9)).grid(row=r + 1, column=0, padx=4, sticky="n", pady=4)
            cb = ttk.Combobox(c, textvariable=t["disp"], width=30, state="readonly")
            cb.configure(postcommand=lambda cb=cb, i=r: self._valores_talisma(cb, i))
            cb.bind("<<ComboboxSelected>>", lambda e, i=r: self._escolher_talisma(i))
            cb.grid(row=r + 1, column=1, sticky="nw", padx=2, pady=2)
            lab = Rot(c, size=9, bold=False, wraplength=300, justify="left")
            lab.grid(row=r + 1, column=2, sticky="w", padx=6, pady=2)
            t["widgets"] = (cb,)
            t["l_efeito"] = lab
            self.talismas.append(t)
        self.l_talism_inv = Rot(c, fg=TINTA2, size=9, bold=False, italic=True, wraplength=460, justify="left")
        self.l_talism_inv.grid(row=9, column=0, columnspan=3, sticky="w", pady=(4, 0))

        c = self.secao(p, "Peças de set", row=2, column=1)
        self.cabecalho(c, ["Peça", "Set", "Nome da peça"], C_ATR)
        c.columnconfigure(2, weight=1)
        self.set_pecas = {}
        nomes_sets = ["— sem set —"] + sorted(x["nome"] for x in self.dados.get("sets", []))
        for r, peca in enumerate(["Capacete", "Peitoral", "Manopla", "Calça", "Bota", "Arma"], start=1):
            sp = {"set": self.var(), "nome": self.var()}
            tk.Label(c, text=peca, bg=PERG, fg=TINTA, font=(FONTE, 10, "bold"), anchor="w").grid(row=r, column=0, sticky="w", padx=6)
            self.ed(ttk.Combobox(c, values=nomes_sets, textvariable=sp["set"], width=18, state="readonly")).grid(row=r, column=1, padx=2, pady=2)
            self.ed(ttk.Entry(c, textvariable=sp["nome"])).grid(row=r, column=2, padx=2, pady=2, sticky="we")
            self.set_pecas[peca] = sp
        self.l_sets = Rot(c, size=9, bold=False, wraplength=460, justify="left")
        self.l_sets.grid(row=8, column=0, columnspan=3, sticky="w", pady=(6, 0))

        c = self.secao(p, "Inventário geral", row=3, column=0, columnspan=2)
        self.l_carga_inv = Rot(c, size=10)
        self.l_carga_inv.grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 6))
        self.cabecalho(c, ["Item", "Carga"], PERG2, row=1, col0=0)
        self.cabecalho(c, ["Item", "Carga"], PERG2, row=1, col0=3)
        tk.Frame(c, width=24, bg=PERG).grid(row=1, column=2)
        c.columnconfigure(0, weight=1)
        c.columnconfigure(3, weight=1)
        self.inv = []
        for i in range(30):
            it = {"item": self.var(), "carga": self.var()}
            r, cc = 2 + i % 15, (i // 15) * 3
            ttk.Entry(c, textvariable=it["item"]).grid(row=r, column=cc, padx=(0, 2), pady=1, sticky="we")
            ttk.Entry(c, textvariable=it["carga"], width=6).grid(row=r, column=cc + 1, padx=2, pady=1)
            self.inv.append(it)
        self.v_dinheiro = self.var()
        dn = tk.Frame(c, bg=C_DIN, padx=8, pady=4)
        dn.grid(row=18, column=3, columnspan=2, sticky="we", pady=(8, 0))
        tk.Label(dn, text="Dinheiro atual", bg=C_DIN, fg=FAIXA, font=(FONTE, 10, "bold")).pack(side="left")
        ttk.Entry(dn, textvariable=self.v_dinheiro, width=16).pack(side="right")

    # ------------------------------------------------------------ V · Encantamentos
    def _pag_encantamentos(self):
        p = ttk.Frame(self.nb, padding=(22, 10, 22, 16), style="Pagina.TFrame")
        self.nb.add(p, text="V · Encantamentos")
        p.columnconfigure(0, weight=5)
        p.columnconfigure(1, weight=3)
        p.rowconfigure(2, weight=1)
        c = self.secao(p, "Encantamentos", row=0, column=0, columnspan=2, pady=(4, 2))
        self.l_enc_esp, _ = self.caixa(c, "Espaços", C_MANA, 0, 0, sub=False, larg=14, big=15)
        self.l_enc_dt, _ = self.caixa(c, "DT dos encantamentos", C_ATR, 0, 1, sub=False, larg=26, big=12)
        self.l_enc_dados, _ = self.caixa(c, "Dados extras de dano", C_ATR, 0, 2, sub=False, larg=26, big=12)
        self.l_enc_contra, _ = self.caixa(c, "Contra-encantos", C_ATR, 0, 3, sub=False, larg=16, big=15)

        add = self.secao(p, "Filtros", row=1, column=0, columnspan=2, pady=(4, 2))
        self.sec_filtros = add.master
        tiers = sorted({v["tier"] for e in self.dados["encantamentos"] for v in e["versoes"]})
        self.f_enc = {"dom": tk.StringVar(value="Todos"), "cat": tk.StringVar(value="Todas"), "tipo": tk.StringVar(value="Todos"),
                      "nv_min": tk.StringVar(value="1"), "nv_max": tk.StringVar(value="10"), "mana": tk.StringVar(value=""),
                      "esp": tk.StringVar(value="Todos"), "sit": tk.StringVar(value="Todos"), "busca": tk.StringVar()}
        for v in self.f_enc.values():
            v.trace_add("write", lambda *a: self._atualizar_catalogo(forcar=True))
        def rot(t, r, c):
            ttk.Label(add, text=t, style="Rot.TLabel").grid(row=r, column=c, sticky="w", padx=(0, 4))
        rot("Domínio", 0, 0)
        ttk.Combobox(add, values=["Todos", "Magia", "Feitiço"], textvariable=self.f_enc["dom"], width=9, state="readonly").grid(row=0, column=1, padx=(0, 12))
        rot("Escola", 0, 2)
        self.cb_enc_cat = ttk.Combobox(add, textvariable=self.f_enc["cat"], width=26, state="readonly")
        self.cb_enc_cat.configure(postcommand=self._valores_cat_enc)
        self.cb_enc_cat.grid(row=0, column=3, padx=(0, 12))
        rot("Tipo", 0, 4)
        ttk.Combobox(add, values=["Todos"] + tiers, textvariable=self.f_enc["tipo"], width=10, state="readonly").grid(row=0, column=5, padx=(0, 12))
        rot("Situação", 0, 6)
        ttk.Combobox(add, values=["Todos", "Posso aprender", "Bloqueados", "Aprendidos"], textvariable=self.f_enc["sit"], width=15,
                     state="readonly").grid(row=0, column=7, padx=(0, 12))
        rot("Nível", 1, 0)
        nv = ttk.Frame(add)
        nv.grid(row=1, column=1, sticky="w", pady=(6, 0))
        ttk.Spinbox(nv, from_=1, to=10, textvariable=self.f_enc["nv_min"], width=3).pack(side="left")
        ttk.Label(nv, text=" a ", style="Rot.TLabel").pack(side="left")
        ttk.Spinbox(nv, from_=1, to=10, textvariable=self.f_enc["nv_max"], width=3).pack(side="left")
        rot("Buscar", 1, 2)
        ttk.Entry(add, textvariable=self.f_enc["busca"], width=28).grid(row=1, column=3, sticky="w", pady=(6, 0))
        rot("Mana até", 1, 4)
        ttk.Entry(add, textvariable=self.f_enc["mana"], width=6).grid(row=1, column=5, sticky="w", pady=(6, 0))
        rot("Espaço", 1, 6)
        ttk.Combobox(add, values=["Todos", "1", "2", "3", "4", "5"], textvariable=self.f_enc["esp"], width=6, state="readonly").grid(row=1, column=7, sticky="w", pady=(6, 0))
        ttk.Button(add, text="Limpar filtros", command=self._limpar_filtros_enc, style="Peq.TButton").grid(row=1, column=8, padx=6, pady=(6, 0))
        ttk.Label(add, text="Nível, mana e tipo usam a versão base (a primeira que se aprende). A busca procura no nome e na descrição.",
                  style="Sub.TLabel").grid(row=2, column=0, columnspan=9, sticky="w", pady=(4, 0))

        cat = self.secao(p, "Catálogo", row=2, column=0, pady=(6, 0))
        self.sec_catalogo = cat.master
        self.pag_enc = p
        cat.rowconfigure(0, weight=1)
        cat.columnconfigure(0, weight=1)
        cols = ("st", "dom", "esc", "tipo", "nv", "mana", "esp", "mot")
        self.tree_cat = ttk.Treeview(cat, columns=cols, show="tree headings", height=12)
        self.tree_cat.heading("#0", text="Nome")
        self.tree_cat.column("#0", width=170)
        for col, t, w in zip(cols, ["", "Domínio", "Escola", "Tipo", "Nv", "Mana", "Esp.", "Por que não"],
                             [24, 62, 140, 70, 34, 54, 40, 190]):
            self.tree_cat.heading(col, text=t)
            self.tree_cat.column(col, width=w, anchor="w", stretch=col in ("esc", "mot"))
        self.tree_cat.tag_configure("bloq", foreground=TINTA2)
        self.tree_cat.tag_configure("ok", foreground=TINTA)
        self.tree_cat.grid(row=0, column=0, sticky="nsew")
        sbc = ttk.Scrollbar(cat, command=self.tree_cat.yview)
        sbc.grid(row=0, column=1, sticky="ns")
        self.tree_cat.configure(yscrollcommand=sbc.set)
        self.tree_cat.bind("<<TreeviewSelect>>", lambda e: self._sel_cat())
        self.tree_cat.bind("<Double-1>", lambda e: self._aprender_enc())
        bc = ttk.Frame(cat)
        bc.grid(row=1, column=0, sticky="w", pady=6)
        ttk.Button(bc, text="Aprender selecionado", command=self._aprender_enc).pack(side="left")
        self.l_cat_cont = Rot(bc, fg=TINTA2, size=9, bold=False, italic=True)
        self.l_cat_cont.pack(side="left", padx=10)
        self._cat_assinatura = None

        dir_ = ttk.Frame(p)
        dir_.grid(row=2, column=1, sticky="nsew")
        dir_.columnconfigure(0, weight=1)
        dir_.rowconfigure(0, weight=1)
        dir_.rowconfigure(1, weight=1)
        lf = self.secao(dir_, "Grimório", row=0, column=0, pady=(6, 0))
        lf.rowconfigure(0, weight=1)
        lf.columnconfigure(0, weight=1)
        cols = ("nv", "mana", "equip", "esp", "conj")
        self.tree_enc = ttk.Treeview(lf, columns=cols, show="tree headings", height=6)
        self.tree_enc.heading("#0", text="Nome")
        self.tree_enc.column("#0", width=150)
        for col, t, w in zip(cols, ["Versões", "Mana", "Equip", "Esp.", "Conjurável"], [60, 50, 46, 40, 110]):
            self.tree_enc.heading(col, text=t)
            self.tree_enc.column(col, width=w, anchor="w")
        self.tree_enc.grid(row=0, column=0, sticky="nsew")
        self.tree_enc.bind("<<TreeviewSelect>>", lambda e: self._sel_tree_enc())
        bts = ttk.Frame(lf)
        bts.grid(row=1, column=0, sticky="w", pady=6)
        ttk.Button(bts, text="Equipar", command=self._toggle_equip_enc, style="Peq.TButton").pack(side="left", padx=(0, 4))
        self.ed(ttk.Button(bts, text="Próxima versão", command=self._aprender_versao, style="Peq.TButton")).pack(side="left", padx=4)
        self.ed(ttk.Button(bts, text="Remover", command=self._remover_enc, style="Peq.TButton")).pack(side="left", padx=4)
        ttk.Button(bts, text="🎲 Conjurar", command=lambda: self.conjurar_menu(self._sel_enc()["familia"] if self._sel_enc() else None),
                   style="Peq.TButton").pack(side="left", padx=4)

        df = self.secao(dir_, "Página do tomo", row=1, column=0, pady=(6, 0))
        df.rowconfigure(0, weight=1)
        df.columnconfigure(0, weight=1)
        self.txt_enc = self.texto(df, height=8, spacing1=2, spacing3=2)
        self.txt_enc.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(df, command=self.txt_enc.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.txt_enc.configure(yscrollcommand=sb.set)
        self.txt_enc.tag_configure("t", font=(FONTE_TIT, 15, "bold"), foreground=VINHO)
        self.txt_enc.tag_configure("ok", foreground=VERDE, font=(FONTE, 10, "bold"))
        self.txt_enc.tag_configure("erro", foreground=VINHO, font=(FONTE, 10, "bold"))

        self._dica_enc = Dica(self, self.tree_cat, lambda iid: self._texto_dica(self._cat_map.get(iid)))
        self._dica_grim = Dica(self, self.tree_enc, lambda iid: self._texto_dica(self.tree_enc.item(iid, "text"), aprendido=True))
        self._cat_map = {}

    # ------------------------------------------------------------ VI · Talentos
    def _pag_talentos(self):
        p = self._pagina("VI · Talentos")
        p.columnconfigure(0, weight=1)
        c = self.secao(p, "Talentos  ·  um a cada nível par", row=0, column=0)
        self.cabecalho(c, ["Nv", "Categoria", "Talento", "Efeito", "", "Situacional"], C_ATR)
        c.columnconfigure(3, weight=1)
        self.tal_ui = {}
        slots = [str(n) for n in range(2, 31, 2)] + ["extra"]
        for r, s in enumerate(slots, start=1):
            ui = {"nome": self.var(), "disp": tk.StringVar(), "cat": tk.StringVar(value="Todas")}
            lab = tk.Label(c, text=s if s != "extra" else "✦", bg=PERG, fg=VINHO, font=(FONTE, 10, "bold"), width=4)
            lab.grid(row=2 * r - 1, column=0, sticky="nw", pady=3)
            cc = ttk.Combobox(c, values=["Todas", "Disponíveis"] + self.categorias_tal, textvariable=ui["cat"], width=22, state="readonly")
            cc.grid(row=2 * r - 1, column=1, padx=3, pady=3, sticky="nw")
            ct = ttk.Combobox(c, textvariable=ui["disp"], width=58, state="readonly")
            ct.configure(postcommand=lambda cb=ct, sl=s: self._valores_talento(cb, sl))
            ct.bind("<<ComboboxSelected>>", lambda e, sl=s: self._escolher_talento(sl))
            ct.grid(row=2 * r - 1, column=2, padx=3, pady=3, sticky="nw")
            le = Rot(c, size=9, bold=False, wraplength=420, justify="left")
            le.grid(row=2 * r - 1, column=3, sticky="nw", padx=6, pady=3)
            self.ed(ttk.Button(c, text="✕", width=3, command=lambda sl=s: self._limpar_talento(sl), style="Peq.TButton")).grid(row=2 * r - 1, column=4, sticky="n", pady=3)
            ui["ativo"] = self.var(False, tk.BooleanVar)
            sw = ttk.Checkbutton(c, text="ativo agora", variable=ui["ativo"])
            sw.grid(row=2 * r - 1, column=5, sticky="nw", padx=(6, 0), pady=3)
            sw.grid_remove()
            self.linha(c, 2 * r, 6)
            ui.update(lbl=lab, cb_cat=cc, cb=ct, efeito=le, sw=sw)
            self.tal_ui[s] = ui
        ttk.Label(c, text="✦  slot extra do talento Versátil (talento de nível 8 ou menor)  ·  talentos com efeito numérico entram sozinhos nos cálculos; "
                          "os situacionais só quando \"ativo agora\" estiver marcado", style="Sub.TLabel").grid(row=40, column=0, columnspan=6, sticky="w", pady=(4, 0))

        c = self.secao(p, "Vínculos e metas", row=1, column=0)
        c.columnconfigure(1, weight=1)
        self.v_vinc_grupo, self.v_vinc_mundo, self.v_metas = self.var(), self.var(), self.var()
        self.v_esp_notas = self.var()
        for r, (t, v) in enumerate([("Vínculo (grupo)", self.v_vinc_grupo), ("Vínculo (mundo)", self.v_vinc_mundo), ("Metas de Vida", self.v_metas),
                                    ("Notas da espécie", self.v_esp_notas)]):
            tk.Label(c, text=t, bg=PERG, fg=TINTA, font=(FONTE, 10, "bold"), anchor="w", width=16).grid(row=r, column=0, sticky="w", pady=3)
            ttk.Entry(c, textvariable=v).grid(row=r, column=1, sticky="we", pady=3)

    def _txt_mod(self, e):
        e.widget.edit_modified(False)

    # ============================================================ estado
    def nivel(self):
        return max(1, min(R.NIVEL_MAX, to_int(self.v_nivel.get(), 1)))

    def atributos_efetivos(self, com_manual=True):
        a = {}
        tb = self.bonus_talismas()
        for k, row in self.atr.items():
            a[k] = (to_int(row["inicial"].get()) + to_int(row["niveis"].get()) + to_int(row["especie"].get())
                    + to_int(row["bonus"].get()) + tb.get(k, 0))
            if com_manual and k in self.manual:
                a[k] = self.manual[k]
        return a

    def talentos_ativos(self):
        """Talentos situacionais com o interruptor "ativo agora" ligado."""
        return {ui["nome"].get() for ui in self.tal_ui.values()
                if ui["nome"].get() and ui["ativo"].get() and R.EFEITOS_TALENTOS.get(ui["nome"].get(), {}).get("tipo") == "sit"}

    def aplicar_efeitos(self, d, ef, manual=None):
        """Soma os efeitos de talento e os valores manuais de Vida/Mana às características derivadas."""
        d["ca"] = max(10, min(25, d["ca"] + ef["ca"]))
        d["movimento"] += ef["mov"]
        d["iniciativa_bonus"] += ef["iniciativa"]
        d["descoberta"] += ef["descoberta"]
        d["contra_encant"] += ef["contra"]
        manual = self.manual if manual is None else manual
        d["vida_auto"], d["mana_auto"] = d["vida"], d["mana"]
        if "vida" in manual:
            d["vida"] = manual["vida"]
        if "mana" in manual:
            d["mana"] = manual["mana"]
        return d

    def _so_edicao(self, oque="Isso"):
        """No Modo Jogo, avisa e devolve True (quem chamou deve parar)."""
        if self.modo == "edicao":
            return False
        messagebox.showinfo(APP_NOME, f"{oque} só pode ser mudado no Modo Edição.\n\nUse o botão \"✎ Modo Edição\" no topo.")
        return True

    def alternar_modo(self):
        self.modo = "jogo" if self.modo == "edicao" else "edicao"
        self._aplicar_modo()
        self.recalc()

    def _aplicar_modo(self):
        """Modo Jogo: só o que se usa na mesa. Modo Edição: criar, subir de nível, escolher e aprender."""
        ed = self.modo == "edicao"
        for w in self.so_edicao:
            try:
                if isinstance(w, tk.Text):
                    w.configure(state="normal" if ed else "disabled")
                elif isinstance(w, ttk.Combobox):
                    w.state(["!disabled", "readonly"] if ed else ["disabled"])
                else:
                    w.state(["!disabled"] if ed else ["disabled"])
            except tk.TclError:
                pass
        for sec in (getattr(self, "sec_filtros", None), getattr(self, "sec_catalogo", None)):
            if sec is not None:
                (sec.grid if ed else sec.grid_remove)()
        if getattr(self, "pag_enc", None) is not None:
            self.pag_enc.columnconfigure(0, weight=5 if ed else 0)
        self.bt_modo.configure(text="⚔ Modo Jogo" if ed else "✎ Modo Edição")
        self.lbl_modo.configure(text="✎ MODO EDIÇÃO — criar, subir de nível, escolher e aprender" if ed else
                                "⚔ MODO JOGO — use na mesa; para mudar a ficha, Modo Edição")

    def editar_manual(self, chave):
        if self._so_edicao("O valor manual"):
            return
        """Janela para digitar um valor que substitui o calculado (atributo, Vida máx. ou Mana máx.)."""
        nomes = dict(R.NOMES_ATR, vida="Vida máxima", mana="Mana máxima")
        if chave in R.ATRIBUTOS:
            auto = self.atributos_efetivos(com_manual=False)[chave]
        else:
            auto = self.d.get(chave + "_auto", self.d.get(chave, 0))
        w = tk.Toplevel(self)
        w.title(f"{nomes[chave]} — valor manual")
        w.configure(background=PERG)
        w.transient(self)
        w.resizable(False, False)
        f = tk.Frame(w, bg=PERG, padx=22, pady=16)
        f.pack()
        tk.Label(f, text=nomes[chave], bg=PERG, fg=VINHO, font=(FONTE_TIT, 14, "bold")).grid(row=0, column=0, columnspan=3, sticky="w")
        tk.Label(f, text=f"Calculado pela ficha: {auto}", bg=PERG, fg=TINTA2, font=(FONTE, 10, "italic")).grid(row=1, column=0, columnspan=3, sticky="w", pady=(2, 10))
        tk.Label(f, text="Valor que você rolou ou definiu:", bg=PERG, fg=TINTA, font=(FONTE, 11)).grid(row=2, column=0, sticky="w")
        v = tk.StringVar(value=str(self.manual.get(chave, auto)))
        e = ttk.Entry(f, textvariable=v, width=8, font=(FONTE, 13))
        e.grid(row=2, column=1, padx=8)
        e.focus_set()
        e.select_range(0, "end")
        msg = tk.Label(f, text="", bg=PERG, fg=VINHO, font=(FONTE, 10, "bold"))
        msg.grid(row=3, column=0, columnspan=3, sticky="w", pady=(6, 0))

        def ok(*_):
            try:
                n = int(str(v.get()).strip())
            except ValueError:
                msg.configure(text="Digite um número inteiro.")
                return
            if n < 0:
                msg.configure(text="O valor não pode ser negativo.")
                return
            self.manual[chave] = n
            w.destroy()
            self.agendar_forcado()

        def auto_():
            self.manual.pop(chave, None)
            w.destroy()
            self.agendar_forcado()
        e.bind("<Return>", ok)
        bt = tk.Frame(f, bg=PERG)
        bt.grid(row=4, column=0, columnspan=3, sticky="e", pady=(12, 0))
        ttk.Button(bt, text="Cancelar", command=w.destroy, style="Peq.TButton").pack(side="right")
        ttk.Button(bt, text="Voltar ao automático", command=auto_).pack(side="right", padx=6)
        ttk.Button(bt, text="Usar este valor", command=ok).pack(side="right")
        w.grab_set()

    def agendar_forcado(self):
        """Marca alteração e recalcula (para mudanças que não passam por uma variável Tk)."""
        if self.inicializado:
            self.alterado = True
            self._titulo()
        self.recalc()

    # ------------------------------------------------------------ talismãs / armadura / sets
    def bonus_talismas(self):
        out = {}
        if not hasattr(self, "talismas"):
            return out
        vagas = R.slots_talismas(self.nivel(), self.talentos_escolhidos())
        for t in self.talismas[:vagas]:
            info = self.tal_info.get(t["nome"].get())
            if info:
                for k, v in info.get("bonus", {}).items():
                    out[k] = out.get(k, 0) + v
        return out

    def _valores_talisma(self, cb, i):
        outros = {self.tal_info[t["nome"].get()]["familia"] for j, t in enumerate(self.talismas)
                  if j != i and t["nome"].get() in self.tal_info}
        vagas = self.d.get("talismas", 1)
        vals = ["— vazio —"]
        for t in self.dados.get("talismas", []):
            m = []
            if t["familia"] in outros and "Relicário" not in self.talentos_escolhidos():
                m.append("já há um da mesma família")
            if i >= vagas:
                m.append(f"só {vagas} espaço(s) de talismã")
            vals.append(f"{OK} {t['nome']}" if not m else f"{NO} {t['nome']}  — {', '.join(m)}")
        cb.configure(values=[vals[0]] + ordenar(vals[1:]))

    def _escolher_talisma(self, i):
        t = self.talismas[i]
        txt = t["disp"].get()
        if txt.startswith("—"):
            t["nome"].set("")
            t["efeito"].set("")
            t["disp"].set("")
            return
        nome = self._nome_de(txt)
        if txt.startswith(NO):
            messagebox.showinfo(APP_NOME, f"Não dá para equipar {nome}:\n\n{txt.split('—', 1)[-1].strip()}")
            t["disp"].set(t["nome"].get())
            return
        t["nome"].set(nome)
        t["efeito"].set(self.tal_info.get(nome, {}).get("efeito", ""))
        t["disp"].set(nome)

    def _protecao(self, chave):
        tab = self.dados.get("armaduras" if chave == "armadura" else "escudos", [])
        return next((x for x in tab if x["nome"] == self.arm[chave].get()), None)

    def _status_protecao(self, chave, item):
        a = self.a if hasattr(self, "a") else self.atributos_efetivos()
        m = []
        forca = max(R.cap(a["FOR"]), R.cap(a["TEN"]))
        if item["req"] and forca < item["req"]:
            m.append(f"{item['req']} de Força ou Tenacidade (tem {forca})")
        if chave == "armadura" and not self.arm["peitoral_set"].get() and self.nivel() < item["nivel"]:
            m.append(f"nível {item['nivel']}")
        if chave == "escudo":
            armas = [self.armas_por_nome.get(g) for g in self.armas_equipadas()]
            if len([x for x in armas if x]) >= 2:
                m.append("as duas mãos estão com armas")
            if "Lança-Arma" in self.armas_equipadas():
                m.append("Lança-Arma já tem escudo")
        return m

    def _valores_protecao(self, cb, chave):
        tab = self.dados.get("armaduras" if chave == "armadura" else "escudos", [])
        vals = []
        for x in tab:
            desc = f"{x['nome']}  (CA +{x['ca']}, peso {x['peso']}" + (f", nv {x['nivel']}" if chave == "armadura" else "") + ")"
            m = self._status_protecao(chave, x)
            vals.append(f"{OK} {desc}" if not m else f"{NO} {desc}  — {', '.join(m)}")
        cb.configure(values=["— nenhuma —" if chave == "armadura" else "— nenhum —"] + ordenar(vals))

    def _escolher_protecao(self, chave):
        ui = self.arm_ui[chave]
        txt = ui["disp"].get()
        if txt.startswith("—"):
            self.arm[chave].set("")
            ui["disp"].set("")
            return
        nome = self._nome_de(txt)
        if txt.startswith(NO):
            messagebox.showinfo(APP_NOME, f"Você ainda não pode usar {nome}:\n\n{txt.split('—', 1)[-1].strip()}")
            ui["disp"].set(self.arm[chave].get())
            return
        self.arm[chave].set(nome)
        ui["disp"].set(nome)

    def ca_peso_protecao(self):
        arm, esc = self._protecao("armadura"), self._protecao("escudo")
        return ((arm or {}).get("ca", 0), (esc or {}).get("ca", 0), (arm or {}).get("peso", 0), (esc or {}).get("peso", 0))

    def sets_ativos(self):
        cont = {}
        for sp in self.set_pecas.values():
            n = sp["set"].get()
            if n and not n.startswith("—"):
                cont[n] = cont.get(n, 0) + 1
        info = {x["nome"]: x for x in self.dados.get("sets", [])}
        out = []
        for n, q in sorted(cont.items(), key=lambda x: -x[1]):
            if q >= 2 and n in info:
                out.append((n, q, info[n]["p2"], info[n]["p4"] if q >= 4 else ""))
        return cont, out

    def talentos_escolhidos(self):
        return {ui["nome"].get() for ui in self.tal_ui.values() if ui["nome"].get()}

    def pericias_treinadas(self):
        return {n for n, p in self.per.items() if p["var"].get()}

    def armas_equipadas(self):
        return [ui["grupo"].get() for ui in self.armas_ui if ui["grupo"].get()]

    def soma_dados_vida(self, n_dados):
        if self.v_vida_modo.get() == "media":
            return 7 * n_dados
        return sum(self.vida_rolagens[:n_dados])

    # ============================================================ recálculo
    def recalc(self):
        self._recalc_agendado = False
        nivel = self.nivel()
        a = self.atributos_efetivos()
        tal = self.talentos_escolhidos()
        n_vida = R.curva(a["VIT"]) + (3 if "Vida Dura" in tal else 0)
        d = R.derivadas(a, nivel, tal, self.soma_dados_vida(n_vida),
                        *self.ca_peso_protecao()[:2], to_int(self.arm["ca_extra"].get()))
        ef = R.efeitos_talentos(tal, self.talentos_ativos(), self.arm["armadura"].get())
        self.aplicar_efeitos(d, ef)
        self.d, self.a, self.ef = d, a, ef
        avisos = []

        # subida de nível
        if nivel > self.nivel_anterior and not self._carregando:
            self.after(50, lambda n0=self.nivel_anterior, n1=nivel: self._popup_nivel(n0, n1))
        self.nivel_anterior = nivel

        # atributos
        for k, row in self.atr.items():
            v = a[k]
            row["l_total"].configure(text=str(v) if row["inicial"].get() or v else "—", style="Erro.TLabel" if v > 99 or (v < 1 and row["inicial"].get()) else "Valor.TLabel")
            row["l_curva"].configure(text=f"Curva {d['curva'][k]}")
            row["l_bc"].configure(text=f"BC +{d['bc'][k]}")
            row["l_vant"].configure(text="· vantagem" if R.vantagem(v) else "")
            row["l_dados"].configure(text=f"{1 + R.cap(v) // 20}d20 em perícia" + ("  ·  ✎ manual" if k in self.manual else ""))
        ini_vals = [self.atr[k]["inicial"].get() for k in R.ATRIBUTOS]
        usados = [to_int(x) for x in ini_vals if x]
        faltam_ini = sorted(set(R.VALORES_INICIAIS) - set(usados), reverse=True)
        dup = sorted({x for x in usados if usados.count(x) > 1})
        disp = R.pontos_de_nivel(nivel, self.sem_alma)
        gastos = sum(to_int(self.atr[k]["niveis"].get()) for k in R.ATRIBUTOS)
        resto = disp - gastos
        total_pts = sum(R.VALORES_INICIAIS) + disp
        total_gasto = sum(usados) + gastos
        txt = f"Pontos de nível: {gastos}/{disp} gastos" + ("  (sem alma: +2 por nível)" if self.sem_alma else "")
        if resto > 0:
            txt += f"  —  FALTAM {resto} pontos para distribuir"
            avisos.append(("erro", f"Faltam {resto} pontos de atributo para distribuir (nível {nivel})"
                                   + (" — use o Modo Edição." if self.modo == "jogo" else ".")))
        elif resto < 0:
            txt += f"  —  EXCEDEU em {-resto} pontos"
            avisos.append(("erro", f"Você gastou {-resto} pontos de atributo a mais do que tem."))
        else:
            txt += "  —  tudo distribuído ✓"
        if faltam_ini:
            avisos.append(("erro", "Distribuição inicial: faltam os valores " + ", ".join(map(str, faltam_ini)) + "."))
        if dup:
            avisos.append(("erro", "Distribuição inicial: valores repetidos " + ", ".join(map(str, dup)) + "."))
        esp_soma = sum(to_int(self.atr[k]["especie"].get()) for k in R.ATRIBUTOS)
        if esp_soma != 0:
            avisos.append(("erro", f"Espécie: bônus e prejuízo deveriam se anular (soma atual {esp_soma:+d})."))
        for k in R.ATRIBUTOS:
            if a[k] > 99:
                avisos.append(("ok", f"{R.NOMES_ATR[k]} {a[k]}: acima de 99 conta como 99 nas tabelas."))
        self.lbl_pontos.configure(text=txt, style="Erro.TLabel" if resto else "Ok.TLabel")
        self.lbl_pontos_topo.configure(text=f"{total_gasto} / {total_pts}", fg=ALERTA if resto else OURO2)
        self.lbl_pontos_topo_sub.configure(text=(f"faltam {resto} para distribuir" if resto > 0 else
                                                  f"excedeu {-resto}" if resto < 0 else "tudo distribuído ✓"))

        # vida
        n_rol = len(self.vida_rolagens)
        self.l_vida.configure(text=str(d["vida"]) + ("✎" if "vida" in self.manual else ""))
        self.l_mana.configure(text=str(d["mana"]) + ("✎" if "mana" in self.manual else ""))
        for k in sorted(self.manual):
            nome = R.NOMES_ATR.get(k, {"vida": "Vida máx.", "mana": "Mana máx."}.get(k, k))
            avisos.append(("ok", f"{nome} está com valor manual ({self.manual[k]}); clique no número para voltar ao automático."))
        self.l_vigor.configure(text=str(d["vigor"]))
        self.l_vigor_regen.configure(text=f"O Vigor recupera {d['vigor_regen']} por turno (Curva da Força ÷ 4).")
        if self.v_vida_modo.get() == "rolar":
            falta = max(0, n_vida - n_rol)
            rol = self.vida_rolagens[:n_vida]
            self.l_vida_dados.configure(text=f"{n_vida} dados de vida • rolados: {min(n_rol, n_vida)} (soma {sum(rol)})"
                                             + (f" • FALTAM {falta} para rolar" if falta else "")
                                             + (f"\nRolagens: {', '.join(map(str, rol))}" if rol else ""))
            self.btn_rolar.state(["!disabled"] if falta else ["disabled"])
            if falta:
                avisos.append(("erro", f"Vida: role {falta} dado(s) de vida novo(s) (aba Personagem)."))
        else:
            self.l_vida_dados.configure(text=f"{n_vida} dados de vida × 7 = {7 * n_vida}  (+10 iniciais, +5 por nível acima do 1º)")
            self.btn_rolar.state(["disabled"])

        # características
        carga_atual = self._carga_atual()
        lim_lent = 0.6 if "Mochileiro" in tal else 0.5
        lentidao = carga_atual >= d["carga"] * lim_lent and carga_atual > 0
        exaustao = d["carga"] - carga_atual <= 10 and carga_atual > 0
        mov = min(6, d["movimento"]) if lentidao else d["movimento"]
        def cx(nome, big, sub=""):
            v, sl = self.caixas[nome]
            v.configure(text=big)
            if sl is not None:
                sl.configure(text=sub)
        cx("ca", str(d["ca"]), f"TEN +{d['ca_ten']}")
        cx("ca1", str(d["ca"]), f"TEN +{d['ca_ten']}")
        mov_txt, mov_sub = f"{mov} m", (f"{mov / 1.5:.0f} quadrados" + (" · Lentidão" if lentidao else ""))
        cx("mov", mov_txt, mov_sub)
        cx("mov1", mov_txt, mov_sub)
        cx("carga", str(d["carga"]), f"atual {carga_atual:g}")
        cx("ini", f"+{d['iniciativa_bonus']}", f"{d['iniciativa_dados']}d20, fica o maior")
        cx("acoes", str(d["acoes_extras"]), "Exaustão: só 1 de cada" if exaustao else "por DES")
        cx("rd", f"{d['rd']}d4" if d["rd"] else "—", "1d4 a cada 20 TEN")
        cx("desc", str(d["descoberta"]), "Arcano")
        n_tal = sum(1 for t in self.talismas if t["nome"].get().strip())
        cx("talism", f"{n_tal}/{d['talismas']}", "equipados")
        for nome, (lab, lim) in self.res_labels.items():
            tem = nome in d["resistencias"]
            lab.configure(text=f"{'☑' if tem else '☐'} {nome} {lim}", fg=VERDE if tem else TINTA2,
                          font=(FONTE, 9, "bold" if tem else "normal"))
        if lentidao:
            avisos.append(("erro", f"Carga {carga_atual:g}/{d['carga']}: Lentidão (movimento preso em 6m)."))
        if exaustao:
            avisos.append(("erro", "Carga: 10 ou menos espaços livres — Exaustão."))
        if carga_atual > d["carga"]:
            avisos.append(("erro", "Carga acima do máximo!"))
        if n_tal > d["talismas"]:
            avisos.append(("erro", f"Talismãs: {n_tal} equipados, limite {d['talismas']}."))
        for i, t in enumerate(self.talismas):
            for w in t["widgets"]:
                w.state(["!disabled", "readonly"] if (i < d["talismas"] or t["nome"].get()) and self.modo == "edicao" else ["disabled"])
            info = self.tal_info.get(t["nome"].get())
            t["l_efeito"].configure(text=(info or {}).get("efeito", t["efeito"].get()) if t["nome"].get() else "",
                                    style="Erro.TLabel" if (t["nome"].get() and i >= d["talismas"]) else "TLabel")
            if t["disp"].get() != t["nome"].get():
                t["disp"].set(t["nome"].get())
        tb = self.bonus_talismas()
        if tb:
            avisos.append(("ok", "Talismãs somando nos atributos: " + ", ".join(f"+{v} {R.NOMES_ATR[k]}" for k, v in tb.items()) + "."))
        fams = [self.tal_info[t["nome"].get()]["familia"] for t in self.talismas if t["nome"].get() in self.tal_info]
        if len(fams) != len(set(fams)) and "Relicário" not in tal:
            avisos.append(("erro", "Talismãs: dois da mesma família equipados."))
        # armadura / escudo
        ca_arm, ca_esc, p_arm, p_esc = self.ca_peso_protecao()
        for chave in ("armadura", "escudo"):
            ui, item = self.arm_ui[chave], self._protecao(chave)
            if ui["disp"].get() != self.arm[chave].get():
                ui["disp"].set(self.arm[chave].get())
            if not item:
                ui["l_ca"].configure(text="—")
                ui["l_peso"].configure(text="—")
                ui["l_req"].configure(text="", style="TLabel")
                continue
            m = self._status_protecao(chave, item)
            ui["l_ca"].configure(text=f"+{item['ca']}")
            ui["l_peso"].configure(text=str(item["peso"]))
            req = (f"{item['req']} FOR ou TEN" if item["req"] else "sem requisito de atributo") + (f" · nível {item['nivel']}" if chave == "armadura" else "")
            ui["l_req"].configure(text=req + (f"   {NO} {', '.join(m)}" if m else f"   {OK}"), style="Erro.TLabel" if m else "Ok.TLabel")
            if m:
                avisos.append(("erro", f"{item['nome']}: {', '.join(m)}."))
        arm = self._protecao("armadura")
        if arm and arm["req"] >= 30 and R.cap(a["TEN"]) < 40:
            avisos.append(("ok", f"{arm['nome']} sem 40 de Tenacidade: desvantagem em Acrobacia e Furtividade."))
        self.l_ca_total.configure(text=f"CA total {d['ca']}  =  10 + armadura {ca_arm} + escudo {ca_esc} + Tenacidade {d['ca_ten']}"
                                       + (f" + outros {to_int(self.arm['ca_extra'].get())}" if to_int(self.arm['ca_extra'].get()) else ""))
        # sets
        cont, ativos = self.sets_ativos()
        if ativos:
            linhas = []
            for n, q, e2, e4 in ativos:
                linhas.append(f"{n} ({q} peças) — 2 peças: {e2}" + (f"\n      4 peças: {e4}" if e4 else ""))
            self.l_sets.configure(text="\n".join(linhas), style="TLabel")
        else:
            self.l_sets.configure(text="Nenhum set ativo (2 peças do mesmo set ativam o primeiro efeito, 4 ativam o segundo).", style="TLabel")
        self.l_talism_inv.configure(text=f"Espaços de talismã: {d['talismas']} (1 + 1 a cada 6 níveis, máx. 5; talentos podem somar). Cada talismã pesa 1.")
        self.l_carga_inv.configure(text=f"Carga: {carga_atual:g} / {d['carga']}   (Lentidão a partir de {d['carga'] * lim_lent:g}; Exaustão com 10 ou menos livres)",
                                   style="Erro.TLabel" if (lentidao or exaustao) else "Titulo.TLabel")

        # perícias
        treinadas = self.pericias_treinadas()
        for nome, pinfo in self.per.items():
            atrs = pinfo["attrs"] or [self.v_prev_attr.get() or "ARC"]
            _, bonus, dados = R.pericia_fora(a, nivel, atrs, nome in treinadas)
            bonus += ef["pericia"].get(nome, 0)
            pinfo["bonus"].configure(text=f"+{bonus}" + ("*" if nome in ef["pericia"] else ""))
            pinfo["dados"].configure(text=f"{dados}d20")
        self.l_per_cont.configure(text=f"Treinadas fora de combate: {len(treinadas)}/{d['pericias_treinadas_max']}",
                                  style="Erro.TLabel" if len(treinadas) > d["pericias_treinadas_max"] else "Ok.TLabel")
        if len(treinadas) > d["pericias_treinadas_max"]:
            avisos.append(("erro", f"Perícias treinadas: {len(treinadas)} de {d['pericias_treinadas_max']} permitidas."))
        elif len(treinadas) < d["pericias_treinadas_max"]:
            avisos.append(("ok", f"Você pode treinar mais {d['pericias_treinadas_max'] - len(treinadas)} perícia(s) fora de combate."))

        # combate
        n3 = nivel // 3
        for n, atrs in R.PERICIAS_ATAQUE:
            partes = []
            for k in atrs:
                partes.append(f"+{d['bc'][k] + n3}" + (" (vant.)" if R.vantagem(a[k]) else "") + (f" [{k}]" if len(atrs) > 1 else ""))
            if self.ef["acerto"] and n in ("Luta", "Pontaria"):
                partes = [x + f" (+{self.ef['acerto']} talento)" for x in partes]
            self.l_atk[n].configure(text="  /  ".join(partes))
        bonus_def = {"Fortitude de Ferro", "Reflexos de Gato", "Mente Blindada", "Vontade Inabalável"}
        for n, k, tname in R.PERICIAS_DEFESA:
            extra = 2 if tname in tal else 0
            self.l_def[n].configure(text=f"+{d['bc'][k] + n3 + extra}" + (" (vant.)" if R.vantagem(a[k]) else ""))
        self.l_dts.configure(text=f"DT encantamentos/alma/armas: Feitiçaria {d['dt_feiticaria']} • Desejo {d['dt_desejo']}")
        self._recalc_armas(a, nivel, avisos)
        for i, b in enumerate(self.bt_rolar_arma):
            g = self.armas_ui[i]["grupo"].get()
            b.configure(text=f"🎲 {g} nv {self.armas_ui[i]['nivel'].get()}" if g else f"🎲 Arma {i + 1} (vazia)")
            b.state(["!disabled"] if g else ["disabled"])
        partes = []
        for nome in sorted(tal):
            e_ = R.EFEITOS_TALENTOS.get(nome)
            if not e_:
                continue
            if e_["tipo"] == "sit" and nome not in self.talentos_ativos():
                continue
            bits = [f"{'+' if v > 0 else ''}{v} {rot}" for k_, rot in (("ca", "CA"), ("mov", "m"), ("acerto", "acerto"), ("iniciativa", "iniciativa"),
                    ("descoberta", "Descoberta"), ("contra", "contra-encant."), ("dt_alma", "DT alma"), ("dano_nivel", "nível de dano"))
                    for v in [e_.get(k_, 0)] if v]
            bits += [f"+{v} {p_}" for p_, v in e_.get("pericia", {}).items()]
            partes.append(f"{nome}{' (ativo)' if e_['tipo'] == 'sit' else ''}: {', '.join(bits)}")
        self.l_ef_mestre.configure(text=("Do mestre — " + "  ·  ".join(
            f"{e['nome']} ({e['rodadas']} rodada(s))" if e.get("rodadas") else f"{e['nome']} (sem fim)" for e in self.efeitos_mestre))
            if self.efeitos_mestre else "")
        self.l_ef_ativos.configure(text=("Efeitos de talento em uso — " + "  ·  ".join(partes)) if partes else
                                   "Nenhum efeito de talento em uso. Talentos situacionais são ligados na aba Talentos (\"ativo agora\").")

        # encantamentos
        self._recalc_enc(a, nivel, avisos)

        # talentos
        self._recalc_talentos(a, nivel, avisos)

        # alma
        self.l_alma_nivel.configure(text=str(d["alma_nivel"]))
        k = self.alma["atr"].get() or "INT"
        self.l_alma_dt.configure(text=str(10 + d["bc"][k] + n3 + ef["dt_alma"]))
        self.l_alma_dt_sub.configure(text=f"10 + BC {k} + nível ÷ 3")
        self.l_alma_usos.configure(text=str(d["alma_usos"]))
        self.l_alma_ativas.configure(text=f"{d['alma_ativas']} + 1 passiva")

        # avisos
        self.txt_avisos.configure(state="normal")
        self.txt_avisos.delete("1.0", "end")
        erros = [x for x in avisos if x[0] == "erro"]
        if not erros:
            self.txt_avisos.insert("end", "✓ Nada pendente na ficha.\n\n", "ok")
        for tag, msg in erros + [x for x in avisos if x[0] == "ok"]:
            self.txt_avisos.insert("end", ("• " if tag == "erro" else "ℹ ") + msg + "\n", tag)
        self.txt_avisos.configure(state="disabled")

    def _carga_atual(self):
        tot = 0.0
        for it in self.inv:
            try:
                tot += float(str(it["carga"].get()).replace(",", ".") or 0)
            except ValueError:
                pass
        _, _, p_arm, p_esc = self.ca_peso_protecao()
        tot += p_arm + p_esc
        if "Veterano de Armadura" in self.talentos_escolhidos() and p_arm:
            tot -= 2
        tot += sum(1 for t in self.talismas if t["nome"].get().strip())
        for ui in self.armas_ui:
            g = ui["grupo"].get()
            if g in self.armas_por_nome:
                nv = to_int(ui["nivel"].get(), 1)
                linha = self._linha_arma(g, nv)
                if linha:
                    tot += linha["espaco"]
        return tot

    # ============================================================ armas
    def _linha_arma(self, grupo, nv):
        arma = self.armas_por_nome.get(grupo)
        if not arma:
            return None
        for l in arma["tabela"]:
            if l["nivel"] == nv:
                return l
        return None

    def _status_arma(self, grupo, nv):
        arma = self.armas_por_nome[grupo]
        mot = []
        if nv > self.d.get("max_nivel_arma", 1):
            mot.append(f"nível de personagem {2 * nv - 1}")
        mot += R.req_falta(R.req_arma(arma, nv), self.a)
        return mot

    def _valores_armas(self, cb, idx):
        vals = []
        for arma in self.dados["armas"]:
            m = self._status_arma(arma["nome"], 1)
            vals.append(f"{OK} {arma['nome']}" if not m else f"{NO} {arma['nome']}  — falta: {', '.join(m)}")
        cb.configure(values=ordenar(vals))

    def _escolher_arma(self, idx):
        ui = self.armas_ui[idx]
        txt = ui["disp_grupo"].get()
        nome = self._nome_de(txt)
        if txt.startswith(NO):
            messagebox.showinfo(APP_NOME, f"Você ainda não pode usar {nome}.\n\n{txt.split('—', 1)[-1].strip()}")
            ui["disp_grupo"].set(self._disp_arma(ui["grupo"].get()))
            return
        ui["grupo"].set(nome)
        nv = to_int(ui["nivel"].get(), 1)
        if self._status_arma(nome, nv):
            ui["nivel"].set("1")
        ui["disp_nivel"].set(f"Nível {ui['nivel'].get()}")
        ui["disp_grupo"].set(self._disp_arma(nome))

    def _disp_arma(self, nome):
        return nome or ""

    def _valores_nivel_arma(self, cb, idx):
        g = self.armas_ui[idx]["grupo"].get()
        if not g:
            cb.configure(values=[])
            return
        vals = []
        for nv in range(1, 11):
            m = self._status_arma(g, nv)
            l = self._linha_arma(g, nv)
            desc = f"Nível {nv}  ({l['dano']}, crít {l['critico']})" if l else f"Nível {nv}"
            vals.append(f"{OK} {desc}" if not m else f"{NO} {desc} — falta: {', '.join(m)}")
        cb.configure(values=ordenar(vals))

    def _escolher_nivel_arma(self, idx):
        ui = self.armas_ui[idx]
        txt = ui["disp_nivel"].get()
        nv = to_int(txt.split("Nível", 1)[1].split()[0], 1) if "Nível" in txt else 1
        if txt.startswith(NO):
            messagebox.showinfo(APP_NOME, f"Você ainda não pode usar este nível.\n\n{txt.split('—', 1)[-1].strip()}")
        else:
            ui["nivel"].set(str(nv))
        ui["disp_nivel"].set(f"Nível {ui['nivel'].get()}")

    def mostrar_acoes_arma(self, nome):
        arma = self.armas_por_nome.get(nome)
        if not arma:
            messagebox.showinfo(APP_NOME, "Escolha uma arma primeiro.")
            return
        w = tk.Toplevel(self)
        w.title(f"Ações — {nome}")
        w.configure(background=PERG)
        w.geometry("640x620")
        w.transient(self)
        t = self.texto(w, spacing1=3, spacing3=3)
        sb = ttk.Scrollbar(w, command=t.yview)
        t.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        t.pack(fill="both", expand=True, padx=12, pady=12)
        t.tag_configure("t", font=(FONTE_TIT, 16, "bold"), foreground=VINHO)
        t.tag_configure("n", font=(FONTE, 11, "bold"), foreground=VINHO)
        t.tag_configure("sub", lmargin1=24, lmargin2=24)
        t.tag_configure("d", foreground=TINTA2, font=(FONTE, 10, "italic"))
        t.insert("end", f"{nome}\n", "t")
        if arma.get("descricao"):
            t.insert("end", arma["descricao"] + "\n\n", "d")
        for a in arma.get("acoes", []):
            tags = ("sub",) if a.get("sub") else ()
            t.insert("end", ("↳ " if a.get("sub") else "") + a["nome"] + "\n", ("n",) + tags)
            t.insert("end", a["texto"] + "\n\n", tags)
        t.configure(state="disabled")

    def _remover_arma(self, idx):
        ui = self.armas_ui[idx]
        ui["grupo"].set("")
        ui["nivel"].set("1")
        ui["disp_grupo"].set("")
        ui["disp_nivel"].set("")

    def _recalc_armas(self, a, nivel, avisos):
        d = self.d
        reqs = []
        for i, ui in enumerate(self.armas_ui):
            g = ui["grupo"].get()
            labels = ["l_dano", "l_tipo", "l_acerto", "l_crit", "l_props_max", "l_peso", "l_vigor", "l_dt"]
            if g not in self.armas_por_nome:
                for k in labels:
                    ui[k].configure(text="—")
                ui["l_req"].configure(text="")
                reqs.append(None)
                continue
            arma = self.armas_por_nome[g]
            nv = to_int(ui["nivel"].get(), 1)
            l = self._linha_arma(g, nv)
            k = arma["ataque"]
            extra = R.cap(a[k]) // 30
            ui["l_dano"].configure(text=R.dano_com_dados(l["dano"], extra) + (f"  (+{extra} dado por {k})" if extra else ""))
            ui["l_tipo"].configure(text=l["tipo"])
            acerto = d["bc"][k] + nivel // 3 + R.ACERTO_ARMA.get(nv, 0) + self.ef["acerto"]
            ui["l_acerto"].configure(text=f"1d20 +{acerto}" + (" (2d20, maior)" if R.vantagem(a[k]) else "") + f"  [{k}]")
            ui["l_crit"].configure(text=str(l["critico"]))
            ui["l_props_max"].configure(text=str(l["propriedades"]))
            ui["l_peso"].configure(text=str(l["espaco"]))
            vig = 10 if nv >= 8 else 8 if nv >= 4 else 5
            ui["l_vigor"].configure(text=str(vig) if arma.get("vigor") else "—")
            ui["l_dt"].configure(text=str(10 + d["bc"][k] + nivel // 3))
            rq = R.req_arma(arma, nv)
            falta = self._status_arma(g, nv)
            ui["l_req"].configure(text="Requisitos: " + ", ".join(f"{v} {R.NOMES_ATR[x]}" for x, v in rq.items())
                                       + (f"   {NO} falta: {', '.join(falta)}" if falta else f"   {OK}"),
                                  style="Erro.TLabel" if falta else "Ok.TLabel")
            if falta:
                avisos.append(("erro", f"Arma {i + 1} ({g} nv {nv}): requisitos não cumpridos — {', '.join(falta)}."))
            reqs.append((arma, nv, rq))
        # uso duplo
        if reqs[0] and reqs[1]:
            (a1, n1, r1), (a2, n2, r2) = reqs
            if not (a1["uso_duplo"] and a2["uso_duplo"]):
                self.l_duplo.configure(text=f"{NO} {a1['nome'] if not a1['uso_duplo'] else a2['nome']} não permite uso duplo (Vigor, duas mãos ou escudo embutido). Use uma por vez.",
                                       style="Erro.TLabel")
            elif a1["nome"] == "Bastão" and a["DES"] < 50 or a2["nome"] == "Bastão" and a["DES"] < 50:
                self.l_duplo.configure(text=f"{NO} Bastão só entra em uso duplo com 50+ de Destreza.", style="Erro.TLabel")
            else:
                rq = R.req_uso_duplo(r1, r2)
                if "Empunhadura Folgada" in self.talentos_escolhidos():
                    rq = {k: max(v - 4, r1.get(k, 0), r2.get(k, 0)) for k, v in rq.items()}
                falta = R.req_falta(rq, a)
                dt = 8 + max(n1, n2)
                coord = d["bc"]["DES"] + nivel // 3 + (2 if "Mãos Gêmeas" in self.talentos_escolhidos() else 0)
                txt = (f"Requisitos combinados (maior + metade do outro): " + ", ".join(f"{v} {R.NOMES_ATR[k]}" for k, v in rq.items())
                       + (f"   {NO} falta: {', '.join(falta)}" if falta else f"   {OK} pode usar as duas")
                       + f"\nTeste de coordenação: 1d20 +{coord} (DES){' com vantagem' if R.vantagem(a['DES']) else ''} contra DT {dt}. "
                         "Falha: dano das armas cai 1 nível neste turno. Ataque da 2ª arma: ação bônus.")
                self.l_duplo.configure(text=txt, style="Erro.TLabel" if falta else "TLabel")
                if falta:
                    avisos.append(("erro", "Uso duplo: requisitos combinados não cumpridos — só pode usar uma arma por vez."))
        else:
            self.l_duplo.configure(text="Equipe duas armas para ver os requisitos combinados e o teste de coordenação.", style="TLabel")
        if nivel == 1 and any(g in ("Cajado", "Selo") for g in self.armas_equipadas()) and not self.encantamentos:
            avisos.append(("ok", "Começando com cajado/selo: o personagem pode começar com 3 encantamentos."))

    # ============================================================ encantamentos
    def _nome_de(self, txt):
        s = txt[2:] if txt[:1] in (OK, NO) else txt
        for sep in ("  —", " (Esp", "  (", " — "):
            if sep in s:
                s = s.split(sep, 1)[0]
        return s.strip()

    def _impl_inicial(self):
        return self.nivel() == 1 and any(g in ("Cajado", "Selo") for g in self.armas_equipadas())

    def _nivel_impl(self, dominio):
        alvo = "Cajado" if dominio == "Magia" else "Selo"
        nvs = [to_int(ui["nivel"].get(), 1) for ui in self.armas_ui if ui["grupo"].get() == alvo]
        return max(nvs) if nvs else 0

    def _valores_cat_enc(self):
        dom = self.f_enc["dom"].get()
        cats = [c for c in self.categorias_enc if dom == "Todos" or (dom == "Magia") == c.startswith("Magias")]
        self.cb_enc_cat.configure(values=["Todas"] + cats)

    def _limpar_filtros_enc(self):
        for k, v in {"dom": "Todos", "cat": "Todas", "tipo": "Todos", "nv_min": "1", "nv_max": "10", "mana": "",
                     "esp": "Todos", "sit": "Todos", "busca": ""}.items():
            self.f_enc[k].set(v)

    def _linhas_catalogo(self):
        f = {k: v.get() for k, v in self.f_enc.items()}
        busca = f["busca"].strip().lower()
        nv_min, nv_max = to_int(f["nv_min"], 1), to_int(f["nv_max"], 10)
        mana_max = to_int(f["mana"], -1) if f["mana"].strip() else None
        aprendidos = {e["familia"] for e in self.encantamentos}
        ok, bloq = [], []
        for e in self.dados["encantamentos"]:
            base = e["versoes"][0]
            if f["dom"] != "Todos" and e["dominio"] != f["dom"]:
                continue
            if f["cat"] != "Todas" and e["categoria"] != f["cat"]:
                continue
            if f["tipo"] != "Todos" and base["tier"] != f["tipo"]:
                continue
            if not (nv_min <= base["nivel"] <= nv_max):
                continue
            if mana_max is not None and (base.get("mana_num") or 0) > mana_max:
                continue
            if f["esp"] != "Todos" and e["espaco"] != to_int(f["esp"]):
                continue
            if busca and busca not in e["nome"].lower() and busca not in e["categoria"].lower() \
                    and not any(busca in v["descricao"].lower() for v in e["versoes"]):
                continue
            ja = e["nome"] in aprendidos
            m = ["já aprendido"] if ja else R.status_versao(base, e["dominio"], self.a, self.nivel(), self._impl_inicial())
            if f["sit"] == "Posso aprender" and m:
                continue
            if f["sit"] == "Bloqueados" and (not m or ja):
                continue
            if f["sit"] == "Aprendidos" and not ja:
                continue
            (bloq if m else ok).append((e, base, m))
        return ok + bloq

    def _atualizar_catalogo(self, forcar=False):
        if not hasattr(self, "tree_cat") or not hasattr(self, "a"):
            return
        linhas = self._linhas_catalogo()
        assin = tuple((e["nome"], tuple(m)) for e, _, m in linhas)
        if not forcar and assin == self._cat_assinatura:
            return
        self._cat_assinatura = assin
        sel = self._cat_map.get((self.tree_cat.selection() or [None])[0])
        self.tree_cat.delete(*self.tree_cat.get_children())
        self._cat_map = {}
        for i, (e, base, m) in enumerate(linhas):
            iid = self.tree_cat.insert("", "end", text=e["nome"], tags=("bloq" if m else "ok",),
                                       values=(NO if m else OK, e["dominio"], re.sub(r"^(Magias|Feitiços)( de| da| do)? ", "", e["categoria"]).capitalize(),
                                               base["tier"], base["nivel"], base.get("mana_num") or base["mana"], e["espaco"], ", ".join(m)))
            self._cat_map[iid] = e["nome"]
            if e["nome"] == sel:
                self.tree_cat.selection_set(iid)
        n_ok = sum(1 for _, _, m in linhas if not m)
        self.l_cat_cont.configure(text=f"{len(linhas)} encontrados · {n_ok} podem ser aprendidos agora")

    def _sel_cat(self):
        s = self.tree_cat.selection()
        if s and s[0] in self._cat_map:
            self._mostrar_enc(self._cat_map[s[0]])

    def _texto_dica(self, nome, aprendido=False):
        e = self.enc_por_nome.get(nome)
        if not e:
            return None
        x = next((y for y in self.encantamentos if y["familia"] == nome), None)
        vs = [v for v in e["versoes"] if x and v["nivel"] in x["versoes"]] if aprendido else []
        v = vs[-1] if vs else e["versoes"][0]
        desc = v["descricao"]
        if len(desc) > 700:
            desc = desc[:700].rsplit(" ", 1)[0] + "…"
        titulo = f"{e['nome']}  ·  {v['tier']} — Nível {v['nivel']}"
        corpo = (f"{e['dominio']} · {e['categoria']} · Espaço {e['espaco']}\n"
                 f"Mana {v['mana']}  ·  Ação {v['acao']}  ·  Distância {v['distancia']}\n"
                 f"Requisitos: {v['req_texto']}\n\n{desc}")
        return titulo, corpo

    def _mostrar_enc(self, nome):
        e = self.enc_por_nome.get(nome)
        t = self.txt_enc
        t.configure(state="normal")
        t.delete("1.0", "end")
        if not e:
            t.configure(state="disabled")
            return
        aprendido = next((x for x in self.encantamentos if x["familia"] == nome), None)
        t.insert("end", f"{e['nome']}\n", "t")
        t.insert("end", f"{e['dominio']} • {e['categoria']} • Espaço {e['espaco']} • {len(e['versoes'])} versão(ões)\n")
        if e["categoria"] == "Magias Lunares":
            t.insert("end", "Magias Lunares só estão disponíveis a partir do 2º andar.\n", "erro")
        t.insert("end", "\n")
        nimpl = self._nivel_impl(e["dominio"])
        for v in e["versoes"]:
            m = R.status_versao(v, e["dominio"], self.a, self.nivel(), self._impl_inicial())
            ja = aprendido and v["nivel"] in aprendido["versoes"]
            tag = "ok" if (ja or not m) else "erro"
            estado = "APRENDIDA" if ja else ("pode aprender" if not m else "bloqueada: " + ", ".join(m))
            t.insert("end", f"{v['tier']} — Nível {v['nivel']}{' (base)' if v['base'] else ''}   [{estado}]\n", tag)
            dt = 15 + 3 * (v["nivel"] - 1)
            impl = "Cajado" if e["dominio"] == "Magia" else "Selo"
            t.insert("end", f"Mana: {v['mana']} • Ação: {v['acao']} • Distância: {v['distancia']}\n"
                            f"Requisitos: {v['req_texto']} • Teste de aprendizado: DT {dt} • {impl} nv {v['nivel']}+ para conjurar"
                            f"{'' if nimpl >= v['nivel'] else f' (seu: {nimpl or 'nenhum'})'}\n")
            t.insert("end", f"{v['descricao']}\n\n")
        t.configure(state="disabled")

    def _aprender_enc(self):
        sel = self.tree_cat.selection()
        if not sel or sel[0] not in self._cat_map:
            messagebox.showinfo(APP_NOME, "Selecione um encantamento no catálogo.")
            return
        nome = self._cat_map[sel[0]]
        e = self.enc_por_nome[nome]
        if any(x["familia"] == nome for x in self.encantamentos):
            messagebox.showinfo(APP_NOME, f"{nome} já está no grimório.")
            return
        m = R.status_versao(e["versoes"][0], e["dominio"], self.a, self.nivel(), self._impl_inicial())
        if m:
            messagebox.showinfo(APP_NOME, f"Você ainda não pode aprender {nome}:\n\n" + ", ".join(m))
            return
        self.encantamentos.append({"familia": nome, "versoes": [e["versoes"][0]["nivel"]], "equipado": False})
        self._atualizar_tree_enc()
        self.agendar()
        self._mostrar_enc(nome)

    def _sel_enc(self):
        s = self.tree_enc.selection()
        if not s:
            return None
        try:
            nome = self.tree_enc.item(s[0], "text")
        except Exception:
            return None
        return next((x for x in self.encantamentos if x["familia"] == nome), None)

    def _sel_tree_enc(self):
        x = self._sel_enc()
        if x:
            self._mostrar_enc(x["familia"])

    def _toggle_equip_enc(self):
        x = self._sel_enc()
        if not x:
            return
        if not x["equipado"]:
            e = self.enc_por_nome[x["familia"]]
            usados = sum(self.enc_por_nome[y["familia"]]["espaco"] for y in self.encantamentos if y["equipado"])
            if usados + e["espaco"] > self.d["espacos_encant"]:
                messagebox.showinfo(APP_NOME, f"Sem espaço: {usados}/{self.d['espacos_encant']} usados, {x['familia']} ocupa {e['espaco']}.")
                return
        x["equipado"] = not x["equipado"]
        self._atualizar_tree_enc(x["familia"])
        self.agendar()

    def _aprender_versao(self):
        x = self._sel_enc()
        if not x:
            return
        e = self.enc_por_nome[x["familia"]]
        prox = [v for v in e["versoes"] if v["nivel"] not in x["versoes"]]
        if not prox:
            messagebox.showinfo(APP_NOME, "Todas as versões já foram aprendidas.")
            return
        v = prox[0]
        m = R.status_versao(v, e["dominio"], self.a, self.nivel())
        if m:
            messagebox.showinfo(APP_NOME, f"Próxima versão (Nível {v['nivel']}) bloqueada:\n\n" + ", ".join(m))
            return
        x["versoes"].append(v["nivel"])
        x["versoes"].sort()
        self._atualizar_tree_enc(x["familia"])
        self._mostrar_enc(x["familia"])
        self.agendar()

    def _remover_enc(self):
        x = self._sel_enc()
        if x and messagebox.askyesno(APP_NOME, f"Remover {x['familia']} da ficha?"):
            self.encantamentos.remove(x)
            self._atualizar_tree_enc()
            self.agendar()

    def _atualizar_tree_enc(self, selecionar=None):
        self.tree_enc.delete(*self.tree_enc.get_children())
        for x in self.encantamentos:
            e = self.enc_por_nome.get(x["familia"])
            if not e:
                continue
            nimpl = self._nivel_impl(e["dominio"])
            conj = []
            for v in e["versoes"]:
                if v["nivel"] in x["versoes"]:
                    ok = nimpl >= v["nivel"] and not [r for r in v["req_attrs"] if self.a[r["attr"]] < r["valor"]]
                    conj.append(f"{OK if ok else NO}{v['nivel']}")
            impl = "Cajado" if e["dominio"] == "Magia" else "Selo"
            vs = [v for v in e["versoes"] if v["nivel"] in x["versoes"]] or e["versoes"][:1]
            top = vs[-1]
            efeito = top["descricao"][:70] + ("…" if len(top["descricao"]) > 70 else "")
            iid = self.tree_enc.insert("", "end", text=x["familia"],
                                       values=(", ".join(map(str, x["versoes"])), top["mana"].replace(" Mana", ""), "✓" if x["equipado"] else "",
                                               e["espaco"], " ".join(conj) + ("" if nimpl else f" (sem {impl})")))
            if x["familia"] == selecionar:
                self.tree_enc.selection_set(iid)

    def _recalc_enc(self, a, nivel, avisos):
        d = self.d
        usados = sum(self.enc_por_nome[x["familia"]]["espaco"] for x in self.encantamentos if x["equipado"] and x["familia"] in self.enc_por_nome)
        self.l_enc_esp.configure(text=f"{usados}/{d['espacos_encant']}", style="Erro.TLabel" if usados > d["espacos_encant"] else "Valor.TLabel")
        self.l_enc_dt.configure(text=f"Feitiçaria {d['dt_feiticaria']} • Desejo {d['dt_desejo']}")
        self.l_enc_dados.configure(text=f"Magias +{d['dados_extra_magia']} • Feitiços +{d['dados_extra_feitico']}")
        self.l_enc_contra.configure(text=str(d["contra_encant"]))
        if usados > d["espacos_encant"]:
            avisos.append(("erro", f"Encantamentos equipados ocupam {usados} espaços; máximo {d['espacos_encant']}."))
        livres = d["espacos_encant"] - usados
        if livres > 0 and self.encantamentos:
            avisos.append(("ok", f"{livres} espaço(s) de encantamento livre(s)."))
        # novas versões disponíveis
        for x in self.encantamentos:
            e = self.enc_por_nome.get(x["familia"])
            if not e:
                continue
            for v in e["versoes"]:
                if v["nivel"] not in x["versoes"] and not R.status_versao(v, e["dominio"], a, nivel):
                    avisos.append(("ok", f"{x['familia']}: versão Nível {v['nivel']} já pode ser aprendida (DT {15 + 3 * (v['nivel'] - 1)})."))
                    break
        sel = self._sel_enc()
        self._atualizar_tree_enc(sel["familia"] if sel else None)
        self._atualizar_catalogo()

    # ============================================================ talentos
    def _slots_ordenados(self):
        return [str(n) for n in range(2, 31, 2)] + ["extra"]

    def _nivel_slot(self, s):
        return 8 if s == "extra" else int(s)

    def _status_tal(self, t, slot):
        slots = self._slots_ordenados()
        idx = slots.index(slot)
        antes = {self.tal_ui[s]["nome"].get() for s in slots[:idx] if self.tal_ui[s]["nome"].get()}
        if slot == "extra":
            antes = {self.tal_ui[s]["nome"].get() for s in slots[:-1] if self.tal_ui[s]["nome"].get() and self._nivel_slot(s) <= self.nivel()}
        outros = {self.tal_ui[s]["nome"].get() for s in slots if s != slot and self.tal_ui[s]["nome"].get()}
        m = R.status_talento(t, self._nivel_slot(slot), antes, self.a, self.pericias_treinadas(), self.armas_equipadas(), outros)
        if slot != "extra" and int(slot) > self.nivel():
            m.insert(0, f"slot do nível {slot}")
        return m

    def _valores_talento(self, cb, slot):
        cat = self.tal_ui[slot]["cat"].get()
        vals = []
        for t in self.dados["talentos"]:
            if cat not in ("Todas", "Disponíveis") and t["categoria"] != cat:
                continue
            m = self._status_tal(t, slot)
            if cat == "Disponíveis" and m:
                continue
            base = f"{t['nome']}  (Nv {t['nivel']}{' · ' + t['requisito'] if t['requisito'] else ''})"
            vals.append(f"{OK} {base}" if not m else f"{NO} {base}  — {', '.join(m)}")
        cb.configure(values=ordenar(vals))

    def _escolher_talento(self, slot):
        ui = self.tal_ui[slot]
        txt = ui["disp"].get()
        nome = self._nome_de(txt)
        if txt.startswith(NO):
            messagebox.showinfo(APP_NOME, f"Você não pode escolher {nome} neste slot:\n\n{txt.split('—', 1)[-1].strip()}")
            ui["disp"].set(ui["nome"].get())
            return
        ui["nome"].set(nome)
        ui["disp"].set(nome)

    def _limpar_talento(self, slot):
        self.tal_ui[slot]["nome"].set("")
        self.tal_ui[slot]["disp"].set("")

    def _recalc_talentos(self, a, nivel, avisos):
        tal = self.talentos_escolhidos()
        for s_, ui_ in self.tal_ui.items():
            ef_ = R.EFEITOS_TALENTOS.get(ui_["nome"].get())
            if ef_ and ef_["tipo"] == "sit":
                ui_["sw"].grid()
                ui_["sw"].configure(text="ativo agora" + (f" ({ef_['nota']})" if ef_.get("nota") else ""))
            else:
                ui_["sw"].grid_remove()
                if ui_["ativo"].get():
                    ui_["ativo"].set(False)
        for s, ui in self.tal_ui.items():
            if s == "extra":
                ativo = "Versátil" in tal
            else:
                ativo = int(s) <= nivel
            st = ["!disabled", "readonly"] if ativo and self.modo == "edicao" else ["disabled"]
            ui["cb"].state(st)
            ui["cb_cat"].state(st)
            nome = ui["nome"].get()
            t = self.tal_por_nome.get(nome)
            if t:
                m = self._status_tal(t, s)
                ef_t = R.EFEITOS_TALENTOS.get(nome)
                marca = ""
                if ef_t:
                    marca = "[aplicado na ficha] " if ef_t["tipo"] == "perm" else ("[ATIVO] " if ui["ativo"].get() else "[situacional] ")
                ui["efeito"].configure(text=(f"{NO} {', '.join(m)} — " if m else "") + marca + t["descricao"],
                                       style="Erro.TLabel" if m else "TLabel")
                if m:
                    avisos.append(("erro", f"Talento {nome} (nível {s}): requisito não cumprido — {', '.join(m)}."))
            else:
                ui["efeito"].configure(text="", style="TLabel")
                if ativo:
                    avisos.append(("erro", f"Talento do nível {s if s != 'extra' else 'extra (Versátil)'} ainda não escolhido."))

    # ============================================================ dados
    def _rng(self, faces):
        return random.randint(1, faces)

    def _atual(self, var, maximo):
        txt = str(var.get()).strip()
        return maximo if txt == "" else to_int(txt, maximo)

    def _pagar(self, var, maximo, custo, rotulo):
        """Desconta `custo` do recurso. Retorna (ok, texto). Pergunta antes de rolar sem recurso suficiente."""
        if not custo:
            return True, ""
        atual = self._atual(var, maximo)
        if atual < custo:
            if not messagebox.askyesno(APP_NOME, f"{rotulo} insuficiente: você tem {atual} e precisa de {custo}.\n\nRolar mesmo assim, sem descontar?"):
                return False, ""
            return True, f"{rotulo}: não descontado (tinha {atual}, custa {custo})"
        self.desfazer.append((var, var.get(), f"{custo} de {rotulo}"))
        var.set(str(atual - custo))
        return True, f"{rotulo}: −{custo} (restam {atual - custo})"

    def _txt_ataque(self, at):
        d20 = " e ".join(map(str, at["d20"])) + (" (fica o maior)" if len(at["d20"]) > 1 else "")
        txt = f"Acerto: {at['total']}  [d20 {d20} {'+' if at['bonus'] >= 0 else ''}{at['bonus']}]"
        if at["desastre"]:
            txt += "  — DESASTRE: erra sempre; o alvo pode atacar você como ação livre."
        elif at["garantido"]:
            txt += "  — 20 NATURAL: acerto garantido e crítico (dobra os dados)."
        elif at["critico"]:
            txt += "  — CRÍTICO: dobra os dados de dano (o acerto ainda compara com a CA)."
        return txt

    def _txt_dano(self, total, partes):
        detalhe = " ".join(f"{t}[{', '.join(map(str, v))}]" if v else t for t, v, _ in partes)
        return f"Dano: {total}  ({detalhe})"

    def rolar_arma(self, i):
        ui = self.armas_ui[i]
        arma = self.armas_por_nome.get(ui["grupo"].get())
        if not arma:
            messagebox.showinfo(APP_NOME, "Escolha uma arma primeiro (aba Inventário).")
            return
        self.recalc()
        nv = to_int(ui["nivel"].get(), 1)
        k = arma["ataque"]
        ef = self.ef
        nv_dano = min(10, nv + ef["dano_nivel"])
        linha = self._linha_arma(arma["nome"], nv)
        linha_dano = self._linha_arma(arma["nome"], nv_dano) or linha
        bonus = self.d["bc"][k] + self.nivel() // 3 + R.ACERTO_ARMA.get(nv, 0) + ef["acerto"]
        vig = (10 if nv >= 8 else 8 if nv >= 4 else 5) if arma.get("vigor") else 0
        ok, txt_custo = self._pagar(self.v_vigor_atual, self.d["vigor"], vig, "Vigor")
        if not ok:
            return
        at = R.rolar_ataque(bonus, R.vantagem(self.a[k]), to_int(linha["critico"], 20), self._rng)
        linhas = [self._txt_ataque(at)]
        if not at["desastre"]:
            expr = R.dano_com_dados(linha_dano["dano"], R.cap(self.a[k]) // 30)
            total, partes = R.rolar_expr(expr, self._rng, dobrar=at["critico"])
            linhas.append(self._txt_dano(total, partes) + f"  · {linha_dano['tipo']}" + (f"  · dano de nível {nv_dano} (talento)" if nv_dano != nv else ""))
        if txt_custo:
            linhas.append(txt_custo)
        if ef["acerto"]:
            linhas.append(f"Inclui +{ef['acerto']} de acerto de talento situacional.")
        self.registrar(f"⚔ {arma['nome']} nv {nv}", linhas, destaque=at["critico"] or at["desastre"])

    def rolar_iniciativa(self):
        self.recalc()
        n, b = self.d["iniciativa_dados"], self.d["iniciativa_bonus"]
        d = [self._rng(20) for _ in range(n)]
        self.registrar("⏳ Iniciativa", [f"Iniciativa: {max(d) + b}  [d20 {', '.join(map(str, d))} → {max(d)} +{b}]"])

    def conjurar_menu(self, familia=None):
        """Escolhe encantamento e versão para conjurar."""
        self.recalc()
        opcoes = []
        for x in self.encantamentos:
            e = self.enc_por_nome.get(x["familia"])
            if not e or (familia and x["familia"] != familia):
                continue
            for v in e["versoes"]:
                if v["nivel"] in x["versoes"]:
                    opcoes.append((e, v, x.get("equipado")))
        if not opcoes:
            messagebox.showinfo(APP_NOME, "Nenhum encantamento aprendido para conjurar." if not familia else "Selecione um encantamento no Grimório.")
            return
        if len(opcoes) == 1:
            self.conjurar(*opcoes[0][:2])
            return
        w = tk.Toplevel(self)
        w.title("Conjurar")
        w.configure(background=PERG)
        w.transient(self)
        f = tk.Frame(w, bg=PERG, padx=18, pady=14)
        f.pack(fill="both", expand=True)
        tk.Label(f, text="Qual encantamento?", bg=PERG, fg=VINHO, font=(FONTE_TIT, 13, "bold")).pack(anchor="w", pady=(0, 8))
        for e, v, eq in sorted(opcoes, key=lambda o: (not o[2], o[0]["nome"], o[1]["nivel"])):
            txt = f"{e['nome']} — {v['tier']} nv {v['nivel']} · {v['mana']}" + ("" if eq else "  (não equipado)")
            ttk.Button(f, text=txt, command=lambda e=e, v=v: (w.destroy(), self.conjurar(e, v))).pack(fill="x", pady=2)
        w.grab_set()

    def conjurar(self, e, v):
        self.recalc()
        k = "INT" if e["dominio"] == "Magia" else "FE"
        pericia = "Feitiçaria" if k == "INT" else "Desejo"
        avisos = []
        x = next((y for y in self.encantamentos if y["familia"] == e["nome"]), {})
        if not x.get("equipado"):
            avisos.append("Atenção: este encantamento não está equipado.")
        if self._nivel_impl(e["dominio"]) < v["nivel"]:
            avisos.append(f"Atenção: precisa de {'cajado' if k == 'INT' else 'selo'} de nível {v['nivel']} ou maior equipado.")
        ok, txt_custo = self._pagar(self.v_mana_atual, self.d["mana"], R.custo_mana(v), "Mana")
        if not ok:
            return
        bonus = self.d["bc"][k] + self.nivel() // 3
        at = R.rolar_ataque(bonus, R.vantagem(self.a[k]), 20, self._rng)
        dt = self.d["dt_feiticaria"] if k == "INT" else self.d["dt_desejo"]
        linhas = [f"{pericia}: " + self._txt_ataque(at).split(": ", 1)[1], f"DT para o alvo resistir: {dt}"]
        expr = R.dano_do_encantamento(v["descricao"])
        if expr and not at["desastre"]:
            extra = self.d["dados_extra_magia"] if k == "INT" else self.d["dados_extra_feitico"]
            total, partes = R.rolar_expr(R.dano_com_dados(expr, extra), self._rng, dobrar=at["critico"])
            linhas.append(self._txt_dano(total, partes).replace("Dano:", "Dados do encantamento:") + (f"  · +{extra} dado por {k}" if extra else ""))
        elif not expr:
            linhas.append("Este encantamento não tem dados na descrição.")
        if txt_custo:
            linhas.append(txt_custo)
        linhas += avisos
        self.registrar(f"✧ {e['nome']} ({v['tier']} nv {v['nivel']})", linhas, destaque=at["critico"] or at["desastre"])

    def registrar(self, titulo, linhas, destaque=False):
        import datetime
        self.abrir_diario()
        t = self.diario_txt
        t.configure(state="normal")
        t.insert("1.0", "\n")
        for ln in reversed(linhas):
            t.insert("1.0", "   " + ln + "\n", ("crit",) if destaque and ln is linhas[0] else ())
        t.insert("1.0", f"{titulo}   {datetime.datetime.now():%H:%M:%S}\n", ("t",))
        t.configure(state="disabled")
        self.diario_ultimo.configure(text=titulo + " — " + linhas[0])
        self.diario.lift()

    def abrir_diario(self):
        if self.diario is not None and self.diario.winfo_exists():
            self.diario.deiconify()
            self.diario.lift()
            return
        w = tk.Toplevel(self)
        w.title("Diário de rolagens")
        w.configure(background=PERG)
        w.geometry("560x520")
        topo = tk.Frame(w, bg=PERG, padx=12, pady=8)
        topo.pack(fill="x")
        tk.Label(topo, text="📜 Diário de rolagens", bg=PERG, fg=VINHO, font=(FONTE_TIT, 14, "bold")).pack(side="left")
        ttk.Button(topo, text="Desfazer custo", command=self.desfazer_custo, style="Peq.TButton").pack(side="right")
        ttk.Button(topo, text="Limpar", command=self._limpar_diario, style="Peq.TButton").pack(side="right", padx=6)
        self.diario_ultimo = Rot(w, size=10, wraplength=520, justify="left")
        self.diario_ultimo.pack(fill="x", padx=12)
        t = self.texto(w, spacing1=2, spacing3=2)
        t.pack(fill="both", expand=True, padx=12, pady=(6, 12))
        t.tag_configure("t", font=(FONTE, 11, "bold"), foreground=VINHO)
        t.tag_configure("crit", font=(FONTE, 10, "bold"))
        t.configure(state="disabled")
        self.diario, self.diario_txt = w, t

    def _limpar_diario(self):
        self.diario_txt.configure(state="normal")
        self.diario_txt.delete("1.0", "end")
        self.diario_txt.configure(state="disabled")

    def desfazer_custo(self):
        if not self.desfazer:
            messagebox.showinfo(APP_NOME, "Não há custo para desfazer.")
            return
        var, antigo, desc = self.desfazer.pop()
        var.set(antigo)
        self.registrar("↺ Custo desfeito", [f"Devolvido: {desc}."])

    # ============================================================ rolagem
    def _roda(self, e, direcao, delta):
        try:
            w = self.winfo_containing(e.x_root, e.y_root)
        except (KeyError, tk.TclError):
            return
        if w is None or w.winfo_toplevel() is not self:
            return
        if w.winfo_class() in ("Text", "Treeview", "Listbox", "TCombobox", "TSpinbox", "Spinbox"):
            return  # esses rolam sozinhos
        while w is not None and not isinstance(w, ScrollFrame):
            w = w.master
        if w is not None:
            w.rolar(direcao * max(1, round(delta / 120)) * 3)

    # ============================================================ tema
    def alternar_tema(self):
        estado = self.estado()
        arq, alt, ini = self.arquivo, self.alterado, self.inicializado
        try:
            aba = self.nb.index(self.nb.select())
        except tk.TclError:
            aba = 0
        novo_tema = "diurno" if NOTURNO else "noturno"
        aplicar_tema(novo_tema)
        gravar_pref(tema=novo_tema)
        for w in list(self.winfo_children()):
            if w is not self.janela_sessao:   # a sessão em rede continua aberta durante a troca de tema
                w.destroy()
        self.caixas = {}
        self.so_edicao = []
        self._estilo()
        self._menu()
        self._montar()
        self._aplicar_modo()
        self.aplicar(estado)
        self.arquivo, self.alterado, self.inicializado = arq, alt, ini
        self._atualizar_capa()
        try:
            self.nb.select(aba)
        except tk.TclError:
            pass
        self._titulo()

    # ============================================================ comparar
    def comparar(self):
        w = tk.Toplevel(self)
        w.title("Comparar fichas")
        w.configure(background=PERG)
        w.geometry("860x720")
        w.transient(self)
        corpo = tk.Frame(w, bg=PERG, padx=20, pady=14)
        corpo.pack(fill="both", expand=True)
        tk.Label(corpo, text="⚖  Comparar fichas", bg=PERG, fg=VINHO, font=(FONTE_TIT, 16, "bold")).grid(row=0, column=0, columnspan=4, sticky="w")
        tk.Label(corpo, text="A diferença mostra quanto a Ficha B tem a mais (verde) ou a menos (vermelho) que a Ficha A.",
                 bg=PERG, fg=TINTA2, font=(FONTE, 10, "italic")).grid(row=1, column=0, columnspan=4, sticky="w", pady=(0, 10))
        fichas = {"A": None, "B": None}
        rotulos = {}

        def escolher(lado, atual=False):
            if atual:
                if not self.inicializado:
                    messagebox.showinfo(APP_NOME, "Não há ficha aberta.", parent=w)
                    return
                fichas[lado] = (self.v_nome.get() or "ficha aberta", self.estado())
            else:
                fn = filedialog.askopenfilename(parent=w, title=f"Ficha {lado}", filetypes=[("Ficha Prevalecentes", "*.json"), ("Todos", "*.*")])
                if not fn:
                    return
                try:
                    with open(fn, encoding="utf-8") as f:
                        st = json.load(f)
                except Exception as ex:
                    messagebox.showerror(APP_NOME, f"Não consegui abrir:\n{ex}", parent=w)
                    return
                fichas[lado] = (st.get("identidade", {}).get("nome") or os.path.basename(fn), st)
            rotulos[lado].configure(text=fichas[lado][0])
            preencher()

        for i, lado in enumerate("AB"):
            f = tk.Frame(corpo, bg=PERG)
            f.grid(row=2, column=i * 2, columnspan=2, sticky="w", padx=(0, 30))
            tk.Label(f, text=f"Ficha {lado}", bg=C_ATR, fg=FAIXA, font=(FONTE, 9, "bold"), padx=8, pady=2).pack(side="left")
            rotulos[lado] = Rot(f, size=11)
            rotulos[lado].configure(text="—")
            rotulos[lado].pack(side="left", padx=8)
            ttk.Button(f, text="Abrir arquivo…", command=lambda l=lado: escolher(l), style="Peq.TButton").pack(side="left", padx=2)
            ttk.Button(f, text="Usar a aberta", command=lambda l=lado: escolher(l, True), style="Peq.TButton").pack(side="left", padx=2)

        tv = ttk.Treeview(corpo, columns=("a", "b", "d"), show="tree headings")
        tv.heading("#0", text="Item")
        tv.column("#0", width=250)
        for c, t, wd in (("a", "Ficha A", 210), ("b", "Ficha B", 210), ("d", "Diferença", 110)):
            tv.heading(c, text=t)
            tv.column(c, width=wd, anchor="w")
        tv.tag_configure("mais", foreground=VERDE)
        tv.tag_configure("menos", foreground=VINHO)
        tv.tag_configure("grupo", font=(FONTE, 10, "bold"))
        tv.grid(row=3, column=0, columnspan=4, sticky="nsew", pady=(12, 0))
        sb = ttk.Scrollbar(corpo, command=tv.yview)
        sb.grid(row=3, column=4, sticky="ns", pady=(12, 0))
        tv.configure(yscrollcommand=sb.set)
        corpo.rowconfigure(3, weight=1)
        corpo.columnconfigure(3, weight=1)

        def preencher():
            tv.delete(*tv.get_children())
            ra = self.resumo(fichas["A"][1]) if fichas["A"] else None
            rb = self.resumo(fichas["B"][1]) if fichas["B"] else None
            base = ra or rb
            if not base:
                return
            for grupo, itens in base.items():
                g = tv.insert("", "end", text=grupo, open=True, tags=("grupo",))
                chaves = list(itens)
                outro = (rb if base is ra else ra) or {}
                for k in outro.get(grupo, {}):
                    if k not in chaves:
                        chaves.append(k)
                for k in chaves:
                    va = (ra or {}).get(grupo, {}).get(k, "")
                    vb = (rb or {}).get(grupo, {}).get(k, "")
                    dif, tag = "", ()
                    if isinstance(va, (int, float)) and isinstance(vb, (int, float)) and ra and rb:
                        dv = vb - va
                        dif = f"{dv:+g}" if dv else "="
                        tag = ("mais",) if dv > 0 else ("menos",) if dv < 0 else ()
                    elif ra and rb and va != vb:
                        dif = "≠"
                    tv.insert(g, "end", text=k, values=(self._fmt(va), self._fmt(vb), dif), tags=tag)

        if self.inicializado:
            escolher("A", True)

    @staticmethod
    def _fmt(v):
        if isinstance(v, bool):
            return "sim" if v else "—"
        if isinstance(v, int):
            return str(v)
        return str(v) if v not in (None, "") else "—"

    def resumo(self, s):
        """Calcula os números principais de uma ficha salva (dict), sem carregá-la na tela."""
        idt = s.get("identidade", {})
        nivel = max(1, min(R.NIVEL_MAX, to_int(idt.get("nivel", 1), 1)))
        a = {}
        for k in R.ATRIBUTOS:
            x = s.get("atributos", {}).get(k, {})
            a[k] = sum(to_int(x.get(c, 0)) for c in ("inicial", "niveis", "especie", "bonus"))
        tal = {t for t in s.get("talentos", {}).values() if t}
        vida = s.get("vida", {})
        n_vida = R.curva(a["VIT"]) + (3 if "Vida Dura" in tal else 0)
        soma = 7 * n_vida if vida.get("modo", "media") == "media" else sum(vida.get("rolagens", [])[:n_vida])
        eq = s.get("equip", {})
        ca_a = next((x["ca"] for x in self.dados.get("armaduras", []) if x["nome"] == eq.get("armadura")), to_int(eq.get("armadura_ca")))
        ca_e = next((x["ca"] for x in self.dados.get("escudos", []) if x["nome"] == eq.get("escudo")), to_int(eq.get("escudo_ca")))
        vagas = R.slots_talismas(nivel, tal)
        for t in s.get("talismas", [])[:vagas]:
            for k, v in self.tal_info.get(t.get("nome"), {}).get("bonus", {}).items():
                a[k] += v
        manual = {k: to_int(v) for k, v in (s.get("manual") or {}).items()}
        for k in R.ATRIBUTOS:
            if k in manual:
                a[k] = manual[k]
        n_vida = R.curva(a["VIT"]) + (3 if "Vida Dura" in tal else 0)
        soma = 7 * n_vida if vida.get("modo", "media") == "media" else sum(vida.get("rolagens", [])[:n_vida])
        d = R.derivadas(a, nivel, tal, soma, ca_a, ca_e, to_int(eq.get("ca_extra")))
        ef = R.efeitos_talentos(tal, set(s.get("talentos_ativos", [])), eq.get("armadura", ""))
        self.aplicar_efeitos(d, ef, manual)
        n3 = nivel // 3
        out = {}
        out["Identidade"] = {"Nome": idt.get("nome", ""), "Player": idt.get("player", ""), "Espécie": idt.get("especie", ""), "Nível": nivel,
                             "Alma": "sem alma" if s.get("sem_alma") else "com alma"}
        out["Atributos"] = {R.NOMES_ATR[k]: a[k] for k in R.ATRIBUTOS}
        out["Curva"] = {R.NOMES_ATR[k]: d["curva"][k] for k in R.ATRIBUTOS}
        out["Características"] = {
            "Vida máx.": d["vida"], "Mana máx.": d["mana"], "Vigor máx.": d["vigor"], "Vigor por turno": d["vigor_regen"],
            "CA": d["ca"], "Carga máx.": d["carga"], "Movimento (m)": d["movimento"], "Iniciativa (bônus)": d["iniciativa_bonus"],
            "Iniciativa (d20)": d["iniciativa_dados"], "Ações extras": d["acoes_extras"], "Redução de dano (d4)": d["rd"],
            "Descoberta": d["descoberta"], "Resistências": len(d["resistencias"])}
        out["Ataque e defesa"] = {}
        for n, atrs in R.PERICIAS_ATAQUE:
            out["Ataque e defesa"][f"{n} ({'/'.join(atrs)})"] = max(d["bc"][k] for k in atrs) + n3
        for n, k, tn in R.PERICIAS_DEFESA:
            out["Ataque e defesa"][f"{n} ({k})"] = d["bc"][k] + n3 + (2 if tn in tal else 0)
        out["Ataque e defesa"]["DT Feitiçaria"] = d["dt_feiticaria"]
        out["Ataque e defesa"]["DT Desejo"] = d["dt_desejo"]
        treinadas = set(s.get("pericias", []))
        out["Perícias"] = {}
        for nome, atrs, _ in R.PERICIAS:
            atrs = atrs or [s.get("prevalencia_attr", "ARC")]
            _, b, dd = R.pericia_fora(a, nivel, atrs, nome in treinadas)
            out["Perícias"][nome + (" •" if nome in treinadas else "")] = b
        out["Armas"] = {}
        for i, ar in enumerate(s.get("armas", [])[:2], start=1):
            out["Armas"][f"Arma {i}"] = f"{ar.get('grupo')} nv {ar.get('nivel')}" if ar.get("grupo") else ""
        out["Armas"]["Armadura"] = eq.get("armadura", "")
        out["Armas"]["Escudo"] = eq.get("escudo", "")
        encs = s.get("encantamentos", [])
        out["Encantamentos"] = {"Espaços máx.": d["espacos_encant"],
                                "Espaços usados": sum(self.enc_por_nome[x["familia"]]["espaco"] for x in encs
                                                      if x.get("equipado") and x.get("familia") in self.enc_por_nome),
                                "Aprendidos": len(encs)}
        for x in encs:
            out["Encantamentos"][x["familia"]] = "nv " + ", ".join(map(str, x.get("versoes", []))) + (" (equipado)" if x.get("equipado") else "")
        out["Talentos"] = {"Quantidade": len(tal)}
        for t in sorted(tal):
            out["Talentos"][t] = "✓"
        out["Alma"] = {"Nível da alma": d["alma_nivel"], "Usos por descanso": d["alma_usos"], "Talismãs (espaços)": d["talismas"]}
        out["Talismãs e sets"] = {}
        for t in s.get("talismas", []):
            if t.get("nome"):
                out["Talismãs e sets"][t["nome"]] = "✓"
        cont = {}
        for x in s.get("set", {}).values():
            n = x.get("set", "")
            if n and not n.startswith("—"):
                cont[n] = cont.get(n, 0) + 1
        for n, q in cont.items():
            out["Talismãs e sets"][f"Set {n} (peças)"] = q
        return out

    # ============================================================ inicializar
    def _atualizar_capa(self):
        if self.inicializado:
            self.capa.place_forget()
        else:
            self.capa.place(in_=self.nb, relx=0, rely=0, relwidth=1, relheight=1)
            self.capa.lift()

    def inicializar(self, nova=False):
        w = tk.Toplevel(self)
        w.title("Nova ficha" if nova else "Distribuição inicial")
        w.configure(background=PERG)
        w.transient(self)
        w.resizable(False, False)
        corpo = tk.Frame(w, bg=PERG, padx=26, pady=18)
        corpo.pack(fill="both", expand=True)
        v_nome, v_player, v_esp = tk.StringVar(value=self.v_nome.get()), tk.StringVar(value=self.v_player.get()), tk.StringVar(value=self.v_especie.get())
        if nova:
            tk.Label(corpo, text="Novo Sonhador", bg=PERG, fg=VINHO, font=(FONTE_TIT, 16, "bold")).grid(row=0, column=0, columnspan=4, sticky="w")
        idf = tk.Frame(corpo, bg=PERG)
        if nova:
            idf.grid(row=1, column=0, columnspan=4, sticky="w", pady=(6, 10))
            for j, (t, v, wd) in enumerate([("Nome", v_nome, 22), ("Player", v_player, 14), ("Espécie", v_esp, 14)]):
                tk.Label(idf, text=t, bg=PERG, fg=TINTA2, font=(FONTE, 10)).grid(row=0, column=2 * j, sticky="w", padx=(0, 4))
                ttk.Entry(idf, textvariable=v, width=wd).grid(row=0, column=2 * j + 1, sticky="w", padx=(0, 14))
        cab = tk.Frame(corpo, bg=PERG)
        cab.grid(row=2, column=0, columnspan=4, sticky="w")
        tk.Label(cab, text="Atributos iniciais", bg=PERG, fg=VINHO, font=(FONTE_TIT, 14, "bold")).pack(anchor="w")
        tk.Label(corpo, text="Use cada valor uma vez: 16, 14, 12, 11, 10, 9, 8 e 7.", bg=PERG, fg=TINTA2,
                 font=(FONTE, 10, "italic")).grid(row=3, column=0, columnspan=4, sticky="w", pady=(0, 10))
        vars_ini = {}

        def livres(k):
            usados = {v.get() for kk, v in vars_ini.items() if kk != k and v.get()}
            return [""] + [str(x) for x in R.VALORES_INICIAIS if str(x) not in usados]

        for i, k in enumerate(R.ATRIBUTOS):
            r, c = 4 + i % 4, (i // 4) * 2
            v = tk.StringVar(value=self.atr[k]["inicial"].get())
            vars_ini[k] = v
            tk.Label(corpo, text=R.NOMES_ATR[k], bg=PERG, fg=TINTA, font=(FONTE, 11), anchor="w", width=13).grid(row=r, column=c, sticky="w", pady=3)
            cb = ttk.Combobox(corpo, textvariable=v, width=5, state="readonly")
            cb.configure(postcommand=lambda cb=cb, k=k: cb.configure(values=livres(k)))
            cb.grid(row=r, column=c + 1, sticky="w", padx=(0, 26), pady=3)

        tk.Frame(corpo, height=1, bg=OURO).grid(row=8, column=0, columnspan=4, sticky="we", pady=12)
        tk.Label(corpo, text="Espécie", bg=PERG, fg=VINHO, font=(FONTE_TIT, 13, "bold")).grid(row=9, column=0, columnspan=4, sticky="w")
        tk.Label(corpo, text="Bônus em um atributo e prejuízo do mesmo valor (1 a 5) em outro. Deixe 0 se não houver.",
                 bg=PERG, fg=TINTA2, font=(FONTE, 10, "italic")).grid(row=10, column=0, columnspan=4, sticky="w", pady=(0, 6))
        atual = {k: to_int(self.atr[k]["especie"].get()) for k in R.ATRIBUTOS}
        b0 = next((k for k, x in atual.items() if x > 0), "")
        p0 = next((k for k, x in atual.items() if x < 0), "")
        v_bon, v_pre = tk.StringVar(value=R.NOMES_ATR.get(b0, "")), tk.StringVar(value=R.NOMES_ATR.get(p0, ""))
        v_val = tk.StringVar(value=str(atual.get(b0, 0) if b0 else 0))
        nomes = [""] + [R.NOMES_ATR[k] for k in R.ATRIBUTOS]
        tk.Label(corpo, text="Bônus em", bg=PERG, fg=TINTA, font=(FONTE, 11)).grid(row=11, column=0, sticky="w")
        ttk.Combobox(corpo, values=nomes, textvariable=v_bon, width=13, state="readonly").grid(row=11, column=1, sticky="w")
        tk.Label(corpo, text="Prejuízo em", bg=PERG, fg=TINTA, font=(FONTE, 11)).grid(row=12, column=0, sticky="w", pady=4)
        ttk.Combobox(corpo, values=nomes, textvariable=v_pre, width=13, state="readonly").grid(row=12, column=1, sticky="w", pady=4)
        tk.Label(corpo, text="Valor", bg=PERG, fg=TINTA, font=(FONTE, 11)).grid(row=11, column=2, sticky="w")
        ttk.Spinbox(corpo, from_=0, to=5, textvariable=v_val, width=4).grid(row=11, column=3, sticky="w")

        tk.Frame(corpo, height=1, bg=OURO).grid(row=12, column=0, columnspan=4, sticky="we", pady=12)
        v_sem_alma = tk.BooleanVar(value=self.sem_alma if self.inicializado else False)
        sa = tk.Frame(corpo, bg=PERG)
        sa.grid(row=13, column=0, columnspan=4, sticky="w")
        bt_sa = ttk.Checkbutton(sa, variable=v_sem_alma, style="Alternar.TCheckbutton", width=16)
        bt_sa.pack(side="left")
        info_sa = tk.Label(sa, bg=PERG, fg=TINTA2, font=(FONTE, 10, "italic"), justify="left")
        info_sa.pack(side="left", padx=12)

        def att_sa(*_):
            sem = v_sem_alma.get()
            bt_sa.configure(text="☠  Sem alma" if sem else "✧  Com alma")
            info_sa.configure(text="+2 pontos de atributo a cada nível; a aba Alma some." if sem else
                              "Clique para jogar sem alma (+2 pontos de atributo por nível).")
        v_sem_alma.trace_add("write", att_sa)
        att_sa()

        msg = tk.Label(corpo, text="", bg=PERG, fg=VINHO, font=(FONTE, 10, "bold"))
        msg.grid(row=14, column=0, columnspan=4, sticky="w", pady=(10, 0))

        def confirmar():
            vals = [vars_ini[k].get() for k in R.ATRIBUTOS]
            if "" in vals or len(set(vals)) != 8:
                msg.configure(text="Atribua todos os oito valores, cada um uma vez.")
                return
            val = max(0, min(5, to_int(v_val.get())))
            kb, kp = R.ATR_POR_NOME.get(v_bon.get()), R.ATR_POR_NOME.get(v_pre.get())
            if val and (not kb or not kp or kb == kp):
                msg.configure(text="Escolha atributos diferentes para o bônus e o prejuízo da espécie.")
                return
            if self.inicializado and not nova and not messagebox.askyesno(APP_NOME, "Substituir os atributos iniciais e a espécie atuais?", parent=w):
                return
            if self.inicializado and not nova and v_sem_alma.get() != self.sem_alma:
                if not messagebox.askyesno(APP_NOME, ("Jogar sem alma muda os pontos por nível (+2 por nível)" if v_sem_alma.get() else
                                                      "Voltar a ter alma tira os +2 pontos por nível") +
                                           ". Revise a distribuição dos pontos de nível depois. Continuar?", parent=w):
                    return
            self._carregando = True
            if nova:
                self.v_nome.set(v_nome.get().strip())
                self.v_player.set(v_player.get().strip())
                self.v_especie.set(v_esp.get().strip())
            self.sem_alma = v_sem_alma.get()
            for k in R.ATRIBUTOS:
                self.atr[k]["inicial"].set(vars_ini[k].get())
                self.atr[k]["especie"].set(str(val if k == kb else -val if k == kp else 0) if val else "0")
            self._carregando = False
            self.inicializado = True
            self._atualizar_capa()
            self._renumerar_abas()
            w.destroy()
            self.alterado = True
            self.agendar()
            if nova:
                self.after(100, lambda: self.salvar(como=True))

        bt = tk.Frame(corpo, bg=PERG)
        bt.grid(row=15, column=0, columnspan=4, sticky="e", pady=(14, 0))
        ttk.Button(bt, text="Cancelar", command=w.destroy).pack(side="right")
        ttk.Button(bt, text="Criar e salvar ficha" if nova else "Confirmar", command=confirmar).pack(side="right", padx=8)
        w.grab_set()
        w.focus_set()

    # ============================================================ vida
    def rolar_vida(self):
        tal = self.talentos_escolhidos()
        n = R.curva(self.atributos_efetivos()["VIT"]) + (3 if "Vida Dura" in tal else 0)
        falta = n - len(self.vida_rolagens)
        if falta <= 0:
            return
        novos = [random.randint(1, 12) for _ in range(falta)]
        self.vida_rolagens.extend(novos)
        messagebox.showinfo(APP_NOME, f"Rolou {falta}d12: {', '.join(map(str, novos))}\nTotal: +{sum(novos)} de Vida")
        self.agendar()

    def zerar_rolagens(self):
        if self.vida_rolagens and messagebox.askyesno(APP_NOME, "Apagar todas as rolagens de vida guardadas?"):
            self.vida_rolagens = []
            self.agendar()

    def _popup_nivel(self, n0, n1):
        ganhos = sum(R.ganho_no_nivel(n, self.sem_alma) for n in range(n0 + 1, n1 + 1))
        linhas = [f"Subiu do nível {n0} para o {n1}!", "", f"• +{ganhos} pontos de atributo (+10 por nível, +5 nos múltiplos de 3" + (", +2 por ser sem alma)" if self.sem_alma else ")"),
                  f"• +{5 * (n1 - n0)} de Vida base"]
        pares = [n for n in range(n0 + 1, n1 + 1) if n % 2 == 0]
        if pares:
            linhas.append(f"• Novo(s) talento(s) no(s) nível(is) {', '.join(map(str, pares))}")
        if R.nivel_alma(n1) > R.nivel_alma(n0) and not self.sem_alma:
            linhas.append(f"• Alma sobe para o nível {R.nivel_alma(n1)}")
        if R.max_nivel_arma(n1) > R.max_nivel_arma(n0):
            linhas.append(f"• Armas podem chegar ao nível {R.max_nivel_arma(n1)}")
        if any(n % 6 == 0 and n <= 24 for n in range(n0 + 1, n1 + 1)):
            linhas.append("• +1 espaço de talismã")
        if any(n in (10, 20, 30) for n in range(n0 + 1, n1 + 1)) and not self.sem_alma:
            linhas.append("• Nova habilidade ativa da alma liberada")
        if any(n % 2 == 0 for n in range(n0 + 1, n1 + 1)):
            linhas.append(f"• Encantamentos de até nível {min(10, n1 // 2)} podem ser aprendidos")
        resto = R.pontos_de_nivel(n1, self.sem_alma) - sum(to_int(self.atr[k]["niveis"].get()) for k in R.ATRIBUTOS)
        linhas += ["", f"Faltam {resto} pontos de atributo para distribuir."]
        messagebox.showinfo("Subiu de nível", "\n".join(linhas))

    # ============================================================ salvar/abrir
    def estado(self):
        g = lambda v: v.get()
        return {
            "versao": 1,
            "inicializado": self.inicializado,
            "identidade": {"nome": g(self.v_nome), "player": g(self.v_player), "nivel": self.nivel(), "especie": g(self.v_especie),
                           "sonho": g(self.v_sonho), "guilda": g(self.v_guilda)},
            "atributos": {k: {c: g(row[c]) for c in ("inicial", "niveis", "especie", "bonus")} for k, row in self.atr.items()},
            "vida": {"modo": g(self.v_vida_modo), "rolagens": self.vida_rolagens, "atual": g(self.v_vida_atual),
                     "mana_atual": g(self.v_mana_atual), "vigor_atual": g(self.v_vigor_atual)},
            "pericias": sorted(self.pericias_treinadas()), "prevalencia_attr": g(self.v_prev_attr), "pericia_ataque": g(self.v_per_ataque),
            "armas": [{"grupo": g(ui["grupo"]), "nivel": g(ui["nivel"]), "props": g(ui["props"])} for ui in self.armas_ui],
            "equip": dict({k: g(v) for k, v in self.arm.items()}, **dict(zip(("armadura_ca", "escudo_ca", "armadura_peso", "escudo_peso"),
                                                                             self.ca_peso_protecao()))),
            "encantamentos": self.encantamentos,
            "talentos": {s: g(ui["nome"]) for s, ui in self.tal_ui.items()},
            "alma": {"nome": g(self.alma["nome"]), "atr": g(self.alma["atr"]), "restantes": g(self.alma["restantes"]),
                     "historia": self.txt_alma.get("1.0", "end-1c"),
                     "habilidades": [{k: g(h[k]) for k in ("nome", "efeito", "tipo")} for h in self.alma_hab]},
            "talismas": [{"nome": g(t["nome"]), "efeito": g(t["efeito"])} for t in self.talismas],
            "set": {p: {"set": g(sp["set"]), "nome": g(sp["nome"])} for p, sp in self.set_pecas.items()},
            "inventario": [{"item": g(i["item"]), "carga": g(i["carga"])} for i in self.inv], "dinheiro": g(self.v_dinheiro),
            "condicoes": {n: {k: g(c[k]) for k in ("max", "atual", "notas")} for n, c in self.cond.items()},
            "portao": {n: [g(v) for v in vs] for n, vs in self.portao.items()}, "cicatrizes": g(self.v_cicatrizes),
            "vinculos": {"grupo": g(self.v_vinc_grupo), "mundo": g(self.v_vinc_mundo), "metas": g(self.v_metas)},
            "receitas": getattr(self, "_receitas_salvas", ""),
            "sem_alma": getattr(self, "sem_alma", False),
            "manual": dict(self.manual),
            "talentos_ativos": sorted(self.talentos_ativos()),
            "especie_notas": self.v_esp_notas.get(),
        }

    def aplicar(self, s):
        self._carregando = True
        try:
            i = s.get("identidade", {})
            self.v_nome.set(i.get("nome", "")); self.v_player.set(i.get("player", ""))
            self.v_nivel.set(str(i.get("nivel", 1))); self.v_especie.set(i.get("especie", ""))
            self.v_sonho.set(i.get("sonho", "")); self.v_guilda.set(i.get("guilda", ""))
            for k, row in self.atr.items():
                at = s.get("atributos", {}).get(k, {})
                row["inicial"].set(at.get("inicial", "")); row["niveis"].set(at.get("niveis", "0"))
                row["especie"].set(at.get("especie", "0")); row["bonus"].set(at.get("bonus", "0"))
            v = s.get("vida", {})
            self.v_vida_modo.set(v.get("modo", "media")); self.vida_rolagens = list(v.get("rolagens", []))
            self.v_vida_atual.set(v.get("atual", "")); self.v_mana_atual.set(v.get("mana_atual", "")); self.v_vigor_atual.set(v.get("vigor_atual", ""))
            per = set(s.get("pericias", []))
            for n, p in self.per.items():
                p["var"].set(n in per)
            self.v_prev_attr.set(s.get("prevalencia_attr", "ARC")); self.v_per_ataque.set(s.get("pericia_ataque", "Luta"))
            armas = s.get("armas", [{}, {}])
            for ui, ar in zip(self.armas_ui, armas + [{}] * 2):
                ui["grupo"].set(ar.get("grupo", "")); ui["nivel"].set(ar.get("nivel", "1")); ui["props"].set(ar.get("props", ""))
                ui["disp_grupo"].set(ar.get("grupo", "")); ui["disp_nivel"].set(f"Nível {ar.get('nivel', '1')}" if ar.get("grupo") else "")
            eq = s.get("equip", {})
            nomes_arm = {x["nome"] for x in self.dados.get("armaduras", [])}
            nomes_esc = {x["nome"] for x in self.dados.get("escudos", [])}
            self.arm["armadura"].set(eq.get("armadura", "") if eq.get("armadura", "") in nomes_arm else "")
            self.arm["escudo"].set(eq.get("escudo", "") if eq.get("escudo", "") in nomes_esc else "")
            self.arm["ca_extra"].set(eq.get("ca_extra", ""))
            self.arm["peitoral_set"].set(bool(eq.get("peitoral_set", False)))
            self.encantamentos = [x for x in s.get("encantamentos", []) if x.get("familia") in self.enc_por_nome]
            for sl, ui in self.tal_ui.items():
                n = s.get("talentos", {}).get(sl, "")
                ui["nome"].set(n); ui["disp"].set(n); ui["cat"].set("Todas")
                ui["ativo"].set(n in set(s.get("talentos_ativos", [])))
            al = s.get("alma", {})
            self.alma["nome"].set(al.get("nome", "")); self.alma["atr"].set(al.get("atr", "INT")); self.alma["restantes"].set(al.get("restantes", ""))
            self.txt_alma.delete("1.0", "end"); self.txt_alma.insert("1.0", al.get("historia", ""))
            for h, hv in zip(self.alma_hab, al.get("habilidades", []) + [{}] * 6):
                for k in ("nome", "efeito", "tipo"):
                    h[k].set(hv.get(k, ""))
            for t, tv in zip(self.talismas, s.get("talismas", []) + [{}] * 7):
                nm = tv.get("nome", "")
                t["nome"].set(nm if nm in self.tal_info else ""); t["efeito"].set(tv.get("efeito", "")); t["disp"].set(t["nome"].get())
            for p, sv in self.set_pecas.items():
                x = s.get("set", {}).get(p, {})
                sv["set"].set(x.get("set", "")); sv["nome"].set(x.get("nome", ""))
            for it, iv in zip(self.inv, s.get("inventario", []) + [{}] * 30):
                it["item"].set(iv.get("item", "")); it["carga"].set(iv.get("carga", ""))
            self.v_dinheiro.set(s.get("dinheiro", ""))
            for n, c in self.cond.items():
                x = s.get("condicoes", {}).get(n, {})
                c["max"].set(x.get("max", "100")); c["atual"].set(x.get("atual", "")); c["notas"].set(x.get("notas", ""))
            for n, vs in self.portao.items():
                for v_, b in zip(vs, s.get("portao", {}).get(n, []) + [False] * 5):
                    v_.set(bool(b))
            self.v_cicatrizes.set(s.get("cicatrizes", ""))
            vi = s.get("vinculos", {})
            self.v_vinc_grupo.set(vi.get("grupo", "")); self.v_vinc_mundo.set(vi.get("mundo", "")); self.v_metas.set(vi.get("metas", ""))
            self._receitas_salvas = s.get("receitas", "")
            self.sem_alma = bool(s.get("sem_alma", False))
            self.manual = {k: int(v) for k, v in (s.get("manual") or {}).items() if str(v).lstrip("-").isdigit()}
            self.desfazer = []
            self.v_esp_notas.set(s.get("especie_notas", ""))
            self.nivel_anterior = to_int(i.get("nivel", 1), 1)
            self.inicializado = s.get("inicializado", all(self.atr[k]["inicial"].get() for k in R.ATRIBUTOS))
        finally:
            self._carregando = False
        self.a = self.atributos_efetivos()
        self.recalc()
        self._atualizar_capa()
        self._renumerar_abas()
        self._atualizar_tree_enc()
        self.txt_enc.configure(state="normal"); self.txt_enc.delete("1.0", "end"); self.txt_enc.configure(state="disabled")

    def _titulo(self):
        nome = os.path.basename(self.arquivo) if self.arquivo else ("ficha nova (não salva)" if self.inicializado else "")
        self.title(f"{APP_NOME}" + (f" — {nome}" if nome else "") + (" *" if self.alterado and self.inicializado else ""))

    def _descartar_ok(self):
        """Pergunta antes de perder alterações. Retorna True se pode seguir."""
        if not (self.inicializado and self.alterado):
            return True
        r = messagebox.askyesnocancel(APP_NOME, "A ficha atual tem alterações não salvas.\nSalvar antes de continuar?")
        if r is None:
            return False
        if r:
            return self.salvar()
        return True

    def novo(self, perguntar=True):
        """Cria uma ficha nova: limpa tudo, abre a distribuição inicial e depois salva o arquivo."""
        if perguntar and not self._descartar_ok():
            return
        self.arquivo = None
        self.aplicar({})
        self.alterado = False
        self._titulo()
        if perguntar:
            self.abrir_assistente()

    def abrir_assistente(self):
        import assistente
        cores = {k: globals()[k] for k in ("FUNDO", "PERG", "CAMPO", "TINTA", "TINTA2", "OURO", "OURO2", "VINHO", "VERDE",
                                           "FAIXA", "MESA_TXT", "FONTE", "FONTE_TIT")}
        assistente.Assistente(self, cores)

    def criar_de_assistente(self, estado):
        self.arquivo = None
        self.modo = "edicao"          # ficha recém-criada: ainda falta equipar e ajustar
        self.aplicar(estado)
        self._aplicar_modo()
        self.alterado = True
        self._titulo()
        self.after(100, lambda: self.salvar(como=True))

    def abrir(self):
        if not self._descartar_ok():
            return
        fn = filedialog.askopenfilename(title="Abrir ficha", filetypes=[("Ficha Prevalecentes", "*.json"), ("Todos", "*.*")])
        if not fn:
            return
        try:
            with open(fn, encoding="utf-8") as f:
                s = json.load(f)
        except Exception as e:
            messagebox.showerror(APP_NOME, f"Não consegui abrir o arquivo:\n{e}")
            return
        self.arquivo = fn
        self.modo = "jogo"            # ficha salva abre pronta para a mesa
        self.aplicar(s)
        self._aplicar_modo()
        self.alterado = False
        self._titulo()

    def salvar(self, como=False):
        """Salva a ficha. Retorna True se salvou."""
        if not self.inicializado:
            messagebox.showinfo(APP_NOME, "Crie uma ficha nova (ou abra uma) antes de salvar.")
            return False
        if como or not self.arquivo:
            nome = (self.v_nome.get() or "personagem").strip().replace(" ", "_")
            fn = filedialog.asksaveasfilename(title="Salvar ficha", defaultextension=".json", initialfile=f"{nome}.json",
                                              filetypes=[("Ficha Prevalecentes", "*.json")])
            if not fn:
                return False
            self.arquivo = fn
        try:
            with open(self.arquivo, "w", encoding="utf-8") as f:
                json.dump(self.estado(), f, ensure_ascii=False, indent=1)
        except Exception as e:
            messagebox.showerror(APP_NOME, f"Não consegui salvar:\n{e}")
            return False
        self.alterado = False
        self._titulo()
        return True

    def exportar_pdf(self):
        if not self.inicializado:
            messagebox.showinfo(APP_NOME, "Crie ou abra uma ficha antes de exportar.")
            return
        try:
            import pdf_ficha
        except ImportError:
            messagebox.showerror(APP_NOME, "Para exportar em PDF é preciso o pacote reportlab.\n\n"
                                           "No Prompt de Comando: py -m pip install reportlab\n"
                                           "(o GERAR_EXE.bat já instala e embute no .exe)")
            return
        nome = (self.v_nome.get() or "ficha").strip().replace(" ", "_")
        pasta = os.path.dirname(self.arquivo) if self.arquivo else None
        fn = filedialog.asksaveasfilename(title="Exportar ficha em PDF", defaultextension=".pdf", initialfile=f"{nome}.pdf",
                                          initialdir=pasta, filetypes=[("PDF", "*.pdf")])
        if not fn:
            return
        self.recalc()
        try:
            pdf_ficha.gerar_pdf(fn, self)
        except PermissionError:
            messagebox.showerror(APP_NOME, "Não consegui gravar o PDF. Ele está aberto em outro programa?")
            return
        except Exception as ex:
            messagebox.showerror(APP_NOME, f"Erro ao gerar o PDF:\n{ex}")
            return
        if messagebox.askyesno(APP_NOME, f"PDF salvo em:\n{fn}\n\nAbrir agora?"):
            try:
                os.startfile(fn)  # Windows
            except AttributeError:
                import subprocess
                subprocess.Popen(["xdg-open", fn])
            except Exception:
                pass

    def fechar(self):
        if self._descartar_ok():
            if getattr(self, "janela_sessao", None):
                try:
                    self.janela_sessao.fechar()
                except tk.TclError:
                    pass
            self.destroy()

    def abrir_sessao(self):
        """Janela de sessão em rede: o jogador levanta a mão, o mestre recebe o aviso."""
        j = getattr(self, "janela_sessao", None)
        if j is not None:
            try:
                j.deiconify()
                j.lift()
                return
            except tk.TclError:
                pass
        cores = dict(FUNDO=FUNDO, CAMPO=CAMPO, VINHO=VINHO, OURO=OURO, OURO2=OURO2, VERDE=VERDE, PERG=PERG, PERG2=PERG2,
                     TINTA=TINTA, TINTA2=TINTA2, FAIXA=FAIXA, LINHA=LINHA, C_VIDA=C_VIDA, C_MANA=C_MANA, C_VIGOR=C_VIGOR,
                     ALERTA=ALERTA, TINTA2_FUNDO=MESA_TXT, FONTE=FONTE, ULTIMO_IP=ler_pref().get("sessao_ip", ""))

        def ao_fechar(ip):
            self.janela_sessao = None
            if ip:
                gravar_pref(sessao_ip=ip)

        ponte = PonteSessao(self) if self.inicializado else None
        self.janela_sessao = sessao.JanelaSessao(self, cores, self.v_nome.get().strip(), ao_fechar, ponte)

    def mostrar_regras(self):
        w = tk.Toplevel(self)
        w.title("Regras usadas nos cálculos")
        t = tk.Text(w, wrap="word", width=96, height=34)
        t.pack(fill="both", expand=True)
        t.insert("1.0", REGRAS_TXT)
        t.configure(state="disabled")


class PonteSessao:
    """Liga a ficha aberta à sessão: manda o resumo ao mestre e recebe dano e condições."""

    def __init__(self, app):
        self.app = app

    def resumo(self):
        a = self.app
        if not a.inicializado:
            return None
        d = a.d
        return {"personagem": a.v_nome.get().strip(), "especie": a.v_especie.get().strip(), "nivel": a.nivel(),
                "vida": a._atual(a.v_vida_atual, d["vida"]), "vida_max": d["vida"],
                "mana": a._atual(a.v_mana_atual, d["mana"]), "mana_max": d["mana"],
                "vigor": a._atual(a.v_vigor_atual, d["vigor"]), "vigor_max": d["vigor"],
                "ca": d["ca"], "movimento": d["movimento"], "iniciativa": d["iniciativa_bonus"],
                "portao": [sum(v.get() for v in a.portao["Sucessos"]), sum(v.get() for v in a.portao["Falhas"])],
                "condicoes": [[n, to_int(c["atual"].get()), to_int(c["max"].get(), 100)] for n, c in a.cond.items() if to_int(c["atual"].get())],
                "sem_alma": a.sem_alma}

    def aplicar_dano(self, valor, tipo, desc):
        """valor > 0 tira Vida; valor < 0 cura (sem passar do máximo). Devolve o texto do resultado."""
        a = self.app
        a.recalc()
        maximo = a.d["vida"]
        antes = a._atual(a.v_vida_atual, maximo)
        depois = max(0, min(maximo, antes - valor))
        a.v_vida_atual.set(str(depois))
        txt = f"Vida: {antes} → {depois}"
        if depois == 0 and antes > 0:
            txt += "  — INCAPAZ: role o Portão da Morte no início do seu turno."
        oque = f"Cura de {-valor}" if valor < 0 else f"{valor} de dano" + (f" ({tipo})" if tipo else "")
        a.registrar("📣 Do mestre", [oque + (f" — {desc}" if desc else ""), txt])
        return txt

    def efeitos(self, lista, rodada):
        self.app.efeitos_mestre = list(lista)
        self.app.recalc()

    def aviso(self, texto):
        pass   # o próprio diário já registra o dano; condições aparecem na aba Combate


REGRAS_TXT = """Fórmulas (PREVA 3.1)

Atributos: distribuição inicial 16/14/12/11/10/9/8/7; +10 pontos por nível e +5 extras em níveis múltiplos de 3 (nível máx. 30).
Sem alma ("Jogando sem uma Alma"): +2 pontos de atributo a mais por nível, e a aba Alma não é usada.
Acima de 99 conta como 99 nas tabelas.
Curva: +1 a cada 5 pontos até 20; +2 a cada 5 de 25 a 35; +3 de 40 a 55; +4 de 60 a 75; +5 de 80 a 95; +2 no 99 (99 = 60).
Bônus de Combate: +1 a cada 20 pontos (99 = +5). Vantagem (2d20) com 60+.

Vida = 10 + 5 por nível acima do 1º + (Curva da VIT) dados de 1d12 (ou 7 fixo por dado).
Mana = 2 × Mente + 2 × Curva da Mente.
Vigor = 20 + Força + Curva da Força. Recupera Curva da Força ÷ 4 por turno. Armas de Vigor: 5 por ataque, 8 a partir do nv 4, 10 a partir do nv 8.
Descoberta = 10 + 10 a cada 15 de Arcano.
CA = 10 + armadura + escudo + 1 a cada 20 TEN (máx. +4); entre 10 e 25.
Carga = 10 + 2 × TEN + FOR ÷ 2 + Curva da TEN. Lentidão a partir de metade; Exaustão com 10 ou menos livres.
Movimento = 9 m; +3 m aos 30 de DES e a cada 15 acima.
Ações extras: 1 a cada um destes valores de DES: 15, 30, 45, 55, 65, 75, 85, 95.
Iniciativa: 1d20 + 1d20 a cada 20 DES (fica com o maior) + BC de DES.
Redução de Dano: 1d4 a cada 20 TEN (máx. 4d4). Resistências por TEN: 20 Fogo … 90 Sagrado.

Perícias fora de combate: nível/2, + Curva do atributo se treinada; +1d20 a cada 20 pontos no atributo.
Treinadas: 1 de ataque + 5 fora de combate, +1 a cada 10 em INT ou MEN (o programa usa o maior dos dois).
Ataque: 1d20 + BC + nível/3 + acerto da arma (nv1 +0 … nv10 +5). Defesa: 1d20 + BC + nível/3.
DT (encantamentos, alma, armas) = 10 + BC + nível/3.

Armas: nível máximo = metade do nível do personagem, arredondado para cima. +1 dado de dano a cada 30 no atributo de ataque.
Uso duplo: em cada atributo, maior requisito + metade do outro. Coordenação: DT 8 + maior nível.

Encantamentos: Espaços = 1 + 1 a cada 6 pontos de INT + FÉ somados. Versão de nível N exige o atributo da tabela
(10/15/25/30/40/45/55/65/75/85) e personagem de nível 2 × N (nível 1 com cajado/selo inicial). Conjurar exige cajado (Magia)
ou selo (Feitiço) de nível igual ou maior. Teste de aprendizado: DT 15 + 3 por nível acima do 1º.
+1 dado de dano a cada 30 de INT (Magias) / FÉ (Feitiços). Contra-encantamentos: 1 a cada 10 em INT ou FÉ (o maior).

Alma: nível = nível do personagem ÷ 3. Usos por descanso longo = 2 + nível da alma ÷ 3. Nova ativa nos níveis 10, 20 e 30.
Talismãs: 1 espaço + 1 a cada 6 níveis (máx. 5).

Talentos aplicados automaticamente: Vida Dura, Fôlego de Guerreiro, Mochileiro, Mula de Carga, Cabeça Cheia, Mente Expandida,
Pé Ligeiro, Pele Grossa, Mão Extra, Mente Infinita, Treinado, Colecionador de Talismãs, Relicário, Veterano de Armadura,
Mãos Gêmeas, Empunhadura Folgada e os +2 de defesa (Fortitude de Ferro, Reflexos de Gato, Mente Blindada, Vontade Inabalável).

Os dados de armas, encantamentos e talentos vêm do livro. Para corrigir algo, coloque um arquivo dados_prevalecentes.json
ao lado do programa (mesmo formato) e ele será usado no lugar dos dados embutidos.
"""


if __name__ == "__main__":
    App().mainloop()
