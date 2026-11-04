#!/usr/bin/env python3
"""
probar_orientaciones.py  -  Solaris Core / MHD-INT
Diagnostico: la validacion contra LROC dio correlacion media (Pearson 0.74 / Spearman 0.68) y
nuestro % de Sol quedo MENOR que el medido en muchos sitios. Esto prueba si la causa es la
ORIENTACION del DEM (convencion de ejes x,y -> longitud).

Repite el calculo de Sol (mismo periodo que LROC) con las 8 orientaciones posibles del plano
(4 giros x espejo o no) y mide cual se parece mas al mapa de LROC. Tambien prueba el efecto
de contar el radio del disco solar (0.27 grados) como "parcialmente iluminado".

Uso (desde luna_polo_sur, despues de validar_iluminacion.py):
    python probar_orientaciones.py

Requiere: salida_2010/candidatos_evaluados.csv, salida_2010/validacion_iluminacion.csv,
          datos/Site04_surf.tif y la carpeta kernels/.
"""
import argparse
import csv
import math
import os
import sys

import numpy as np
import rasterio
from scipy.ndimage import map_coordinates

import calcular_candidatos as cc

# 8 orientaciones del plano (grupo diedrico): matrices ortogonales aplicadas a (x, y)
VARIANTES = [
    ("0  normal (x=rho*sin(lon), y=rho*cos(lon))", np.array([[1, 0], [0, 1]], float)),
    ("1  giro 90", np.array([[0, -1], [1, 0]], float)),
    ("2  giro 180", np.array([[-1, 0], [0, -1]], float)),
    ("3  giro 270", np.array([[0, 1], [-1, 0]], float)),
    ("4  espejo en x", np.array([[-1, 0], [0, 1]], float)),
    ("5  espejo en y", np.array([[1, 0], [0, -1]], float)),
    ("6  intercambio x<->y", np.array([[0, 1], [1, 0]], float)),
    ("7  intercambio y espejo", np.array([[0, -1], [-1, 0]], float)),
]


def horizonte_M(z, transform, x0, y0, M, altura, n_az=180, paso_m=5.0):
    """Igual que cc.horizonte pero con la orientacion M: (x',y') = M (x,y) define lat/lon."""
    inv = ~transform
    col0, row0 = inv * (x0, y0)
    z0 = map_coordinates(z, [[row0 - 0.5], [col0 - 0.5]], order=1, mode="nearest")[0] + altura
    xp, yp = M @ np.array([x0, y0])
    lat, lon = cc.xy_a_latlon(xp, yp)
    lam = math.radians(lon)
    radial = np.array([math.sin(lam), math.cos(lam)])
    este = np.array([math.cos(lam), -math.sin(lam)])
    azs = np.linspace(0, 360, n_az, endpoint=False)
    res = abs(transform.a)
    dist = np.arange(1, int(max(z.shape) * res / paso_m) + 1) * paso_m
    hor = np.empty(n_az)
    for i, az in enumerate(np.radians(azs)):
        d_p = math.cos(az) * radial + math.sin(az) * este     # direccion en el plano primado
        d_o = M.T @ d_p                                       # de vuelta al plano del DEM
        cols, rows = inv * (x0 + d_o[0] * dist, y0 + d_o[1] * dist)
        zz = map_coordinates(z, [rows - 0.5, cols - 0.5], order=1, mode="constant", cval=np.nan)
        ang = np.degrees(np.arctan2(zz - z0 - dist ** 2 / (2.0 * cc.R_M), dist))
        hor[i] = np.nanmax(ang) if np.any(~np.isnan(ang)) else -90.0
    return azs, hor, lat, lon


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
    ap.add_argument("--cand", default="salida_2010/candidatos_evaluados.csv")
    ap.add_argument("--val", default="salida_2010/validacion_iluminacion.csv")
    ap.add_argument("--dem", default="datos/Site04_surf.tif")
    ap.add_argument("--kernels", default="kernels")
    ap.add_argument("--start", default="2010-02-15")
    ap.add_argument("--years", type=float, default=0.972)
    ap.add_argument("--step-hours", type=float, default=2.0)
    ap.add_argument("--altura", type=float, default=2.0)
    ap.add_argument("--radio-solar", type=float, default=0.27, help="grados")
    a = ap.parse_args()

    for p in (a.cand, a.val, a.dem):
        if not os.path.isfile(p):
            print("ERROR: no existe", p)
            sys.exit(1)

    with open(a.cand, newline="", encoding="utf-8") as f:
        cand = {r["id"]: r for r in csv.DictReader(f)}
    with open(a.val, newline="", encoding="utf-8") as f:
        val = [r for r in csv.DictReader(f)]
    ids = [r["id"] for r in val if r["id"] in cand]
    lroc_media = np.array([float(r["lroc_media"]) for r in val if r["id"] in cand])
    lroc_centro = np.array([float(r["lroc_centro"]) for r in val if r["id"] in cand])

    with rasterio.open(a.dem) as d:
        z = d.read(1).astype("float64")
        tr = d.transform

    print("Efemerides ...")
    marco, sol, tie = cc.efemerides(a.kernels, a.start, a.years, a.step_hours)
    print(f"Marco {marco}; {len(sol)} instantes; {len(ids)} candidatos.\n")

    print(f"{'variante':<46} {'Pearson':>7} {'Spearman':>8} {'dif.media':>9}   |  con radio solar {a.radio_solar:g}: {'Pearson':>7} {'Spearman':>8} {'dif.media':>9}")
    resumen = []
    for nombre, M in VARIANTES:
        p0, p1 = [], []
        for i in ids:
            x, y = float(cand[i]["x_m"]), float(cand[i]["y_m"])
            azs, hor, lat, lon = horizonte_M(z, tr, x, y, M, a.altura)
            xi, yi = ~tr * (x, y)
            href = map_coordinates(z, [[yi - 0.5], [xi - 0.5]], order=1, mode="nearest")[0]
            la, lo = math.radians(lat), math.radians(lon)
            este, norte, arriba = cc.base_local(la, lo)
            sitio = np.array([math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la)]) \
                * (cc.R_KM + (href + a.altura) / 1000.0)
            e_s, az_s = cc.elev_az_vec(sol - sitio, este, norte, arriba)
            hs = np.interp(az_s, np.append(azs, 360.0), np.append(hor, hor[0]))
            p0.append(100 * np.mean(e_s > hs))
            p1.append(100 * np.mean(e_s + a.radio_solar > hs))
        p0, p1 = np.array(p0), np.array(p1)

        def met(p):
            return (np.corrcoef(p, lroc_media)[0, 1],
                    np.corrcoef(rangos(p), rangos(lroc_media))[0, 1],
                    (p - lroc_media).mean())
        m0, m1 = met(p0), met(p1)
        resumen.append((nombre, m0, m1))
        print(f"{nombre:<46} {m0[0]:>7.2f} {m0[1]:>8.2f} {m0[2]:>+9.1f}   |  {'':>20}{m1[0]:>7.2f} {m1[1]:>8.2f} {m1[2]:>+9.1f}")

    mejor = max(resumen, key=lambda r: -9 if np.isnan(r[1][1]) else r[1][1])
    print(f"\nMejor orientacion por correlacion de rangos (sin radio solar): {mejor[0]}  (Spearman {mejor[1][1]:.2f})")
    print("Si la mejor es la 0 (normal) y con buena ventaja, la orientacion esta bien y la diferencia viene de otras causas.")
    print("Si gana otra con ventaja clara, la convencion de ejes del DEM es distinta de la supuesta.")


if __name__ == "__main__":
    main()
