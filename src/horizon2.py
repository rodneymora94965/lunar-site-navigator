"""Horizonte local por trazado de rayos sobre DEM LOLA (5 m en el recorte Site04, 80 m hasta 304 km del polo, 120 m mas alla).

El terreno se carga solo cuando se pide y se puede sustituir por una superficie sintetica,
lo que permite probar el trazado contra soluciones analiticas (tests/test_project.py).
"""
import math
import os
from pathlib import Path

import numpy as np

R = 1737400.0
FINE = dict(x0=-9000.0, y0=1000.0, d=5.0, name="Site04_surf.tif")
WIDE = dict(x0=-304000.0, y0=304000.0, d=80.0, name="LDEM_80S_80MPP_ADJ.TIF")
FAR = dict(x0=-931200.0, y0=931200.0, d=120.0, name="LDEM_60S_120MPP_ADJ.TIF")  # solo donde el de 80 m no llega
RAYS = np.r_[np.arange(10, 3000, 10.0), np.arange(3000, 200000, 80.0)]  # configuracion de la app


def bil(Z, x0, y0, d, x, y):
    j = (x - x0) / d - 0.5
    i = (y0 - y) / d - 0.5
    ok = (i >= 0) & (j >= 0) & (i < Z.shape[0] - 1) & (j < Z.shape[1] - 1)
    i2 = np.clip(i, 0, Z.shape[0] - 2)
    j2 = np.clip(j, 0, Z.shape[1] - 2)
    i0 = np.floor(i2).astype(int)
    j0 = np.floor(j2).astype(int)
    fi = i2 - i0
    fj = j2 - j0
    v = Z[i0, j0] * (1 - fi) * (1 - fj) + Z[i0 + 1, j0] * fi * (1 - fj) + Z[i0, j0 + 1] * (1 - fi) * fj + Z[i0 + 1, j0 + 1] * fi * fj
    return np.where(ok, v, np.nan)


class Terrain:
    """Hasta tres rasteres (fino, ancho y lejano) en estereografica polar sur, con z en metros."""

    def __init__(self, fine=None, wide=None, far=None):
        self.fine = fine  # (Z, x0, y0, d) o None
        self.wide = wide
        self.far = far

    def z(self, x, y):
        a = bil(*self.fine, x, y) if self.fine else np.full(np.shape(x), np.nan)
        if self.wide is None:
            return a
        a = np.where(np.isnan(a), bil(*self.wide, x, y), a)
        if self.far is None:
            return a
        # El lejano solo cuenta fuera de la extension del de 80 m, nunca para rellenar huecos dentro de ella.
        half = abs(WIDE["x0"])
        return np.where(np.isnan(a) & ((np.abs(x) >= half - WIDE["d"]) | (np.abs(y) >= half - WIDE["d"])), bil(*self.far, x, y), a)


def data_dir():
    default = Path(__file__).resolve().parents[2] / "luna_polo_sur" / "datos"
    return Path(os.environ.get("LOLA_DATA_DIR", default))


def load_terrain(center=None, radius_m=None):
    """Carga los DEM. Con center y radius_m lee solo una ventana del DEM ancho (ahorra memoria)."""
    import rasterio
    from rasterio.windows import Window

    d = data_dir()
    with rasterio.open(d / FINE["name"]) as f:
        fine = (f.read(1).astype(np.float32), FINE["x0"], FINE["y0"], FINE["d"])
    with rasterio.open(d / WIDE["name"]) as f:
        if center is None:
            wide = (f.read(1).astype(np.float32), WIDE["x0"], WIDE["y0"], WIDE["d"])
        else:
            hw = int(radius_m / WIDE["d"]) + 2
            c = int((center[0] - WIDE["x0"]) / WIDE["d"])
            r = int((WIDE["y0"] - center[1]) / WIDE["d"])
            r0, c0 = max(r - hw, 0), max(c - hw, 0)
            r1, c1 = min(r + hw, f.height), min(c + hw, f.width)
            Z = f.read(1, window=Window(c0, r0, c1 - c0, r1 - r0)).astype(np.float32)
            wide = (Z, WIDE["x0"] + c0 * WIDE["d"], WIDE["y0"] - r0 * WIDE["d"], WIDE["d"])
    return Terrain(fine, wide, load_far(d, center, radius_m))


def needs_far(center, radius_m):
    """True si el circulo pedido se sale de la extension del DEM de 80 m."""
    return center is not None and max(abs(center[0]), abs(center[1])) + radius_m > abs(WIDE["x0"])


def load_far(d, center, radius_m):
    """Lee solo la ventana necesaria del DEM de 120 m. Si hace falta y no esta, falla en vez de truncar en silencio."""
    if not needs_far(center, radius_m):
        return None
    import rasterio
    from rasterio.windows import Window

    p = d / FAR["name"]
    if not p.exists():
        raise FileNotFoundError(f"Falta {p}. Este sitio necesita terreno mas alla de 304 km del polo; ver scripts/obtener_datos.md.")
    hw = int(radius_m / FAR["d"]) + 2
    c = int((center[0] - FAR["x0"]) / FAR["d"])
    r = int((FAR["y0"] - center[1]) / FAR["d"])
    with rasterio.open(p) as f:
        r0, c0 = max(r - hw, 0), max(c - hw, 0)
        r1, c1 = min(r + hw, f.height), min(c + hw, f.width)
        Z = f.read(1, window=Window(c0, r0, c1 - c0, r1 - r0)).astype(np.float32)
    return (Z, FAR["x0"] + c0 * FAR["d"], FAR["y0"] - r0 * FAR["d"], FAR["d"])


def horizon(terrain, x, y, hobs, naz=360, rays=RAYS, radius=R):
    """Devuelve (azimuts, horizonte en grados). Azimut 0 = norte local (hacia afuera del polo sur)."""
    z0 = float(terrain.z(np.array([x]), np.array([y]))[0]) + hobs
    azs = np.arange(naz) * 360.0 / naz
    lam = math.atan2(x, y)
    s, c = math.sin(lam), math.cos(lam)
    hz = np.full(naz, -90.0)
    drop = rays ** 2 / (2 * radius)
    for k, az in enumerate(azs):
        a = math.radians(az)
        dx = math.cos(a) * s + math.sin(a) * c
        dy = math.cos(a) * c - math.sin(a) * s
        ang = np.degrees(np.arctan2(terrain.z(x + rays * dx, y + rays * dy) - z0 - drop, rays))
        ang = ang[~np.isnan(ang)]
        if len(ang):
            hz[k] = ang.max()
    return azs, hz


def xy_from_latlon(lat, lon, radius=R):
    th = math.radians(90 + lat)
    rho = 2 * radius * math.tan(th / 2)
    return rho * math.sin(math.radians(lon)), rho * math.cos(math.radians(lon))


def latlon_from_xy(x, y, radius=R):
    rho = math.hypot(x, y)
    return -90 + math.degrees(2 * math.atan(rho / (2 * radius))), math.degrees(math.atan2(x, y))


def az_el(v, lat, lon, r_km=1737.4):
    """Azimut y elevacion de vectores v (n, 3) en el marco lunar, desde un punto sobre la esfera."""
    la, lo = math.radians(lat), math.radians(lon)
    sl, cl, so, co = math.sin(la), math.cos(la), math.sin(lo), math.cos(lo)
    E = np.array([-so, co, 0.0])
    N = np.array([-sl * co, -sl * so, cl])
    U = np.array([cl * co, cl * so, sl])
    w = v - U * r_km
    d = np.linalg.norm(w, axis=1)
    return np.degrees(np.arctan2(w @ E, w @ N)) % 360, np.degrees(np.arcsin(np.clip(w @ U / d, -1, 1)))


def above(az, el, azs, hz, margin=0.0, radius=0.0):
    H = np.interp(az % 360, np.r_[azs, 360.0], np.r_[hz, hz[0]])
    return el + radius - H > margin


def longest_false(m, step_days):
    x = np.r_[0, (~m).astype(np.int8), 0]
    d = np.diff(x)
    i, f = np.where(d == 1)[0], np.where(d == -1)[0]
    return float((f - i).max() * step_days) if len(i) else 0.0
