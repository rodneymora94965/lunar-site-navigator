#!/usr/bin/env python3
"""Motor comun para probar cuando y desde donde llega la luz contra fotogramas WAC con fecha.

Calcula, para una malla de puntos del recorte Site04 y una fecha UTC, si cada punto ve el centro del Sol con la
configuracion de la app (observador a 5 m, DEM 5 m + 80 m, alcance 200 km). Usa un rayo por punto hacia el azimut exacto
del Sol, sin interpolar entre 360 azimuts. Variantes de control: azimut espejado y Sol girado 180 grados.
"""
import math, os, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
SRC = Path(os.environ.get("LUNAR_SOURCE_DIR", ROOT.parent / "luna_polo_sur"))
os.environ.setdefault("LOLA_DATA_DIR", str(SRC / "datos"))
import horizon2 as hz
_loaded = False


def kernels():
    global _loaded
    import spiceypy as sp
    if not _loaded:
        for k in ["naif0012.tls", "de440s.bsp", "pck00011.tpc", "moon_de440_250416.tf", "moon_pa_de440_200625.bpc"]:
            sp.furnsh(str(SRC / "kernels" / k))
        _loaded = True
    return sp


def sun_vector(utc):
    sp = kernels()
    return np.array(sp.spkpos("SUN", sp.str2et(utc + " UTC"), "MOON_ME", "LT+S", "MOON")[0])


def grid(step=200.0, x0=-8900.0, x1=6900.0, y0=-14900.0, y1=900.0):
    xs = np.arange(x0, x1 + 1, step)
    ys = np.arange(y0, y1 + 1, step)
    X, Y = np.meshgrid(xs, ys)
    return X.ravel(), Y.ravel()


def lit_state(T, X, Y, V, hobs=5.0, control=None):
    """Estado iluminado de cada punto. control: None, 'espejo' o 'giro180'. Devuelve (mascara, az, el)."""
    lit = np.zeros(len(X), bool)
    az_all, el_all = np.zeros(len(X)), np.zeros(len(X))
    rays = hz.RAYS
    drop = rays ** 2 / (2 * hz.R)
    Z0 = T.z(X, Y) + hobs
    for i, (x, y) in enumerate(zip(X, Y)):
        lat, lon = hz.latlon_from_xy(x, y)
        az, el = hz.az_el(V[None, :], lat, lon)
        az, el = float(az[0]), float(el[0])
        az_all[i], el_all[i] = az, el
        a = az
        if control == "espejo":
            a = -az
        elif control == "giro180":
            a = az + 180.0
        lam = math.atan2(x, y)
        s, c = math.sin(lam), math.cos(lam)
        r = math.radians(a)
        dx = math.cos(r) * s + math.sin(r) * c
        dy = math.cos(r) * c - math.sin(r) * s
        ang = np.degrees(np.arctan2(T.z(x + rays * dx, y + rays * dy) - Z0[i] - drop, rays))
        lit[i] = el > np.nanmax(ang)
    return lit, az_all, el_all
