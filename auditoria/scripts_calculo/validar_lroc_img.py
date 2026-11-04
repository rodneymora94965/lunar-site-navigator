#!/usr/bin/env python3
"""Valida el modelo contra el producto cientifico de LROC (IMG), no contra el GeoTIFF de navegacion de 8 bits.

Busca WAC_POLE_ILL_PCT_SOUTH_100M.IMG en auditoria/validacion/ o auditoria/datos_externos/. Lee formato y escala de su
etiqueta PDS incrustada. Compara con auditoria/validacion/validacion_config_app.csv y escribe
auditoria/validacion/validacion_lroc_img.txt y .csv. No aplica ningun factor de calibracion.
"""
import csv, re
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
VAL = ROOT / "auditoria" / "validacion"
EXT = VAL if (VAL / "WAC_POLE_ILL_PCT_SOUTH_100M.IMG").exists() else ROOT / "auditoria" / "datos_externos"
IMG = EXT / "WAC_POLE_ILL_PCT_SOUTH_100M.IMG"
LBL = EXT / "WAC_POLE_ILL_PCT_SOUTH_100M.LBL"
OUT = []
def say(*a):
    t = " ".join(str(v) for v in a)
    OUT.append(t)
    print(t)
txt = (LBL.read_bytes() if LBL.exists() else IMG.read_bytes()[:65536]).decode("latin-1")
def key(k, default=None):
    m = re.search(rf"^\s*{k}\s*=\s*\"?([^\s\"<]+)", txt, re.M)
    return m.group(1) if m else default
lines, samples, bits = int(key("LINES")), int(key("LINE_SAMPLES")), int(key("SAMPLE_BITS"))
stype = key("SAMPLE_TYPE")
scale, offset = float(key("SCALING_FACTOR", 1)), float(key("OFFSET", 0))
missing = key("MISSING_CONSTANT")
say("Etiqueta PDS:", {"lines": lines, "samples": samples, "bits": bits, "type": stype, "scaling_factor": scale, "offset": offset})
dt = {("PC_REAL", 32): "<f4", ("IEEE_REAL", 32): ">f4", ("LSB_INTEGER", 16): "<i2", ("MSB_INTEGER", 16): ">i2", ("UNSIGNED_INTEGER", 8): "u1", ("LSB_UNSIGNED_INTEGER", 8): "u1"}[(stype, bits)]
size = lines * samples * (bits // 8)
raw = IMG.read_bytes()
A = np.frombuffer(raw[len(raw) - size:], dtype=dt).reshape(lines, samples).astype(float) * scale + offset
A[A < -1e30] = np.nan  # valores especiales ISIS (CORE_NULL y similares)
say(f"Rango valido: {np.nanmin(A):.2f} a {np.nanmax(A):.2f} %; percentiles 50/99/99,9: {np.nanpercentile(A, [50, 99, 99.9]).round(2).tolist()}")
rows = list(csv.DictReader(open(VAL / "validacion_config_app.csv", encoding="utf-8")))
def val(x, y):  # 100 m/pixel, origen -60700/+60700 (LINE y SAMPLE_PROJECTION_OFFSET = 606,5)
    return A[int((60700 - y) / 100), int((x + 60700) / 100)]
say("Periodo del modelo: 2010-02-15, 0,972 anos, cada hora. Config. de la app: 5 m, Sol puntual, 360 azimuts, 200 km.")
say("tipo       config     n    sesgo   MAE   r      pendiente")
for tipo in ("celda", "candidato"):
    rr = [r for r in rows if r["tipo"] == tipo]
    l = np.array([val(float(r["x_m"]), float(r["y_m"])) for r in rr])
    for col in ("h2_punto", "h5_punto", "h5_disco", "h10_punto"):
        m = np.array([float(r[col]) for r in rr]); d = m - l
        say(f"{tipo:10s} {col:10s} {len(rr):<4d} {d.mean():+6.1f} {abs(d).mean():5.1f} {np.corrcoef(m, l)[0, 1]:6.3f} {np.polyfit(l, m, 1)[0]:6.2f}")
(VAL / "validacion_lroc_img.txt").write_text("\n".join(OUT) + "\n", encoding="utf-8")
with open(VAL / "validacion_lroc_img.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["tipo", "id", "x_m", "y_m", "lroc_img_pct", "h2_punto", "h5_punto", "h5_disco", "h10_punto", "dif_h5_punto"])
    for r in rows:
        v = float(val(float(r["x_m"]), float(r["y_m"])))
        w.writerow([r["tipo"], r["id"], r["x_m"], r["y_m"], round(v, 2), r["h2_punto"], r["h5_punto"], r["h5_disco"], r["h10_punto"], round(float(r["h5_punto"]) - v, 2)])
