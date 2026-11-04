#!/usr/bin/env python3
"""Analiza el sitio 14 contra PGDA y arma la tabla de los 10 candidatos con modelo, LROC IMG y PGDA. No calibra nada.
Requiere el resultado de diagnostico_sitio14_pgda.py en PRECALC_CACHE. Escribe auditoria/validacion/diagnostico_sitio14_pgda.txt y candidatos_tres_fuentes.csv."""
import csv, json, os
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
EXT, VAL = ROOT / "auditoria" / "datos_externos", ROOT / "auditoria" / "validacion"
CACHE = Path(os.environ.get("PRECALC_CACHE", ROOT / ".cache"))
S = np.memmap(EXT / "AVGVISIB_85S_060M_201608.IMG", dtype="<i2", mode="r", shape=(5058, 5058))
T = np.memmap(EXT / "AVGVISIB_85S_060M_201608_EARTH.IMG", dtype="<i2", mode="r", shape=(5058, 5058))
raw = (VAL / "WAC_POLE_ILL_PCT_SOUTH_100M.IMG").read_bytes()
L = np.frombuffer(raw[9712:], dtype="<f4").reshape(1214, 1214)
out = []
def say(*a):
    t = " ".join(str(v) for v in a); out.append(t); print(t)
def pix(x, y):
    return int(np.rint(2528.5 - y / 60)), int(np.rint(2528.5 + x / 60))
def disc(x, y, rad):
    r0, c0 = pix(x, y); n = int(rad // 60) + 1
    a, b = [], []
    for r in range(r0 - n, r0 + n + 1):
        for c in range(c0 - n, c0 + n + 1):
            if np.hypot((c - 2528.5) * 60 - x, (2528.5 - r) * 60 - y) <= rad:
                a.append(S[r, c] * 4e-3); b.append(T[r, c] * 4e-3)
    return np.array(a), np.array(b)
# ---------- 1. registro de PGDA frente a LROC, sin usar el modelo ----------
xs = np.arange(-8900.0, 6901.0, 100.0); ys = np.arange(-14900.0, 901.0, 100.0)
X, Y = np.meshgrid(xs, ys); X, Y = X.ravel(), Y.ravel()
lv = np.array([L[int((60700 - y) / 100), int((x + 60700) / 100)] for x, y in zip(X, Y)], float)
say("1. Registro de PGDA frente a LROC IMG en Site04, sin modelo (n=%d)" % len(X))
res = []
for dr in range(-3, 4):
    for dc in range(-3, 4):
        r, c = np.rint(2528.5 - Y / 60).astype(int) + dr, np.rint(2528.5 + X / 60).astype(int) + dc
        res.append((np.corrcoef(S[r, c] * 4e-3, lv)[0, 1], dc, dr))
res.sort(reverse=True)
say("   mejores (r, dcol, dfila):", [(round(a, 3), b, c) for a, b, c in res[:4]])
say("   lectura de la etiqueta (0,0): r", round([a for a, b, c in res if (b, c) == (0, 0)][0], 3), "| lectura anterior (-1,-1): r", round([a for a, b, c in res if (b, c) == (-1, -1)][0], 3))
# ---------- 2. sitio 14 ----------
x0, y0 = 204.0, 625.0
r0, c0 = pix(x0, y0)
say("\n2. Sitio 14")
say(f"   Pixel segun etiqueta: fila {r0}, col {c0}: PGDA Sol {S[r0, c0] * 4e-3:.1f}, Tierra {T[r0, c0] * 4e-3:.1f}")
say(f"   Pixel de la lectura anterior: fila {r0 - 1}, col {c0 - 1}: PGDA Sol {S[r0 - 1, c0 - 1] * 4e-3:.1f}, Tierra {T[r0 - 1, c0 - 1] * 4e-3:.1f}")
say(f"   Area del bolson 0,33195 km2 = {0.33195e6 / 3600:.0f} pixeles de 60 m = {0.33195e6 / 1e4:.0f} pixeles de 100 m; radio equivalente {np.sqrt(0.33195e6 / np.pi):.0f} m")
for rad in (100, 200, 325):
    a, b = disc(x0, y0, rad)
    say(f"   PGDA en radio {rad} m (n={len(a)}): Sol media {a.mean():.1f}, mediana {np.median(a):.1f}, ceros {100 * (a == 0).mean():.0f} %, media sin ceros {a[a > 0].mean():.1f} | Tierra media {b.mean():.1f}, mediana {np.median(b):.1f}, ceros {100 * (b == 0).mean():.0f} %, media sin ceros {b[b > 0].mean():.1f}")
g = {}
for f in CACHE.glob("diag14_*.json"):
    g.update(json.loads(f.read_text()))
P = np.array([[S[r0 + dr, c0 + dc] * 4e-3 for dc in range(-5, 6)] for dr in range(-5, 6)])
Q = np.array([[T[r0 + dr, c0 + dc] * 4e-3 for dc in range(-5, 6)] for dr in range(-5, 6)])
def speck(A):
    d1 = np.abs(np.diff(A, axis=0)); d2 = np.abs(np.diff(A, axis=1))
    return 100 * (np.r_[d1.ravel(), d2.ravel()] > 25).mean()
say("   Ventana 11x11 (+-300 m). Sol y Tierra con cualquier parte del disco, como PGDA. Salto >25 pp = pares vecinos con diferencia mayor a 25 puntos.")
say(f"   {'fuente':20s} {'Sol centro':>10s} {'Sol media':>9s} {'Sol ceros%':>10s} {'Sol salto%':>10s} {'Tie centro':>10s} {'Tie media':>9s} {'Tie ceros%':>10s} {'Tie salto%':>10s} {'r Sol':>6s} {'r Tie':>6s}")
say(f"   {'PGDA':20s} {P[5, 5]:10.1f} {P.mean():9.1f} {100 * (P == 0).mean():10.0f} {speck(P):10.0f} {Q[5, 5]:10.1f} {Q.mean():9.1f} {100 * (Q == 0).mean():10.0f} {speck(Q):10.0f}")
tab = {}
for dem in ("5m", "60m"):
    for h in (0, 2, 5):
        A = np.array([[g[f"14|{dr}|{dc}|{dem}|{h}"][0] for dc in range(-5, 6)] for dr in range(-5, 6)])
        B = np.array([[g[f"14|{dr}|{dc}|{dem}|{h}"][1] for dc in range(-5, 6)] for dr in range(-5, 6)])
        tab[(dem, h)] = (A, B)
        say(f"   {'modelo DEM ' + dem + ', ' + str(h) + ' m':20s} {A[5, 5]:10.1f} {A.mean():9.1f} {100 * (A == 0).mean():10.0f} {speck(A):10.0f} {B[5, 5]:10.1f} {B.mean():9.1f} {100 * (B == 0).mean():10.0f} {speck(B):10.0f} {np.corrcoef(A.ravel(), P.ravel())[0, 1]:6.2f} {np.corrcoef(B.ravel(), Q.ravel())[0, 1]:6.2f}")
yy, xx = np.mgrid[r0 - 5:r0 + 6, c0 - 5:c0 + 6]
say("\n   PGDA Sol, ventana 11x11 (norte arriba):")
for row in P: say("   " + " ".join(f"{v:3.0f}" for v in row))
say("   Modelo DEM 5 m, 5 m, Sol con disco:")
for row in tab[("5m", 5)][0]: say("   " + " ".join(f"{v:3.0f}" for v in row))
say("   Modelo DEM 60 m, 0 m, Sol con disco:")
for row in tab[("60m", 0)][0]: say("   " + " ".join(f"{v:3.0f}" for v in row))
# ---------- 3. candidatos ----------
model = {r["id"]: r for r in csv.DictReader(open(VAL / "validacion_pgda_modelo.csv", encoding="utf-8")) if r["tipo"] == "candidato"}
res19 = {r["id"]: r for r in csv.DictReader(open(ROOT / "auditoria" / "resultados_sitios.csv", encoding="utf-8"))}
lroc = {r["id"]: r for r in csv.DictReader(open(VAL / "validacion_lroc_img.csv", encoding="utf-8")) if r["tipo"] == "candidato"}
data = json.loads((ROOT / "data" / "data.json").read_text(encoding="utf-8"))
sites = {s["id"]: s for s in data["sites"]}
rows = []
for sid, m in model.items():
    x, y = float(m["x_m"]), float(m["y_m"])
    r, c = pix(x, y)
    a, b = disc(x, y, 100)
    q = res19[sid]
    rows.append(dict(id=sid, area_km2=round(sites[sid]["area"], 2), pendiente=sites[sid]["slope"], modelo_sol_2010=lroc[sid]["h5_punto"], lroc_sol=lroc[sid]["lroc_img_pct"], modelo_sol_19a=q["sun_19y"], sol_min=q["sun_min"], sol_max=q["sun_max"], modelo_disco=m["h5_sol_disco"], pgda_sol_pixel=round(float(S[r, c]) * 4e-3, 1), pgda_sol_mediana_r100=round(float(np.median(a)), 1), pgda_sol_ceros_r100=round(100 * float((a == 0).mean())), modelo_tierra=m["h5_tierra_centro"], modelo_limbo=m["h5_tierra_limbo"], tierra_min=q["earth_min"], tierra_max=q["earth_max"], pgda_tierra_pixel=round(float(T[r, c]) * 4e-3, 1), pgda_tierra_mediana_r100=round(float(np.median(b)), 1), ambos_19a=q["both_19y"], ambos_min=q["both_min"], ambos_max=q["both_max"], noche_19a=q["night_19y"], noche_min=q["night_min"], noche_max=q["night_max"]))
rows.sort(key=lambda t: -float(t["ambos_19a"]))
with open(VAL / "candidatos_tres_fuentes.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
say("\n3. Candidatos")
for r in rows: say("  ", r)
(VAL / "diagnostico_sitio14_pgda.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
# ---------- 4. el moteado de PGDA frente a LROC ----------
say("\n4. Moteado: pares vecinos con diferencia >25 pp y pixeles en cero, en ventanas de +-300 m")
say(f"   {'sitio':8s} {'PGDA Sol ceros%':>15s} {'PGDA Sol salto%':>15s} {'LROC ceros%':>11s} {'LROC <1%':>9s} {'LROC salto%':>11s} {'LROC min/med/max':>20s} {'mod 5m ceros%':>13s}")
def speck2(A):
    return 100 * (np.r_[np.abs(np.diff(A, axis=0)).ravel(), np.abs(np.diff(A, axis=1)).ravel()] > 25).mean()
for sid in ("14", "1358", "456", "964", "1417", "2298"):
    m = model[sid]; x, y = float(m["x_m"]), float(m["y_m"])
    r, c = pix(x, y)
    W = np.array(S[r - 5:r + 6, c - 5:c + 6], float) * 4e-3
    lr, lc = int((60700 - y) / 100), int((x + 60700) / 100)
    Lw = np.array(L[lr - 3:lr + 4, lc - 3:lc + 4], float)
    say(f"   {sid:8s} {100 * (W == 0).mean():15.0f} {speck2(W):15.0f} {100 * (Lw <= 0).mean():11.0f} {100 * (Lw < 1).mean():9.0f} {speck2(Lw):11.0f} {Lw.min():6.1f}/{np.median(Lw):5.1f}/{Lw.max():5.1f}")
say("   Moteado de PGDA por distancia al polo en todo el mapa (pares vecinos con salto >25 pp, Sol y Tierra):")
c = 2528
for a, b in ((0, 1), (1, 2), (2, 4), (4, 8), (8, 15), (15, 25), (25, 50), (50, 100)):
    n = int(b * 1000 / 60) + 2
    A = np.array(S[c - n:c + n, c - n:c + n], float) * 4e-3; B = np.array(T[c - n:c + n, c - n:c + n], float) * 4e-3
    yy, xx = np.mgrid[c - n:c + n, c - n:c + n]
    D = np.hypot((xx - 2528.5) * 60, (2528.5 - yy) * 60)[:, :-1]
    k = (D >= a * 1e3) & (D < b * 1e3)
    say(f"   {a:>3}-{b:<3} km: Sol {100 * (np.abs(np.diff(A, axis=1))[k] > 25).mean():5.1f} %  Tierra {100 * (np.abs(np.diff(B, axis=1))[k] > 25).mean():5.1f} %")
(VAL / "diagnostico_sitio14_pgda.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
