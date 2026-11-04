#!/usr/bin/env python3
"""
validar_celda.py  -  Solaris Core / MHD-INT
Prueba de la hipotesis de ESCALA: nuestro modelo calcula el Sol en UN punto (DEM de 5 m) y LROC
da un valor por celda de 100 m x 100 m. Si comparamos punto vs celda aparece una "compresion hacia
el medio" aunque el modelo sea correcto.

Aqui, para cada celda LROC de una malla, calculamos el % de Sol en sub x sub puntos repartidos
DENTRO de la celda (por defecto 4 x 4 = 16 puntos, cada 25 m) y los promediamos. Luego comparamos
con LROC, y lo contrastamos con el valor de un solo punto (el centro de la celda).

Uso (desde luna_polo_sur):
    python validar_celda.py
    python validar_celda.py --paso 1000 --sub 4        (por defecto)
    python validar_celda.py --paso 500 --sub 3          (mas celdas, menos puntos por celda)

Salida (salida_2010/): validacion_celda.csv, validacion_celda.txt, validacion_celda.png
Tarda unos minutos (cada punto requiere un horizonte completo). Imprime avance.

Como leer el resultado: si el error absoluto medio del PROMEDIO DE CELDA es claramente menor que
el del punto (y la pendiente de regresion se acerca a 1), la causa principal era de escala y el
modelo esta bien. Si casi no cambia, esa hipotesis queda descartada.
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
    pend = np.polyfit(l, n, 1)[0]
    return (float((n - l).mean()), float(np.corrcoef(n, l)[0, 1]),
            float(np.corrcoef(rangos(n), rangos(l))[0, 1]),
            float(np.abs(n - l).mean()), float(pend))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dem", default="datos/Site04_surf.tif")
    ap.add_argument("--lroc", default="datos/WAC_POLE_ILL_PCT_SOUTH_100M.TIF")
    ap.add_argument("--kernels", default="kernels")
    ap.add_argument("--start", default="2010-02-15")
    ap.add_argument("--years", type=float, default=0.972)
    ap.add_argument("--step-hours", type=float, default=2.0)
    ap.add_argument("--paso", type=float, default=1000.0, help="separacion de la malla de celdas (m)")
    ap.add_argument("--margen", type=float, default=3000.0)
    ap.add_argument("--sub", type=int, default=4, help="sub x sub puntos dentro de cada celda LROC")
    ap.add_argument("--altura", type=float, default=2.0)
    ap.add_argument("--radio-solar", type=float, default=0.27)
    ap.add_argument("--az", type=int, default=90)
    ap.add_argument("--paso-rayo", type=float, default=10.0)
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
    lroc = arr * (1.0 if np.nanmax(arr) <= 100.5 else 100.0 / 255.0)
    tam = abs(ltr.a)  # tamano de celda LROC (m)

    def a_lroc(px, py):
        return warp_transform(NUESTRO_CRS, lcrs, px, py) if lcrs is not None else (px, py)

    def de_lroc(px, py):
        return warp_transform(lcrs, NUESTRO_CRS, px, py) if lcrs is not None else (px, py)

    # malla de celdas: se toma el centro del pixel LROC que contiene cada punto de la malla
    xs = np.arange(math.ceil((b.left + a.margen) / a.paso) * a.paso, b.right - a.margen + 1, a.paso)
    ys = np.arange(math.ceil((b.bottom + a.margen) / a.paso) * a.paso, b.top - a.margen + 1, a.paso)
    pts = [(x, y) for y in ys for x in xs if math.hypot(x, y) > 300]
    tx, ty = a_lroc([p[0] for p in pts], [p[1] for p in pts])
    celdas = []  # (cx_lroc, cy_lroc, valor_pixel, media3x3)
    vistos = set()
    for x, y in zip(tx, ty):
        r, c = rasterio.transform.rowcol(ltr, x, y)
        if (r, c) in vistos or not (1 <= r < arr.shape[0] - 1 and 1 <= c < arr.shape[1] - 1):
            continue
        if np.isnan(lroc[r, c]):
            continue
        vistos.add((r, c))
        cx, cy = rasterio.transform.xy(ltr, r, c)
        celdas.append((cx, cy, lroc[r, c], np.nanmean(lroc[r - 1:r + 2, c - 1:c + 2])))
    n_sub = a.sub * a.sub
    print(f"{len(celdas)} celdas LROC x {n_sub} sub-puntos (+1 centro) = {len(celdas) * (n_sub + 1)} horizontes.")
    print("Efemerides ...")
    marco, sol, _ = cc.efemerides(a.kernels, a.start, a.years, a.step_hours)
    print(f"Marco {marco}; {len(sol)} instantes.\n")

    off = (np.arange(a.sub) + 0.5) / a.sub - 0.5  # fracciones de celda, centradas

    def pct_sol(x, y):
        lat, lon = cc.xy_a_latlon(x, y)
        la, lo = math.radians(lat), math.radians(lon)
        este, norte, arriba = cc.base_local(la, lo)
        col, row = ~tr * (x, y)
        href = map_coordinates(z, [[row - 0.5], [col - 0.5]], order=1, mode="nearest")[0]
        azs, hor = cc.horizonte(z, tr, x, y, lon, a.altura, n_az=a.az, paso_m=a.paso_rayo)
        sitio = np.array([math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la)]) \
            * (cc.R_KM + (href + a.altura) / 1000.0)
        e_s, az_s = cc.elev_az_vec(sol - sitio, este, norte, arriba)
        hs = np.interp(az_s, np.append(azs, 360.0), np.append(hor, hor[0]))
        return 100.0 * np.mean(e_s + a.radio_solar > hs)

    filas = []
    for k, (cx, cy, v_pix, v_med) in enumerate(celdas):
        # puntos dentro de la celda, definidos en el plano de LROC y llevados a nuestro plano
        gx = np.array([cx + fx * tam for fy in off for fx in off])
        gy = np.array([cy + fy * tam for fy in off for fx in off])
        sx, sy = de_lroc(list(gx), list(gy))
        ox, oy = de_lroc([cx], [cy])
        vals = [pct_sol(x, y) for x, y in zip(sx, sy)]
        centro = pct_sol(ox[0], oy[0])
        filas.append((ox[0], oy[0], v_pix, v_med, centro, float(np.mean(vals)), float(np.min(vals)), float(np.max(vals))))
        if (k + 1) % 10 == 0:
            print(f"  {k + 1}/{len(celdas)}")

    f = np.array(filas)
    lr_pix, lr_med, pto, cel = f[:, 2], f[:, 3], f[:, 4], f[:, 5]
    L = [f"Celdas comparadas: {len(f)}  |  sub-puntos por celda: {n_sub}  |  altura {a.altura:g} m, radio solar {a.radio_solar:g}",
         f"{'comparacion':<38} {'sesgo':>7} {'Pearson':>8} {'Spearman':>9} {'error abs':>9} {'pendiente':>9}"]
    for nombre, n_, l_ in [("1 punto (centro)  vs LROC pixel", pto, lr_pix),
                           ("promedio de celda vs LROC pixel", cel, lr_pix),
                           ("1 punto (centro)  vs LROC media 3x3", pto, lr_med),
                           ("promedio de celda vs LROC media 3x3", cel, lr_med)]:
        s, pe, sp_, ea, pend = metricas(n_, l_)
        L.append(f"{nombre:<38} {s:>+7.1f} {pe:>8.2f} {sp_:>9.2f} {ea:>9.1f} {pend:>9.2f}")
    L.append("(pendiente: 1.0 = sin compresion; menor que 1 = nuestro modelo comprime hacia el medio)")
    L.append(f"Variacion interna media dentro de una celda (max-min de los sub-puntos): {np.mean(f[:, 7] - f[:, 6]):.1f} puntos")
    txt = "\n".join(L)
    print("\n" + txt)
    with open(os.path.join(a.out, "validacion_celda.txt"), "w", encoding="utf-8") as fh:
        fh.write(txt + "\n")
    with open(os.path.join(a.out, "validacion_celda.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["x_m", "y_m", "lroc_pixel", "lroc_media3x3", "nuestro_punto", "nuestro_celda_media", "celda_min", "celda_max"])
        for r_ in filas:
            w.writerow([round(v, 2) for v in r_])
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(11, 5), sharey=True)
        for axx, v, t in [(ax[0], pto, "1 punto (centro)"), (ax[1], cel, "promedio de la celda")]:
            axx.scatter(lr_pix, v, s=10, alpha=0.6)
            axx.plot([0, 100], [0, 100], "k--", lw=0.8)
            axx.set_xlabel("LROC pixel (% iluminado)")
            axx.set_title(t)
        ax[0].set_ylabel("Nuestro (% Sol)")
        fig.tight_layout()
        fig.savefig(os.path.join(a.out, "validacion_celda.png"), dpi=120)
    except Exception as e:
        print("Aviso: sin grafico:", e)
    print("\nListo. Archivos en:", os.path.abspath(a.out))


if __name__ == "__main__":
    main()
