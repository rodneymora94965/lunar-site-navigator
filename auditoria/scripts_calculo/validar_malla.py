#!/usr/bin/env python3
"""
validar_malla.py  -  Solaris Core / MHD-INT
Validacion mas robusta que la de 15 candidatos: compara nuestro % de Sol con el mapa LROC en
una MALLA regular de puntos (cientos) sobre el recorte, en el mismo periodo (15-feb-2010 ..
5-feb-2011). Los puntos estan en el centro de pixeles LROC y lejos del borde del recorte.

Prueba 4 configuraciones: radio solar 0 / 0.27 grados  x  altura del observador 0 / 2 m.

Uso (desde luna_polo_sur):
    python validar_malla.py
    python validar_malla.py --paso 500 --margen 3000

Salida (salida_2010/): validacion_malla.csv, validacion_malla.png, validacion_malla.txt

Nota: la orientacion del DEM casi no afecta el % de Sol (el Sol recorre todos los azimuts cada mes
y su elevacion cerca del polo depende de la epoca del ano, no del azimut); por eso se usa la
orientacion normal. Para la TIERRA (direccion casi fija hacia el meridiano 0) si importaria.
"""
import argparse
import csv
import math
import os
import sys

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.warp import transform as warp_transform
from scipy.ndimage import map_coordinates

import calcular_candidatos as cc

NUESTRO_CRS = CRS.from_string("+proj=stere +lat_0=-90 +lon_0=0 +k=1 +x_0=0 +y_0=0 +R=1737400 +units=m +no_defs")


def rangos(v):
    v = np.asarray(v, float)
    o = np.argsort(v, kind="mergesort")
    r = np.empty(len(v))
    r[o] = np.arange(len(v))
    for val in np.unique(v):
        m = v == val
        r[m] = r[m].mean()
    return r


def metricas(n, l):
    return (float((n - l).mean()), float(np.corrcoef(n, l)[0, 1]),
            float(np.corrcoef(rangos(n), rangos(l))[0, 1]),
            float(np.abs(n - l).mean()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dem", default="datos/Site04_surf.tif")
    ap.add_argument("--lroc", default="datos/WAC_POLE_ILL_PCT_SOUTH_100M.TIF")
    ap.add_argument("--kernels", default="kernels")
    ap.add_argument("--start", default="2010-02-15")
    ap.add_argument("--years", type=float, default=0.972)
    ap.add_argument("--step-hours", type=float, default=2.0)
    ap.add_argument("--paso", type=float, default=500.0, help="separacion de la malla (m)")
    ap.add_argument("--margen", type=float, default=3000.0, help="distancia minima al borde del recorte (m)")
    ap.add_argument("--radio-solar", type=float, default=0.27)
    ap.add_argument("--az", type=int, default=90, help="numero de azimuts del horizonte (mas = mas fino y mas lento)")
    ap.add_argument("--paso-rayo", type=float, default=10.0, help="paso del rayo del horizonte (m)")
    ap.add_argument("--escala", type=float, default=None)
    ap.add_argument("--out", default="salida_2010")
    a = ap.parse_args()

    for p in (a.dem, a.lroc):
        if not os.path.isfile(p):
            print("ERROR: no existe", p)
            sys.exit(1)
    os.makedirs(a.out, exist_ok=True)

    with rasterio.open(a.dem) as d:
        z = d.read(1).astype("float64")
        tr = d.transform
        b = d.bounds
    with rasterio.open(a.lroc) as d:
        arr = d.read(1).astype("float64")
        ltr, lcrs, lnod = d.transform, d.crs, d.nodata
    if lnod is not None:
        arr[arr == lnod] = np.nan
    escala = 1.0 if np.nanmax(arr) <= 100.5 else 100.0 / 255.0
    if a.escala:
        escala = 100.0 / 255.0 if a.escala == 255 else a.escala
    lroc = arr * escala

    xs = np.arange(math.ceil((b.left + a.margen) / a.paso) * a.paso, b.right - a.margen + 1, a.paso)
    ys = np.arange(math.ceil((b.bottom + a.margen) / a.paso) * a.paso, b.top - a.margen + 1, a.paso)
    pts = [(x, y) for y in ys for x in xs if math.hypot(x, y) > 300]
    px, py = [p[0] for p in pts], [p[1] for p in pts]
    if lcrs is not None:
        tx, ty = warp_transform(NUESTRO_CRS, lcrs, px, py)
    else:
        tx, ty = px, py
    # LROC: valor del pixel que contiene el punto (y media 3x3)
    val_c, val_m, keep = [], [], []
    for i, (x, y) in enumerate(zip(tx, ty)):
        r, c = rasterio.transform.rowcol(ltr, x, y)
        if 1 <= r < arr.shape[0] - 1 and 1 <= c < arr.shape[1] - 1 and not np.isnan(lroc[r, c]):
            val_c.append(lroc[r, c])
            val_m.append(np.nanmean(lroc[r - 1:r + 2, c - 1:c + 2]))
            keep.append(i)
    pts = [pts[i] for i in keep]
    val_c, val_m = np.array(val_c), np.array(val_m)
    print(f"Malla: {len(pts)} puntos (paso {a.paso:g} m, margen {a.margen:g} m). Horizonte: {a.az} azimuts, rayo cada {a.paso_rayo:g} m.")

    print("Efemerides ...")
    marco, sol, _ = cc.efemerides(a.kernels, a.start, a.years, a.step_hours)
    print(f"Marco {marco}; {len(sol)} instantes.\n")

    configs = [(0.0, 0.0), (a.radio_solar, 0.0), (0.0, 2.0), (a.radio_solar, 2.0)]
    res = {c: [] for c in configs}
    for k, (x, y) in enumerate(pts):
        lat, lon = cc.xy_a_latlon(x, y)
        la, lo = math.radians(lat), math.radians(lon)
        este, norte, arriba = cc.base_local(la, lo)
        inv = ~tr
        col, row = inv * (x, y)
        href = map_coordinates(z, [[row - 0.5], [col - 0.5]], order=1, mode="nearest")[0]
        for alt in (0.0, 2.0):
            azs, hor = cc.horizonte(z, tr, x, y, lon, alt, n_az=a.az, paso_m=a.paso_rayo)
            sitio = np.array([math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la)]) \
                * (cc.R_KM + (href + alt) / 1000.0)
            e_s, az_s = cc.elev_az_vec(sol - sitio, este, norte, arriba)
            hs = np.interp(az_s, np.append(azs, 360.0), np.append(hor, hor[0]))
            for rs in (0.0, a.radio_solar):
                res[(rs, alt)].append(100.0 * np.mean(e_s + rs > hs))
        if (k + 1) % 50 == 0:
            print(f"  {k+1}/{len(pts)}")

    L = []
    L.append(f"{'config':<34} {'sesgo(nuestro-LROC)':>19} {'Pearson':>8} {'Spearman':>9} {'error abs':>9}")
    for c in configs:
        n = np.array(res[c])
        sesgo, pe, sp_, ea = metricas(n, val_m)
        L.append(f"radio solar {c[0]:<5g} altura {c[1]:<4g} m       {sesgo:>+19.1f} {pe:>8.2f} {sp_:>9.2f} {ea:>9.1f}")
    # por rangos de LROC (configuracion radio solar + 2 m)
    n = np.array(res[(a.radio_solar, 2.0)])
    L.append("\nPor nivel de iluminacion LROC (config radio solar + 2 m): nuestro medio vs LROC medio")
    for lo_, hi_ in [(0, 10), (10, 30), (30, 60), (60, 101)]:
        m = (val_m >= lo_) & (val_m < hi_)
        if m.sum():
            L.append(f"  LROC {lo_:>3}-{min(hi_,100):<3} %: {m.sum():>4} puntos | LROC {val_m[m].mean():5.1f} | nuestro {n[m].mean():5.1f} | dif {n[m].mean()-val_m[m].mean():+6.1f}")
    txt = "\n".join(L)
    print("\n" + txt)
    with open(os.path.join(a.out, "validacion_malla.txt"), "w", encoding="utf-8") as f:
        f.write(txt + "\n")
    with open(os.path.join(a.out, "validacion_malla.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["x_m", "y_m", "lroc_pixel", "lroc_media3x3"] + [f"nuestro_rs{c[0]:g}_h{c[1]:g}" for c in configs])
        for i, (x, y) in enumerate(pts):
            w.writerow([x, y, round(val_c[i], 1), round(val_m[i], 1)] + [round(res[c][i], 1) for c in configs])

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(11, 5))
        ax[0].scatter(val_m, n, s=8, alpha=0.6)
        ax[0].plot([0, 100], [0, 100], "k--", lw=0.8)
        ax[0].set_xlabel("LROC (% iluminado, media 3x3)")
        ax[0].set_ylabel("Nuestro (% Sol)")
        ax[0].set_title("radio solar + altura 2 m")
        xs_ = [p[0] / 1000 for p in pts]
        ys_ = [p[1] / 1000 for p in pts]
        sc = ax[1].scatter(xs_, ys_, c=n - val_m, s=14, cmap="coolwarm", vmin=-60, vmax=60)
        fig.colorbar(sc, ax=ax[1], label="nuestro - LROC (puntos %)")
        ax[1].set_title("Donde difiere (km)")
        ax[1].set_aspect("equal")
        fig.tight_layout()
        fig.savefig(os.path.join(a.out, "validacion_malla.png"), dpi=120)
    except Exception as e:
        print("Aviso: sin grafico:", e)
    print("\nListo. Archivos en:", os.path.abspath(a.out))


if __name__ == "__main__":
    main()
