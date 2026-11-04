#!/usr/bin/env python3
"""Marca como ilustrativos los renders de la galeria y las tomas antiguas del sitio 14.

Lee los originales de auditoria/antes/renders_originales/ y escribe en renders/ (o en MARCAR_SALIDA).
NO genera ni toca la portada, la imagen principal, la comparacion ni los videos del sitio 456: esos renders se hacen aparte.
Tampoco rehace los archivos antiguos del 14 que estos reemplazaron (hero.jpg, video.mp4, portada v4, comparacion v1).
Uso: python scripts/marcar_renders.py
"""
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ORIG = ROOT / "auditoria" / "antes" / "renders_originales"
OUT = Path(os.environ.get("MARCAR_SALIDA", ROOT / "renders"))
BOLD = "DejaVuSans-Bold.ttf"
MARK_L = "ILLUSTRATIVE RENDER · AI-ASSISTED · lander, rocks, stars and Earth's continents are invented"
MARK = "ILLUSTRATIVE RENDER · AI-ASSISTED · rocks, stars and Earth's continents are invented"
PROTEGIDOS = {"hero_sitio456.jpg", "video_sitio456_app.mp4", "luna_portada_v5_sitio456.png", "luna_comparacion_4_sitios_v2.png", "luna_sitio456_linea_tiempo.mp4", "luna_sitio456_toma_lander.png", "luna_video456_cuadro.png"}


def font(name, size):
    for base in (name, "/usr/share/fonts/truetype/dejavu/" + name, "C:/Windows/Fonts/arialbd.ttf"):
        try:
            return ImageFont.truetype(base, size)
        except OSError:
            pass
    return ImageFont.load_default()


def stamp(im, text):
    im = im.convert("RGB")
    W, H = im.size
    size = max(11, W // 62)
    f = font(BOLD, size)
    while f.getlength(text) > W - 16 and size > 8:
        size -= 1
        f = font(BOLD, size)
    h = int(size * 1.9)
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.rectangle([0, H - h, W, H], fill=(0, 0, 0, 185))
    d.text((W / 2, H - h / 2), text, font=f, fill=(255, 214, 120, 255), anchor="mm")
    return Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")


def guardar(im, name, **kw):
    if name in PROTEGIDOS:
        raise RuntimeError(f"{name} es un render protegido: este script no lo escribe")
    im.save(OUT / name, **kw)


OUT.mkdir(parents=True, exist_ok=True)
for name in ("14.jpg", "456.jpg", "964.jpg", "1358.jpg"):
    guardar(stamp(Image.open(ORIG / name), MARK), name, quality=88)
for name, text in (("luna_sitio14_toma_v1_1920.png", MARK), ("luna_sitio14_toma_v2_lander.png", MARK_L), ("luna_tierra_zoom.png", "ILLUSTRATIVE · AI-ASSISTED · Earth's continents are invented; phase is computed")):
    guardar(stamp(Image.open(ORIG / name), text), name)
print("listo")
