#!/usr/bin/env python3
"""Valida contra el mapa LROC WAC la MISMA configuracion de la app, en alturas de 2, 5 y 10 m.

Evalua las 121 celdas de Site04 y los 10 candidatos. Periodo: el del mapa LROC (2010-02-15, 0,972 anos, cada hora).
Este script calcula el modelo en cada punto. Sus columnas y metricas contra LROC usan el GeoTIFF de 8 bits con la lectura
equivocada 100 x DN / 255 y son obsoletas: para comparar usa validar_lroc_img.py, que lee el producto IMG.

Uso (reanudable, guarda en AUDIT_CACHE): python auditoria/scripts_calculo/validar_config_app.py
"""
import csv, json, os, sys, time
from pathlib import Path
import numpy as np, rasterio, spiceypy as sp
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
SRC = Path(os.environ.get("LUNAR_SOURCE_DIR", ROOT.parent / "luna_polo_sur"))
os.environ.setdefault("LOLA_DATA_DIR", str(SRC / "datos"))
import horizon2 as hz
CACHE = Path(os.environ.get("AUDIT_CACHE", ROOT / ".cache"))
CACHE.mkdir(exist_ok=True, parents=True)
LIMIT = float(os.environ.get("TIME_LIMIT", 1e9))
t0 = time.time()
pts = []
with open(SRC / "salida_2010" / "validacion_ancho.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        pts.append(("celda", f"{r['x_m']}_{r['y_m']}", float(r["x_m"]), float(r["y_m"])))
with open(ROOT / "auditoria" / "entrega_anterior" / "candidatos_finales.csv", encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        pts.append(("candidato", r["id"], float(r["x_m"]), float(r["y_m"])))
sfile = CACHE / "sol_2010_1h.npy"
if not sfile.exists():
    for k in ["naif0012.tls", "de440s.bsp", "pck00011.tpc", "moon_de440_250416.tf", "moon_pa_de440_200625.bpc"]:
        sp.furnsh(str(SRC / "kernels" / k))
    et = sp.str2et("2010-02-15 00:00:00 UTC")
    n = int(round(0.972 * 365.25 * 24))
    np.save(sfile, np.array([sp.spkpos("SUN", et + i * 3600.0, "MOON_ME", "LT+S", "MOON")[0] for i in range(n)]))
S = np.load(sfile)
cf = CACHE / "valid_app.json"
res = json.loads(cf.read_text()) if cf.exists() else {}
T = hz.load_terrain(center=(-2000.0, -7000.0), radius_m=215000)
for kind, pid, x, y in pts:
    if time.time() - t0 > LIMIT:
        break
    k = f"{kind}:{pid}"
    if k in res:
        continue
    lat, lon = hz.latlon_from_xy(x, y)
    az, el = hz.az_el(S, lat, lon)
    res[k] = {}
    for h in (2.0, 5.0, 10.0):
        azs, H = hz.horizon(T, x, y, h)
        res[k][f"h{int(h)}_punto"] = round(100 * hz.above(az, el, azs, H).mean(), 2)
        res[k][f"h{int(h)}_disco"] = round(100 * hz.above(az, el, azs, H, radius=0.2665).mean(), 2)
    cf.write_text(json.dumps(res))
print("puntos", len(res), "de", len(pts), "t", round(time.time() - t0))
if len(res) == len(pts):
    def read(name):
        with rasterio.open(SRC / "datos" / name) as d:
            return d.read(1).astype(float), d.transform
    pct, tr = read("WAC_POLE_ILL_PCT_SOUTH_100M.TIF")
    twi, _ = read("WAC_POLE_ILL_TWI_SOUTH_100M.TIF")
    def dn(a, x, y):
        r, c = rasterio.transform.rowcol(tr, x, y)
        return a[r, c]
    def met(m, l):
        d = m - l
        return f"{d.mean():+.1f} | {np.abs(d).mean():.1f} | {np.corrcoef(m, l)[0, 1]:.3f} | {np.polyfit(l, m, 1)[0]:.2f}"
    out = ["# Validacion con la configuracion de la app (360 azimuts, alcance 200 km, DEM 5 m + 80 m)", "",
           "Periodo: 15-feb-2010, 0,972 anos, cada hora, igual que el mapa LROC WAC.",
           "OBSOLETO: GeoTIFF de 8 bits leido como 100 x DN / 255. Esa lectura es equivocada: ver escala_lroc.md y validacion_lroc_img.txt.",
           "", "| Conjunto | n | Observador | Sol | Mapa LROC | Sesgo (pp) | MAE (pp) | Pearson | Pendiente |", "|---|---|---|---|---|---|---|---|---|"]
    rows = []
    for kind, pid, x, y in pts:
        k = f"{kind}:{pid}"
        rows.append(dict(tipo=kind, id=pid, x_m=x, y_m=y, lroc_pct_nominal=round(dn(pct, x, y) * 100 / 255, 2), lroc_twi_nominal=round(dn(twi, x, y) * 100 / 255, 2), dn_pct=int(dn(pct, x, y)), **res[k]))
    for kind, label in (("celda", "121 celdas Site04"), ("candidato", "10 candidatos")):
        rr = [r for r in rows if r["tipo"] == kind]
        for sel, lab in ((rr, ""), ([r for r in rr if r["lroc_pct_nominal"] >= 1], " (solo con luz)")):
            for h in (2, 5, 10):
                for mode in ("punto", "disco"):
                    m = np.array([r[f"h{h}_{mode}"] for r in sel])
                    for col, mp in (("lroc_pct_nominal", "PCT"), ("lroc_twi_nominal", "TWI")):
                        if mp == "TWI" and not (h == 5 and mode == "punto"):
                            continue
                        out.append(f"| {label}{lab} | {len(sel)} | {h} m | {mode} | {mp} | {met(m, np.array([r[col] for r in sel]))} |")
    with open(ROOT / "auditoria" / "validacion" / "validacion_config_app.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    out += ["", "La configuracion que publica la app es 5 m con Sol puntual.", "Datos por punto: validacion_config_app.csv"]
    (ROOT / "auditoria" / "validacion" / "validacion_config_app.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))
