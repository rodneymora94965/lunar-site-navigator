"""Construye la app de un solo archivo. Uso: python build.py [salida.html]"""
import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "final.html"
t = (ROOT / "src" / "template.html").read_text(encoding="utf-8")
t = t.replace("__CORE__", (ROOT / "src" / "core.js").read_text(encoding="utf-8"))
t = t.replace("__APP__", (ROOT / "src" / "app.js").read_text(encoding="utf-8"))
HERO, VIDEO = "hero_sitio456.jpg", "video_sitio456_app.mp4"
for key in ("14", "456", "964", "1358"):
    t = t.replace(f"__IMG_{key}__", base64.b64encode((ROOT / "renders" / f"{key}.jpg").read_bytes()).decode())
t = t.replace("__IMG_hero__", base64.b64encode((ROOT / "renders" / HERO).read_bytes()).decode())
t = t.replace("__VIDEO__", base64.b64encode((ROOT / "renders" / VIDEO).read_bytes()).decode())
t = t.replace("__DATA__", (ROOT / "data" / "data.json").read_text(encoding="utf-8"))
OUT.write_text(t, encoding="utf-8", newline="\n")
print(f"{len(t) / 1e6:.2f} MB -> {OUT}")
