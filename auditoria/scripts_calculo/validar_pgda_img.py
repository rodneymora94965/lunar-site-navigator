#!/usr/bin/env python3
"""Compara el modelo con los mapas PGDA/LOLA (AVGVISIB_85S_060M_201608 y su version EARTH) en formato IMG.
Lee escala y tamano de la etiqueta PDS3 (.LBL): fraccion = DN * SCALING_FACTOR + OFFSET. Sin calibracion.
Salida: auditoria/validacion/validacion_pgda.txt y .csv
"""
import csv, re, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lectura_productos import indices_mapa, metricas
EXT = ROOT / "auditoria" / "datos_externos"
OUTDIR = ROOT / "auditoria" / "validacion"
MODELO = OUTDIR / "validacion_pgda_modelo.csv"

def leer(nombre):
    lbl = (EXT / (nombre + ".LBL")).read_text(errors="replace")
    g = lambda k: re.search(rf"^\s*{k}\s*=\s*\"?([^\s\"<]+)", lbl, re.M).group(1)
    n, m = int(g("LINES")), int(g("LINE_SAMPLES"))
    assert g("SAMPLE_TYPE") == "LSB_INTEGER" and int(g("SAMPLE_BITS")) == 16, "formato inesperado"
    sc, off = float(g("SCALING_FACTOR")), float(g("OFFSET"))
    px = float(re.search(r"MAP_SCALE\s*=\s*([\d.]+)", lbl).group(1))
    c = float(g("LINE_PROJECTION_OFFSET")); cs = float(g("SAMPLE_PROJECTION_OFFSET"))
    A = np.fromfile(EXT / (nombre + ".IMG"), dtype="<i2").reshape(n, m).astype(float)
    return A, sc, off, px, c, cs, int(g("DERIVED_MAXIMUM"))

def muestrear(A, sc, off, px, c, cs, xs, ys, flip=(1, 1, 0)):
    # CORREGIDO: el OFFSET ya es la distancia desde el centro del primer pixel, asi que en indices 0-based el origen esta en
    # (c, cs), no en (c-1, cs-1). Comprobacion: con 5058 pixeles y mapa simetrico, el centro 0-based es 2528,5 = OFFSET.
    # La version anterior (ver auditoria/antes/ronda_pgda_img/) leia un pixel al oeste y otro al norte, unos 85 m.
    sx, sy, sw = flip
    x, y = (ys, xs) if sw else (xs, ys)
    row, col = indices_mapa(sx * x, sy * y, px, c, cs)
    ok = (row >= 0) & (row < A.shape[0]) & (col >= 0) & (col < A.shape[1])
    v = np.full(len(xs), np.nan); v[ok] = A[row[ok], col[ok]] * sc + off
    return 100 * v

rows = list(csv.DictReader(open(MODELO, encoding="utf-8")))
xs = np.array([float(r["x_m"]) for r in rows]); ys = np.array([float(r["y_m"]) for r in rows])
out = []
def say(*a):
    t = " ".join(str(v) for v in a); out.append(t); print(t)
refs = {}
for name, fn, col in (("Sol", "AVGVISIB_85S_060M_201608", "h5_sol_punto"), ("Tierra", "AVGVISIB_85S_060M_201608_EARTH", "h5_tierra_centro")):
    A, sc, off, px, c, cs, dmax = leer(fn)
    say(f"{name}: {fn} {A.shape} escala {sc} offset {off} px {px} m origen ({c},{cs}) DN max etiqueta {dmax}, DN max real {int(A.max())} -> {100*A.max()*sc:.1f} %")
    m = np.array([float(r[col]) for r in rows])
    # comprobacion de orientacion (no es calibracion de valores): correlacion con 8 orientaciones posibles
    best = []
    for sx in (1, -1):
        for sy in (1, -1):
            for sw in (0, 1):
                v = muestrear(A, sc, off, px, c, cs, xs, ys, (sx, sy, sw)); k = np.isfinite(v)
                best.append((np.corrcoef(m[k], v[k])[0, 1], (sx, sy, sw)))
    best.sort(reverse=True)
    say(f"  orientacion (sx,sy,swap) por correlacion: " + "; ".join(f"{b[1]}: {b[0]:.3f}" for b in best[:3]))
    refs[name] = muestrear(A, sc, off, px, c, cs, xs, ys, (1, 1, 0))
say("Sin factor de calibracion. Modelo: 19 anos desde 2026, cada 6 h. PGDA: promedio de 18,6 anos segun NASA PGDA, disco completo ('cualquier fraccion'); 2009-2013 en la etiqueta son las fechas de los datos LOLA.")
say("magnitud  conjunto    config                   n    sesgo   MAE    r      pendiente")
tabla = [("Sol", "h5_sol_punto", "5 m, punto (app)"), ("Tierra", "h5_tierra_centro", "5 m, centro (app)"), ("Sol", "h5_sol_disco", "5 m, disco (como PGDA)"), ("Tierra", "h5_tierra_limbo", "5 m, limbo (como PGDA)"), ("Sol", "h2_sol_punto", "2 m, punto"), ("Tierra", "h2_tierra_centro", "2 m, centro"), ("Sol", "h10_sol_punto", "10 m, punto"), ("Tierra", "h10_tierra_centro", "10 m, centro")]
for mag, col, lab in tabla:
    for tipo in ("celda", "candidato"):
        k = np.array([r["tipo"] == tipo for r in rows]) & np.isfinite(refs[mag])
        m = np.array([float(r[col]) for r in rows])[k]
        q = metricas(m, refs[mag][k])
        say(f"{mag:9s} {tipo:10s} {lab:24s} {q['n']:<4d} {q['sesgo']:+6.1f} {q['mae']:6.1f} {q['r']:6.3f} {q['pendiente']:7.2f}")
with open(OUTDIR / "validacion_pgda.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["tipo", "id", "x_m", "y_m", "pgda_sol", "pgda_tierra", "h5_sol_punto", "h5_tierra_centro", "dif_sol", "dif_tierra"])
    for r, a, b in zip(rows, refs["Sol"], refs["Tierra"]):
        w.writerow([r["tipo"], r["id"], r["x_m"], r["y_m"], round(a, 2), round(b, 2), r["h5_sol_punto"], r["h5_tierra_centro"], round(float(r["h5_sol_punto"]) - a, 2), round(float(r["h5_tierra_centro"]) - b, 2)])
for mag, col in (("Sol", "h5_sol_punto"), ("Tierra", "h5_tierra_centro")):
    dif = sorted(((float(r[col]) - v, r["tipo"], r["id"]) for r, v in zip(rows, refs[mag]) if np.isfinite(v)), key=lambda t: -abs(t[0]))
    say(f"Mayores diferencias en {mag}: " + "; ".join(f"{t} {i}: {d:+.1f}" for d, t, i in dif[:6]))
(OUTDIR / "validacion_pgda.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
