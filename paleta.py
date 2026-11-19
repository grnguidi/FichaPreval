"""Minha paleta: cada pessoa escolhe 5 cores (pedra, moldura, destaque, vidro 1 e vidro 2) e se é clara ou escura.
O resto do tema é derivado delas, com ajuste automático de contraste. O código PAL-... é o mesmo do celular."""
import re

CHAVES = [("pedra", "Pedra", "Fundo das páginas"), ("moldura", "Moldura", "Cabeçalho e barra de abas"),
          ("destaque", "Destaque", "Títulos e botões"), ("v1", "Vidro 1", "Vitrais e rosácea"), ("v2", "Vidro 2", "Vitrais e destaques verdes")]
MODELOS = [
    dict(nome="Catedral", pedra="#ebe5dc", moldura="#2a1a3d", destaque="#5e3591", v1="#b79ad6", v2="#a8d89a", escuro=False),
    dict(nome="Vigília", pedra="#121016", moldura="#08070b", destaque="#9a62e0", v1="#c9a8f0", v2="#b6f0a4", escuro=True),
    dict(nome="Rubi", pedra="#efe6e2", moldura="#3b1018", destaque="#9b1d36", v1="#e58a9b", v2="#f0c96a", escuro=False),
    dict(nome="Esmeralda", pedra="#e6ebe2", moldura="#13281c", destaque="#1f6b42", v1="#7cc9a0", v2="#e6d29e", escuro=False),
    dict(nome="Âmbar", pedra="#f1e9da", moldura="#3a2410", destaque="#9a5a12", v1="#f0b45a", v2="#9cc3d9", escuro=False),
    dict(nome="Abismo", pedra="#0d1418", moldura="#05090c", destaque="#3fa7c9", v1="#7fd3f0", v2="#c9a8f0", escuro=True),
    dict(nome="Brasa", pedra="#151010", moldura="#0a0606", destaque="#e0603a", v1="#ff9a6b", v2="#f0d98c", escuro=True),
]


def _rgb(h):
    h = str(h or "").lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) if re.fullmatch(r"[0-9a-fA-F]{6}", h) else (0, 0, 0)


def _hex(c):
    return "#" + "".join(f"{max(0, min(255, round(v))):02x}" for v in c)


def mistura(a, b, t):
    x, y = _rgb(a), _rgb(b)
    return _hex([x[i] + (y[i] - x[i]) * t for i in range(3)])


def lumin(h):
    c = [v / 255 for v in _rgb(h)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contraste(a, b):
    x, y = lumin(a), lumin(b)
    return (max(x, y) + 0.05) / (min(x, y) + 0.05)


def legivel(cor, fundo, minimo):
    """Empurra a cor para o preto (ou o branco) até ficar legível sobre o fundo."""
    alvo = "#000000" if contraste("#000000", fundo) >= contraste("#ffffff", fundo) else "#ffffff"
    for k in range(21):
        c = mistura(cor, alvo, k / 20)
        if contraste(c, fundo) >= minimo:
            return c
    return alvo


def valida(p):
    return isinstance(p, dict) and all(re.fullmatch(r"#[0-9a-fA-F]{6}", str(p.get(k, ""))) for k, _, _ in CHAVES)


def derivar(p):
    """As 5 cores viram o tema; devolve (cores, avisos)."""
    e, pedra, avisos = bool(p.get("escuro")), p["pedra"], []
    mold = p["moldura"]
    k = 1
    while lumin(mold) > 0.06 and k <= 20:      # a moldura leva textos claros: precisa ser escura
        mold = mistura(p["moldura"], "#000000", k / 20)
        k += 1
    if mold != p["moldura"]:
        avisos.append("a moldura foi escurecida para os textos claros sobre ela continuarem legíveis")
    V = dict(fundo=mold, fundo2=mistura(mold, "#ffffff", 0.07 if e else 0.12), perg=pedra,
             perg2=mistura(pedra, "#ffffff" if e else "#000000", 0.07), campo=mistura(pedra, "#ffffff", 0.04 if e else 0.5))
    tinta0 = mistura(p["v1"], "#ffffff", 0.75) if e else mistura(mold, "#000000", 0.2)
    V["tinta"] = legivel(tinta0, V["campo"], 7)
    if V["tinta"] != tinta0:
        avisos.append("o texto foi ajustado para ficar legível")
    V["tinta2"] = legivel(mistura(V["tinta"], pedra, 0.38), V["campo"], 4.5)
    V["linha"] = mistura(pedra, V["tinta"], 0.16 if e else 0.18)
    dest0 = mistura(p["destaque"], "#ffffff", 0.35) if e else p["destaque"]
    V["vinho"] = legivel(dest0, pedra, 4.5)
    if V["vinho"] != dest0:
        avisos.append("o destaque foi ajustado para aparecer sobre a pedra")
    V["verde"] = legivel(p["v2"] if e else mistura(p["v2"], "#000000", 0.4), pedra, 3)
    V["ouro"], V["ouro2"] = "#b8955a", "#e6d29e"
    V["lilas"], V["lilas2"], V["verdec"] = p["v1"], mistura(p["v1"], "#ffffff", 0.45), p["v2"]
    V["chumbo"] = "#000000" if e else mistura(mold, "#000000", 0.25)
    V["faixa"] = mistura(pedra, "#ffffff", 0.6)
    V["rosa"] = mistura(pedra, "#a3334f", 0.18 if e else 0.08)
    V["agua"] = mistura(pedra, p["v2"], 0.12 if e else 0.18)
    V["vidros"] = [mistura(p["destaque"], p["v1"], 0.35), p["v2"], p["v1"], "#e2cf9a", V["lilas2"], mistura(p["v2"], "#000000", 0.15)]
    return V, avisos


def tema_pc(p):
    """Cores no formato dos TEMAS do programa de PC."""
    V, _ = derivar(p)
    e = bool(p.get("escuro"))
    base = dict(C_VIDA="#c2405e" if e else "#a3334f", C_MANA="#6d5fd0" if e else "#5b4fae", C_VIGOR="#5aa04f" if e else "#4e8a4a",
                C_MOV="#3f8a7a", C_CA="#6f6678", C_PER="#8a5a9e", C_TAL="#4e8a4a", C_DIN="#4e8a4a")
    base.update(C_ATK=base["C_VIDA"], C_DEF=base["C_MANA"])
    return dict(FUNDO=V["fundo"], FUNDO2=V["fundo2"], PERG=V["perg"], PERG2=V["perg2"], CAMPO=V["campo"],
                TINTA=V["tinta"], TINTA2=V["tinta2"], OURO=V["ouro"], OURO2=V["ouro2"], VINHO=V["vinho"],
                VINHO_BG=legivel(p["destaque"], "#ffffff", 4.5), VERDE=V["verde"], FAIXA=V["faixa"], LINHA=V["linha"],
                ROSA=V["rosa"], AGUA=V["agua"], MESA_CAMPO=V["fundo2"], MESA_BORDA=mistura(V["fundo"], p["v1"], 0.35),
                MESA_ATIVO=mistura(V["fundo"], "#ffffff", 0.1), MESA_TXT=legivel(V["lilas2"], V["fundo"], 4.5),
                ALERTA="#ff8fab" if e else "#f6b8cf", C_ATR=V["fundo2"], **base)


def codigo(p):
    return "PAL-" + "-".join(p[k].lstrip("#").lower() for k, _, _ in CHAVES) + ("-e" if p.get("escuro") else "-c")


def ler_codigo(txt):
    m = re.search(r"PAL-([0-9a-f]{6})-([0-9a-f]{6})-([0-9a-f]{6})-([0-9a-f]{6})-([0-9a-f]{6})-([ce])", str(txt or ""), re.I)
    if not m:
        return None
    p = {k: "#" + m.group(i + 1).lower() for i, (k, _, _) in enumerate(CHAVES)}
    p.update(nome="Paleta recebida", escuro=m.group(6).lower() == "e")
    return p
