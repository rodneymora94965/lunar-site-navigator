#!/usr/bin/env python3
"""Compara las efemerides SPICE del proyecto contra JPL Horizons (fuente independiente).

Consulta azimut y elevacion aparentes de Sol y Tierra para 20 fechas repartidas en 2026-2045, en
tres sitios (polo cercano, sitio medio e IM-2), y guarda la respuesta en
tests/fixtures/horizons_sol_tierra.csv para que las pruebas funcionen sin red.

Uso: python auditoria/scripts_calculo/validar_horizons.py   (LUNAR_SOURCE_DIR = carpeta con kernels/)
"""
import csv, math, os, re, statistics as st, urllib.parse, urllib.request
from pathlib import Path
import numpy as np
import spiceypy as sp

ROOT = Path(__file__).resolve().parents[2]
SRC = Path(os.environ.get("LUNAR_SOURCE_DIR", ROOT.parent / "luna_polo_sur"))
SITES = {"14": (-89.97832, 18.0767), "456": (-89.69654, -120.8512), "im2": (-84.7906, 29.1957)}
EPOCHS = sorted(["%04d-%02d-%02d %02d:00" % (2026 + k, 1 + (k * 5) % 12, 3 + (k * 7) % 25, (k * 5) % 24) for k in range(1, 20)] + ["2030-06-21 11:00"])
for k in ["naif0012.tls", "de440s.bsp", "pck00011.tpc", "moon_de440_250416.tf", "moon_pa_de440_200625.bpc"]:
    sp.furnsh(str(SRC / "kernels" / k))


def horizons(body, lat, lon):
    q = {"format": "text", "COMMAND": f"'{body}'", "OBJ_DATA": "'NO'", "MAKE_EPHEM": "'YES'", "EPHEM_TYPE": "'OBSERVER'",
         "CENTER": "'coord@301'", "COORD_TYPE": "'GEODETIC'", "SITE_COORD": f"'{lon % 360:.5f},{lat:.5f},0'",
         "TLIST": ",".join(f"'{e}'" for e in EPOCHS), "QUANTITIES": "'4'", "ANG_FORMAT": "'DEG'", "EXTRA_PREC": "'YES'",
         "TIME_DIGITS": "'MINUTES'", "CSV_FORMAT": "'YES'"}
    txt = urllib.request.urlopen("https://ssd.jpl.nasa.gov/api/horizons.api?" + urllib.parse.urlencode(q), timeout=60).read().decode()
    m = re.search(r"\$\$SOE(.*?)\$\$EOE", txt, re.S)
    if not m:
        raise RuntimeError(txt[-1500:])
    out = {}
    for line in m.group(1).strip().splitlines():
        c = [x.strip() for x in line.split(",")]
        nums = [x for x in c[1:] if re.fullmatch(r"-?\d+\.\d+", x)]
        out[c[0]] = (float(nums[0]), float(nums[1]))
    return list(out.values())


def spice(body, lat, lon, epoch):
    et = sp.str2et(epoch + " UTC")
    v = np.array(sp.spkpos(body, et, "MOON_ME", "LT+S", "MOON")[0])
    la, lo = math.radians(lat), math.radians(lon)
    sl, cl, so, co = math.sin(la), math.cos(la), math.sin(lo), math.cos(lo)
    E, N, U = np.array([-so, co, 0.0]), np.array([-sl * co, -sl * so, cl]), np.array([cl * co, cl * so, sl])
    v = v - U * 1737.4
    d = np.linalg.norm(v)
    return math.degrees(math.asin(v @ U / d)), math.degrees(math.atan2(v @ E, v @ N)) % 360


rows = []
for sid, (lat, lon) in SITES.items():
    for name, code, spname in (("sol", "10", "SUN"), ("tierra", "399", "EARTH")):
        for ep, (az, el) in zip(EPOCHS, horizons(code, lat, lon)):
            e2, a2 = spice(spname, lat, lon, ep)
            rows.append(dict(sitio=sid, lat=lat, lon=lon, cuerpo=name, utc=ep, hz_az=az, hz_el=el, sp_az=round(a2, 5), sp_el=round(e2, 5),
                             d_el=round(e2 - el, 5), d_az=round((a2 - az + 180) % 360 - 180, 5)))
with open(ROOT / "tests" / "fixtures" / "horizons_sol_tierra.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
L = ["# Validacion de efemerides contra JPL Horizons", "",
     "Comparacion directa de SPICE (DE440s, MOON_ME, LT+S; observador sobre la esfera de 1737,4 km) con la API de JPL Horizons (azimut y elevacion aparentes, sin atmosfera), en 20 fechas de 2026 a 2045.",
     "", "| Sitio | Cuerpo | n | max abs d_elev (grados) | RMS d_elev | max abs d_azim | RMS d_azim |", "|---|---|---|---|---|---|---|"]
for sid in SITES:
    for name in ("sol", "tierra"):
        r = [x for x in rows if x["sitio"] == sid and x["cuerpo"] == name]
        de, da = [x["d_el"] for x in r], [x["d_az"] for x in r]
        L.append(f"| {sid} | {name} | {len(r)} | {max(map(abs, de)):.5f} | {math.sqrt(st.mean(v * v for v in de)):.5f} | {max(map(abs, da)):.5f} | {math.sqrt(st.mean(v * v for v in da)):.5f} |")
L += ["", "Las diferencias se redondean a 0,00001 grados; un 0,00000 significa menos que eso.",
      "Alcance: valida la posicion de Sol y Tierra y nuestra conversion a azimut y elevacion. No valida el horizonte ni el terreno.",
      "Limite: Horizons y los kernels vienen de la misma familia de efemerides de JPL. Es una implementacion independiente de la conversion, no una medicion independiente de la orbita lunar.",
      "Datos crudos: tests/fixtures/horizons_sol_tierra.csv"]
(ROOT / "auditoria" / "validacion" / "validacion_horizons.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
