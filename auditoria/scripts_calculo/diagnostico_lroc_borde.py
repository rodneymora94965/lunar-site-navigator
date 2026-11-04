#!/usr/bin/env python3
"""Diagnostico posterior: como se comparan LROC y PGDA segun la distancia al polo, sin usar el modelo.

Se escribio despues de ver que de Gerlache Rim 2 da modelo 56,5 % y LROC 15,9 %. No cambia ninguna cifra y no demuestra la causa.
Salida: auditoria/regiones/diagnostico_lroc_borde.txt
"""
import re, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lectura_productos import indices_mapa, read_pds_image
EXT = ROOT / "auditoria" / "datos_externos"
A, x0, y0, sc, _ = read_pds_image(EXT / "WAC_POLE_ILL_PCT_SOUTH_100M.IMG")
n = "AVGVISIB_85S_060M_201608"
t = (EXT / (n + ".LBL")).read_text(errors="replace")
g = lambda k: re.search(rf"^\s*{k}\s*=\s*\"?([^\s\"<]+)", t, re.M).group(1)
P = np.fromfile(EXT / (n + ".IMG"), dtype="<i2").reshape(int(g("LINES")), int(g("LINE_SAMPLES")))
s, off, px, c, cs = float(g("SCALING_FACTOR")), float(g("OFFSET")), float(re.search(r"MAP_SCALE\s*=\s*([\d.]+)", t).group(1)), float(g("LINE_PROJECTION_OFFSET")), float(g("SAMPLE_PROJECTION_OFFSET"))
xs = np.arange(-60000, 60001, 500.0)
X, Y = np.meshgrid(xs, xs)
X, Y = X.ravel(), Y.ravel()
rl, kl = indices_mapa(X, Y, sc, y0 / sc, -x0 / sc)
L = np.array(A[rl, kl], dtype=float)
rp, kp = indices_mapa(X, Y, px, c, cs)
V = 100 * (P[rp, kp] * s + off)
R = np.hypot(X, Y) / 1e3
out = ["LROC y PGDA (Sol) en una malla de 500 m, sin el modelo. Diagnostico posterior; no demuestra la causa.", "km del polo | puntos validos en LROC | mediana LROC | mediana PGDA | mediana PGDA-LROC, puntos con PGDA >= 40 %"]
for a, b in ((0, 20), (20, 30), (30, 40), (40, 50), (50, 55), (55, 60)):
    q = (R >= a) & (R < b)
    v = q & (L > -1e30) & (L <= 100) & (V >= 0) & (V <= 100)
    h = v & (V >= 40)
    out.append(f"{a}-{b} | {v.sum()} de {q.sum()} | {np.median(L[v]):.1f} | {np.median(V[v]):.1f} | {np.median((V - L)[h]) if h.any() else float('nan'):+.1f} ({h.sum()})")
(ROOT / "auditoria" / "regiones" / "diagnostico_lroc_borde.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
