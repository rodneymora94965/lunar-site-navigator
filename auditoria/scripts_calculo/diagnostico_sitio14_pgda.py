#!/usr/bin/env python3
"""Por que el sitio 14 parece cambiar tanto en PGDA: modelo y mapa en la misma malla de pixeles de 60 m alrededor del sitio.

Calcula el modelo en los centros de pixel de PGDA (11x11, +-300 m) con DEM de 5 m y con DEM degradado a 60 m, a 0, 2 y 5 m de altura,
contando el Sol y la Tierra como PGDA (cualquier parte del disco). Reanudable. Uso: diagnostico_sitio14_pgda.py [parte partes]
"""
import json, os, sys, time
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
SRC = Path(os.environ.get("LUNAR_SOURCE_DIR", ROOT.parent / "luna_polo_sur"))
os.environ.setdefault("LOLA_DATA_DIR", str(SRC / "datos"))
import horizon2 as hz
CACHE = Path(os.environ.get("PRECALC_CACHE", ROOT / ".cache"))
LIMIT, t0 = float(os.environ.get("TIME_LIMIT", 1e9)), time.time()
part, parts = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 1)
d = np.load(next(CACHE.glob("eph_*.npz")))
S, E = d["S"][::6], d["E"][::6]
SITES = json.loads(os.environ.get("DIAG_SITES", '{"14":[204.0,625.0]}'))
T5 = hz.load_terrain(center=(0.0, 0.0), radius_m=215000)
Z = T5.fine[0]
# bloque de 60 m alineado con los pixeles de PGDA: y0 = 960 (multiplo de 60), x0 = -9000
Zc = Z[8:]
h, w = Zc.shape[0] // 12 * 12, Zc.shape[1] // 12 * 12
Z60 = Zc[:h, :w].reshape(h // 12, 12, w // 12, 12).mean(axis=(1, 3), dtype=np.float32)
T60 = hz.Terrain((Z60, -9000.0, 960.0, 60.0), T5.wide)
f = CACHE / f"diag14_{part}.json"
res = json.loads(f.read_text()) if f.exists() else {}
keys = []
for sid, (x0, y0) in SITES.items():
    c0, r0 = int(np.rint(2528.5 + x0 / 60)), int(np.rint(2528.5 - y0 / 60))
    for dr in range(-5, 6):
        for dc in range(-5, 6):
            x, y = (c0 + dc - 2528.5) * 60, (2528.5 - (r0 + dr)) * 60
            for dem, T in (("5m", T5), ("60m", T60)):
                for hh in (0.0, 2.0, 5.0):
                    keys.append((f"{sid}|{dr}|{dc}|{dem}|{int(hh)}", x, y, T, hh))
for n, (k, x, y, T, hh) in enumerate(keys):
    if n % parts != part or k in res:
        continue
    if time.time() - t0 > LIMIT:
        break
    la, lo = hz.latlon_from_xy(x, y)
    sa, se = hz.az_el(S, la, lo)
    ta, te = hz.az_el(E, la, lo)
    azs, H = hz.horizon(T, x, y, hh, naz=180)
    res[k] = [round(100 * hz.above(sa, se, azs, H, radius=0.2665).mean(), 1), round(100 * hz.above(ta, te, azs, H, radius=0.95).mean(), 1)]
    if n % 10 == 0:
        f.write_text(json.dumps(res))
f.write_text(json.dumps(res))
print("parte", part, "listos", len(res), "de", len(keys) // parts, "t", round(time.time() - t0))
