#!/usr/bin/env python3
"""
validar_iluminacion.py  -  Solaris Core / MHD-INT
Compara NUESTRO porcentaje de tiempo con Sol (calculado con DEM + efemerides para
15-feb-2010 .. 5-feb-2011) contra el mapa de iluminacion MEDIDO de LROC WAC
(WAC_POLE_ILL_PCT_SOUTH_100M.TIF, mismo periodo, 100 m/pixel).

Uso (desde luna_polo_sur):
    python validar_iluminacion.py
    python validar_iluminacion.py --lroc datos/WAC_POLE_ILL_PCT_SOUTH_100M.TIF \
        --cand salida_2010/candidatos_evaluados.csv

Como leer el resultado:
 - Nuestro valor tiende a ser MAYOR (horizonte limitado al recorte, centro del Sol, altura de
   observador). Una diferencia moderada y positiva es normal.
 - Lo importante es el ORDEN: si los sitios mejor iluminados segun LROC tambien lo son segun
   nosotros (correlacion de rangos alta), el modelo y la orientacion estan bien.
 - Si la correlacion es baja o negativa, probablemente hay un error de orientacion/convencion.
LIMITES: LROC es un mapa por imagenes (muestreo no uniforme en el tiempo, resolucion 100 m, sin
asumir una altura clara de observador); nuestro modelo es por geometria a 5 m. Es una
comparacion aproximada, no una igualdad.
"""
import argparse
import csv
import os
import sys

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.warp import transform as warp_transform

NUESTRO_CRS = CRS.from_string("+proj=stere +lat_0=-90 +lon_0=0 +k=1 +x_0=0 +y_0=0 +R=1737400 +units=m +no_defs")


def rangos(v):
    v = np.asarray(v, float)
    orden = np.argsort(v, kind="mergesort")
    r = np.empty(len(v))
    r[orden] = np.arange(len(v))
    # promedio para empates
    for val in np.unique(v):
        m = v == val
        r[m] = r[m].mean()
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lroc", default="datos/WAC_POLE_ILL_PCT_SOUTH_100M.TIF")
    ap.add_argument("--cand", default="salida_2010/candidatos_evaluados.csv")
    ap.add_argument("--escala", type=float, default=None,
                    help="si el raster va de 0 a 255, usa --escala 255 para convertir a %%")
    ap.add_argument("--ventana", type=int, default=2, help="radio de ventana en pixeles LROC (2 -> 5x5 = 500 m)")
    ap.add_argument("--out", default="salida_2010")
    a = ap.parse_args()

    for p in (a.lroc, a.cand):
        if not os.path.isfile(p):
            print("ERROR: no existe", p)
            sys.exit(1)
    os.makedirs(a.out, exist_ok=True)

    with rasterio.open(a.lroc) as d:
        arr = d.read(1).astype("float64")
        crs = d.crs
        tr = d.transform
        nod = d.nodata
        print(f"LROC: {d.width} x {d.height} px, res {d.res}, tipo {d.dtypes[0]}, nodata {nod}")
        print(f"      limites {d.bounds}")
        print(f"      CRS: {'(sin CRS)' if crs is None else crs.to_string()[:120]}")
    if nod is not None:
        arr[arr == nod] = np.nan
    vmax = np.nanmax(arr)
    print(f"      valores: min {np.nanmin(arr):g}, max {vmax:g}")
    escala = a.escala
    if escala is None:
        if vmax <= 100.5:
            escala = 1.0
        else:
            escala = 100.0 / 255.0
            print("      AVISO: valores > 100; supongo escala 0-255 -> % (x100/255). "
                  "Si no es asi, corre con --escala.")
    elif a.escala == 255:
        escala = 100.0 / 255.0
    pct_map = arr * escala

    with open(a.cand, newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    xs = [float(r["x_m"]) for r in filas]
    ys = [float(r["y_m"]) for r in filas]
    if crs is not None:
        tx, ty = warp_transform(NUESTRO_CRS, crs, xs, ys)
    else:
        print("AVISO: el raster no trae CRS; supongo la misma estereografica que el DEM.")
        tx, ty = xs, ys

    sal = []
    for r, x, y in zip(filas, tx, ty):
        row, col = rasterio.transform.rowcol(tr, x, y)
        k = a.ventana
        r0, r1 = max(0, row - k), min(arr.shape[0], row + k + 1)
        c0, c1 = max(0, col - k), min(arr.shape[1], col + k + 1)
        if r0 >= r1 or c0 >= c1:
            sal.append((r["id"], r["lat"], float(r["pct_sol"]), np.nan, np.nan, np.nan, np.nan))
            continue
        win = pct_map[r0:r1, c0:c1]
        centro = pct_map[min(max(row, 0), arr.shape[0] - 1), min(max(col, 0), arr.shape[1] - 1)]
        sal.append((r["id"], r["lat"], float(r["pct_sol"]), centro, np.nanmean(win),
                    np.nanmin(win), np.nanmax(win)))

    print(f"\n{'id':>6} {'lat':>8} {'%Sol_nuestro':>12} {'LROC_centro':>11} {'LROC_media':>10} {'LROC_min':>8} {'LROC_max':>8} {'nuestro-LROC':>12}")
    for s in sal:
        dif = s[2] - s[4] if not np.isnan(s[4]) else np.nan
        print(f"{s[0]:>6} {s[1]:>8} {s[2]:>12.1f} {s[3]:>11.1f} {s[4]:>10.1f} {s[5]:>8.1f} {s[6]:>8.1f} {dif:>12.1f}")

    nuestro = np.array([s[2] for s in sal])
    lroc = np.array([s[4] for s in sal])
    ok = ~np.isnan(lroc)
    lines = []
    if ok.sum() >= 3:
        pear = np.corrcoef(nuestro[ok], lroc[ok])[0, 1]
        spear = np.corrcoef(rangos(nuestro[ok]), rangos(lroc[ok]))[0, 1]
        dif = nuestro[ok] - lroc[ok]
        lines.append(f"Candidatos comparados: {ok.sum()}")
        lines.append(f"Diferencia media (nuestro - LROC): {dif.mean():+.1f} puntos porcentuales "
                     f"(rango {dif.min():+.1f} a {dif.max():+.1f})")
        lines.append(f"Correlacion de Pearson: {pear:.2f}   |   correlacion de rangos (Spearman): {spear:.2f}")
    else:
        lines.append("Muy pocos candidatos para correlacionar.")
    print("\n" + "\n".join(lines))
    with open(os.path.join(a.out, "validacion_iluminacion.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(a.out, "validacion_iluminacion.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "lat", "pct_sol_nuestro", "lroc_centro", "lroc_media", "lroc_min", "lroc_max"])
        w.writerows(sal)
    print("Listo. Archivos en:", os.path.abspath(a.out))


if __name__ == "__main__":
    main()
