#!/usr/bin/env python3
"""Genera data/data.json: efemerides, horizontes, sensibilidad a +-100 m y DEM reducido.

Etapas (cada una se guarda en PRECALC_CACHE y se puede reanudar):
    python src/precalc.py eph          efemerides SPICE horarias, independientes del sitio
    python src/precalc.py sites        horizonte de cada sitio
    python src/precalc.py heat 0 1     malla de +-100 m alrededor de cada sitio (parte 0 de 1)
    python src/precalc.py dem          DEM reducido para coordenadas propias en el navegador
    python src/precalc.py assemble     escribe data/data.json y auditoria/resultados_sitios.csv
    python src/precalc.py all          todo lo anterior
Variables: LUNAR_SOURCE_DIR (carpeta con datos/ y kernels/), PRECALC_CACHE, PRECALC_YEARS, TIME_LIMIT.
"""
import base64, csv, json, math, os, sys, time, zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
SRC = Path(os.environ.get("LUNAR_SOURCE_DIR", ROOT.parent / "luna_polo_sur")).resolve()
os.environ.setdefault("LOLA_DATA_DIR", str(SRC / "datos"))
import horizon2 as hz

CACHE = Path(os.environ.get("PRECALC_CACHE", ROOT / ".cache"))
CACHE.mkdir(parents=True, exist_ok=True)
YEARS = float(os.environ.get("PRECALC_YEARS", 19))
N = int(round(YEARS * 365.25 * 24))
T0 = "2026-11-01"
HOBS = 5.0
AU_KM = 149597870.7
KERNELS = ["naif0012.tls", "de440s.bsp", "pck00011.tpc", "moon_de440_250416.tf", "moon_pa_de440_200625.bpc"]
LIMIT = float(os.environ.get("TIME_LIMIT", 1e9))
START = time.time()
OFFS = np.arange(-100, 101, 25.0)
FINE_F, WIDE_F = 4, int(os.environ.get("DEM_WIDE_F", 6))  # 20 m y 480 m


def sites():
    out = []
    with open(ROOT / "auditoria" / "entrega_anterior" / "candidatos_finales.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            sid = r["id"]
            out.append(dict(id=sid, es=f"Sitio {sid}", en=f"Site {sid}", lat=float(r["lat_deg"]), lon=float(r["lon_east_deg"]), x=float(r["x_m"]), y=float(r["y_m"]),
                            kind="cand", res="5 m + 80 m", area=float(r["area_centers_m2"]) / 1e6, slope=float(r["mean_slope_deg"])))
    refs = [("im2", "IM-2 Athena (aterrizó en 2025)", "IM-2 Athena (landed 2025)", -84.7906, 29.1957, "real", "80 m"),
            ("shack", "Cráter Shackleton (centro)", "Shackleton crater (center)", -89.67, 129.78, "ref", "80 m"),
            ("polo", "Polo Sur geográfico", "Geographic South Pole", -90.0, 0.0, "ref", "5 m + 80 m")]
    for sid, es, en, lat, lon, kind, res in refs:
        x, y = hz.xy_from_latlon(lat, lon)
        out.append(dict(id=sid, es=es, en=en, lat=lat, lon=lon, x=x, y=y, kind=kind, res=res, area=None, slope=None))
    # Regiones nombradas por la NASA: un punto publicado por Wueller et al. 2026, fuera del ranking. Ver auditoria/regiones/.
    vf = ROOT / "auditoria" / "regiones" / "validacion_regiones.csv"
    val = {r["id"]: {k: float(v) for k, v in r.items() if k not in ("id", "region", "lat", "lon") and v != ""} for r in csv.DictReader(open(vf, encoding="utf-8"))} if vf.exists() else {}
    with open(ROOT / "auditoria" / "regiones" / "puntos_representativos.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            lat, lon = float(r["lat"]), float(r["lon"])
            x, y = hz.xy_from_latlon(lat, lon)
            out.append(dict(id=r["id"], es=f"Región {r['region']} (punto representativo)", en=f"{r['region']} region (representative point)", lat=lat, lon=lon, x=x, y=y, kind="region",
                            res="80 m + 120 m" if hz.needs_far((x, y), 215000) else "80 m", area=None, slope=None, pub=r["sitio_publicado"], spread=float(r["radio_grupo_km"]), val=val.get(r["id"], {})))
    return out


def stage_eph():
    import spiceypy as sp
    f = CACHE / f"eph_{N}.npz"
    if f.exists():
        return
    for k in KERNELS:
        sp.furnsh(str(SRC / "kernels" / k))
    et0 = sp.str2et(T0 + " 00:00:00 UTC")
    S, E = np.empty((N, 3)), np.empty((N, 3))
    for i in range(N):
        et = et0 + i * 3600.0
        S[i] = sp.spkpos("SUN", et, "MOON_ME", "LT+S", "MOON")[0]
        E[i] = sp.spkpos("EARTH", et, "MOON_ME", "LT+S", "MOON")[0]
    np.savez(f, S=S, E=E)


def load_eph():
    d = np.load(CACHE / f"eph_{N}.npz")
    return d["S"], d["E"]


def terrain(s):
    return hz.load_terrain(center=(s["x"], s["y"]), radius_m=215000)


def stats(V_s, V_e, lat, lon, azs, H):
    sa, se = hz.az_el(V_s, lat, lon)
    ta, te = hz.az_el(V_e, lat, lon)
    a, b = hz.above(sa, se, azs, H), hz.above(ta, te, azs, H)
    return dict(sun=100 * a.mean(), earth=100 * b.mean(), both=100 * (a & b).mean(), night=hz.longest_false(a, 1 / 24), noearth=hz.longest_false(b, 1 / 24))


def stage_sites():
    for s in sites():
        f = CACHE / f"hz_{s['id']}.npy"
        if f.exists():
            continue
        T = terrain(s)
        _, H = hz.horizon(T, s["x"], s["y"], HOBS)
        np.save(f, H)
        np.save(CACHE / f"z_{s['id']}.npy", T.z(np.array([s["x"]]), np.array([s["y"]])))


def stage_heat(part=0, parts=1):
    S, E = load_eph()
    S, E = S[::3], E[::3]  # cada 3 h: suficiente para el mapa de sensibilidad
    for k, s in enumerate(sites()):
        if k % parts != part:
            continue
        f = CACHE / f"heat_{s['id']}.json"
        g = json.loads(f.read_text()) if f.exists() else {}
        if len(g) == len(OFFS) ** 2:
            continue
        T = terrain(s)
        for dy in OFFS:
            for dx in OFFS:
                key = f"{dx:.0f},{dy:.0f}"
                if key in g:
                    continue
                if time.time() - START > LIMIT:
                    f.write_text(json.dumps(g))
                    print("pausa", s["id"], len(g))
                    return
                x, y = s["x"] + dx, s["y"] + dy
                lat, lon = hz.latlon_from_xy(x, y)
                azs, H = hz.horizon(T, x, y, HOBS)
                sa, se = hz.az_el(S, lat, lon)
                ta, te = hz.az_el(E, lat, lon)
                a, b = hz.above(sa, se, azs, H), hz.above(ta, te, azs, H)
                g[key] = [round(100 * a.mean(), 1), round(100 * b.mean(), 1), round(100 * (a & b).mean(), 1), round(hz.longest_false(a, 1 / 8), 1)]
        f.write_text(json.dumps(g))
        print("listo", s["id"], flush=True)


def grid_b64(Z):
    I = np.round(Z).astype("<i2")
    D = I.copy()
    D[1:] = I[1:] - I[:-1]
    return base64.b64encode(zlib.compress(D.astype("<i2").tobytes(), 9)).decode()


def reduce_mean(Z, f):
    h, w = (Z.shape[0] // f) * f, (Z.shape[1] // f) * f
    return Z[:h, :w].reshape(h // f, f, w // f, f).mean(axis=(1, 3), dtype=np.float32)


def stage_dem():
    import rasterio
    d = hz.data_dir()
    with rasterio.open(d / hz.FINE["name"]) as src:
        a = reduce_mean(src.read(1), FINE_F)
    np.save(CACHE / "dem_fine.npy", a)
    with rasterio.open(d / hz.WIDE["name"]) as src:
        # 200 km mas alla del borde de 80S no existen datos: se usa la cobertura completa del DEM
        wf = src.read(1, out_shape=(src.height // WIDE_F, src.width // WIDE_F), resampling=rasterio.enums.Resampling.average)
    np.save(CACHE / f"dem_wide_{WIDE_F}.npy", wf)


def pack(a, scale):
    v = np.round(a * scale).astype(np.int64)
    d = np.diff(v)
    assert abs(d).max() < 32000, abs(d).max()
    return [int(v[0]), base64.b64encode(zlib.compress(d.astype("<i2").tobytes(), 9)).decode()]


def sub_point(V):
    r = np.linalg.norm(V, axis=1)
    return np.degrees(np.arcsin(V[:, 2] / r)), np.degrees(np.unwrap(np.arctan2(V[:, 1], V[:, 0]))), r


def stage_assemble():
    S, E = load_eph()
    slat, slon, sd = sub_point(S)
    elat, elon, ed = sub_point(E)
    azs = np.arange(360.0)
    out, rows = [], []
    n10 = int(round(10 * 365.25 * 24))
    for s in sites():
        H = np.load(CACHE / f"hz_{s['id']}.npy")
        s10 = stats(S[:n10], E[:n10], s["lat"], s["lon"], azs, H)
        s19 = stats(S, E, s["lat"], s["lon"], azs, H)
        g = json.loads((CACHE / f"heat_{s['id']}.json").read_text())
        heat = [g[f"{dx:.0f},{dy:.0f}"] for dy in OFFS for dx in OFFS]
        h = np.array(heat)
        s.update(z0=float(np.load(CACHE / f"z_{s['id']}.npy")[0]), hz=base64.b64encode(np.round(H * 100).astype("<i2").tobytes()).decode(), heat=heat,
                 rng=dict(sun=[float(h[:, 0].min()), float(h[:, 0].max())], earth=[float(h[:, 1].min()), float(h[:, 1].max())], both=[float(h[:, 2].min()), float(h[:, 2].max())], night=[float(h[:, 3].min()), float(h[:, 3].max())]))
        out.append(s)
        rows.append(dict(id=s["id"], lat=s["lat"], lon=s["lon"], **{f"{k}_10y": round(v, 2) for k, v in s10.items()}, **{f"{k}_19y": round(v, 2) for k, v in s19.items()},
                         **{f"{k}_min": s["rng"][k][0] for k in s["rng"]}, **{f"{k}_max": s["rng"][k][1] for k in s["rng"]}))
    # Orden numerico por tiempo con ambos, luego noche mas corta, luego pendiente. NO es la recomendacion:
    # el sitio principal (456) se elige con el criterio de robustez de RESUMEN_VALIDACION.md.
    cands = [(r, s) for r, s in zip(rows, out) if s["kind"] == "cand"]
    best = sorted(cands, key=lambda p: (-p[0]["both_19y"], p[0]["night_19y"], p[1]["slope"]))
    for k, (r, s) in enumerate(best):
        s["rank"] = k + 1
        r["puesto_candidatos"] = k + 1
    wide = np.load(CACHE / f"dem_wide_{WIDE_F}.npy")
    fine = np.load(CACHE / "dem_fine.npy")
    data = dict(t0=T0 + "T00:00:00Z", n=N, step_h=1, hobs=HOBS, offs=[float(o) for o in OFFS],
                eph=dict(slat=pack(slat, 1000), slon=pack(slon, 1000), sd=pack(sd / AU_KM, 1e5), elat=pack(elat, 1000), elon=pack(elon, 1000), ed=pack(ed, 1)),
                dem=dict(fine=dict(x0=hz.FINE["x0"], y0=hz.FINE["y0"], d=hz.FINE["d"] * FINE_F, h=fine.shape[0], w=fine.shape[1], z=grid_b64(fine)),
                         wide=dict(x0=hz.WIDE["x0"], y0=hz.WIDE["y0"], d=hz.WIDE["d"] * WIDE_F, h=wide.shape[0], w=wide.shape[1], z=grid_b64(wide))),
                sites=out)
    (ROOT / "data" / "data.json").write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    keys = sorted({k for r in rows for k in r}, key=lambda k: (k != "id", k))
    with open(ROOT / "auditoria" / "resultados_sitios.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print("bytes", (ROOT / "data" / "data.json").stat().st_size)


if __name__ == "__main__":
    st = sys.argv[1] if len(sys.argv) > 1 else "all"
    if st in ("eph", "all"):
        stage_eph()
    if st in ("sites", "all"):
        stage_sites()
    if st in ("heat", "all"):
        stage_heat(*(int(v) for v in sys.argv[2:4])) if len(sys.argv) > 3 else stage_heat()
    if st in ("dem", "all"):
        stage_dem()
    if st in ("assemble", "all"):
        stage_assemble()
