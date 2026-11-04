#!/usr/bin/env python3
"""
bolsones.py  -  Solaris Core / MHD-INT
Encuentra "bolsones" de aterrizaje: zonas donde una huella circular de radio R
(el modulo) cabe ENTERA sobre celdas con pendiente <= umbral.

Uso (desde luna_polo_sur, despues de analizar_dem.py):
    python bolsones.py
    python bolsones.py --umbral 10 --huella-radio 20 --min-celdas 100

Salida (carpeta salida/):
    <nombre>_bolsones.csv   -> un bolson por fila (ordenados por area)
    <nombre>_bolsones.png   -> mapa de los bolsones sobre la pendiente

PARAMETROS DEL PROTOTIPO (no son requisitos oficiales de la NASA; se ajustan
cuando el reto publique sus criterios):
    --umbral         pendiente maxima permitida (grados)
    --huella-radio   radio de la huella del modulo (m)
    --min-celdas     tamano minimo de un bolson (celdas de centros validos)
"""
import argparse
import csv
import os
import sys

import numpy as np
import rasterio
from scipy import ndimage as ndi

R_LUNA_M = 1737400.0


def xy_a_latlon(x, y, radio=R_LUNA_M):
    rho = np.hypot(x, y)
    c = 2.0 * np.arctan(rho / (2.0 * radio))
    return -90.0 + np.degrees(c), np.degrees(np.arctan2(x, y))


def disco(radio_px):
    r = int(radio_px)
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    return (xx * xx + yy * yy) <= r * r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dem", default="datos/Site04_surf.tif")
    ap.add_argument("--pend", default="salida/Site04_surf_pendiente_calculada.tif")
    ap.add_argument("--umbral", type=float, default=10.0)
    ap.add_argument("--huella-radio", type=float, default=20.0, help="metros")
    ap.add_argument("--min-celdas", type=int, default=100)
    ap.add_argument("--top", type=int, default=15, help="cuantos bolsones imprimir")
    ap.add_argument("--out", default="salida")
    a = ap.parse_args()

    for p in (a.dem, a.pend):
        if not os.path.isfile(p):
            print("ERROR: no existe", p, "(corre antes analizar_dem.py)")
            sys.exit(1)
    os.makedirs(a.out, exist_ok=True)
    nombre = os.path.splitext(os.path.basename(a.dem))[0]

    with rasterio.open(a.dem) as d:
        z = d.read(1).astype("float64")
        res = d.res[0]
        tr = d.transform
        b = d.bounds
    with rasterio.open(a.pend) as s:
        pend = s.read(1).astype("float64")

    segura = (pend <= a.umbral + 1e-6) & ~np.isnan(pend)
    rpx = max(1, int(round(a.huella_radio / res)))
    # un centro es valido si TODA la huella cae en celdas seguras
    # (los bordes del raster cuentan como no seguros: border_value=0)
    centros = ndi.binary_erosion(segura, structure=disco(rpx), border_value=0)

    lab, n = ndi.label(centros, structure=np.ones((3, 3)))
    if n == 0:
        print("No hay ningun bolson con esos parametros.")
        return
    idx = np.arange(1, n + 1)
    areas = ndi.sum(centros, lab, idx)          # en celdas
    keep = idx[areas >= a.min_celdas]
    print(f"Huella: radio {a.huella_radio:g} m ({rpx} px). Umbral {a.umbral:g} grados.")
    print(f"Celdas seguras: {100*segura.sum()/np.sum(~np.isnan(pend)):.1f} %  |  "
          f"centros validos: {100*centros.sum()/centros.size:.2f} % del recorte")
    print(f"Bolsones (>= {a.min_celdas} celdas de centros): {len(keep)} de {n} componentes")
    if len(keep) == 0:
        print("Ninguno cumple el tamano minimo. Prueba otro umbral o una huella menor.")
        return

    cy_cx = ndi.center_of_mass(centros, lab, keep)
    pm = ndi.mean(pend, lab, keep)
    zm = ndi.mean(z, lab, keep)
    ar = ndi.sum(centros, lab, keep) * res * res
    filas = []
    for k, (cy, cx), p, e, A in zip(keep, cy_cx, pm, zm, ar):
        x, y = tr * (cx + 0.5, cy + 0.5)
        la, lo = xy_a_latlon(x, y)
        filas.append(dict(id=int(k), x_m=round(x, 1), y_m=round(y, 1), lat=round(float(la), 5),
                          lon=round(float(lo), 4), area_centros_m2=round(float(A), 0),
                          pend_media_deg=round(float(p), 2), elev_media_m=round(float(e), 1),
                          dist_polo_km=round(float(np.hypot(x, y)) / 1000, 3)))
    filas.sort(key=lambda r: -r["area_centros_m2"])

    ruta = os.path.join(a.out, f"{nombre}_bolsones.csv")
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)

    print(f"\nTop {min(a.top, len(filas))} por area:")
    print(f"{'id':>6} {'x_m':>9} {'y_m':>9} {'lat':>9} {'lon':>9} {'area_m2':>9} {'pend':>6} {'elev_m':>8} {'d_polo_km':>9}")
    for r in filas[:a.top]:
        print(f"{r['id']:>6} {r['x_m']:>9} {r['y_m']:>9} {r['lat']:>9} {r['lon']:>9} "
              f"{r['area_centros_m2']:>9.0f} {r['pend_media_deg']:>6} {r['elev_media_m']:>8} {r['dist_polo_km']:>9}")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        mascara = np.isin(lab, keep)
        ext = [b.left / 1000, b.right / 1000, b.bottom / 1000, b.top / 1000]
        fig, ax = plt.subplots(figsize=(8, 8))
        im = ax.imshow(pend, extent=ext, cmap="gray_r", vmin=0, vmax=40)
        ov = np.ma.masked_where(~mascara, mascara)
        ax.imshow(ov, extent=ext, cmap="autumn", alpha=0.9)
        for i, r in enumerate(filas[:10], 1):
            ax.annotate(str(i), (r["x_m"] / 1000, r["y_m"] / 1000), color="cyan", fontsize=9, weight="bold")
        ax.plot(0, 0, "b+", ms=12)
        ax.set_title(f"{nombre}: bolsones (naranja) - huella {a.huella_radio:g} m, pendiente <= {a.umbral:g} grados\n"
                     "numeros = ranking por area; + azul = polo sur")
        ax.set_xlabel("x (km)"); ax.set_ylabel("y (km)")
        fig.colorbar(im, ax=ax, shrink=0.7, label="pendiente (grados)")
        fig.tight_layout()
        fig.savefig(os.path.join(a.out, f"{nombre}_bolsones.png"), dpi=120)
    except Exception as e:
        print("Aviso: no se pudo generar el grafico:", e)

    print("\nListo. Archivos en:", os.path.abspath(a.out))


if __name__ == "__main__":
    main()
