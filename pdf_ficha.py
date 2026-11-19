# -*- coding: utf-8 -*-
"""Exporta a ficha aberta para PDF (reportlab), no visual Vitral gótico: roxo profundo, lilás e verde-claro,
com dourado e chumbo; enfeites de vitral, rosáceas e janelas em arco."""
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

PERG = colors.HexColor("#f3eef6")
PERG2 = colors.HexColor("#e6dcee")
CAMPO = colors.HexColor("#fbf9fd")
ZEBRA = colors.HexColor("#efe8f4")
TINTA = colors.HexColor("#2a1f33")
TINTA2 = colors.HexColor("#5f5370")
OURO = colors.HexColor("#b8955a")
OURO2 = colors.HexColor("#e6d29e")
VINHO = colors.HexColor("#6a3d9a")     # roxo dos títulos de seção
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
        c.circle(cx + math.cos(a) * r * 0.52, cy + math.sin(a) * r * 0.52, r * 0.17, stroke=1, fill=0)
    c.setLineWidth(max(0.8, r * 0.13))
    c.circle(cx, cy, r, stroke=1, fill=0)
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


class Secao(Flowable):
    """Título de seção: uma rosácea pequena, o título em roxo e um filete lilás embaixo."""

    def __init__(self, texto, fonte, largura):
        super().__init__()
        self.texto, self.fonte, self.width, self.height = texto, fonte, largura, 21
        self.keepWithNext = True

    def wrap(self, *_):
        return self.width, self.height

    def draw(self):
        c = self.canv
        _rosacea(c, 2.8 * mm, 8, 2.6 * mm)
        c.setFillColor(VINHO)
        t = c.beginText(8 * mm, 5)
        t.setFont(self.fonte, 11.5)
        t.setCharSpace(1.4)
        t.textOut(self.texto)
        c.drawText(t)
        _filete(c, 0, self.width, 1, LILAS, 1.1)


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
    e.append(Paragraph(L("Ficha do Sonhador · edição 3.3"), s_sub))
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
        canv.setStrokeColor(OURO)
        canv.setLineWidth(1.2)
        canv.rect(9 * mm, 9 * mm, A4[0] - 18 * mm, A4[1] - 18 * mm)
        canv.setLineWidth(0.4)
        canv.rect(10.5 * mm, 10.5 * mm, A4[0] - 21 * mm, A4[1] - 21 * mm)
        # faixa de vitral no alto; embaixo, uma fileira de janelas em arco em cada canto
        _faixa_vitral(canv, 10.5 * mm, A4[1] - 10.5 * mm - 6.5 * mm, A4[0] - 21 * mm)
        for i in range(5):
            _lanceta(canv, 13 * mm + i * 5.2 * mm, 11.5 * mm)
            _lanceta(canv, A4[0] - 13 * mm - 4.2 * mm - i * 5.2 * mm, 11.5 * mm)
        _filete(canv, 40 * mm, A4[0] - 40 * mm, 12 * mm, LILAS, 0.8)
        if doc.page == 1:
            _rosacea(canv, 25 * mm, A4[1] - 33 * mm, 8 * mm)
            if not _foto(canv, st.get("foto"), A4[0] - 15 * mm - 32 * mm, A4[1] - 20.5 * mm - 32 * mm, 32 * mm):
                _rosacea(canv, A4[0] - 25 * mm, A4[1] - 33 * mm, 8 * mm)
            _filete(canv, A4[0] / 2 - 46 * mm, A4[0] / 2 - 8 * mm, A4[1] - 40.4 * mm, OURO, 0.9)
            _filete(canv, A4[0] / 2 + 8 * mm, A4[0] / 2 + 46 * mm, A4[1] - 40.4 * mm, OURO, 0.9)
        canv.setFont(FI, 8)
        canv.setFillColor(TINTA2)
        canv.drawCentredString(A4[0] / 2, 5.5 * mm, L(f"{idt.get('nome') or 'Sonhador'} · Prevalecentes · página {doc.page}"))
        canv.restoreState()

    doc = SimpleDocTemplate(caminho, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=21 * mm, bottomMargin=19 * mm,
                            title=f"Ficha — {idt.get('nome') or 'Sonhador'}", author=idt.get("player", ""))
    doc.build(e, onFirstPage=fundo, onLaterPages=fundo)
