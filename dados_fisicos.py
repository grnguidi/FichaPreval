"""Dados físicos: em vez de rolar, o app diz quantos e quais dados pegar e quanto somar (mesmo texto do celular).
Os objetos devolvidos imitam os de regras.rolar_* com "fisico": True e total None."""
import re


def limpa(e):
    s = re.sub(r"\s+", " ", str(e or ""))
    s = re.sub(r"\s*\+\s*", " + ", s)
    return re.sub(r"\s*-\s*", " − ", s).strip()


def critico(e, mult=2):
    """No crítico os dados se multiplicam (×2, ou ×3 com Destruidora); os bônus fixos não."""
    return limpa(re.sub(r"(\d+)\s*d\s*(\d+)", lambda m: f"{int(m.group(1)) * mult}d{m.group(2)}", str(e or "")))


class Pedido:
    """Dados pedidos numa ação, para o resumo "Pegue: 2d20 · 3d10"."""
    def __init__(self):
        self.lista = []

    def pedir(self, n, f):
        if n > 0:
            self.lista.append((n, f))

    def resumo(self):
        por = {}
        for n, f in self.lista:
            por[f] = por.get(f, 0) + n
        self.lista = []
        return ("🎲 Pegue: " + " · ".join(f"{por[f]}d{f}" for f in sorted(por, reverse=True))) if por else ""


def ataque(pedido, bonus, vant, margem=20, desv=False):
    dois = bool(vant) != bool(desv)
    pedido.pedir(2 if dois else 1, 20)
    return {"fisico": True, "d20": [], "n": 2 if dois else 1, "menor": bool(desv) and not vant, "bonus": bonus, "total": None,
            "margem": margem, "critico": False, "garantido": False, "desastre": False, "natural": None}


def teste(pedido, bonus, nd20=1):
    n = max(1, int(nd20 or 1))
    pedido.pedir(n, 20)
    return {"fisico": True, "d20": [], "n": n, "bonus": bonus, "total": None}


def expr(pedido, e, mult=2):
    for m in re.finditer(r"(\d+)\s*d\s*(\d+)", str(e or "")):
        pedido.pedir(int(m.group(1)), int(m.group(2)))
    return None, {"expr": limpa(e), "crit": critico(e, mult) if "d" in str(e) else ""}


def qtos_d20(n, menor=False):
    return f"{n}d20 e fique com o {'menor' if menor else 'maior'}" if n > 1 else "1d20"


def sinal(b):
    return f"{'+' if b >= 0 else '−'} {abs(b)}"


def nota_rerrolar(tipo, talentos):
    if tipo == "pericia" and "Sortudo" in talentos:
        return "  ↻ Sortudo: 1x por descanso longo, pode rerrolar este teste."
    if tipo in ("ataque", "resist") and "Sortudo maior" in talentos:
        return "  ↻ Sortudo maior: 1x por descanso longo, pode rerrolar este teste."
    return ""


def txt_ataque(at, rot, talentos=()):
    crit = f"{at['margem']} a 20 no dado" if at["margem"] < 20 else "20 no dado"
    return (f"{rot}: role {qtos_d20(at['n'], at['menor'])} {sinal(at['bonus'])} e compare com a CA. {crit} = crítico (role o dano do "
            f"crítico) · 20 natural acerta sempre · 1 natural é desastre." + nota_rerrolar("ataque", talentos))


def txt_dano(info, rot="Dano"):
    if not info["expr"]:
        return f"{rot}: —"
    return f"{rot}: role {info['expr']}" + (f"  · no crítico: {info['crit']}" if info["crit"] and info["crit"] != info["expr"] else "")


def txt_teste(nome, r, tipo="pericia", talentos=()):
    return f"{nome}: role {qtos_d20(r['n'])} {sinal(r['bonus'])}." + nota_rerrolar(tipo, talentos)
