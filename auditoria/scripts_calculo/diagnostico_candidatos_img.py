#!/usr/bin/env python3
"""Prueba por que el modelo da mas luz que LROC en los 10 candidatos, sin ajustar nada.

Periodo y metodo iguales a validar_config_app.py (5 m, Sol puntual, 360 azimuts, 200 km). Compara, contra el IMG de LROC:
 - centro: el punto del candidato (lo que publica la app).
 - media_pixel: media de una malla dentro del pixel de 100 m (5x5 en candidatos, 3x3 en los demas; 120 azimuts).
 - pixel_mitad / pixel_todo: instantes con al menos la mitad, o todos, los puntos de la malla iluminados.
Grupos: los 10 candidatos (los 10 bolsones de mayor area), un control de 40 bolsones de pendiente baja no elegidos, y 40 celdas de Site04.
Reanudable con AUDIT_CACHE. Uso: python auditoria/scripts_calculo/diagnostico_candidatos_img.py [parte partes]
"""
import csv, json, os, sys, time
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
SRC = Path(os.environ.get("LUNAR_SOURCE_DIR", ROOT.parent / "luna_polo_sur"))
os.environ.setdefault("LOLA_DATA_DIR", str(SRC / "datos"))
import horizon2 as hz
CACHE = Path(os.environ.get("AUDIT_CACHE", ROOT / ".cache"))
LIMIT = float(os.environ.get("TIME_LIMIT", 1e9))
part, parts = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 1)
t0 = time.time()
S = np.load(CACHE / "sol_2010_1h.npy")[::2]
pockets = list(csv.DictReader(open(ROOT / "auditoria" / "validacion" / "Site04_surf_bolsones.csv", encoding="utf-8")))
pts = [("candidato", r["id"], float(r["x_m"]), float(r["y_m"])) for r in pockets[:10]]
rng = np.random.default_rng(20261103)
for k in sorted(rng.choice(np.arange(10, len(pockets)), size=40, replace=False)):
    r = pockets[int(k)]
    pts.append(("control_bolson", r["id"], float(r["x_m"]), float(r["y_m"])))
cells = list(csv.DictReader(open(ROOT / "auditoria" / "validacion" / "validacion_ancho.csv", encoding="utf-8")))
for k in sorted(rng.choice(np.arange(len(cells)), size=40, replace=False)):
    r = cells[int(k)]
    pts.append(("celda", f"{r['x_m']}_{r['y_m']}", float(r["x_m"]), float(r["y_m"])))
f = CACHE / f"diag_img2_{part}.json"
res = json.loads(f.read_text()) if f.exists() else {}
T = hz.load_terrain(center=(-2000.0, -7000.0), radius_m=215000)
OFF = {"candidato": (np.arange(5) - 2) * 20.0, "control_bolson": (np.arange(3) - 1) * 33.0, "celda": (np.arange(3) - 1) * 33.0}
for n, (kind, pid, x, y) in enumerate(pts):
    k = f"{kind}:{pid}"
    if n % parts != part or k in res:
        continue
    if time.time() - t0 > LIMIT:
        break
    px0 = -60700 + (np.floor((x + 60700) / 100) + 0.5) * 100  # centro del pixel LROC
    py0 = 60700 - (np.floor((60700 - y) / 100) + 0.5) * 100
    masks = []
    for dy in OFF[kind]:
        for dx in OFF[kind]:
            la, lo = hz.latlon_from_xy(px0 + dx, py0 + dy)
            a, e = hz.az_el(S, la, lo)
            azs, H = hz.horizon(T, px0 + dx, py0 + dy, 5.0, naz=120)
            masks.append(hz.above(a, e, azs, H))
    M = np.array(masks)
    la, lo = hz.latlon_from_xy(x, y)
    a, e = hz.az_el(S, la, lo)
    azs, H = hz.horizon(T, x, y, 5.0)
    c = M.mean(axis=0)
    res[k] = dict(tipo=kind, id=pid, x=x, y=y, centro=round(100 * hz.above(a, e, azs, H).mean(), 2), media_pixel=round(100 * M.mean(), 2), pixel_mitad=round(100 * (c >= 0.5).mean(), 2), pixel_todo=round(100 * (c >= 0.999).mean(), 2))
    f.write_text(json.dumps(res))
print("parte", part, "listos", len(res), "t", round(time.time() - t0))
