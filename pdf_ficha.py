# -*- coding: utf-8 -*-
"""Exporta a ficha aberta para PDF (reportlab), no visual Vitral: creme, dourado e verde musgo,
com vitrais e vinhas de enfeite."""
import math
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Flowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)

PERG = colors.HexColor("#f4ecd8")
PERG2 = colors.HexColor("#e9dfc3")
CAMPO = colors.HexColor("#fbf6e9")
ZEBRA = colors.HexColor("#f3ebd3")
TINTA = colors.HexColor("#2f3a22")
TINTA2 = colors.HexColor("#666e50")
OURO = colors.HexColor("#b08a3e")
OURO2 = colors.HexColor("#e3cd8f")
VINHO = colors.HexColor("#7d5f1c")     # cor dos títulos (dourado escuro)
VERDE = colors.HexColor("#5d7340")
MUSGO = colors.HexColor("#3f4f2e")     # chumbo dos vitrais e hastes
FOLHA = colors.HexColor("#7d9157")
FAIXA = colors.HexColor("#f8f1dc")
C = {k: colors.HexColor(v) for k, v in dict(VIDA="#9a4a3a", MANA="#4a6a7a", VIGOR="#5d7340", MOV="#4f7a6a", CA="#7a715a",
                                            ATK="#a0553f", DEF="#56708a", PER="#86661f", TAL="#5d7340", ATR="#4a5a36",
                                            DIN="#5d7340").items()}
VIDROS = [OURO, PERG, FOLHA, OURO2]


# ---------------------------------------------------------------- enfeites: só vinhas e vitrais
def _folha(c, x, y, ang, t=3.2 * mm):
    c.saveState()
    c.translate(x, y)
    c.rotate(ang)
    p = c.beginPath()
    p.moveTo(0, 0)
    p.curveTo(t * 0.3, -t * 0.42, t * 0.8, -t * 0.32, t, 0)
    p.curveTo(t * 0.8, t * 0.32, t * 0.3, t * 0.42, 0, 0)
    c.drawPath(p, stroke=0, fill=1)
    c.restoreState()


def _vinha(c, x0, x1, y, amp=1.1 * mm, passo=9 * mm, t=2.6 * mm):
    """Ramo ondulado de x0 a x1 com folhas alternadas."""
    c.saveState()
    c.setStrokeColor(FOLHA)
    c.setFillColor(FOLHA)
    c.setLineWidth(0.6)
    n = max(1, int(abs(x1 - x0) / passo))
    dx = (x1 - x0) / n
    p = c.beginPath()
    p.moveTo(x0, y)
    for i in range(n):
        s = 1 if i % 2 == 0 else -1
        p.curveTo(x0 + dx * (i + 0.33), y + amp * s, x0 + dx * (i + 0.66), y + amp * s, x0 + dx * (i + 1), y)
    c.drawPath(p, stroke=1, fill=0)
    for i in range(n):
        s = 1 if i % 2 == 0 else -1
        _folha(c, x0 + dx * (i + 0.5), y + amp * 0.75 * s, (48 if dx > 0 else 132) * s, t)
    c.restoreState()


def _canto(c, x, y, sx, sy, tam=30 * mm):
    """Vinha de canto: nasce no canto (x, y) e sobe pelos dois lados; sx/sy = +1 ou -1 dizem para onde."""
    c.saveState()
    c.translate(x, y)
    c.scale(sx, sy)
    c.setStrokeColor(FOLHA)
    c.setFillColor(FOLHA)
    c.setLineWidth(0.7)
    for horizontal in (True, False):
        p = c.beginPath()
        p.moveTo(1.5 * mm, 1.5 * mm)
        pts = [(tam * 0.30, 3.6 * mm, tam * 0.55, 0.4 * mm, tam * 0.80, 2.4 * mm), (tam * 0.90, 3.2 * mm, tam * 0.96, 4.4 * mm, tam, 4.0 * mm)]
        for a in pts:
            p.curveTo(*(a if horizontal else (a[1], a[0], a[3], a[2], a[5], a[4])))
        c.drawPath(p, stroke=1, fill=0)
        for f, alt, ang in ((0.18, 2.6, 62), (0.34, 2.7, -48), (0.50, 1.5, 58), (0.66, 1.5, -44), (0.82, 2.6, 52), (0.97, 4.1, 20)):
            px, py, an = tam * f, alt * mm, ang
            if not horizontal:
                px, py, an = py, px, 90 - ang
            _folha(c, px, py, an, 3.0 * mm)
    c.restoreState()


def _faixa_vitral(c, x, y, larg, alt=6.5 * mm):
    """Faixa de vitral: vidros coloridos com um arco em cada um, separados por chumbo."""
    n = max(4, int(round(larg / (8.5 * mm))))
    w = larg / n
    c.saveState()
    c.setStrokeColor(MUSGO)
    c.setLineWidth(0.7)
    for i in range(n):
        c.setFillColor(VIDROS[i % 4])
        c.rect(x + i * w, y, w, alt, stroke=1, fill=1)
        c.setFillColor(VIDROS[(i + 2) % 4])
        p = c.beginPath()
        p.moveTo(x + i * w + w * 0.18, y)
        p.lineTo(x + i * w + w * 0.18, y + alt * 0.42)
        p.curveTo(x + i * w + w * 0.18, y + alt * 0.78, x + i * w + w * 0.42, y + alt * 0.92, x + i * w + w * 0.5, y + alt * 0.95)
        p.curveTo(x + i * w + w * 0.58, y + alt * 0.92, x + i * w + w * 0.82, y + alt * 0.78, x + i * w + w * 0.82, y + alt * 0.42)
        p.lineTo(x + i * w + w * 0.82, y)
        p.close()
        c.drawPath(p, stroke=1, fill=1)
    c.restoreState()


def _janela(c, x, y, w=11 * mm, h=17 * mm):
    """Vitral em arco (janela): quatro vidros e uma rosácea no meio."""
    c.saveState()
    c.setStrokeColor(MUSGO)
    c.setLineWidth(0.9)
    m, base = x + w / 2, y + h * 0.52

    def arco(esq):
        p = c.beginPath()
        p.moveTo(m, base)
        p.lineTo(m, y + h)
        x_fora = x if esq else x + w
        p.curveTo(m + (x_fora - m) * 0.55, y + h * 0.97, x_fora, y + h * 0.80, x_fora, base)
        p.close()
        return p
    c.setFillColor(OURO2)
    c.drawPath(arco(True), stroke=1, fill=1)
    c.setFillColor(FOLHA)
    c.drawPath(arco(False), stroke=1, fill=1)
    c.setFillColor(PERG)
    c.rect(x, y, w / 2, h * 0.52, stroke=1, fill=1)
    c.setFillColor(OURO)
    c.rect(m, y, w / 2, h * 0.52, stroke=1, fill=1)
    c.line(x, y + h * 0.26, x + w, y + h * 0.26)
    c.setFillColor(FAIXA)
    c.circle(m, base, w * 0.17, stroke=1, fill=1)
    c.restoreState()


class Secao(Flowable):
    """Título de seção: um raminho de vinha, o título em dourado escuro e um fio dourado embaixo."""

    def __init__(self, texto, fonte, largura):
        super().__init__()
        self.texto, self.fonte, self.width, self.height = texto, fonte, largura, 21
        self.keepWithNext = True

    def wrap(self, *_):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setStrokeColor(FOLHA)
        c.setFillColor(FOLHA)
        c.setLineWidth(0.6)
        c.line(0, 8, 8 * mm, 8)
        for px, ang in ((0.6 * mm, 40), (3.0 * mm, -40), (5.4 * mm, 40)):
            _folha(c, px, 8, ang, 2.6 * mm)
        c.setFillColor(VINHO)
        t = c.beginText(10.5 * mm, 5)
        t.setFont(self.fonte, 11.5)
        t.setCharSpace(1.6)
        t.textOut(self.texto)
        c.drawText(t)
        c.setStrokeColor(OURO)
        c.setLineWidth(0.6)
        c.line(0, 1, self.width, 1)


def _fontes():
    """Usa Palatino/Book Antiqua do Windows se existirem; senão Times (embutida no PDF)."""
    pastas = [os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts"), "/usr/share/fonts/truetype/dejavu"]
    opcoes = [("pala.ttf", "palab.ttf", "palai.ttf"), ("BKANT.TTF", "ANTQUAB.TTF", "ANTQUAI.TTF"),
              ("georgia.ttf", "georgiab.ttf", "georgiai.ttf"), ("DejaVuSerif.ttf", "DejaVuSerif-Bold.ttf", "DejaVuSerif-Italic.ttf")]
    for pasta in pastas:
        for reg, neg, ita in opcoes:
            arqs = [os.path.join(pasta, f) for f in (reg, neg, ita)]
            if all(os.path.exists(a) for a in arqs):
                try:
                    pdfmetrics.registerFont(TTFont("Ficha", arqs[0]))
                    pdfmetrics.registerFont(TTFont("Ficha-B", arqs[1]))
                    pdfmetrics.registerFont(TTFont("Ficha-I", arqs[2]))
                    return "Ficha", "Ficha-B", "Ficha-I", True
                except Exception:
                    pass
    return "Times-Roman", "Times-Bold", "Times-Italic", False


def _limpa(txt, unicode_ok):
    txt = "" if txt is None else str(txt)
    txt = txt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    if not unicode_ok:
        for a, b in {"✓": "sim", "✗": "não", "•": "·", "—": "-", "…": "...", "⚜": "", "❧": "", "✦": "*", "÷": "/", "≠": "!="}.items():
            txt = txt.replace(a, b)
    return txt


def gerar_pdf(caminho, app):
    F, FB, FI, uni = _fontes()
    L = lambda t: _limpa(t, uni)  # noqa: E731
    st = app.estado()
    res = app.resumo(st)
    d = app.d
    idt = st["identidade"]

    s_txt = ParagraphStyle("t", fontName=F, fontSize=9, leading=11.5, textColor=TINTA)
    s_peq = ParagraphStyle("p", parent=s_txt, fontSize=8, leading=10, textColor=TINTA2)
    s_cel = ParagraphStyle("c", parent=s_txt, fontSize=8.5, leading=10.5)
    s_cab = ParagraphStyle("h", parent=s_txt, fontName=FB, fontSize=8, leading=10, textColor=FAIXA)
    s_sec = ParagraphStyle("s", fontName=FB, fontSize=11.5, leading=14, textColor=VINHO, spaceBefore=8, spaceAfter=3)
    s_tit = ParagraphStyle("T", fontName=FB, fontSize=24, leading=28, textColor=VINHO, alignment=TA_CENTER)
    s_sub = ParagraphStyle("S", fontName=FI, fontSize=10, leading=13, textColor=TINTA2, alignment=TA_CENTER)
    s_num = ParagraphStyle("n", fontName=FB, fontSize=16, leading=19, textColor=TINTA, alignment=TA_CENTER)
    s_rot = ParagraphStyle("r", fontName=FB, fontSize=7, leading=9, textColor=FAIXA, alignment=TA_CENTER)

    W = A4[0] - 30 * mm

    def P(t, s=s_cel):
        return Paragraph(L(t), s)

    def secao(titulo):
        return Secao(_limpa(titulo.upper(), uni).replace("&amp;", "&"), FB, W)

    def tabela(cab, linhas, larg, cor=C["ATR"], zebra=True):
        sc = s_cab if cor != PERG2 else ParagraphStyle("h2", parent=s_cab, textColor=TINTA)
        dados = [[Paragraph(L(c), sc) for c in cab]] + [[x if hasattr(x, "wrap") else P(x) for x in ln] for ln in linhas]
        t = Table(dados, colWidths=larg, repeatRows=1)
        estilo = [("BACKGROUND", (0, 0), (-1, 0), cor), ("GRID", (0, 0), (-1, -1), 0.3, OURO),
                  ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                  ("BACKGROUND", (0, 1), (-1, -1), CAMPO)]
        if zebra:
            for i in range(2, len(dados), 2):
                estilo.append(("BACKGROUND", (0, i), (-1, i), ZEBRA))
        t.setStyle(TableStyle(estilo))
        return t

    def caixas(itens, cor_padrao=C["ATR"]):
        cel = []
        for rot, val, sub, cor in itens:
            inner = Table([[Paragraph(L(rot.upper()), s_rot)], [Paragraph(L(val), s_num)], [Paragraph(L(sub), ParagraphStyle("x", parent=s_peq, alignment=TA_CENTER))]],
                          colWidths=[W / len(itens) - 4])
            inner.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, 0), cor or cor_padrao), ("BACKGROUND", (0, 1), (0, -1), CAMPO),
                                       ("BOX", (0, 0), (-1, -1), 0.6, OURO), ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
            cel.append(inner)
        t = Table([cel], colWidths=[W / len(itens)] * len(itens))
        t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 2), ("RIGHTPADDING", (0, 0), (-1, -1), 2)]))
        return t

    e = []
    e.append(Paragraph(L("Prevalecentes"), s_tit))
    e.append(Paragraph(L("Ficha do Sonhador · edição 3.2"), s_sub))
    e.append(Spacer(1, 22))
    ident = [["Nome", idt.get("nome", ""), "Player", idt.get("player", ""), "Nível", str(idt.get("nivel", 1))],
             ["Espécie", idt.get("especie", ""), "Sonho", idt.get("sonho", ""), "Guilda", idt.get("guilda", "")]]
    ident = [[c if j % 2 else c.upper() for j, c in enumerate(r)] for r in ident]
    t = Table([[Paragraph(L(c), ParagraphStyle("i", parent=s_peq, fontName=FB, fontSize=7) if j % 2 == 0 else s_cel) for j, c in enumerate(r)] for r in ident],
              colWidths=[19 * mm, 56 * mm, 19 * mm, 40 * mm, 19 * mm, W - 153 * mm])
    t.setStyle(TableStyle([("LINEBELOW", (1, 0), (1, -1), 0.4, OURO), ("LINEBELOW", (3, 0), (3, -1), 0.4, OURO),
                           ("LINEBELOW", (5, 0), (5, -1), 0.4, OURO), ("VALIGN", (0, 0), (-1, -1), "BOTTOM")]))
    e.append(t)

    # características de espécie: os ajustes de atributo e o par descritivo (vantagem e desvantagem)
    nomes_atr = {"VIT": "Vitalidade", "MEN": "Mente", "TEN": "Tenacidade", "FOR": "Força", "DES": "Destreza", "INT": "Inteligência", "FE": "Fé", "ARC": "Arcano"}
    ajustes = []
    for k, nome in nomes_atr.items():
        try:
            v = int(str((st.get("atributos") or {}).get(k, {}).get("especie", "0")).strip() or 0)
        except ValueError:
            v = 0
        if v:
            ajustes.append(f"{'+' if v > 0 else '−'}{abs(v)} {nome}")
    notas_esp = str(st.get("especie_notas") or "").strip()
    if idt.get("especie") or ajustes or notas_esp:
        e.append(secao("Características de espécie"))
        e.append(Paragraph(f"<b>{L(idt.get('especie') or 'Espécie')}</b>" + (f" — atributos: {L(', '.join(ajustes))}" if ajustes else ""), s_txt))
        e.append(Paragraph(L(notas_esp).replace("\n", "<br/>") if notas_esp else L("Sem par descritivo anotado (vantagem e desvantagem da espécie)."),
                           s_txt if notas_esp else s_peq))

    ch = res["Características"]
    e.append(secao("Vigor do corpo"))
    e.append(caixas([("Vida", str(ch["Vida máx."]), f"atual {st['vida'].get('atual') or '—'}", C["VIDA"]),
                     ("Mana", str(ch["Mana máx."]), f"atual {st['vida'].get('mana_atual') or '—'}", C["MANA"]),
                     ("Vigor", str(ch["Vigor máx."]), f"+{ch['Vigor por turno']} por turno", C["VIGOR"]),
                     ("Movimento", f"{ch['Movimento (m)']} m", f"{ch['Movimento (m)'] / 1.5:.0f} quadrados", C["MOV"]),
                     ("CA", str(ch["CA"]), "classe de armadura", C["CA"])]))
    e.append(Spacer(1, 4))
    e.append(caixas([("Carga máx.", str(ch["Carga máx."]), f"atual {app._carga_atual():g}", None),
                     ("Iniciativa", f"+{ch['Iniciativa (bônus)']}", f"{ch['Iniciativa (d20)']}d20 (maior)", None),
                     ("Ações extras", str(ch["Ações extras"]), "por Destreza", None),
                     ("Red. de dano", f"{ch['Redução de dano (d4)']}d4" if ch["Redução de dano (d4)"] else "—", "por Tenacidade", None),
                     ("Descoberta", str(ch["Descoberta"]), "por Arcano", None)]))
    e.append(Paragraph(L("Resistências: " + (", ".join(d.get("resistencias", [])) or "nenhuma")), s_peq))

    e.append(secao("Atributos"))
    linhas = []
    for k in ["VIT", "MEN", "TEN", "FOR", "DES", "INT", "FE", "ARC"]:
        nome = {"VIT": "Vitalidade", "MEN": "Mente", "TEN": "Tenacidade", "FOR": "Força", "DES": "Destreza", "INT": "Inteligência", "FE": "Fé", "ARC": "Arcano"}[k]
        v = res["Atributos"][nome]
        bc = d["bc"][k]
        linhas.append([nome, str(v), str(res["Curva"][nome]), f"+{bc}", f"{1 + min(99, v) // 20}d20", "sim" if v >= 60 else ""])
    e.append(tabela(["Atributo", "Pontos", "Curva", "BC", "Dados", "Vantagem"], linhas, [40 * mm, 22 * mm, 22 * mm, 22 * mm, 22 * mm, W - 128 * mm]))

    e.append(secao("Ataque e defesa"))
    ad = list(res["Ataque e defesa"].items())
    atk, dfs = ad[0:4] + [ad[8]], ad[4:8] + [ad[9]]
    fmt = lambda kv: f"+{kv[1]}" if not kv[0].startswith("DT") else str(kv[1])  # noqa: E731
    e.append(tabela(["Ataque", "Bônus", "Defesa", "Bônus"], [[atk[i][0], fmt(atk[i]), dfs[i][0], fmt(dfs[i])] for i in range(5)],
                    [55 * mm, W / 2 - 55 * mm, 55 * mm, W / 2 - 55 * mm], cor=C["ATK"]))

    e.append(secao("Perícias"))
    per = list(res["Perícias"].items())
    met = (len(per) + 1) // 2
    e.append(tabela(["Perícia (• treinada)", "Bônus", "Perícia (• treinada)", "Bônus"],
                    [[per[i][0], f"+{per[i][1]}", per[i + met][0] if i + met < len(per) else "", f"+{per[i + met][1]}" if i + met < len(per) else ""]
                     for i in range(met)], [60 * mm, W / 2 - 60 * mm, 60 * mm, W / 2 - 60 * mm], cor=C["PER"]))

    e.append(secao("Armas"))
    linhas = []
    for i, ui in enumerate(app.armas_ui, start=1):
        if not ui["grupo"].get():
            continue
        g = lambda k: ui[k].cget("text")  # noqa: E731
        linhas.append([f"{ui['grupo'].get()} nv {ui['nivel'].get()}", g("l_dano"), g("l_tipo"), g("l_crit"), g("l_acerto"), g("l_peso"),
                       ui["props"].get()])
    e.append(tabela(["Arma", "Dano", "Tipo", "Crít.", "Ataque", "Peso", "Propriedades"], linhas or [["—", "", "", "", "", "", ""]],
                    [32 * mm, 28 * mm, 22 * mm, 12 * mm, 38 * mm, 12 * mm, W - 144 * mm], cor=C["ATK"]))
    for ui in app.armas_ui:
        arma = app.armas_por_nome.get(ui["grupo"].get())
        if not arma or not arma.get("acoes"):
            continue
        e.append(Paragraph(L(f"Ações — {arma['nome']}"), ParagraphStyle("aa", parent=s_txt, fontName=FB, textColor=VINHO, spaceBefore=6)))
        for x in arma["acoes"]:
            e.append(Paragraph(("&nbsp;&nbsp;&nbsp;&nbsp;" if x.get("sub") else "") + f"<b>{L(x['nome'])}</b> — {L(x['texto'])}",
                               ParagraphStyle("ax", parent=s_txt, fontSize=8.5, leading=10.5, spaceAfter=1.5)))
    eq = st["equip"]
    e.append(Spacer(1, 4))
    e.append(tabela(["Proteção", "Equipamento", "CA", "Peso"],
                    [["Armadura", eq.get("armadura") or "—", f"+{eq.get('armadura_ca', 0)}", str(eq.get("armadura_peso", 0))],
                     ["Escudo", eq.get("escudo") or "—", f"+{eq.get('escudo_ca', 0)}", str(eq.get("escudo_peso", 0))]],
                    [30 * mm, W - 70 * mm, 20 * mm, 20 * mm], cor=C["CA"]))

    e.append(secao("Talismãs e sets"))
    tl = [[t["nome"], app.tal_info.get(t["nome"], {}).get("efeito", t.get("efeito", ""))] for t in st["talismas"] if t.get("nome")]
    e.append(tabela(["Talismã", "Efeito"], tl or [["—", ""]], [55 * mm, W - 55 * mm], cor=C["TAL"]))
    e.append(Spacer(1, 4))
    sp = [[p, x.get("set") if x.get("set") and not x.get("set", "").startswith("—") else "—", x.get("nome", "")] for p, x in st["set"].items()]
    e.append(tabela(["Peça", "Set", "Nome"], sp, [30 * mm, 50 * mm, W - 80 * mm]))
    for n, q, e2, e4 in app.sets_ativos()[1]:
        e.append(Paragraph(L(f"<b>{n}</b> ({q} peças): {e2}" + (f" <br/>4 peças: {e4}" if e4 else "")).replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>").replace("&lt;br/&gt;", "<br/>"), s_txt))

    e.append(secao("Inventário"))
    inv = [[x["item"], x.get("qtd") or "1", x["carga"]] for x in st["inventario"] if x.get("item")]
    e.append(tabela(["Item", "Qtd", "Peso"], inv or [["—", "", ""]], [W - 45 * mm, 20 * mm, 25 * mm], cor=PERG2))
    e.append(Paragraph(L(f"Carga atual {app._carga_atual():g} de {ch['Carga máx.']}  ·  Dinheiro: {st.get('dinheiro') or '—'}"), s_peq))

    e.append(secao("Encantamentos"))
    e.append(Paragraph(L(f"Espaços {res['Encantamentos']['Espaços usados']}/{res['Encantamentos']['Espaços máx.']}  ·  "
                         f"DT Feitiçaria {d['dt_feiticaria']}  ·  DT Desejo {d['dt_desejo']}"), s_peq))
    for x in st["encantamentos"]:
        en = app.enc_por_nome.get(x["familia"])
        if not en:
            continue
        vs = [v for v in en["versoes"] if v["nivel"] in x.get("versoes", [])] or en["versoes"][:1]
        v = vs[-1]
        bloco = [Paragraph(L(f"{en['nome']}") + f"<font color='#666e50' size='8'>  {L(en['dominio'])} · {L(en['categoria'])} · Espaço {en['espaco']}"
                           f"{' · EQUIPADO' if x.get('equipado') else ''}</font>", ParagraphStyle("en", parent=s_txt, fontName=FB, textColor=VINHO, spaceBefore=4)),
                 Paragraph(L(f"Versões aprendidas: {', '.join(map(str, x.get('versoes', [])))}  ·  Maior: {v['tier']} nível {v['nivel']}  ·  "
                             f"Mana {v['mana']}  ·  Ação {v['acao']}  ·  Distância {v['distancia']}"), s_peq),
                 Paragraph(L(v["descricao"]), s_txt)]
        e.append(KeepTogether(bloco))

    e.append(secao("Talentos"))
    tal = []
    for sl, nome in st["talentos"].items():
        if nome:
            info = app.tal_por_nome.get(nome, {})
            tal.append([sl if sl != "extra" else "Versátil", nome, info.get("descricao", "")])
    e.append(tabela(["Nv", "Talento", "Efeito"], tal or [["—", "", ""]], [14 * mm, 40 * mm, W - 54 * mm]))

    if st.get("sem_alma"):
        e.append(secao("Alma"))
        e.append(Paragraph(L("Sem alma: recebe 2 pontos de atributo a mais por nível."), s_txt))
    else:
        al = st["alma"]
        e.append(secao("Alma"))
        e.append(Paragraph(L(f"{al.get('nome') or 'Sem nome'}  ·  nível {d['alma_nivel']}  ·  usos por descanso {d['alma_usos']}"), ParagraphStyle("a", parent=s_txt, fontName=FB)))
        if al.get("historia"):
            e.append(Paragraph(L(al["historia"]).replace("\n", "<br/>"), s_txt))
        hab = [[h["nome"], h["efeito"], h["tipo"]] for h in al.get("habilidades", []) if h.get("nome")]
        if hab:
            e.append(tabela(["Habilidade", "Efeito", "Tipo"], hab, [40 * mm, W - 65 * mm, 25 * mm]))

    e.append(secao("Condições e Portão da Morte"))
    co = [[n, x.get("atual") or "0", x.get("max") or "100", x.get("notas", "")] for n, x in st["condicoes"].items()]
    e.append(tabela(["Condição", "Atual", "Máx.", "Notas"], co, [32 * mm, 18 * mm, 18 * mm, W - 68 * mm], cor=PERG2))
    po = st["portao"]
    e.append(Paragraph(L(f"Portão da Morte: {sum(po.get('Sucessos', []))} sucessos, {sum(po.get('Falhas', []))} falhas  ·  "
                         f"Cicatrizes: {st.get('cicatrizes') or '—'}"), s_peq))

    vi = st["vinculos"]
    if any(vi.values()):
        e.append(secao("Vínculos e metas"))
        for r, k in (("Vínculo (grupo)", "grupo"), ("Vínculo (mundo)", "mundo"), ("Metas de vida", "metas")):
            if vi.get(k):
                e.append(Paragraph(f"<b>{L(r)}:</b> {L(vi[k])}", s_txt))
    def fundo(canv, doc):
        canv.saveState()
        canv.setFillColor(PERG)
        canv.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)
        canv.setStrokeColor(OURO)
        canv.setLineWidth(1.2)
        canv.rect(9 * mm, 9 * mm, A4[0] - 18 * mm, A4[1] - 18 * mm)
        canv.setLineWidth(0.4)
        canv.rect(10.5 * mm, 10.5 * mm, A4[0] - 21 * mm, A4[1] - 21 * mm)
        # vitral no alto, vinhas nos cantos de baixo e um ramo acima do rodapé
        _faixa_vitral(canv, 10.5 * mm, A4[1] - 10.5 * mm - 6.5 * mm, A4[0] - 21 * mm)
        _canto(canv, 10.5 * mm, 10.5 * mm, 1, 1)
        _canto(canv, A4[0] - 10.5 * mm, 10.5 * mm, -1, 1)
        if doc.page == 1:
            _janela(canv, 19 * mm, A4[1] - 41 * mm)
            _janela(canv, A4[0] - 30 * mm, A4[1] - 41 * mm)
            _vinha(canv, A4[0] / 2 - 42 * mm, A4[0] / 2 - 6 * mm, A4[1] - 40.4 * mm)
            _vinha(canv, A4[0] / 2 + 42 * mm, A4[0] / 2 + 6 * mm, A4[1] - 40.4 * mm)
        canv.setFont(FI, 8)
        canv.setFillColor(TINTA2)
        canv.drawCentredString(A4[0] / 2, 5.5 * mm, L(f"{idt.get('nome') or 'Sonhador'} · Prevalecentes · página {doc.page}"))
        canv.restoreState()

    doc = SimpleDocTemplate(caminho, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=21 * mm, bottomMargin=19 * mm,
                            title=f"Ficha — {idt.get('nome') or 'Sonhador'}", author=idt.get("player", ""))
    doc.build(e, onFirstPage=fundo, onLaterPages=fundo)
