#!/usr/bin/env python3
"""Elige fotogramas WAC SIN ver las imagenes, con un criterio fijado de antemano.

Entre los nombres publicados del producto WAC_POLE_MOVIE_SOUTH, busca fechas donde el modelo prediga entre 15 y 75 % de
puntos con luz en Site04 y donde la prueba distinga mas entre el Sol real y sus controles. Luego toma 5 fechas con azimut
solar separado al menos 50 grados. Uso: python auditoria/scripts_calculo/seleccionar_fotogramas_lroc.py lista_nombres.txt
"""
import csv, json, os, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import modelo_lroc_fechas as m
names = [n.strip() for n in Path(sys.argv[1]).read_text().replace(",", "\n").splitlines() if n.strip().startswith("WAC_MOVIE_S")]
CACHE = Path(os.environ.get("AUDIT_CACHE", m.ROOT / ".cache"))
LIMIT = float(os.environ.get("TIME_LIMIT", 1e9))
t0 = time.time()
def utc(n):
    s = n.split("_S")[1]
    return f"{s[:4]}-{s[4:6]}-{s[6:8]} {s[9:11]}:{s[11:13]}:00"
rows = []
for n in names:
    a, e = m.hz.az_el(m.sun_vector(utc(n))[None, :], -89.8, -160.0)
    rows.append((n, float(a[0]), float(e[0])))
# una por dia y por sector de 30 grados, ordenadas por sol alto: reduce el costo sin mirar imagenes
best = {}
for n, a, e in rows:
    k = int(a // 30)
    if e > 0.0 and (k not in best or len(best[k]) < 4):
        best.setdefault(k, []).append((n, a, e))
cand = [x for v in best.values() for x in v]
print("nombres", len(rows), "elev. solar min/max", round(min(r[2] for r in rows), 2), round(max(r[2] for r in rows), 2), "candidatos", len(cand), flush=True)
T = m.hz.load_terrain(center=(-1000.0, -7000.0), radius_m=215000)
X, Y = m.grid(step=800.0)
f = CACHE / "sel_frames.json"
res = json.loads(f.read_text()) if f.exists() else {}
for n, a, e in cand:
    if n in res:
        continue
    if time.time() - t0 > LIMIT:
        break
    V = m.sun_vector(utc(n))
    L0, _, _ = m.lit_state(T, X, Y, V)
    L1, _, _ = m.lit_state(T, X, Y, V, control="espejo")
    L2, _, _ = m.lit_state(T, X, Y, V, control="giro180")
    res[n] = dict(az=a, el=e, lit=float(L0.mean()), d_espejo=float((L0 != L1).mean()), d_giro=float((L0 != L2).mean()))
    f.write_text(json.dumps(res))
print("evaluados", len(res), "de", len(cand), "t", round(time.time() - t0), flush=True)
if len(res) == len(cand):
    ok = [(n, r) for n, r in res.items() if 0.15 <= r["lit"] <= 0.75]
    ok.sort(key=lambda p: -(p[1]["d_espejo"] + p[1]["d_giro"]))
    pick = []
    for n, r in ok:
        if all(min(abs(r["az"] - q["az"]) % 360, 360 - abs(r["az"] - q["az"]) % 360) >= 50 for _, q in pick):
            pick.append((n, r))
        if len(pick) == 5:
            break
    out = m.ROOT / "auditoria" / "validacion" / "fotogramas_lroc_seleccion.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["producto", "utc_nombre", "az_sol_deg", "el_sol_deg", "frac_luz_modelo", "desacuerdo_espejo", "desacuerdo_giro180"])
        for n, r in pick:
            w.writerow([n, utc(n), round(r["az"], 1), round(r["el"], 3), round(r["lit"], 3), round(r["d_espejo"], 3), round(r["d_giro"], 3)])
    print(out.read_text())
