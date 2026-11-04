#!/usr/bin/env python3
"""ALTERNATIVO, solo para los mapas en TIF. La validacion vigente usa los IMG con validar_pgda_img.py.

Compara Sol y Tierra con los mapas de NASA PGDA (Mazarico et al. 2011), sin suponer su escala.

Etapa 1 (no necesita los mapas): python validar_pgda.py modelo [parte partes]
    Calcula el modelo en las celdas de Site04 y los 10 candidatos, a 2, 5 y 10 m, en auditoria/validacion/validacion_pgda_modelo.csv.
Etapa 2: python validar_pgda.py comparar
    Lee AVGVISIB_85S_060M_201608.TIF y AVGVISIB_85S_060M_201608_EARTH.TIF de auditoria/datos_externos/ y escribe validacion_pgda.txt y .csv.

La configuracion de la app es 5 m, Sol puntual y centro de la Tierra. PGDA promedia 18,6 anos, trata el Sol como disco finito y cuenta
la Tierra si se ve cualquier parte del disco, asi que tambien se reporta la variante con esas definiciones.
"""
import csv, json, os, sys, time
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from lectura_productos import EscalaDudosa, metricas, read_percent_map
ROOT = HERE.parents[1]
VAL = ROOT / "auditoria" / "validacion"
EXT = Path(os.environ.get("PGDA_DIR", ROOT / "auditoria" / "datos_externos"))
MODELO = Path(os.environ.get("PGDA_MODELO", VAL / "validacion_pgda_modelo.csv"))
OUTDIR = Path(os.environ.get("PGDA_OUT", VAL))
COLS = ["h5_sol_punto", "h5_tierra_centro", "h5_sol_disco", "h5_tierra_limbo", "h2_sol_punto", "h2_tierra_centro", "h10_sol_punto", "h10_tierra_centro"]


def puntos():
    out = [(r["tipo"], r["id"], float(r["x_m"]), float(r["y_m"])) for r in csv.DictReader(open(VAL / "validacion_config_app.csv", encoding="utf-8"))]
    return out


def modelo(part, parts):
    sys.path.insert(0, str(ROOT / "src"))
    SRC = Path(os.environ.get("LUNAR_SOURCE_DIR", ROOT.parent / "luna_polo_sur"))
    os.environ.setdefault("LOLA_DATA_DIR", str(SRC / "datos"))
    import horizon2 as hz
    cache = Path(os.environ.get("PRECALC_CACHE", ROOT / ".cache"))
    limit, t0 = float(os.environ.get("TIME_LIMIT", 1e9)), time.time()
    d = np.load(next(cache.glob("eph_*.npz")))
    S, E = d["S"][::6], d["E"][::6]
    T = hz.load_terrain(center=(-1000.0, -7000.0), radius_m=215000)
    f = cache / f"pgda_modelo_{part}.json"
    res = json.loads(f.read_text()) if f.exists() else {}
    for n, (tipo, pid, x, y) in enumerate(puntos()):
        k = f"{tipo}:{pid}"
        if n % parts != part or k in res:
            continue
        if time.time() - t0 > limit:
            break
        lat, lon = hz.latlon_from_xy(x, y)
        sa, se = hz.az_el(S, lat, lon)
        ta, te = hz.az_el(E, lat, lon)
        r = dict(tipo=tipo, id=pid, x_m=x, y_m=y)
        for h in (5.0, 2.0, 10.0):
            azs, H = hz.horizon(T, x, y, h)
            p = f"h{int(h)}_"
            r[p + "sol_punto"] = round(100 * hz.above(sa, se, azs, H).mean(), 2)
            r[p + "tierra_centro"] = round(100 * hz.above(ta, te, azs, H).mean(), 2)
            if h == 5.0:
                r[p + "sol_disco"] = round(100 * hz.above(sa, se, azs, H, radius=0.2665).mean(), 2)
                r[p + "tierra_limbo"] = round(100 * hz.above(ta, te, azs, H, radius=0.95).mean(), 2)
        res[k] = r
        f.write_text(json.dumps(res))
    print("parte", part, "listos", len(res), "t", round(time.time() - t0))
    faltan = {f"{t}:{i}" for t, i, _, _ in puntos()}
    total = {}
    for g in cache.glob("pgda_modelo_*.json"):
        total.update(json.loads(g.read_text()))
    if faltan <= set(total):
        with open(MODELO, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["tipo", "id", "x_m", "y_m"] + COLS)
            w.writeheader()
            for t, i, _, _ in puntos():
                w.writerow(total[f"{t}:{i}"])
        print("modelo completo:", MODELO)


def sample(path, rows, info):
    import rasterio
    from rasterio.crs import CRS
    from rasterio.warp import transform
    ours = CRS.from_string("+proj=stere +lat_0=-90 +lon_0=0 +k=1 +x_0=0 +y_0=0 +R=1737400 +units=m +no_defs")
    with rasterio.open(path) as f:
        xs, ys = [float(r["x_m"]) for r in rows], [float(r["y_m"]) for r in rows]
        if f.crs is not None:
            xs, ys = transform(ours, f.crs, xs, ys)
        vals = np.array([v[0] for v in f.sample(list(zip(xs, ys)))], dtype=float)
        if f.nodata is not None:
            vals[vals == f.nodata] = np.nan
        vals = vals * f.scales[0] + f.offsets[0]
    return vals * info["factor"]


def comparar():
    rows = list(csv.DictReader(open(MODELO, encoding="utf-8")))
    out = []
    def say(*a):
        t = " ".join(str(v) for v in a)
        out.append(t)
        print(t)
    refs = {}
    for name, fn in (("Sol", "AVGVISIB_85S_060M_201608.TIF"), ("Tierra", "AVGVISIB_85S_060M_201608_EARTH.TIF")):
        path = EXT / fn
        info = read_percent_map(path)
        say(f"{name}: {info}")
        refs[name] = sample(path, rows, info)
    say("Sin factor de calibracion. Modelo: 19 anos, cada 6 h. PGDA: 18,6 anos.")
    say("magnitud  conjunto    config              n    sesgo   MAE    r      pendiente")
    tabla = [("Sol", "h5_sol_punto", "5 m, punto (app)"), ("Tierra", "h5_tierra_centro", "5 m, centro (app)"), ("Sol", "h5_sol_disco", "5 m, disco (como PGDA)"), ("Tierra", "h5_tierra_limbo", "5 m, limbo (como PGDA)"), ("Sol", "h2_sol_punto", "2 m, punto"), ("Tierra", "h2_tierra_centro", "2 m, centro"), ("Sol", "h10_sol_punto", "10 m, punto"), ("Tierra", "h10_tierra_centro", "10 m, centro")]
    for mag, col, lab in tabla:
        for tipo in ("celda", "candidato"):
            k = np.array([r["tipo"] == tipo for r in rows]) & np.isfinite(refs[mag])
            m = np.array([float(r[col]) for r in rows])[k]
            q = metricas(m, refs[mag][k])
            say(f"{mag:9s} {tipo:10s} {lab:24s} {q['n']:<4d} {q['sesgo']:+6.1f} {q['mae']:6.1f} {q['r']:6.3f} {q['pendiente']:7.2f}")
    with open(OUTDIR / "validacion_pgda.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["tipo", "id", "x_m", "y_m", "pgda_sol", "pgda_tierra", "h5_sol_punto", "h5_tierra_centro", "dif_sol", "dif_tierra"])
        for r, a, b in zip(rows, refs["Sol"], refs["Tierra"]):
            w.writerow([r["tipo"], r["id"], r["x_m"], r["y_m"], round(a, 2), round(b, 2), r["h5_sol_punto"], r["h5_tierra_centro"], round(float(r["h5_sol_punto"]) - a, 2), round(float(r["h5_tierra_centro"]) - b, 2)])
    for mag, col, ref in (("Sol", "h5_sol_punto", refs["Sol"]), ("Tierra", "h5_tierra_centro", refs["Tierra"])):
        dif = sorted(((float(r[col]) - v, r["tipo"], r["id"]) for r, v in zip(rows, ref) if np.isfinite(v)), key=lambda t: -abs(t[0]))
        say(f"Mayores diferencias en {mag}: " + "; ".join(f"{t} {i}: {d:+.1f}" for d, t, i in dif[:8]))
    (OUTDIR / "validacion_pgda.txt").write_text("\n".join(out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    st = sys.argv[1] if len(sys.argv) > 1 else "comparar"
    if st == "modelo":
        a = [int(v) for v in sys.argv[2:4]] or [0, 1]
        modelo(*a)
    else:
        try:
            comparar()
        except EscalaDudosa as e:
            sys.exit("DETENIDO, no se comparo: " + str(e))
