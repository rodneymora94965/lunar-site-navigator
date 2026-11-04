#!/usr/bin/env python3
"""
validar_ancho.py  -  Solaris Core / MHD-INT
Prueba de la hipotesis "falta terreno fuera del recorte de 16 km".

Recalcula el % de Sol en las MISMAS celdas de validar_celda.py (lee salida_2010/validacion_celda.csv),
pero con un horizonte que combina:
  - DEM fino de 5 m (Site04_surf.tif) donde existe,
  - DEM polar ancho de 80 m (LDEM_80S_80MPP_ADJ.TIF) para el resto, hasta --dmax km.

Antes de calcular, comprueba que ambos DEM coinciden donde se solapan (misma proyeccion, mismas
unidades). Si no coinciden, se detiene y lo dice: asi no se calcula con datos incompatibles.

Uso (desde luna_polo_sur, despues de bajar el DEM de 80 m a datos/):
    python validar_ancho.py
    python validar_ancho.py --dmax 150

Salida (salida_2010/): validacion_ancho.csv, validacion_ancho.txt, validacion_ancho.png
Como leer: si el piso de ~28-30 % en las celdas con LROC = 0 baja hacia 0 y el error absoluto cae
claramente, la causa era el terreno fuera del recorte. Si no cambia, esa hipotesis queda descartada.
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


def leer_lroc(path, xs, ys):
    """Valor (en %) del pixel LROC que contiene cada punto (x, y) de nuestro plano."""
    with rasterio.open(path) as d:
        arr = d.read(1).astype("float64")
        tr, crs, nod = d.transform, d.crs, d.nodata
    if nod is not None:
        arr[arr == nod] = np.nan
    escala = 1.0 if np.nanmax(arr) <= 100.5 else 100.0 / 255.0
    arr = arr * escala
    tx, ty = warp_transform(NUESTRO_CRS, crs, list(xs), list(ys)) if crs is not None else (xs, ys)
    out = np.full(len(xs), np.nan)
    for i, (x, y) in enumerate(zip(tx, ty)):
        r, c = rasterio.transform.rowcol(tr, x, y)
        if 0 <= r < arr.shape[0] and 0 <= c < arr.shape[1]:
            out[i] = arr[r, c]
    return out


def cargar(path, dtype):
    with rasterio.open(path) as d:
        z = d.read(1).astype(dtype)
        nod = d.nodata
        sc = d.scales[0] if d.scales and d.scales[0] is not None else 1.0
        of = d.offsets[0] if d.offsets and d.offsets[0] is not None else 0.0
        tr, crs, b = d.transform, d.crs, d.bounds
    if nod is not None:
        z[z == nod] = np.nan
    if sc != 1.0 or of != 0.0:
        z = z * sc + of
    return z, tr, crs, b, sc, of


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
            float(np.abs(n - l).mean()), float(np.polyfit(l, n, 1)[0]))


def muestrear(z, tr, xs, ys):
    c, r = ~tr * (xs, ys)
    return map_coordinates(z, [r - 0.5, c - 0.5], order=1, mode="constant", cval=np.nan)


def horizonte2(zf, trf, zc, trc, x0, y0, lon_deg, altura, dist, n_az):
    c0, r0 = ~trf * (x0, y0)
    z0 = map_coordinates(zf, [[r0 - 0.5], [c0 - 0.5]], order=1, mode="nearest")[0] + altura
    lam = math.radians(lon_deg)
    radial = np.array([math.sin(lam), math.cos(lam)])
    este = np.array([math.cos(lam), -math.sin(lam)])
    azs = np.linspace(0, 360, n_az, endpoint=False)
    hor = np.empty(n_az)
    curv = dist ** 2 / (2.0 * cc.R_M)
    for i, az in enumerate(np.radians(azs)):
        d = math.cos(az) * radial + math.sin(az) * este
        xs, ys = x0 + d[0] * dist, y0 + d[1] * dist
        zz = muestrear(zf, trf, xs, ys)
        zz = np.where(np.isnan(zz), muestrear(zc, trc, xs, ys), zz)
        ang = np.degrees(np.arctan2(zz - z0 - curv, dist))
        hor[i] = np.nanmax(ang) if np.any(~np.isnan(ang)) else -90.0
    return azs, hor


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dem", default="datos/Site04_surf.tif")
    ap.add_argument("--dem-ancho", default="datos/LDEM_80S_80MPP_ADJ.TIF")
    ap.add_argument("--celdas", default="salida_2010/validacion_celda.csv")
    ap.add_argument("--lroc", default=None,
                    help="otro mapa LROC para comparar (p. ej. datos/WAC_POLE_ILL_TWI_SOUTH_100M.TIF); "
                         "por defecto usa los valores de --celdas")
    ap.add_argument("--kernels", default="kernels")
    ap.add_argument("--start", default="2010-02-15")
    ap.add_argument("--years", type=float, default=0.972)
    ap.add_argument("--step-hours", type=float, default=2.0)
    ap.add_argument("--altura", type=float, default=2.0)
    ap.add_argument("--radio-solar", type=float, default=0.27)
    ap.add_argument("--az", type=int, default=90)
    ap.add_argument("--dmax", type=float, default=120.0, help="alcance maximo del horizonte (km)")
    ap.add_argument("--dmin", type=float, default=0.0,
                    help="ignora el terreno mas cercano que esta distancia (m); LROC trabaja a 100 m y no ve el micro-relieve cercano")
    ap.add_argument("--sub", type=int, default=1,
                    help="sub x sub puntos dentro de cada celda de 100 m (1 = solo el centro). Con --sub 3 o mas "
                         "tambien se evalua el MAXIMO de la celda (LROC marca un pixel como iluminado si lo esta alguna parte)")
    ap.add_argument("--celda", type=float, default=100.0, help="tamano de la celda LROC (m)")
    ap.add_argument("--out", default="salida_2010")
    a = ap.parse_args()

    for p in (a.dem, a.dem_ancho, a.celdas):
        if not os.path.isfile(p):
            print("ERROR: no existe", p)
            sys.exit(1)
    os.makedirs(a.out, exist_ok=True)

    zf, trf, crsf, bf, scf, off_ = cargar(a.dem, "float64")
    zc, trc, crsc, bc, scc, occ = cargar(a.dem_ancho, "float32")
    print(f"DEM fino : {zf.shape}, res {abs(trf.a):g} m, limites {bf}")
    print(f"DEM ancho: {zc.shape}, res {abs(trc.a):g} m, limites {bc}, escala {scc:g}, offset {occ:g}")
    print(f"           CRS ancho: {(crsc.to_string() if crsc else '(sin CRS)')[:110]}")

    # --- comprobacion de coherencia entre ambos DEM (misma proyeccion y unidades) ---
    rng = np.random.default_rng(1)
    xs = rng.uniform(bf.left + 500, bf.right - 500, 3000)
    ys = rng.uniform(bf.bottom + 500, bf.top - 500, 3000)
    vf, vc = muestrear(zf, trf, xs, ys), muestrear(zc, trc, xs, ys)
    ok = ~np.isnan(vf) & ~np.isnan(vc)
    if ok.sum() < 100:
        print("ERROR: casi no hay solape valido entre los dos DEM; revisa proyeccion/limites.")
        sys.exit(1)
    dif = vc[ok] - vf[ok]
    print(f"\nCoherencia en {ok.sum()} puntos del solape: diferencia mediana {np.median(dif):+.1f} m, "
          f"|dif| percentil 95 = {np.percentile(np.abs(dif), 95):.1f} m")
    if abs(np.median(dif)) > 100 or np.percentile(np.abs(dif), 95) > 400:
        print("ERROR: los DEM no coinciden (unidades, offset o proyeccion distintos). No continuo.")
        print("Mandame esta salida completa y lo corregimos.")
        sys.exit(1)
    print("Coherencia aceptable (el DEM de 80 m es mas suave, por eso hay diferencias de unos metros).\n")

    with open(a.celdas, newline="", encoding="utf-8") as f:
        celdas = list(csv.DictReader(f))
    print(f"{len(celdas)} celdas (las mismas de validar_celda.py).")
    print("Efemerides ...")
    marco, sol, _ = cc.efemerides(a.kernels, a.start, a.years, a.step_hours)
    print(f"Marco {marco}; {len(sol)} instantes.\n")

    dist = np.concatenate([np.arange(10.0, 20000.0, 10.0), np.arange(20000.0, a.dmax * 1000.0, 80.0)])
    dist = dist[dist >= max(a.dmin, 10.0)]

    off = (np.arange(a.sub) + 0.5) / a.sub - 0.5 if a.sub > 1 else np.array([0.0])

    def pct_sol(x, y):
        lat, lon = cc.xy_a_latlon(x, y)
        la, lo = math.radians(lat), math.radians(lon)
        este, norte, arriba = cc.base_local(la, lo)
        c0, r0 = ~trf * (x, y)
        href = map_coordinates(zf, [[r0 - 0.5], [c0 - 0.5]], order=1, mode="nearest")[0]
        azs, hor = horizonte2(zf, trf, zc, trc, x, y, lon, a.altura, dist, a.az)
        sitio = np.array([math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la)]) \
            * (cc.R_KM + (href + a.altura) / 1000.0)
        e_s, az_s = cc.elev_az_vec(sol - sitio, este, norte, arriba)
        hs = np.interp(az_s, np.append(azs, 360.0), np.append(hor, hor[0]))
        return 100.0 * np.mean(e_s + a.radio_solar > hs)

    lroc_alt = None
    if a.lroc:
        if not os.path.isfile(a.lroc):
            print("ERROR: no existe", a.lroc)
            sys.exit(1)
        lroc_alt = leer_lroc(a.lroc, [float(r["x_m"]) for r in celdas], [float(r["y_m"]) for r in celdas])
        print(f"Mapa LROC alterno: {a.lroc}  ({int(np.sum(~np.isnan(lroc_alt)))} de {len(celdas)} celdas con dato)")

    nuevo, viejo, lroc, cmedia, cmax = [], [], [], [], []
    for k, r in enumerate(celdas):
        x, y = float(r["x_m"]), float(r["y_m"])
        nuevo.append(pct_sol(x, y))
        if a.sub > 1:
            v = [pct_sol(x + fx * a.celda, y + fy * a.celda) for fy in off for fx in off]
            cmedia.append(float(np.mean(v)))
            cmax.append(float(np.max(v)))
        viejo.append(float(r["nuestro_punto"]))
        lroc.append(float(r["lroc_pixel"]) if lroc_alt is None else float(lroc_alt[k]))
        if (k + 1) % 10 == 0:
            print(f"  {k + 1}/{len(celdas)}")

    nuevo, viejo, lroc = map(np.array, (nuevo, viejo, lroc))
    if lroc_alt is not None:
        ok = ~np.isnan(lroc)
        nuevo, viejo, lroc = nuevo[ok], viejo[ok], lroc[ok]
        cmedia = list(np.array(cmedia)[ok]) if cmedia else cmedia
        cmax = list(np.array(cmax)[ok]) if cmax else cmax
        celdas = [r for r, o in zip(celdas, ok) if o]
    L = [f"Celdas: {len(lroc)} | alcance del horizonte {a.dmin:g} m a {a.dmax:g} km | altura {a.altura:g} m | radio solar {a.radio_solar:g}",
         f"{'modelo':<40} {'sesgo':>7} {'Pearson':>8} {'Spearman':>9} {'error abs':>9} {'pendiente':>9}"]
    comps = [("antes (solo DEM de 5 m)", viejo), ("ahora: centro (5 m + 80 m)", nuevo)]
    if a.sub > 1:
        comps += [(f"ahora: MEDIA de la celda ({a.sub}x{a.sub})", np.array(cmedia)),
                  (f"ahora: MAXIMO de la celda ({a.sub}x{a.sub})", np.array(cmax))]
    for nombre, v in comps:
        s, pe, sp_, ea, pend = metricas(v, lroc)
        L.append(f"{nombre:<40} {s:>+7.1f} {pe:>8.2f} {sp_:>9.2f} {ea:>9.1f} {pend:>9.2f}")
    L.append("")
    L.append("Percentiles [0,10,25,50,75,90,100] de nuestro % de Sol:")
    q = [0, 10, 25, 50, 75, 90, 100]
    L.append("  LROC   " + str(np.percentile(lroc, q).round(0)))
    L.append("  antes  " + str(np.percentile(viejo, q).round(0)))
    L.append("  ahora  " + str(np.percentile(nuevo, q).round(0)))
    if a.sub > 1:
        L.append("  maximo " + str(np.percentile(np.array(cmax), q).round(0)))
    m0 = lroc < 1
    m1 = lroc >= 99
    if m0.any():
        L.append(f"Celdas con LROC = 0 ({m0.sum()}): nuestro medio antes {viejo[m0].mean():.1f} -> ahora {nuevo[m0].mean():.1f}")
    if m1.any():
        L.append(f"Celdas con LROC = 100 ({m1.sum()}): nuestro medio antes {viejo[m1].mean():.1f} -> ahora {nuevo[m1].mean():.1f}")
    txt = "\n".join(L)
    print("\n" + txt)
    with open(os.path.join(a.out, "validacion_ancho.txt"), "w", encoding="utf-8") as fh:
        fh.write(txt + "\n")
    with open(os.path.join(a.out, "validacion_ancho.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["x_m", "y_m", "lroc_pixel", "nuestro_antes", "nuestro_ahora"])
        for r, v0, v1, l in zip(celdas, viejo, nuevo, lroc):
            w.writerow([r["x_m"], r["y_m"], l, round(v0, 1), round(v1, 1)])
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(11, 5), sharey=True)
        for axx, v, t in [(ax[0], viejo, "antes: solo DEM de 5 m"), (ax[1], nuevo, "ahora: 5 m + 80 m")]:
            axx.scatter(lroc, v, s=10, alpha=0.6)
            axx.plot([0, 100], [0, 100], "k--", lw=0.8)
            axx.set_xlabel("LROC pixel (% iluminado)")
            axx.set_title(t)
        ax[0].set_ylabel("Nuestro (% Sol)")
        fig.tight_layout()
        fig.savefig(os.path.join(a.out, "validacion_ancho.png"), dpi=120)
    except Exception as e:
        print("Aviso: sin grafico:", e)
    print("\nListo. Archivos en:", os.path.abspath(a.out))


if __name__ == "__main__":
    main()
