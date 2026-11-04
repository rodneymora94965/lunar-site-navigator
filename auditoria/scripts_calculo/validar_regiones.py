#!/usr/bin/env python3
"""Compara cada punto representativo de region con LROC (solo cubre de 88 a 90 grados S) y, a 85 grados S o mas al sur, con PGDA. Sin calibrar.

Es una comparacion por punto: no aprueba ni reprueba. Modelo: observador a 5 m, Sol puntual, centro de la Tierra, terreno de 80 m y 120 m.
LROC: periodo del mapa (2010-02-15, 0,972 anos, cada hora). PGDA: efemerides de 19 anos cada 6 h, como validar_pgda.py.
Rango: minimo y maximo del mapa en los 3x3 pixeles alrededor del punto.
Uso: PRECALC_CACHE=<carpeta con eph_*.npz> AUDIT_CACHE=<carpeta con sol_2010_1h.npy> python auditoria/scripts_calculo/validar_regiones.py
"""
import csv, os, re, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("LOLA_DATA_DIR", str(ROOT.parent / "luna_polo_sur" / "datos"))
import horizon2 as hz
from lectura_productos import indices_mapa, read_pds_image
EXT = ROOT / "auditoria" / "datos_externos"
OUT = ROOT / "auditoria" / "regiones"
PC, AC = Path(os.environ["PRECALC_CACHE"]), Path(os.environ["AUDIT_CACHE"])
d = np.load(next(PC.glob("eph_*.npz")))
S19, E19 = d["S"][::6], d["E"][::6]
S10 = np.load(AC / "sol_2010_1h.npy")
A, x0, y0, sc, _ = read_pds_image(EXT / "WAC_POLE_ILL_PCT_SOUTH_100M.IMG")
lo, so = y0 / sc, -x0 / sc


def leer_pgda(n):
    t = (EXT / (n + ".LBL")).read_text(errors="replace")
    g = lambda k: re.search(rf"^\s*{k}\s*=\s*\"?([^\s\"<]+)", t, re.M).group(1)
    a = np.fromfile(EXT / (n + ".IMG"), dtype="<i2").reshape(int(g("LINES")), int(g("LINE_SAMPLES")))
    return a, float(g("SCALING_FACTOR")), float(g("OFFSET")), float(re.search(r"MAP_SCALE\s*=\s*([\d.]+)", t).group(1)), float(g("LINE_PROJECTION_OFFSET")), float(g("SAMPLE_PROJECTION_OFFSET"))


PS, PE = leer_pgda("AVGVISIB_85S_060M_201608"), leer_pgda("AVGVISIB_85S_060M_201608_EARTH")


def ventana(M, f, px, c, cs, x, y):
    r, k = indices_mapa(x, y, px, c, cs)
    if r < 1 or k < 1 or r + 2 > M.shape[0] or k + 2 > M.shape[1]:
        return None  # el mapa no cubre este punto (LROC solo llega de 88 a 90 grados S)
    w = np.asarray(M[r - 1:r + 2, k - 1:k + 2], dtype=float)
    w = f(w)
    w[(w < 0) | (w > 100)] = np.nan
    if not np.isfinite(w[1, 1]):
        return None
    return float(w[1, 1]), float(np.nanmin(w)), float(np.nanmax(w))


rows = []
for r in csv.DictReader(open(OUT / "puntos_representativos.csv", encoding="utf-8")):
    lat, lon = float(r["lat"]), float(r["lon"])
    x, y = hz.xy_from_latlon(lat, lon)
    T = hz.load_terrain(center=(x, y), radius_m=215000)
    azs, H = hz.horizon(T, x, y, 5.0)
    a, e = hz.az_el(S10, lat, lon)
    m_l = 100 * hz.above(a, e, azs, H).mean()
    q = dict(id=r["id"], region=r["region"], lat=lat, lon=lon)
    vl = ventana(A, lambda w: w, sc, lo, so, x, y)
    if vl:
        q.update(modelo_sol_2010=round(float(m_l), 1), lroc=round(vl[0], 1), lroc_min3x3=round(vl[1], 1), lroc_max3x3=round(vl[2], 1))
    if lat <= -85:
        sa, se = hz.az_el(S19, lat, lon)
        ta, te = hz.az_el(E19, lat, lon)
        ms, mt = 100 * hz.above(sa, se, azs, H).mean(), 100 * hz.above(ta, te, azs, H).mean()
        for name, P, m in (("sol", PS, ms), ("tierra", PE, mt)):
            vp = ventana(P[0], lambda w: 100 * (w * P[1] + P[2]), P[3], P[4], P[5], x, y)
            if vp:
                q.update({f"modelo_{name}": round(float(m), 1), f"pgda_{name}": round(vp[0], 1), f"pgda_{name}_min3x3": round(vp[1], 1), f"pgda_{name}_max3x3": round(vp[2], 1)})
    rows.append(q)
    print(q, flush=True)
keys = ["id", "region", "lat", "lon", "modelo_sol_2010", "lroc", "lroc_min3x3", "lroc_max3x3", "modelo_sol", "pgda_sol", "pgda_sol_min3x3", "pgda_sol_max3x3", "modelo_tierra", "pgda_tierra", "pgda_tierra_min3x3", "pgda_tierra_max3x3"]
with open(OUT / "validacion_regiones.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=keys)
    w.writeheader()
    w.writerows(rows)
