#!/usr/bin/env python3
"""
calcular_candidatos.py  -  Solaris Core / MHD-INT
Para cada bolson candidato (salida de bolsones.py) calcula, durante varios anos:
  - horizonte local real (a partir del DEM LOLA),
  - porcentaje de tiempo con el Sol sobre ese horizonte,
  - porcentaje de tiempo con la Tierra sobre ese horizonte (linea de vista de comunicaciones),
  - porcentaje con AMBOS a la vez,
  - la noche continua mas larga (dias sin Sol) -> clave para energia.

Uso (desde luna_polo_sur, despues de bolsones.py):
    python calcular_candidatos.py
    python calcular_candidatos.py --top 15 --years 10 --step-hours 3 --altura 2

SUPUESTOS Y LIMITES (leelos antes de confiar en los numeros):
 1. El horizonte solo ve el terreno DENTRO del recorte (16 x 16 km). Montanas fuera del
    recorte que tapen el Sol/Tierra NO se cuentan -> los porcentajes son COTA SUPERIOR
    (optimistas) sobre todo para el Sol, que va muy bajo (+-1.5 grados) en el polo.
 2. "Sol visible" = el CENTRO del disco solar sobre el horizonte (sin radio solar ~0.27 grados
    ni penumbra). Es una simplificacion.
 3. Se incluye la curvatura lunar (caida d^2/2R). Altura del observador: --altura (m).
 4. Convencion de orientacion del DEM: estereografica polar sur estandar (x = rho*sin(lon),
    y = rho*cos(lon), lon este positivo), como define PROJ. Es una suposicion de formula,
    no se verifico contra un dato independiente.
 5. Marco lunar fijo: MOON_ME (kernel DE440), igual que efemerides_polo_sur.py.
"""
import argparse
import csv
import math
import os
import sys

import numpy as np
import rasterio
from scipy.ndimage import map_coordinates

R_M = 1737400.0   # esfera de referencia (m), igual que el CRS del DEM
R_KM = R_M / 1000.0

KERNELS = ["naif0012.tls", "de440s.bsp", "pck00011.tpc",
           "moon_de440_250416.tf", "moon_pa_de440_200625.bpc"]
MARCOS = ["MOON_ME_DE440", "MOON_ME", "MOON_PA_DE440"]


# ---------------- geometria ----------------
def base_local(lat_rad, lon_rad):
    sl, cl = math.sin(lat_rad), math.cos(lat_rad)
    so, co = math.sin(lon_rad), math.cos(lon_rad)
    este = np.array([-so, co, 0.0])
    norte = np.array([-sl * co, -sl * so, cl])
    arriba = np.array([cl * co, cl * so, sl])
    return este, norte, arriba


def elev_az_vec(v, este, norte, arriba):
    """v: (n,3). Devuelve elevacion y azimut (grados, azimut desde el norte hacia el este)."""
    d = np.linalg.norm(v, axis=1)
    elev = np.degrees(np.arcsin(np.clip(v @ arriba / d, -1, 1)))
    az = np.degrees(np.arctan2(v @ este, v @ norte)) % 360.0
    return elev, az


def xy_a_latlon(x, y):
    rho = math.hypot(x, y)
    c = 2.0 * math.atan(rho / (2.0 * R_M))
    return -90.0 + math.degrees(c), math.degrees(math.atan2(x, y))


def horizonte(z, transform, x0, y0, lon_deg, altura, n_az=180, paso_m=5.0, curvatura=True):
    """Elevacion del horizonte (grados) para n_az azimuts (0..360 desde el norte local)."""
    inv = ~transform
    col0, row0 = inv * (x0, y0)
    z0 = map_coordinates(z, [[row0 - 0.5], [col0 - 0.5]], order=1, mode="nearest")[0] + altura
    lam = math.radians(lon_deg)
    radial = np.array([math.sin(lam), math.cos(lam)])      # norte local en el plano (x,y)
    este_xy = np.array([math.cos(lam), -math.sin(lam)])    # este local en el plano (x,y)
    azs = np.linspace(0, 360, n_az, endpoint=False)
    res = abs(transform.a)
    nmax = int(max(z.shape) * res / paso_m)
    dist = np.arange(1, nmax + 1) * paso_m
    hor = np.empty(n_az)
    for i, az in enumerate(np.radians(azs)):
        dxy = math.cos(az) * radial + math.sin(az) * este_xy
        xs = x0 + dxy[0] * dist
        ys = y0 + dxy[1] * dist
        cols, rows = inv * (xs, ys)
        zz = map_coordinates(z, [rows - 0.5, cols - 0.5], order=1, mode="constant", cval=np.nan)
        caida = (dist ** 2) / (2.0 * R_M) if curvatura else 0.0
        ang = np.degrees(np.arctan2(zz - z0 - caida, dist))
        hor[i] = np.nanmax(ang) if np.any(~np.isnan(ang)) else -90.0
    return azs, hor


def racha_maxima(mascara_falso, paso_dias):
    """Mayor numero de dias consecutivos en que la mascara es True (aqui: sin Sol)."""
    m = np.concatenate([[0], mascara_falso.astype(np.int8), [0]])
    d = np.diff(m)
    ini, fin = np.where(d == 1)[0], np.where(d == -1)[0]
    return float((fin - ini).max() * paso_dias) if len(ini) else 0.0


# ---------------- SPICE ----------------
def efemerides(kdir, start, anos, paso_h):
    import spiceypy as sp
    faltan = [k for k in KERNELS if not os.path.isfile(os.path.join(kdir, k))]
    if faltan:
        print("ERROR: faltan kernels:", faltan)
        sys.exit(1)
    for k in KERNELS:
        sp.furnsh(os.path.join(kdir, k))
    marco = next((m for m in MARCOS if sp.namfrm(m) != 0), None)
    if marco is None:
        print("ERROR: sin marco lunar")
        sys.exit(1)
    et0 = sp.str2et(f"{start} 00:00:00 UTC")
    n = int(round(anos * 365.25 * 24.0 / paso_h))
    sol = np.empty((n, 3))
    tie = np.empty((n, 3))
    for i in range(n):
        et = et0 + i * paso_h * 3600.0
        sol[i] = sp.spkpos("SUN", et, marco, "LT+S", "MOON")[0]
        tie[i] = sp.spkpos("EARTH", et, marco, "LT+S", "MOON")[0]
    return marco, sol, tie


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="salida/Site04_surf_bolsones.csv")
    ap.add_argument("--dem", default="datos/Site04_surf.tif")
    ap.add_argument("--kernels", default="kernels")
    ap.add_argument("--top", type=int, default=10, help="cuantos bolsones evaluar (por area)")
    ap.add_argument("--start", default="2026-11-01")
    ap.add_argument("--years", type=float, default=10.0)
    ap.add_argument("--step-hours", type=float, default=3.0)
    ap.add_argument("--altura", type=float, default=2.0, help="altura del observador/antena (m)")
    ap.add_argument("--out", default="salida")
    a = ap.parse_args()

    for p in (a.csv, a.dem):
        if not os.path.isfile(p):
            print("ERROR: no existe", p)
            sys.exit(1)
    os.makedirs(a.out, exist_ok=True)

    with open(a.csv, newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))[: a.top]
    with rasterio.open(a.dem) as d:
        z = d.read(1).astype("float64")
        tr = d.transform

    print(f"Efemerides: {a.years} anos, paso {a.step_hours} h ...")
    marco, sol, tie = efemerides(a.kernels, a.start, a.years, a.step_hours)
    n = len(sol)
    paso_dias = a.step_hours / 24.0
    print(f"Marco {marco}; {n} instantes. Evaluando {len(filas)} bolsones...\n")

    res = []
    for r in filas:
        x, y = float(r["x_m"]), float(r["y_m"])
        lat, lon = xy_a_latlon(x, y)
        azs, hor = horizonte(z, tr, x, y, lon, a.altura)
        h_ref = (map_coordinates(z, [[(~tr * (x, y))[1] - 0.5], [(~tr * (x, y))[0] - 0.5]], order=1,
                                 mode="nearest")[0])
        este, norte, arriba = base_local(math.radians(lat), math.radians(lon))
        sitio = np.array([math.cos(math.radians(lat)) * math.cos(math.radians(lon)),
                          math.cos(math.radians(lat)) * math.sin(math.radians(lon)),
                          math.sin(math.radians(lat))]) * (R_KM + (h_ref + a.altura) / 1000.0)

        e_s, az_s = elev_az_vec(sol - sitio, este, norte, arriba)
        e_t, az_t = elev_az_vec(tie - sitio, este, norte, arriba)
        hs = np.interp(az_s, np.append(azs, 360.0), np.append(hor, hor[0]))
        ht = np.interp(az_t, np.append(azs, 360.0), np.append(hor, hor[0]))
        sol_vis = e_s > hs
        tie_vis = e_t > ht
        res.append(dict(
            id=r["id"], x_m=r["x_m"], y_m=r["y_m"], lat=round(lat, 4), lon=round(lon, 3),
            elev_m=round(h_ref, 0), area_centros_m2=r["area_centros_m2"],
            pend_media_deg=r["pend_media_deg"],
            horizonte_max_deg=round(float(hor.max()), 2),
            pct_sol=round(100 * sol_vis.mean(), 1),
            pct_tierra=round(100 * tie_vis.mean(), 1),
            pct_ambos=round(100 * (sol_vis & tie_vis).mean(), 1),
            noche_max_dias=round(racha_maxima(~sol_vis, paso_dias), 1),
            sin_tierra_max_dias=round(racha_maxima(~tie_vis, paso_dias), 1),
        ))

    res.sort(key=lambda q: (-q["pct_ambos"], q["noche_max_dias"]))
    ruta = os.path.join(a.out, "candidatos_evaluados.csv")
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(res[0].keys()))
        w.writeheader()
        w.writerows(res)

    cab = f"{'id':>6} {'lat':>8} {'lon':>8} {'elev_m':>7} {'area_m2':>9} {'horiz':>6} {'%Sol':>6} {'%Tier':>6} {'%Ambos':>6} {'noche_d':>7} {'sinT_d':>6}"
    print(cab)
    for q in res:
        print(f"{q['id']:>6} {q['lat']:>8} {q['lon']:>8} {q['elev_m']:>7.0f} {float(q['area_centros_m2']):>9.0f} "
              f"{q['horizonte_max_deg']:>6} {q['pct_sol']:>6} {q['pct_tierra']:>6} {q['pct_ambos']:>6} "
              f"{q['noche_max_dias']:>7} {q['sin_tierra_max_dias']:>6}")
    print("\nOrdenado por % de tiempo con Sol y Tierra a la vez, y luego por noche mas corta.")
    print("RECUERDA: horizonte limitado al recorte (16 km) -> porcentajes optimistas.")
    print("Listo:", os.path.abspath(ruta))


if __name__ == "__main__":
    main()
