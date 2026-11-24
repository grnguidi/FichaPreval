# -*- coding: utf-8 -*-
"""Exporta a ficha aberta para PDF (reportlab), no visual Catedral: roxo profundo, lilás e verde-claro,
com dourado e chumbo. A página é uma janela de catedral: moldura de chumbo e ouro com cantoneiras, colunas de vitral
nas laterais, faixa de vitral no alto, arcada de claustro embaixo com o fólio em romanos, o título sob um arco ogival
entre rosáceas e lancetas, seções em flâmulas com capitular gótica e os números do corpo em janelas ogivais."""
import math
import os
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Flowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)

PERG = colors.HexColor("#f2eee8")      # pedra clara (tema Catedral)
PERG2 = colors.HexColor("#e2dad0")
CAMPO = colors.HexColor("#faf8f4")
ZEBRA = colors.HexColor("#ece6f0")
TINTA = colors.HexColor("#2a1f33")
TINTA2 = colors.HexColor("#5f5370")
OURO = colors.HexColor("#b8955a")
OURO2 = colors.HexColor("#e6d29e")
VINHO = colors.HexColor("#5e3591")     # roxo dos títulos de seção
AZUL = colors.HexColor("#4a2c6b")      # roxo profundo (nome antigo mantido: faixas e títulos)
VERDE = colors.HexColor("#4e8a4a")
LILAS = colors.HexColor("#b79ad6")
CHUMBO = colors.HexColor("#2a1a3d")
MUSGO = CHUMBO                         # moldura da foto
FAIXA = colors.HexColor("#fbf9fd")
VIDROS = [colors.HexColor(x) for x in ("#b79ad6", "#a8d89a", "#7a4fae", "#e2cf9a", "#dccbf0", "#8fc17f")]
C = {k: colors.HexColor(v) for k, v in dict(VIDA="#a3334f", MANA="#5b4fae", VIGOR="#4e8a4a", MOV="#3f8a7a", CA="#6f6678",
                                            ATK="#a3334f", DEF="#5b4fae", PER="#8a5a9e", TAL="#4e8a4a", ATR="#4a2c6b",
                                            DIN="#4e8a4a").items()}


# ---------------------------------------------------------------- enfeites: vitrais, rosáceas e janelas em arco
def _rosacea(c, cx, cy, r):
    """Rosácea: 8 vidros coloridos com chumbo e um miolo claro."""
    c.saveState()
    c.setStrokeColor(CHUMBO)
    c.setLineWidth(max(0.4, r * 0.06))
    for k in range(8):
        c.setFillColor(VIDROS[k % 4])
        p = c.beginPath()
        p.moveTo(cx, cy)
        p.arcTo(cx - r, cy - r, cx + r, cy + r, k * 45, 45)
        p.close()
        c.drawPath(p, stroke=1, fill=1)
    for k in range(8):
        a = k * math.pi / 4
        c.setFillColor(VIDROS[4])
        c.circle(cx + math.cos(a + math.pi / 8) * r * 0.52, cy + math.sin(a + math.pi / 8) * r * 0.52, r * 0.17, stroke=1, fill=1)
    c.setLineWidth(max(0.8, r * 0.13))
    c.circle(cx, cy, r, stroke=1, fill=0)
    c.setStrokeColor(OURO2)
    c.setLineWidth(max(0.3, r * 0.05))
    c.circle(cx, cy, r * 0.93, stroke=1, fill=0)
    c.setLineWidth(max(0.4, r * 0.06))
    c.setFillColor(colors.HexColor("#f6f1fa"))
    c.circle(cx, cy, r * 0.24, stroke=1, fill=1)
    c.restoreState()


def _roda(c, cx, cy, r, cor=None, aro=None):     # nome antigo: agora é uma rosácea
    _rosacea(c, cx, cy, r)


def _faixa_vitral(c, x, y, larg, alt=6.5 * mm):
    """Faixa do alto: vidros coloridos separados por chumbo."""
    n = max(6, int(larg / (5 * mm)))
    w = larg / n
    c.saveState()
    c.setStrokeColor(CHUMBO)
    c.setLineWidth(1.1)
    for i in range(n):
        c.setFillColor(VIDROS[i % 6])
        c.rect(x + i * w, y, w, alt, stroke=1, fill=1)
    c.setLineWidth(1.6)
    c.rect(x, y, larg, alt, stroke=1, fill=0)
    c.restoreState()


def _lanceta(c, x, y, w=4.2 * mm, h=9 * mm):
    """Janela em arco ogival (lanceta), com dois vidros e chumbo."""
    c.saveState()
    c.setStrokeColor(CHUMBO)
    c.setLineWidth(0.8)
    p = c.beginPath()
    p.moveTo(x, y)
    p.lineTo(x, y + h * 0.6)
    p.curveTo(x, y + h * 0.9, x + w * 0.35, y + h, x + w / 2, y + h)
    p.curveTo(x + w * 0.65, y + h, x + w, y + h * 0.9, x + w, y + h * 0.6)
    p.lineTo(x + w, y)
    p.close()
    c.setFillColor(LILAS)
    c.drawPath(p, stroke=1, fill=1)
    c.setFillColor(VIDROS[1])
    c.rect(x + w / 2, y, w / 2, h * 0.45, stroke=1, fill=1)
    c.line(x + w / 2, y + h * 0.45, x + w / 2, y + h * 0.98)
    c.line(x, y + h * 0.45, x + w, y + h * 0.45)
    c.restoreState()


def _quadrifolio(c, cx, cy, r):
    """Quadrifólio: quatro lóbulos lilás com miolo verde-claro."""
    c.saveState()
    c.setStrokeColor(CHUMBO)
    c.setLineWidth(0.5)
    c.setFillColor(LILAS)
    for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)):
        c.circle(cx + dx * r * 0.5, cy + dy * r * 0.5, r * 0.48, stroke=1, fill=1)
    c.setFillColor(VIDROS[1])
    c.circle(cx, cy, r * 0.3, stroke=1, fill=1)
    c.restoreState()


def _ogiva(p, x, y, w, h_reto, h_arco):
    """Contorno de janela em arco ogival (ponta no alto): lados retos de h_reto e arco de h_arco."""
    p.moveTo(x, y)
    p.lineTo(x, y + h_reto)
    p.curveTo(x, y + h_reto + h_arco * 0.55, x + w * 0.28, y + h_reto + h_arco * 0.92, x + w / 2, y + h_reto + h_arco)
    p.curveTo(x + w * 0.72, y + h_reto + h_arco * 0.92, x + w, y + h_reto + h_arco * 0.55, x + w, y + h_reto)
    p.lineTo(x + w, y)
    p.close()
    return p


def _arcada(c, x0, x1, y, alt=5 * mm):
    """Arcada: fileira de arcos ogivais com trifólios, como o claustro de uma catedral."""
    n = max(4, int((x1 - x0) / (7 * mm)))
    w = (x1 - x0) / n
    c.saveState()
    for i in range(n):
        x = x0 + i * w
        c.setStrokeColor(CHUMBO)
        c.setLineWidth(0.7)
        c.setFillColor(VIDROS[i % 6] if i % 2 else colors.HexColor("#efe8f5"))
        c.drawPath(_ogiva(c.beginPath(), x + 0.6, y, w - 1.2, alt * 0.45, alt * 0.55), stroke=1, fill=1)
        c.setFillColor(OURO2)
        c.setStrokeColor(OURO)
        c.setLineWidth(0.3)
        c.circle(x + w / 2, y + alt * 0.62, alt * 0.09, stroke=1, fill=1)
    c.setStrokeColor(OURO)
    c.setLineWidth(0.8)
    c.line(x0, y, x1, y)
    c.restoreState()


def _coluna_vitral(c, x, y0, y1, larg=2.4 * mm):
    """Coluna lateral de vitral: vidros estreitos empilhados, presos por chumbo."""
    alt = 7 * mm
    n = max(1, int((y1 - y0) / alt))
    alt = (y1 - y0) / n
    c.saveState()
    c.setStrokeColor(CHUMBO)
    c.setLineWidth(0.6)
    for i in range(n):
        c.setFillColor(VIDROS[(i * 2 + (1 if x > A4[0] / 2 else 0)) % 6])
        c.rect(x, y0 + i * alt, larg, alt, stroke=1, fill=1)
        if i % 3 == 1:   # um losango de vidro a cada três
            cx, cy = x + larg / 2, y0 + i * alt + alt / 2
            p = c.beginPath()
            p.moveTo(cx, cy + alt * 0.32)
            p.lineTo(cx + larg * 0.38, cy)
            p.lineTo(cx, cy - alt * 0.32)
            p.lineTo(cx - larg * 0.38, cy)
            p.close()
            c.setFillColor(OURO2)
            c.drawPath(p, stroke=1, fill=1)
    c.setLineWidth(1.0)
    c.rect(x, y0, larg, y1 - y0, stroke=1, fill=0)
    c.restoreState()


def _cantoneira(c, cx, cy, r=3.2 * mm):
    """Canto da moldura: quadrifólio dentro de um losango dourado."""
    c.saveState()
    p = c.beginPath()
    p.moveTo(cx, cy + r * 1.35)
    p.lineTo(cx + r * 1.35, cy)
    p.lineTo(cx, cy - r * 1.35)
    p.lineTo(cx - r * 1.35, cy)
    p.close()
    c.setFillColor(CHUMBO)
    c.setStrokeColor(OURO)
    c.setLineWidth(0.8)
    c.drawPath(p, stroke=1, fill=1)
    c.restoreState()
    _quadrifolio(c, cx, cy, r * 0.85)


def _romano(n):
    out = ""
    for v, s in ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
                 (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= v:
            out += s
            n -= v
    return out


def _filete(c, x0, x1, y, cor=None, larg=1.0):
    c.saveState()
    c.setStrokeColor(cor or LILAS)
    c.setLineWidth(larg)
    c.line(x0, y, x1, y)
    c.restoreState()


def _foto(c, txt, x, y, lado):
    """Foto do personagem numa moldura dourada. Devolve False se a ficha não tem foto (ou ela não pôde ser lida)."""
    try:
        import io
        import foto as F
        from reportlab.lib.utils import ImageReader
        bruto, _ = F.bytes_de(txt)
        if bruto is None:
            return False
        c.drawImage(ImageReader(io.BytesIO(bruto)), x, y, lado, lado, preserveAspectRatio=True, anchor="c", mask="auto")
        c.saveState()
        c.setStrokeColor(OURO)
        c.setLineWidth(1.4)
        c.rect(x, y, lado, lado, stroke=1, fill=0)
        c.setStrokeColor(MUSGO)
        c.setLineWidth(0.4)
        c.rect(x - 1.2, y - 1.2, lado + 2.4, lado + 2.4, stroke=1, fill=0)
        c.restoreState()
        return True
    except Exception:
        return False


FRAK = ""   # letra gótica embutida (KaTeX Fraktur); só é usada quando cobre todas as letras do texto
_FRAK_LETRAS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,;:'-!?()&")


def _frak():
    global FRAK
    if not FRAK:
        base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        arq = os.path.join(base, "fontes", "KaTeX_Fraktur-Bold.ttf")
        try:
            pdfmetrics.registerFont(TTFont("Fraktur", arq))
            FRAK = "Fraktur"
        except Exception:
            FRAK = "-"
    return FRAK if FRAK != "-" else ""


def frak_ok(txt):
    return bool(_frak()) and bool(txt) and all(ch in _FRAK_LETRAS for ch in txt)


class Secao(Flowable):
    """Título de seção: quadrifólio de vitral, capitular gótica em roxo, o resto em versalete e fio duplo dourado."""

    def __init__(self, texto, fonte, largura):
        super().__init__()
        self.texto, self.fonte, self.width, self.height = texto, fonte, largura, 24
        self.keepWithNext = True

    def wrap(self, *_):
        return self.width, self.height

    def draw(self):
        """Flâmula de chumbo com pontas recortadas, capitular dourada em fraktur e o resto em versalete claro."""
        c = self.canv
        cap, resto = self.texto[:1], self.texto[1:]
        usa_frak = frak_ok(cap)
        larg_txt = (pdfmetrics.stringWidth(cap, FRAK, 17) if usa_frak else 0) + pdfmetrics.stringWidth(resto if usa_frak else self.texto, self.fonte, 11) + 1.3 * len(self.texto)
        x0, x1, y0, y1 = 6.5 * mm, 6.5 * mm + larg_txt + 9 * mm, 2.5, 17.5
        c.saveState()
        p = c.beginPath()   # flâmula: retângulo com cauda bifurcada à direita
        p.moveTo(x0, y0)
        p.lineTo(x1, y0)
        p.lineTo(x1 - 3 * mm, (y0 + y1) / 2)
        p.lineTo(x1, y1)
        p.lineTo(x0, y1)
        p.close()
        c.setFillColor(CHUMBO)
        c.setStrokeColor(OURO)
        c.setLineWidth(0.9)
        c.drawPath(p, stroke=1, fill=1)
        c.setStrokeColor(OURO2)
        c.setLineWidth(0.35)
        c.line(x0 + 1.2, y0 + 1.6, x1 - 2.2, y0 + 1.6)
        c.line(x0 + 1.2, y1 - 1.6, x1 - 2.2, y1 - 1.6)
        c.restoreState()
        # fio duplo dourado até o fim da coluna, com um trifólio no final
        _filete(c, x1 + 1.5 * mm, self.width - 3 * mm, (y0 + y1) / 2 + 1.2, OURO, 0.7)
        _filete(c, x1 + 1.5 * mm, self.width - 3 * mm, (y0 + y1) / 2 - 1.2, OURO, 0.7)
        c.saveState()
        c.setFillColor(LILAS)
        c.setStrokeColor(CHUMBO)
        c.setLineWidth(0.4)
        for dx, dy in ((0, 1.3), (-1.2, -0.6), (1.2, -0.6)):
            c.circle(self.width - 1.6 * mm + dx, (y0 + y1) / 2 + dy, 1.25, stroke=1, fill=1)
        c.restoreState()
        _quadrifolio(c, 3 * mm, (y0 + y1) / 2, 2.7 * mm)
        t = c.beginText(x0 + 3.2 * mm, y0 + 4.2)
        if usa_frak:
            t.setFillColor(OURO2)
            t.setFont(FRAK, 17)
            t.textOut(cap)
        else:
            resto = self.texto
        t.setFillColor(colors.HexColor("#f3ecfa"))
        t.setFont(self.fonte, 11)
        t.setCharSpace(1.3)
        t.textOut(resto)
        c.drawText(t)


class CaixasOgivais(Flowable):
    """Fileira de janelas em arco ogival: o vidro colorido do arco leva o rótulo; a pedra embaixo, o valor."""

    def __init__(self, itens, largura, fontes, limpa):
        super().__init__()
        self.itens, self.width, self.height = itens, largura, 25 * mm
        self.F, self.FB, self.FI = fontes
        self.L = limpa

    def wrap(self, *_):
        return self.width, self.height

    def draw(self):
        c = self.canv
        n = len(self.itens)
        w = self.width / n
        for i, (rot, val, sub, cor) in enumerate(self.itens):
            x, larg = i * w + 1.6 * mm, w - 3.2 * mm
            h_reto, h_arco = 13.5 * mm, 9 * mm
            c.saveState()
            # a pedra (corpo) e o vidro (arco) com o rótulo
            c.setFillColor(CAMPO)
            c.setStrokeColor(CHUMBO)
            c.setLineWidth(1.4)
            c.drawPath(_ogiva(c.beginPath(), x, 1, larg, h_reto, h_arco), stroke=1, fill=1)
            p = c.beginPath()
            p.moveTo(x, 1 + h_reto)
            p.curveTo(x, 1 + h_reto + h_arco * 0.55, x + larg * 0.28, 1 + h_reto + h_arco * 0.92, x + larg / 2, 1 + h_reto + h_arco)
            p.curveTo(x + larg * 0.72, 1 + h_reto + h_arco * 0.92, x + larg, 1 + h_reto + h_arco * 0.55, x + larg, 1 + h_reto)
            p.close()
            c.setFillColor(cor or C["ATR"])
            c.drawPath(p, stroke=1, fill=1)
            c.setStrokeColor(OURO)
            c.setLineWidth(0.5)
            c.drawPath(_ogiva(c.beginPath(), x + 1.6, 2.6, larg - 3.2, h_reto - 1.6, h_arco - 1.8), stroke=1, fill=0)
            # rótulo no vidro, valor grande e a linha de apoio
            c.setFillColor(colors.HexColor("#f6f1fa"))
            rot_t = self.L(rot.upper())
            tam = 6.6
            while pdfmetrics.stringWidth(rot_t, self.FB, tam) > larg * 0.78 and tam > 4.8:
                tam -= 0.2
            c.setFont(self.FB, tam)
            c.drawCentredString(x + larg / 2, 1 + h_reto + 2.3 * mm, rot_t)
            c.setFillColor(TINTA)
            v = self.L(val)
            tv = 15
            while pdfmetrics.stringWidth(v, self.FB, tv) > larg * 0.9 and tv > 8:
                tv -= 0.5
            c.setFont(self.FB, tv)
            c.drawCentredString(x + larg / 2, 1 + 6.2 * mm, v)
            c.setFillColor(TINTA2)
            st = self.L(sub)
            ts = 6.8
            while pdfmetrics.stringWidth(st, self.FI, ts) > larg * 0.92 and ts > 4.8:
                ts -= 0.2
            c.setFont(self.FI, ts)
            c.drawCentredString(x + larg / 2, 1 + 2.2 * mm, st)
            c.restoreState()


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
    s_tit = ParagraphStyle("T", fontName=FB, fontSize=24, leading=28, textColor=AZUL, alignment=TA_CENTER)
    s_sub = ParagraphStyle("S", fontName=FI, fontSize=10, leading=13, textColor=TINTA2, alignment=TA_CENTER)
    s_num = ParagraphStyle("n", fontName=FB, fontSize=16, leading=19, textColor=TINTA, alignment=TA_CENTER)
    s_rot = ParagraphStyle("r", fontName=FB, fontSize=7, leading=9, textColor=FAIXA, alignment=TA_CENTER)

    W = A4[0] - 34 * mm

    def P(t, s=s_cel):
        return Paragraph(L(t), s)

    def secao(titulo):
        return Secao(_limpa(titulo.upper(), uni).replace("&amp;", "&"), FB, W)

    def tabela(cab, linhas, larg, cor=C["ATR"], zebra=True):
        sc = s_cab if cor != PERG2 else ParagraphStyle("h2", parent=s_cab, textColor=TINTA)
        dados = [[Paragraph(L(c), sc) for c in cab]] + [[x if hasattr(x, "wrap") else P(x) for x in ln] for ln in linhas]
        t = Table(dados, colWidths=larg, repeatRows=1)
        estilo = [("BACKGROUND", (0, 0), (-1, 0), cor), ("GRID", (0, 0), (-1, -1), 0.3, OURO),
                  ("BOX", (0, 0), (-1, -1), 1.3, CHUMBO), ("LINEBELOW", (0, 0), (-1, 0), 1.2, OURO),
                  ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                  ("BACKGROUND", (0, 1), (-1, -1), CAMPO)]
        if zebra:
            for i in range(2, len(dados), 2):
                estilo.append(("BACKGROUND", (0, i), (-1, i), ZEBRA))
        t.setStyle(TableStyle(estilo))
        return t

    def caixas(itens, cor_padrao=C["ATR"]):
        return CaixasOgivais([(r, v, s, cor or cor_padrao) for r, v, s, cor in itens], W, (F, FB, FI), L)

    e = []
    nome = idt.get("nome") or "Sonhador"
    if frak_ok(nome):
        s_tit = ParagraphStyle("T", parent=s_tit, fontName=FRAK, fontSize=30, leading=32)
    e.append(Paragraph(L(nome), s_tit))
    e.append(Paragraph(L("Conestoga connection · Ficha do Sonhador · edição 3.3"), s_sub))
    e.append(Spacer(1, 22))
    import foto as _F
    tem_foto = _F.valida(st.get("foto"))      # com foto, a identificação encolhe para dar lugar a ela
    ident = [["Nome", idt.get("nome", ""), "Player", idt.get("player", ""), "Nível", str(idt.get("nivel", 1))],
             ["Espécie", idt.get("especie", ""), "Sonho", idt.get("sonho", ""), "Guilda", idt.get("guilda", "")]]
    ident = [[c if j % 2 else c.upper() for j, c in enumerate(r)] for r in ident]
    t = Table([[Paragraph(L(c), ParagraphStyle("i", parent=s_peq, fontName=FB, fontSize=7) if j % 2 == 0 else s_cel) for j, c in enumerate(r)] for r in ident],
              colWidths=([17 * mm, 42 * mm, 17 * mm, 30 * mm, 17 * mm, W - 159 * mm] if tem_foto
                         else [19 * mm, 56 * mm, 19 * mm, 40 * mm, 19 * mm, W - 153 * mm]), hAlign="LEFT")
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
        bloco = [Paragraph(L(f"{en['nome']}") + f"<font color='#5f5546' size='8'>  {L(en['dominio'])} · {L(en['categoria'])} · Espaço {en['espaco']}"
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
        # pedra da catedral: fiadas de blocos bem claras ao fundo
        canv.setStrokeColor(colors.HexColor("#e9e3da"))
        canv.setLineWidth(0.35)
        fiada = 9 * mm
        for j, y in enumerate(range(int(10 * mm), int(A4[1] - 10 * mm), int(fiada))):
            canv.line(10 * mm, y, A4[0] - 10 * mm, y)
            for x in range(int(10 * mm + (0 if j % 2 else 11 * mm)), int(A4[0] - 10 * mm), int(22 * mm)):
                canv.line(x, y, x, y + fiada)
        # a página é uma janela: moldura de chumbo por fora, dourada por dentro, colunas de vitral nas laterais
        canv.setStrokeColor(CHUMBO)
        canv.setLineWidth(2.4)
        canv.rect(8 * mm, 8 * mm, A4[0] - 16 * mm, A4[1] - 16 * mm)
        canv.setStrokeColor(OURO)
        canv.setLineWidth(0.7)
        canv.rect(9.4 * mm, 9.4 * mm, A4[0] - 18.8 * mm, A4[1] - 18.8 * mm)
        _coluna_vitral(canv, 10.6 * mm, 20 * mm, A4[1] - 18 * mm)
        _coluna_vitral(canv, A4[0] - 13 * mm, 20 * mm, A4[1] - 18 * mm)
        _faixa_vitral(canv, 9.4 * mm, A4[1] - 9.4 * mm - 6 * mm, A4[0] - 18.8 * mm, 6 * mm)
        for cx, cy in ((8 * mm, 8 * mm), (A4[0] - 8 * mm, 8 * mm), (8 * mm, A4[1] - 8 * mm), (A4[0] - 8 * mm, A4[1] - 8 * mm)):
            _cantoneira(canv, cx, cy)
        # embaixo, uma arcada de claustro; no meio, o fólio em algarismos romanos num quadrifólio
        _arcada(canv, 14 * mm, A4[0] / 2 - 12 * mm, 10.4 * mm)
        _arcada(canv, A4[0] / 2 + 12 * mm, A4[0] - 14 * mm, 10.4 * mm)
        _quadrifolio(canv, A4[0] / 2, 13.2 * mm, 4.6 * mm)
        canv.setFillColor(CHUMBO)
        canv.setFont(FB, 7)
        canv.drawCentredString(A4[0] / 2, 12.4 * mm, _romano(doc.page))
        if doc.page == 1:
            # o título fica sob um arco ogival dourado, entre rosáceas e lancetas
            canv.saveState()
            canv.setStrokeColor(OURO)
            canv.setLineWidth(1.1)
            canv.drawPath(_ogiva(canv.beginPath(), A4[0] / 2 - 54 * mm, A4[1] - 43 * mm, 108 * mm, 8 * mm, 15 * mm), stroke=1, fill=0)
            canv.setStrokeColor(CHUMBO)
            canv.setLineWidth(0.5)
            canv.drawPath(_ogiva(canv.beginPath(), A4[0] / 2 - 52 * mm, A4[1] - 43 * mm, 104 * mm, 8 * mm, 13.5 * mm), stroke=1, fill=0)
            canv.restoreState()
            _quadrifolio(canv, A4[0] / 2, A4[1] - 18.6 * mm, 2.6 * mm)
            _rosacea(canv, 27 * mm, A4[1] - 32 * mm, 8.5 * mm)
            com_foto = _foto(canv, st.get("foto"), A4[0] - 17 * mm - 32 * mm, A4[1] - 20.5 * mm - 32 * mm, 32 * mm)
            if not com_foto:
                _rosacea(canv, A4[0] - 27 * mm, A4[1] - 32 * mm, 8.5 * mm)
            for k in range(2):   # lancetas ao lado do arco (do lado da foto, ela ocupa o lugar)
                _lanceta(canv, A4[0] / 2 - 65 * mm + k * 5.2 * mm, A4[1] - 43 * mm, h=12 * mm)
                if not com_foto:
                    _lanceta(canv, A4[0] / 2 + 55.6 * mm + k * 5.2 * mm, A4[1] - 43 * mm, h=12 * mm)
        canv.setFont(FI, 7.5)
        canv.setFillColor(TINTA2)
        canv.drawCentredString(A4[0] / 2, 4.2 * mm, L(f"{idt.get('nome') or 'Sonhador'} · Conestoga connection · fólio {_romano(doc.page)}"))
        canv.restoreState()

    doc = SimpleDocTemplate(caminho, pagesize=A4, leftMargin=17 * mm, rightMargin=17 * mm, topMargin=21 * mm, bottomMargin=21 * mm,
                            title=f"Ficha — {idt.get('nome') or 'Sonhador'}", author=idt.get("player", ""))
    doc.build(e, onFirstPage=fundo, onLaterPages=fundo)
