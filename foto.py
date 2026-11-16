# -*- coding: utf-8 -*-
"""Foto do personagem: guardada dentro da ficha como um endereço de dados (data:image/...;base64,...), pequena
(256 px, JPEG), para caber no .json e viajar pela sessão. Com o Pillow instalado, aceita qualquer imagem e mostra
JPEG na tela; sem ele, só PNG ou GIF pequenos."""
import base64
import io
import os

try:
    from PIL import Image
except Exception:      # o Pillow é um extra
    Image = None

LADO = 256
LIMITE_SEM_PIL = 300_000
LIMITE_TEXTO = 400_000     # tamanho máximo do endereço de dados aceito numa ficha


def valida(txt):
    return isinstance(txt, str) and txt.startswith("data:image/") and ";base64," in txt[:40] and len(txt) <= LIMITE_TEXTO


def de_arquivo(caminho):
    """Lê uma imagem e devolve o endereço de dados (quadrada, 256 px). Lança ValueError com a explicação se não der."""
    if Image is not None:
        try:
            im = Image.open(caminho)
            im = im.convert("RGB")
            w, h = im.size
            lado = min(w, h)
            im = im.crop(((w - lado) // 2, (h - lado) // 2, (w - lado) // 2 + lado, (h - lado) // 2 + lado)).resize((LADO, LADO))
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=82)
            return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
        except Exception as e:
            raise ValueError(f"Não consegui ler a imagem: {e}")
    ext = os.path.splitext(caminho)[1].lower()
    if ext not in (".png", ".gif"):
        raise ValueError("Sem o Pillow instalado, só aceito PNG ou GIF. (Instale com: py -m pip install pillow)")
    with open(caminho, "rb") as f:
        bruto = f.read()
    if len(bruto) > LIMITE_SEM_PIL:
        raise ValueError("Imagem grande demais (máximo 300 KB sem o Pillow). Use uma imagem menor, de uns 256 px.")
    return "data:image/%s;base64,%s" % (ext[1:], base64.b64encode(bruto).decode("ascii"))


def bytes_de(txt):
    """(bytes, 'jpeg' | 'png' | 'gif' | ...) de um endereço de dados, ou (None, '')."""
    if not valida(txt):
        return None, ""
    try:
        cab, b64 = txt.split(",", 1)
        return base64.b64decode(b64), cab[len("data:image/"):].split(";")[0]
    except (ValueError, TypeError):
        return None, ""


def para_tk(txt, lado=72):
    """Imagem do Tk pronta para um Label (ou None se não der para mostrar neste computador)."""
    bruto, tipo = bytes_de(txt)
    if bruto is None:
        return None
    try:
        if Image is not None:
            from PIL import ImageTk
            im = Image.open(io.BytesIO(bruto)).convert("RGB").resize((lado, lado))
            return ImageTk.PhotoImage(im)
        if tipo in ("png", "gif"):
            import tkinter as tk
            img = tk.PhotoImage(data=base64.b64encode(bruto).decode("ascii"))
            fator = max(1, round(max(img.width(), img.height()) / lado))
            return img.subsample(fator) if fator > 1 else img
    except Exception:
        return None
    return None
