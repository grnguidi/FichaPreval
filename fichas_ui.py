# -*- coding: utf-8 -*-
"""Fichas da mesa no PC: a janela do mestre (criar, importar, abrir, liberar e excluir fichas) e, para o jogador,
a escolha da ficha ao entrar e o vaivém dela com a mesa (cada mudança volta para o .json do mestre)."""
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog

import foto as F
from fichas_mesa import e_ficha
from grupo_ui import _Base

ARQ_CODIGOS = os.path.join(os.path.expanduser("~"), ".prevalecentes", "codigos_ficha.json")


def _codigos():
    try:
        with open(ARQ_CODIGOS, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _guardar_codigo(slug, codigo):
    d = _codigos()
    d[slug] = codigo
    try:
        os.makedirs(os.path.dirname(ARQ_CODIGOS), exist_ok=True)
        with open(ARQ_CODIGOS, "w", encoding="utf-8") as f:
            json.dump(d, f)
    except OSError:
        pass


def _miniatura(master, fotos, chave, dados_foto, lado=44):
    """Label com a foto (ou um espaço vazio do mesmo tamanho). `fotos` segura as imagens para o Tk não as soltar."""
    img = F.para_tk(dados_foto, lado) if dados_foto else None
    if img is not None:
        fotos[chave] = img
        return tk.Label(master, image=img, bg=master["bg"])
    return tk.Label(master, text="☺" if dados_foto else "", bg=master["bg"], width=5)


class JanelaFichasMestre(_Base):
    """Fichas da mesa (pasta fichas/): o mestre cria, importa, abre, libera e exclui."""

    def __init__(self, pai):
        super().__init__(pai, "Fichas da mesa", "640x560")
        self._fotos = {}
        self.atualizar(True)

    def atualizar(self, forcar=False):
        srv = self.pai.servidor
        if srv is None:
            return
        lista = srv.fichas_lista()
        donos = {f["slug"]: srv.fichas_arq.dono(f["slug"]) for f in lista}
        chave = json.dumps([lista, donos], sort_keys=True, default=str)
        if not forcar and chave == self._ultimo:
            return
        self._ultimo = chave
        self._limpar()
        self._fotos = {}
        c = self.c
        self._sec("Fichas da mesa", f"{len(lista)} ficha(s)")
        self._txt(self.corpo, "Cada jogador escolhe a sua ao entrar e cria um código; a ficha fica presa a ele até você liberar. "
                              "Abrir mostra a ficha de verdade: o que você salvar chega ao jogador na hora.", sub=True, wrap=590)
        for f in lista:
            card = self._cartao()
            linha = tk.Frame(card, bg=card["bg"])
            linha.pack(fill="x")
            dados = srv.fichas_arq.ler(f["slug"])[0] if f["foto"] else None
            _miniatura(linha, self._fotos, f["slug"], (dados or {}).get("foto")).pack(side="left", padx=(0, 8))
            tx = tk.Frame(linha, bg=card["bg"])
            tx.pack(side="left", fill="x", expand=True)
            tk.Label(tx, text=f["nome"], bg=card["bg"], fg=c["VINHO"], font=(self.fonte, 12, "bold"), anchor="w").pack(anchor="w")
            sub = (f"{f['personagem'] or 'sem nome'} · nível {f['nivel'] or 1}" if f["tem"] else "ainda sem ficha (o jogador cria ou traz a dele)")
            d = donos.get(f["slug"])
            sub += f"\n{'em uso por ' + f['uso'] + ' · ' if f['uso'] else ''}" + (f"presa desde {d.get('quando', '?')} · código {d['codigo']}" if d else "livre: ninguém escolheu ainda")
            tk.Label(tx, text=sub, bg=card["bg"], fg=c["TINTA2"], font=(self.fonte, 9, "italic"), justify="left", anchor="w").pack(anchor="w")
            bts = tk.Frame(card, bg=card["bg"])
            bts.pack(fill="x", pady=(6, 0))
            ttk.Button(bts, text="Abrir", command=lambda s=f["slug"], tem=f["tem"]: self._abrir(s, tem)).pack(side="left")
            if d:
                ttk.Button(bts, text="Liberar", command=lambda s=f["slug"], n=f["nome"]: self._liberar(s, n)).pack(side="left", padx=4)
            ttk.Button(bts, text="Esvaziar" if srv.fichas_arq.fixa(f["slug"]) else "Excluir",
                       command=lambda s=f["slug"], n=f["nome"], u=f["uso"]: self._excluir(s, n, u)).pack(side="right")
        rod = tk.Frame(self.corpo, bg=c["PERG"])
        rod.pack(fill="x", pady=(12, 0))
        ttk.Button(rod, text="＋ Nova ficha…", command=self._nova).pack(side="left")
        ttk.Button(rod, text="Importar .json…", command=self._importar).pack(side="left", padx=6)
        self._txt(self.corpo, "Pasta: " + srv.fichas_arq.pasta, sub=True, wrap=590, pady=(8, 0))

    def _abrir(self, slug, tem):
        if not tem:
            messagebox.showinfo("Fichas da mesa", "Esta ficha ainda está vazia. Use \"Importar .json…\" para trazer uma pronta, "
                                                  "ou espere o jogador escolher e criar a dele.", parent=self)
            return
        app = self.pai.master
        if hasattr(app, "abrir_da_mesa"):
            app.abrir_da_mesa(self.pai.servidor.fichas_arq.caminho(slug))

    def _liberar(self, slug, nome):
        if messagebox.askyesno("Fichas da mesa", f"Liberar a ficha “{nome}”?\nO próximo jogador que a escolher vira o dono (o conteúdo continua).", parent=self):
            self.pai.servidor.fichas_arq.liberar(slug)
            self.atualizar(True)

    def _excluir(self, slug, nome, uso):
        aviso = f"\n\n{uso} está com ela aberta agora." if uso else ""
        if messagebox.askyesno("Fichas da mesa", f"Tirar a ficha “{nome}” da mesa?\nUma cópia vai para a pasta fichas/backup.{aviso}", parent=self):
            self.pai.servidor.fichas_arq.excluir(slug)
            self.atualizar(True)

    def _nova(self):
        nome = simpledialog.askstring("Nova ficha", "Nome da ficha (em geral, o nome do jogador):", parent=self)
        if nome and nome.strip():
            if not self.pai.servidor.fichas_arq.criar(nome.strip()):
                messagebox.showerror("Fichas da mesa", "Use um nome com letras ou números.", parent=self)
            self.atualizar(True)

    def _importar(self):
        fn = filedialog.askopenfilename(title="Importar ficha", filetypes=[("Ficha Prevalecentes", "*.json"), ("Todos", "*.*")], parent=self)
        if not fn:
            return
        try:
            with open(fn, encoding="utf-8-sig") as f:
                d = json.load(f)
        except (OSError, ValueError) as e:
            messagebox.showerror("Fichas da mesa", f"Não consegui ler o arquivo:\n{e}", parent=self)
            return
        if not e_ficha(d):
            messagebox.showerror("Fichas da mesa", "Este arquivo não é uma ficha de Prevalecentes.", parent=self)
            return
        idt = d.get("identidade") or {}
        nome = simpledialog.askstring("Importar ficha", "Nome da ficha na mesa:", initialvalue=idt.get("player") or idt.get("nome") or "", parent=self)
        if nome and nome.strip():
            self.pai.servidor.fichas_arq.criar(nome.strip(), d)
            self.atualizar(True)


class JanelaEscolherFicha(_Base):
    """O jogador escolhe a ficha da mesa ao entrar."""

    def __init__(self, pai, lista):
        super().__init__(pai, "Escolha a sua ficha", "520x520")
        self.lista = lista
        self._desenhar()

    def _desenhar(self):
        self._limpar()
        c, cod = self.c, _codigos()
        self._sec("Quem é você?")
        self._txt(self.corpo, "A ficha fica guardada com o mestre e acompanha você na sessão. Na primeira vez você cria um código: "
                              "só entra nela de novo quem souber o código.", sub=True, wrap=470)
        for f in self.lista:
            card = self._cartao()
            tk.Label(card, text=f["nome"], bg=card["bg"], fg=c["VINHO"], font=(self.fonte, 12, "bold"), anchor="w").pack(anchor="w")
            if f["uso"]:
                sub, pode = f"em uso por {f['uso']}", False
            elif f["tem"]:
                sub, pode = f"{f['personagem'] or 'sem nome'} · nível {f['nivel'] or 1}" + (" · é a sua" if f["slug"] in cod and f["presa"] else " · já tem dono (pede o código)" if f["presa"] else ""), True
            else:
                sub, pode = "ainda sem ficha: você traz a sua ou cria do zero" + (" · já tem dono (pede o código)" if f["presa"] and f["slug"] not in cod else ""), True
            tk.Label(card, text=sub, bg=card["bg"], fg=c["TINTA2"], font=(self.fonte, 9, "italic"), anchor="w").pack(anchor="w")
            b = ttk.Button(card, text="Escolher", command=lambda x=f: self._escolher(x))
            b.pack(anchor="e")
            if not pode:
                b.state(["disabled"])
        ttk.Button(self.corpo, text="Agora não (jogar sem ficha da mesa)", command=self.destroy).pack(pady=(12, 0))

    def _escolher(self, f):
        cod = _codigos().get(f["slug"], "")
        if not cod or not f["presa"]:
            txt = ("Esta ficha já tem dono. Digite o código dela:" if f["presa"]
                   else "Crie um código para esta ficha (3 a 12 letras ou números).\nSó entra nela de novo quem souber o código:")
            cod = simpledialog.askstring(f["nome"], txt, parent=self)
            if not cod or len(cod.strip()) < 3:
                return
            cod = cod.strip()[:12]
        self.pai.ficha_escolher(f["slug"], cod)
        self.destroy()


class FichasJogador:
    """Parte da janela da sessão (jogador do PC): escolher a ficha da mesa e mantê-la igual à do mestre."""

    def _fichas_init(self):
        self.ficha_mesa = ""         # slug da ficha da mesa que este jogador está usando
        self.ficha_nome = ""
        self.ficha_ver = ""          # versão do .json do mestre que a ficha aberta reflete
        self._ficha_txt = None       # último conteúdo confirmado pela mesa
        self._ficha_indo = None      # conteúdo enviado, esperando a resposta
        self._ficha_cod = ""
        self._ficha_perguntou = False
        self._ficha_tick = 0
        self._tique_ficha = 0
        self.win_fichas = None

    def _ficha_enviar(self, m):
        return bool(self.cliente) and self.cliente.enviar({"t": "fichas", "m": m})

    def fichas_pedir_lista(self):
        self._ficha_enviar({"acao": "listar"})

    def ficha_escolher(self, slug, codigo):
        self._ficha_cod = codigo
        self._ficha_enviar({"acao": "escolher", "slug": slug, "codigo": codigo})

    def ficha_trocar(self):
        self._ficha_perguntou = False
        self.fichas_pedir_lista()

    def _ficha_estado(self):
        app = self.ponte.app if self.ponte else None
        if app is None or not app.inicializado:
            return None, None
        st = app.estado()
        return st, json.dumps(st, sort_keys=True, ensure_ascii=False)

    def _ficha_rotulo(self):
        if hasattr(self, "lbl_ficha_mesa"):
            try:
                self.lbl_ficha_mesa.config(text=f"Ficha da mesa: {self.ficha_nome}" if self.ficha_mesa else "Sem ficha da mesa")
            except tk.TclError:
                pass

    def _fichas_resp(self, r):
        acao = r.get("acao")
        if acao == "listar" and r.get("ok"):
            lista = r.get("fichas") or []
            if self.ficha_mesa:                       # reconectou: retoma a mesma ficha sem perguntar
                self._ficha_enviar({"acao": "escolher", "slug": self.ficha_mesa, "codigo": self._ficha_cod})
            elif lista and not self._ficha_perguntou:
                self._ficha_perguntou = True
                try:
                    if self.win_fichas is not None and self.win_fichas.winfo_exists():
                        self.win_fichas.destroy()
                except tk.TclError:
                    pass
                self.win_fichas = JanelaEscolherFicha(self, lista)
        elif acao == "escolher":
            if not r.get("ok"):
                if self.ficha_mesa and r.get("motivo") != "ficha_em_uso":
                    self.ficha_mesa = ""
                    self._ficha_rotulo()
                messagebox.showwarning("Ficha da mesa", r.get("erro") or "Não consegui escolher a ficha.", parent=self)
                if not self.ficha_mesa:
                    self._ficha_perguntou = False
                    self.fichas_pedir_lista()
                return
            retomando = self.ficha_mesa == r.get("slug")
            self.ficha_mesa, self.ficha_nome, self.ficha_ver = r.get("slug", ""), r.get("nome", ""), r.get("ver", "")
            _guardar_codigo(self.ficha_mesa, self._ficha_cod)
            self._ficha_indo = None
            self._ficha_rotulo()
            if retomando:
                self._ficha_txt = None                # manda o que mudou enquanto estava sem conexão
            elif r.get("existe") and e_ficha(r.get("ficha")):
                self._ficha_receber(r["ficha"])
            else:
                self._ficha_txt = None
                self._ficha_sem_conteudo()
        elif acao == "salvar":
            if r.get("ok"):
                self.ficha_ver, self._ficha_txt = r.get("ver", ""), self._ficha_indo
            elif r.get("conflito"):                   # o mestre mudou o .json: a versão dele vale
                self._ficha_enviar({"acao": "baixar"})
            self._ficha_indo = None
        elif acao == "baixar" and r.get("ok") and e_ficha(r.get("ficha")):
            self.ficha_ver = r.get("ver", "")
            self._ficha_receber(r["ficha"])
            self._mostrar_aviso("O mestre atualizou a sua ficha.") if hasattr(self, "_mostrar_aviso") else None
        elif acao == "ver" and r.get("ok") and r.get("ver") and r["ver"] != self.ficha_ver and self._ficha_indo is None:
            _, txt = self._ficha_estado()
            if txt == self._ficha_txt:                # nada mudou aqui: baixa a do mestre
                self._ficha_enviar({"acao": "baixar"})

    def _ficha_receber(self, ficha):
        app = self.ponte.app if self.ponte else None
        if app is None:
            return
        app.carregar_da_mesa(ficha)
        self._ficha_txt = self._ficha_estado()[1]
        self._ultima_ficha = None

    def _ficha_sem_conteudo(self):
        """A ficha da mesa ainda está vazia: o jogador liga a ficha que já tem (a aberta ou um .json) ou cria do zero."""
        app = self.ponte.app if self.ponte else None
        if app is None:
            return
        w = tk.Toplevel(self)
        w.title("Ficha da mesa")
        w.configure(background=self.c["PERG"], padx=18, pady=14)
        tk.Label(w, text=f"A ficha “{self.ficha_nome}” ainda está vazia.", bg=self.c["PERG"], fg=self.c["VINHO"], font=(self.fonte, 12, "bold")).pack(anchor="w")
        tk.Label(w, text="Escolha de onde ela vem. Depois disso, cada mudança fica guardada com o mestre.", bg=self.c["PERG"], fg=self.c["TINTA2"],
                 font=(self.fonte, 9, "italic")).pack(anchor="w", pady=(0, 8))

        def fazer(f):
            w.destroy()
            f()
        if app.inicializado:
            nome = app.v_nome.get().strip() or "sem nome"
            ttk.Button(w, text=f"Usar a ficha aberta agora ({nome})", command=lambda: fazer(lambda: None)).pack(fill="x", pady=2)
        ttk.Button(w, text="Abrir um arquivo .json…", command=lambda: fazer(app.abrir)).pack(fill="x", pady=2)
        ttk.Button(w, text="Criar uma ficha do zero", command=lambda: fazer(app.abrir_assistente)).pack(fill="x", pady=2)

    def _ficha_sincronizar(self):
        """A cada 2 s: se a ficha aberta mudou, devolve para a mesa; de tempos em tempos confere se o mestre mexeu nela."""
        if not (self.cliente and self.ficha_mesa and self.ponte):
            return
        self._ficha_tick += 1
        st, txt = self._ficha_estado()
        if st is not None and self._ficha_indo is None and txt != self._ficha_txt:
            self._ficha_indo = txt
            if not self._ficha_enviar({"acao": "salvar", "estado": st, "base": self.ficha_ver or None}):
                self._ficha_indo = None
        elif self._ficha_tick % 3 == 0 and self._ficha_indo is None:
            self._ficha_enviar({"acao": "ver"})
