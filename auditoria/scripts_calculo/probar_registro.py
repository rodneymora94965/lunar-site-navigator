#!/usr/bin/env python3
"""
probar_registro.py  -  Solaris Core / MHD-INT
La validacion en malla dio sesgo ~0 pero error grande (~24 puntos) y una "compresion hacia el
medio" (lo oscuro sale mas claro, lo claro sale mas oscuro). Afinar el horizonte no la quito.
Esa forma es tipica de un DESFASE ESPACIAL entre nuestro mapa y el de LROC (giro, espejo o
corrimiento). Este script lo prueba SIN recalcular nada: usa los valores ya calculados en
salida_2010/validacion_malla.csv y los compara con el mapa LROC leido en posiciones
 (a) giradas/espejadas (8 orientaciones del plano) y
 (b) corridas hasta +-600 m.

Uso (desde luna_polo_sur, despues de validar_malla.py):
    python probar_registro.py

Si la mejor posicion es "normal, sin corrimiento", el registro espacial esta bien y el error
viene de otra causa. Si gana otra, hay un desfase y sabemos cual.
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

VARIANTES = [
    ("0  normal", np.array([[1, 0], [0, 1]], float)),
    ("1  giro 90", np.array([[0, -1], [1, 0]], float)),
    ("2  giro 180", np.array([[-1, 0], [0, -1]], float)),
    ("3  giro 270", np.array([[0, 1], [-1, 0]], float)),
    ("4  espejo en x", np.array([[-1, 0], [0, 1]], float)),
    ("5  espejo en y", np.array([[1, 0], [0, -1]], float)),
    ("6  intercambio x<->y", np.array([[0, 1], [1, 0]], float)),
    ("7  intercambio y espejo", np.array([[0, -1], [-1, 0]], float)),
]


def rangos(v):
    v = np.asarray(v, float)
    o = np.argsort(v, kind="mergesort")
    r = np.empty(len(v))
    r[o] = np.arange(len(v))
    for val in np.unique(v):
        m = v == val
        r[m] = r[m].mean()
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="salida_2010/validacion_malla.csv")
    ap.add_argument("--lroc", default="datos/WAC_POLE_ILL_PCT_SOUTH_100M.TIF")
    ap.add_argument("--col", default="nuestro_rs0.27_h2")
    ap.add_argument("--maxdesp", type=float, default=600.0)
    ap.add_argument("--paso", type=float, default=100.0)
    a = ap.parse_args()
    for p in (a.csv, a.lroc):
        if not os.path.isfile(p):
            print("ERROR: no existe", p)
            sys.exit(1)

    with open(a.csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if a.col not in rows[0]:
        print("ERROR: no hay columna", a.col, "; columnas:", list(rows[0].keys()))
        sys.exit(1)
    xy = np.array([[float(r["x_m"]), float(r["y_m"])] for r in rows])
    ours = np.array([float(r[a.col]) for r in rows])

    with rasterio.open(a.lroc) as d:
        arr = d.read(1).astype("float64")
        tr, crs, nod = d.transform, d.crs, d.nodata
    if nod is not None:
        arr[arr == nod] = np.nan
    arr = arr * (1.0 if np.nanmax(arr) <= 100.5 else 100.0 / 255.0)

    def muestrear(px, py):
        if crs is not None:
            tx, ty = warp_transform(NUESTRO_CRS, crs, list(px), list(py))
        else:
            tx, ty = px, py
        r, c = rasterio.transform.rowcol(tr, tx, ty)
        r, c = np.array(r), np.array(c)
        ok = (r >= 0) & (r < arr.shape[0]) & (c >= 0) & (c < arr.shape[1])
        v = np.full(len(px), np.nan)
        v[ok] = arr[r[ok], c[ok]]
        return v

    def eval_(px, py):
        v = muestrear(px, py)
        m = ~np.isnan(v)
        if m.sum() < 20:
            return np.nan, np.nan, np.nan, int(m.sum())
        return (np.corrcoef(ours[m], v[m])[0, 1],
                np.corrcoef(rangos(ours[m]), rangos(v[m]))[0, 1],
                float((ours[m] - v[m]).mean()), int(m.sum()))

    print(f"{len(ours)} puntos. Columna: {a.col}\n")
    print("(a) Orientaciones del plano al leer LROC:")
    print(f"{'orientacion':<28} {'Pearson':>8} {'Spearman':>9} {'sesgo':>7} {'n':>5}")
    for nombre, M in VARIANTES:
        q = xy @ M.T
        pe, sp_, bi, n = eval_(q[:, 0], q[:, 1])
        print(f"{nombre:<28} {pe:>8.2f} {sp_:>9.2f} {bi:>+7.1f} {n:>5}")

    print(f"\n(b) Corrimientos (orientacion normal), correlacion de Pearson:")
    ds = np.arange(-a.maxdesp, a.maxdesp + 1, a.paso)
    tabla = np.full((len(ds), len(ds)), np.nan)
    for i, dy in enumerate(ds):
        for j, dx in enumerate(ds):
            tabla[i, j] = eval_(xy[:, 0] + dx, xy[:, 1] + dy)[0]
    print("filas: dy (m, de arriba a abajo = " + f"{ds[0]:g}..{ds[-1]:g}); columnas: dx (m)")
    print("        " + " ".join(f"{d:>6g}" for d in ds))
    for i, dy in enumerate(ds):
        print(f"{dy:>7g} " + " ".join(f"{tabla[i, j]:>6.2f}" for j in range(len(ds))))
    i, j = np.unravel_index(np.nanargmax(tabla), tabla.shape)
    cero = tabla[len(ds) // 2, len(ds) // 2]
    print(f"\nMejor corrimiento: dx={ds[j]:g} m, dy={ds[i]:g} m -> Pearson {tabla[i, j]:.2f}  (sin corrimiento: {cero:.2f})")
    print("Interpretacion: si el mejor es (0,0) o la mejora es minima, el registro espacial esta bien.")


if __name__ == "__main__":
    main()
