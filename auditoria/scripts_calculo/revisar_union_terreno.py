#!/usr/bin/env python3
"""Compara el mapa de 80 m con el de 120 m en la franja de 250 a 304 km del polo. No ajusta nada.

Limites fijados antes de mirar: se detiene si |mediana| > 5 m o si el percentil 95 de |diferencia| > 50 m.
Uso: python auditoria/scripts_calculo/revisar_union_terreno.py  Salida: auditoria/truncamiento/union_terreno.txt
"""
import sys
from pathlib import Path
import numpy as np, rasterio
from rasterio.enums import Resampling
from rasterio.windows import from_bounds
ROOT = Path(__file__).resolve().parents[2]
D = ROOT.parent / "luna_polo_sur" / "datos"
B = (-304000, -304000, 304000, 304000)
S = 2  # compara en una malla de 240 m
with rasterio.open(D / "LDEM_80S_80MPP_ADJ.TIF") as a, rasterio.open(D / "LDEM_60S_120MPP_ADJ.TIF") as b:
    n = int(608000 / 240)
    A = a.read(1, out_shape=(n, n), resampling=Resampling.average)
    W = from_bounds(*B, b.transform)
    C = b.read(1, window=W, out_shape=(n, n), resampling=Resampling.average)
xs = -304000 + 240 * (np.arange(n) + .5)
X, Y = np.meshgrid(xs, -xs)
R = np.hypot(X, Y)
k = (R >= 250000) & (R <= 304000) & np.isfinite(A) & np.isfinite(C)
d = (C - A)[k]
med, p95, sd = float(np.median(d)), float(np.percentile(np.abs(d), 95)), float(d.std())
ok = abs(med) <= 5 and p95 <= 50
txt = f"Franja 250-304 km, malla de 240 m, {k.sum()} puntos\nmediana (120 m - 80 m) {med:+.2f} m; media {d.mean():+.2f} m; desviacion {sd:.2f} m; p95 de |dif| {p95:.2f} m; max |dif| {np.abs(d).max():.1f} m\nLimites: |mediana| <= 5 m y p95 <= 50 m. Resultado: {'DENTRO' if ok else 'FUERA: DETENERSE'}\nNo se aplica ningun ajuste.\n"
out = ROOT / "auditoria" / "truncamiento" / "union_terreno.txt"
out.write_text(txt, encoding="utf-8"); print(txt)
