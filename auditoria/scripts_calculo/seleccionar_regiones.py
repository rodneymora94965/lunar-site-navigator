#!/usr/bin/env python3
"""Elige un punto representativo por region a partir de los sitios publicados por Wueller et al. 2026 (Zenodo 17084058, CC BY 4.0).

Regla, fijada antes de abrir los datos: el sitio publicado mas cercano al centro de los sitios de esa region. No mira la luz.
Las coordenadas son las columnas Latitude y Longitude del archivo. La asignacion de codigos a nombres (por ejemplo SP = Slater Plain)
se dedujo de los codigos; el articulo no se pudo leer desde el entorno de trabajo.
Necesita pyshp. Entrada: auditoria/datos_externos/Regiones/Landing_Sites.zip. Salida: auditoria/regiones/puntos_representativos.csv
"""
import collections, csv, io, math, zipfile
from pathlib import Path
import shapefile
ROOT = Path(__file__).resolve().parents[2]
Z = next((ROOT / "auditoria" / "datos_externos").glob("[Rr]egiones/Landing_Sites.zip"))
R = 1737400.0
MAPA = [("PCB", "Peak near Cabeus B"), ("HW", "Haworth"), ("MMA", "Malapert Massif"), ("MMP", "Mons Mouton Plateau"), ("MMO", "Mons Mouton"), ("NR1", "Nobile Rim 1"), ("NR2", "Nobile Rim 2"), ("dGR2", "de Gerlache Rim 2"), ("SP", "Slater Plain")]


def xy(la, lo):
    rho = 2 * R * math.tan(math.radians(90 + la) / 2)
    return rho * math.sin(math.radians(lo)), rho * math.cos(math.radians(lo))


inner = zipfile.ZipFile(io.BytesIO(zipfile.ZipFile(Z).read("Landing_Sites.zip")))
r = shapefile.Reader(dbf=io.BytesIO(inner.read("LandingSites.dbf")))
campos = [f[0] for f in r.fields[1:]]
grupos = collections.defaultdict(list)
for rec in r.records():
    d = dict(zip(campos, rec))
    grupos[d["Landing_Re"]].append(d)
filas = []
for cod, nombre in MAPA:
    v = grupos[cod]
    P = [xy(s["Latitude"], s["Longitude"]) for s in v]
    mx, my = sum(p[0] for p in P) / len(P), sum(p[1] for p in P) / len(P)
    k = min(range(len(v)), key=lambda i: math.hypot(P[i][0] - mx, P[i][1] - my))
    x, y = P[k]
    filas.append(dict(id="r" + cod.lower(), region=nombre, codigo=cod, sitio_publicado=v[k]["Name"], lat=v[k]["Latitude"], lon=v[k]["Longitude"], n_sitios=len(v), dist_centro_km=round(math.hypot(x - mx, y - my) / 1e3, 2), radio_grupo_km=round(max(math.hypot(p[0] - mx, p[1] - my) for p in P) / 1e3, 1), dist_polo_km=round(math.hypot(x, y) / 1e3, 1), necesita_120m=int(max(abs(x), abs(y)) + 215000 > 304000)))
with open(ROOT / "auditoria" / "regiones" / "puntos_representativos.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(filas[0]))
    w.writeheader()
    w.writerows(filas)
print(len(filas))
