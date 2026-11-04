#!/usr/bin/env python3
"""
diagnostico_error.py  -  Solaris Core / MHD-INT
Donde falla nuestro modelo de Sol frente a LROC? Usa salida_2010/validacion_malla.csv (ya calculado)
y el DEM, y reparte el error segun:
  - distancia al borde del recorte (si el error crece cerca del borde, falta terreno fuera del recorte),
  - altura del punto,
  - relieve local (altura del punto menos la media en 1 km: negativo = hondonada, positivo = cresta).

Uso (desde luna_polo_sur):
    python diagnostico_error.py
"""
import argparse
import csv
import os
import sys

import numpy as np
import rasterio
from scipy.ndimage import uniform_filter


def tabla(titulo, valores, bins, etiquetas, ours, lroc):
    print(f"\n{titulo}")
    print(f"{'rango':<22} {'n':>4} {'LROC':>6} {'nuestro':>8} {'sesgo':>7} {'error abs':>9}")
    for (lo, hi), et in zip(bins, etiquetas):
        m = (valores >= lo) & (valores < hi)
        if m.sum() < 5:
            continue
        d = ours[m] - lroc[m]
        print(f"{et:<22} {m.sum():>4} {lroc[m].mean():>6.1f} {ours[m].mean():>8.1f} {d.mean():>+7.1f} {np.abs(d).mean():>9.1f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="salida_2010/validacion_malla.csv")
    ap.add_argument("--dem", default="datos/Site04_surf.tif")
    ap.add_argument("--col", default="nuestro_rs0.27_h2")
    a = ap.parse_args()
    for p in (a.csv, a.dem):
        if not os.path.isfile(p):
            print("ERROR: no existe", p)
            sys.exit(1)

    with open(a.csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    x = np.array([float(r["x_m"]) for r in rows])
    y = np.array([float(r["y_m"]) for r in rows])
    ours = np.array([float(r[a.col]) for r in rows])
    lroc = np.array([float(r["lroc_media3x3"]) for r in rows])

    with rasterio.open(a.dem) as d:
        z = d.read(1).astype("float64")
        tr, b = d.transform, d.bounds
        res = d.res[0]
    z = np.where(np.isnan(z), np.nanmean(z), z)
    media_1km = uniform_filter(z, size=int(1000 / res))
    cols, rws = ~tr * (x, y)
    ci, ri = np.clip(cols.astype(int), 0, z.shape[1] - 1), np.clip(rws.astype(int), 0, z.shape[0] - 1)
    alt = z[ri, ci]
    relieve = alt - media_1km[ri, ci]
    borde = np.minimum.reduce([x - b.left, b.right - x, y - b.bottom, b.top - y])

    err = ours - lroc
    print(f"{len(x)} puntos. Error medio absoluto total: {np.abs(err).mean():.1f}; sesgo {err.mean():+.1f}")
    print(f"Correlacion |error| con distancia al borde: {np.corrcoef(np.abs(err), borde)[0,1]:+.2f}  "
          f"| con altura: {np.corrcoef(np.abs(err), alt)[0,1]:+.2f}  | con relieve local: {np.corrcoef(np.abs(err), relieve)[0,1]:+.2f}")

    tabla("Por distancia al borde del recorte (m)", borde,
          [(3000, 4000), (4000, 5000), (5000, 6000), (6000, 1e9)],
          ["3000-4000", "4000-5000", "5000-6000", "mas de 6000"], ours, lroc)
    q = np.quantile(alt, [0, 1/3, 2/3, 1.0])
    q[-1] += 1e-6
    tabla("Por altura del punto (m) - terciles", alt, [(q[0], q[1]), (q[1], q[2]), (q[2], q[3])],
          [f"{q[0]:.0f} a {q[1]:.0f}", f"{q[1]:.0f} a {q[2]:.0f}", f"{q[2]:.0f} a {q[3]:.0f}"], ours, lroc)
    tabla("Por relieve local (m sobre la media de 1 km)", relieve,
          [(-1e9, -20), (-20, -5), (-5, 5), (5, 20), (20, 1e9)],
          ["hondonada (< -20)", "bajo (-20 a -5)", "plano (-5 a 5)", "alto (5 a 20)", "cresta (> 20)"], ours, lroc)

    osc = lroc < 10
    if osc.sum() > 10:
        tabla("Solo puntos oscuros en LROC (< 10 %): por distancia al borde", borde[osc],
              [(3000, 4500), (4500, 6000), (6000, 1e9)], ["3000-4500", "4500-6000", "mas de 6000"],
              ours[osc], lroc[osc])


if __name__ == "__main__":
    main()
