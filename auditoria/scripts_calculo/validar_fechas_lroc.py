#!/usr/bin/env python3
"""Prueba si el modelo acierta CUANDO y DESDE DONDE llega la luz, contra fotogramas WAC con fecha.

Criterio fijado antes de ver las imagenes (ver auditoria/validacion/prueba_fechas_lroc.md):
 - fotogramas: fotogramas_lroc_seleccion.csv, elegidos sin mirar imagenes;
 - imagen: umbral de Otsu en el recorte Site04, independiente del modelo;
 - modelo: 5 m, Sol puntual, sin ajustar nada;
 - controles: azimut espejado, Sol girado 180 grados y fecha desplazada 14,77 dias (medio mes sinodico).
Aprueba si en cada fotograma el MCC real supera a los tres controles y el MCC medio es de al menos 0,5.

Coloca los archivos en auditoria/datos_externos/fotogramas_lroc/ como WAC_MOVIE_S....IMG (preferido) o .TIF.
Uso: python auditoria/scripts_calculo/validar_fechas_lroc.py
Variables: FOTOGRAMAS_DIR, FOTOGRAMAS_LISTA, FECHAS_OUT, GRID_STEP.
"""
import csv, datetime as dt, os, re, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from lectura_productos import binarias, otsu, pds_key, read_pds_image
ROOT = HERE.parents[1]
VAL = ROOT / "auditoria" / "validacion"
DIR = Path(os.environ.get("FOTOGRAMAS_DIR", ROOT / "auditoria" / "datos_externos" / "fotogramas_lroc"))
LISTA = Path(os.environ.get("FOTOGRAMAS_LISTA", VAL / "fotogramas_lroc_seleccion.csv"))
OUT = Path(os.environ.get("FECHAS_OUT", VAL))
STEP = float(os.environ.get("GRID_STEP", 200))


def leer_valores(path, X, Y):
    """Valor de imagen en cada punto y hora declarada por el archivo, si la trae."""
    if path.suffix.upper() == ".IMG":
        A, x0, y0, sc, label = read_pds_image(path)
        ini, fin = pds_key(label, "START_TIME"), pds_key(label, "STOP_TIME")
        cols = np.round((X - x0) / sc).astype(int)
        rows = np.round((y0 - Y) / sc).astype(int)
        v = np.array(A[rows, cols], dtype=float)
        hora = None
        if ini and fin and ini != "N/A" and fin != "N/A":
            a, b = (dt.datetime.fromisoformat(s[:19]) for s in (ini, fin))
            hora = (a + (b - a) / 2).strftime("%Y-%m-%d %H:%M:%S")
        fmt = f"IMG {pds_key(label, 'SAMPLE_TYPE')} {pds_key(label, 'SAMPLE_BITS')} bits"
    else:
        import rasterio
        with rasterio.open(path) as f:
            v = np.array([q[0] for q in f.sample(list(zip(X, Y)))], dtype=float)
            fmt, hora = f"TIF {f.dtypes[0]} (navegacion)", None
    v[v < -1e30] = np.nan
    return v, hora, fmt


def main():
    import modelo_lroc_fechas as m
    filas = list(csv.DictReader(open(LISTA, encoding="utf-8")))
    falt = [r["producto"] for r in filas if not ((DIR / (r["producto"] + ".IMG")).exists() or (DIR / (r["producto"] + ".TIF")).exists())]
    if falt:
        print("Faltan estos fotogramas en", DIR)
        for n in falt:
            print(" ", n)
        sys.exit(2)
    T = m.hz.load_terrain(center=(-1000.0, -7000.0), radius_m=215000)
    X, Y = m.grid(step=STEP)
    txt, rows = [], []
    def say(s):
        txt.append(s)
        print(s, flush=True)
    resumen = []
    for r in filas:
        n = r["producto"]
        p = DIR / (n + ".IMG") if (DIR / (n + ".IMG")).exists() else DIR / (n + ".TIF")
        v, hora, fmt = leer_valores(p, X, Y)
        utc = hora or r["utc_nombre"]
        k = np.isfinite(v)
        if k.mean() < 0.5:
            say(f"{n}: menos de 50 % de pixeles validos; no se evalua.")
            continue
        um = otsu(v[k])
        obs = v[k] > um
        V = m.sun_vector(utc)
        t2 = (dt.datetime.fromisoformat(utc) + dt.timedelta(days=14.77)).strftime("%Y-%m-%d %H:%M:%S")
        preds = {"modelo": m.lit_state(T, X, Y, V)[0], "espejo": m.lit_state(T, X, Y, V, control="espejo")[0], "giro180": m.lit_state(T, X, Y, V, control="giro180")[0], "fecha+14,77d": m.lit_state(T, X, Y, m.sun_vector(t2))[0]}
        say(f"{n}  hora {utc} ({'archivo' if hora else 'nombre'})  {fmt}  validos {k.mean():.2f}  luz observada {obs.mean():.2f}  umbral {um:.4g}")
        res = {}
        for name, pr in preds.items():
            q = binarias(pr[k], obs)
            res[name] = q
            rows.append(dict(producto=n, utc=utc, prediccion=name, frac_luz_pred=round(float(pr[k].mean()), 3), frac_luz_obs=round(float(obs.mean()), 3), **{a: round(b, 3) for a, b in q.items()}))
            say(f"   {name:13s} acuerdo {q['acuerdo']:.3f}  balanceada {q['balanceada']:.3f}  MCC {q['mcc']:+.3f}  VP {q['vp']} VN {q['vn']} FP {q['fp']} FN {q['fn']}")
        resumen.append((n, res["modelo"]["mcc"], max(res[c]["mcc"] for c in ("espejo", "giro180", "fecha+14,77d"))))
    if resumen:
        mm = float(np.mean([a for _, a, _ in resumen]))
        ok = all(a > b for _, a, b in resumen) and mm >= 0.5
        say(f"MCC medio del modelo {mm:.3f}; supera a todos los controles en {sum(a > b for _, a, b in resumen)} de {len(resumen)} fotogramas.")
        say("RESULTADO DEL CRITERIO: " + ("APRUEBA" if ok and len(resumen) == len(filas) else "NO APRUEBA"))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "validacion_fechas_lroc.txt").write_text("\n".join(txt) + "\n", encoding="utf-8")
    with open(OUT / "validacion_fechas_lroc.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
