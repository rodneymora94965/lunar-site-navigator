#!/usr/bin/env python3
"""Mide cuanto aporta el terreno lejano (mas alla de 304 km del polo) al horizonte de IM-2.

Compara cada azimut sin y con el DEM de 120 m, y con ese DEM reducido a 240 m (sensibilidad a la resolucion).
Uso: python auditoria/scripts_calculo/comprobar_truncamiento.py  Salida: auditoria/truncamiento/comprobacion_im2.txt
"""
import math, os, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("LOLA_DATA_DIR", str(ROOT.parent / "luna_polo_sur" / "datos"))
import horizon2 as hz
x, y = hz.xy_from_latlon(-84.7906, 29.1957)
T = hz.load_terrain(center=(x, y), radius_m=215000)
assert T.far is not None
Z, x0, y0, d = T.far
T240 = hz.Terrain(T.fine, T.wide, (Z[::2, ::2], x0, y0, d * 2))
z0 = float(T.z(np.array([x]), np.array([y]))[0]) + 5
lam = math.atan2(x, y); s, c = math.sin(lam), math.cos(lam)
rays, drop = hz.RAYS, hz.RAYS ** 2 / (2 * hz.R)
out = [f"IM-2: x {x:.0f} m, y {y:.0f} m, distancia al polo {math.hypot(x, y)/1e3:.1f} km, observador {z0:.0f} m"]
n_trunc, n_far_used, margins, worst = 0, 0, [], None
d240 = []
for az in range(360):
    a = math.radians(az)
    dx, dy = math.cos(a) * s + math.sin(a) * c, math.cos(a) * c - math.sin(a) * s
    px, py = x + rays * dx, y + rays * dy
    ow = (np.abs(px) >= 304000 - 80) | (np.abs(py) >= 304000 - 80)
    ang = np.degrees(np.arctan2(T.z(px, py) - z0 - drop, rays))
    ang2 = np.degrees(np.arctan2(T240.z(px, py) - z0 - drop, rays))
    assert not np.isnan(ang).any() and not np.isnan(ang2).any()
    if ow.any():
        n_trunc += 1
        m = float(ang[~ow].max() - ang[ow].max())
        m2 = float(ang2[~ow].max() - ang2[ow].max())
        margins.append(m); d240.append(m2)
        if worst is None or m < worst[1]:
            worst = (az, m, float(rays[ow].min()) / 1e3)
out.append(f"Azimuts que salen de la extension del DEM de 80 m: {n_trunc} de 360. Sin NaN en ninguno con la capa lejana.")
out.append(f"En esos azimuts, el terreno cercano queda por encima del lejano: margen minimo {min(margins):.3f} grados, mediana {np.median(margins):.3f}. Peor azimut {worst[0]}, desde {worst[2]:.1f} km.")
out.append(f"Con 240 m: margen minimo {min(d240):.3f} grados.")
out.append(f"Azimuts donde el terreno lejano define el horizonte: {sum(m < 0 for m in margins)} con 120 m, {sum(m < 0 for m in d240)} con 240 m.")
(ROOT / "auditoria" / "truncamiento" / "comprobacion_im2.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
