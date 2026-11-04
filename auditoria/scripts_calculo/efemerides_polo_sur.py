#!/usr/bin/env python3
"""
efemerides_polo_sur.py  -  Solaris Core / MHD-INT
Posicion del Sol y de la Tierra vistos desde un punto de la superficie lunar
(por defecto el polo sur) durante un rango de anos, usando SPICE (NAIF/JPL).

Uso (desde la carpeta luna_polo_sur, con la subcarpeta kernels/ ya descargada):
    python efemerides_polo_sur.py
    python efemerides_polo_sur.py --lat -89.9 --lon 0 --start 2026-11-01 --years 10 --step-hours 1

Salida (carpeta salida/):
    efemerides_<lat>_<lon>.csv   -> elevacion y azimut del Sol y de la Tierra por hora
    resumen_<lat>_<lon>.txt      -> resumen y chequeos
    elevaciones_<lat>_<lon>.png  -> grafico de elevacion del Sol y de la Tierra

LIMITES (importante): el observador esta sobre la esfera de referencia lunar
(1737.4 km, la que usan los productos LOLA). NO incluye el relieve: "Tierra sobre
el horizonte" aqui significa sobre el horizonte matematico plano. El horizonte real
(crateres, montanas) se calcula despues con el modelo de elevacion (DEM).
"""
import argparse
import csv
import math
import os
import sys

import numpy as np
import spiceypy as sp

R_LUNA_KM = 1737.4  # esfera de referencia lunar (LOLA)

KERNELS = [
    "naif0012.tls",               # segundos intercalares
    "de440s.bsp",                 # posiciones Sol/Tierra/Luna
    "pck00011.tpc",               # constantes (radios)
    "moon_de440_250416.tf",       # definicion de los marcos lunares
    "moon_pa_de440_200625.bpc",   # orientacion de la Luna
]
CANDIDATE_FRAMES = ["MOON_ME_DE440", "MOON_ME", "MOON_PA_DE440"]


def cargar_kernels(carpeta):
    faltan = [k for k in KERNELS if not os.path.isfile(os.path.join(carpeta, k))]
    if faltan:
        print("ERROR: faltan estos kernels en", carpeta)
        for k in faltan:
            print("  -", k)
        sys.exit(1)
    for k in KERNELS:
        sp.furnsh(os.path.join(carpeta, k))


def elegir_marco():
    for nombre in CANDIDATE_FRAMES:
        if sp.namfrm(nombre) != 0:
            return nombre
    print("ERROR: no se encontro ningun marco lunar. Probados:", CANDIDATE_FRAMES)
    sys.exit(1)


def base_local(lat_rad, lon_rad):
    """Vectores unitarios (este, norte, arriba) en el marco fijo a la Luna."""
    sl, cl = math.sin(lat_rad), math.cos(lat_rad)
    so, co = math.sin(lon_rad), math.cos(lon_rad)
    este = np.array([-so, co, 0.0])
    norte = np.array([-sl * co, -sl * so, cl])
    arriba = np.array([cl * co, cl * so, sl])
    return este, norte, arriba


def elev_az(vec, este, norte, arriba):
    d = np.linalg.norm(vec)
    elev = math.degrees(math.asin(np.dot(vec, arriba) / d))
    az = math.degrees(math.atan2(np.dot(vec, este), np.dot(vec, norte))) % 360.0
    return elev, az, d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lat", type=float, default=-90.0, help="latitud selenografica (grados)")
    ap.add_argument("--lon", type=float, default=0.0, help="longitud este (grados)")
    ap.add_argument("--start", default="2026-11-01", help="fecha inicial AAAA-MM-DD (UTC)")
    ap.add_argument("--years", type=float, default=10.0)
    ap.add_argument("--step-hours", type=float, default=1.0)
    ap.add_argument("--kernels", default=None, help="carpeta de kernels (por defecto ./kernels)")
    ap.add_argument("--out", default=None, help="carpeta de salida (por defecto ./salida)")
    a = ap.parse_args()

    aqui = os.path.dirname(os.path.abspath(__file__))
    kdir = a.kernels or os.path.join(aqui, "kernels")
    odir = a.out or os.path.join(aqui, "salida")
    os.makedirs(odir, exist_ok=True)

    cargar_kernels(kdir)
    marco = elegir_marco()
    print("Marco lunar usado:", marco)

    lat, lon = math.radians(a.lat), math.radians(a.lon)
    sitio = np.array(sp.latrec(R_LUNA_KM, lon, lat))
    este, norte, arriba = base_local(lat, lon)

    et0 = sp.str2et(f"{a.start} 00:00:00 UTC")
    n = int(round(a.years * 365.25 * 24.0 / a.step_hours))
    paso = a.step_hours * 3600.0
    print(f"Calculando {n} puntos ({a.years} anos, paso {a.step_hours} h)...")

    etiqueta = f"{a.lat:.2f}_{a.lon:.2f}".replace("-", "S").replace(".", "p")
    ruta_csv = os.path.join(odir, f"efemerides_{etiqueta}.csv")

    sol_el = np.empty(n)
    tie_el = np.empty(n)
    with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["utc", "sol_elev_deg", "sol_az_deg", "tierra_elev_deg",
                    "tierra_az_deg", "tierra_dist_km"])
        for i in range(n):
            et = et0 + i * paso
            sol, _ = sp.spkpos("SUN", et, marco, "LT+S", "MOON")
            tie, _ = sp.spkpos("EARTH", et, marco, "LT+S", "MOON")
            e_s, az_s, _ = elev_az(np.array(sol) - sitio, este, norte, arriba)
            e_t, az_t, d_t = elev_az(np.array(tie) - sitio, este, norte, arriba)
            sol_el[i], tie_el[i] = e_s, e_t
            w.writerow([sp.et2utc(et, "ISOC", 0), f"{e_s:.4f}", f"{az_s:.2f}",
                        f"{e_t:.4f}", f"{az_t:.2f}", f"{d_t:.0f}"])

    # ---- resumen y chequeos de cordura ----
    lineas = []
    lineas.append(f"Sitio: lat {a.lat}, lon {a.lon}  |  inicio {a.start}  |  {a.years} anos  |  paso {a.step_hours} h")
    lineas.append(f"Marco: {marco}")
    lineas.append(f"Sol (centro del disco): elevacion min {sol_el.min():.2f}, max {sol_el.max():.2f} grados")
    lineas.append(f"  fraccion del tiempo con el centro del Sol sobre el horizonte matematico: {100*np.mean(sol_el>0):.1f} %")
    lineas.append(f"Tierra: elevacion min {tie_el.min():.2f}, max {tie_el.max():.2f} grados")
    lineas.append(f"  fraccion del tiempo con la Tierra sobre el horizonte matematico: {100*np.mean(tie_el>0):.1f} %")
    lineas.append("")
    lineas.append("CHEQUEOS:")
    if abs(a.lat) > 89.0:
        ok = abs(sol_el).max() < 2.0
        lineas.append(f"  Sol cerca del polo debe quedar dentro de ~±1.6 grados (oblicuidad lunar ~1.54): "
                      f"{'OK' if ok else 'REVISAR - fuera de rango'}")
        ok2 = abs(tie_el).max() < 10.0
        lineas.append(f"  Tierra cerca del polo debe quedar dentro de ~±10 grados (libracion): "
                      f"{'OK' if ok2 else 'REVISAR - fuera de rango'}")
    lineas.append("  Nota: sin relieve. El horizonte real hay que calcularlo con el DEM.")
    texto = "\n".join(lineas)
    print("\n" + texto)
    with open(os.path.join(odir, f"resumen_{etiqueta}.txt"), "w", encoding="utf-8") as f:
        f.write(texto + "\n")

    # ---- grafico ----
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        dias = np.arange(n) * a.step_hours / 24.0
        paso_g = max(1, n // 6000)
        fig, ax = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
        ax[0].plot(dias[::paso_g], sol_el[::paso_g], lw=0.6)
        ax[0].axhline(0, color="k", lw=0.5)
        ax[0].set_ylabel("Elevacion del Sol (grados)")
        ax[1].plot(dias[::paso_g], tie_el[::paso_g], lw=0.6, color="tab:green")
        ax[1].axhline(0, color="k", lw=0.5)
        ax[1].set_ylabel("Elevacion de la Tierra (grados)")
        ax[1].set_xlabel(f"Dias desde {a.start}")
        fig.suptitle(f"Sol y Tierra vistos desde lat {a.lat}, lon {a.lon} (sin relieve)")
        fig.tight_layout()
        fig.savefig(os.path.join(odir, f"elevaciones_{etiqueta}.png"), dpi=130)
    except Exception as e:  # el grafico es opcional
        print("Aviso: no se pudo generar el grafico:", e)

    print(f"\nListo. Archivos en: {odir}")


if __name__ == "__main__":
    main()
