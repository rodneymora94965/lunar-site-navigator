#!/usr/bin/env python3
"""Lee productos externos sin suponer su escala: si los metadatos no la confirman, se detiene y lo dice."""
import re
from pathlib import Path
import numpy as np


class EscalaDudosa(ValueError):
    pass


def pds_label(path):
    head = Path(path).read_bytes()[:200000].decode("latin-1")
    end = re.search(r"^END\s*$", head, re.M)
    return head[: end.end()] if end else head


def pds_key(label, key, default=None):
    m = re.search(rf"^\s*{key}\s*=\s*\"?([^\s\"<]+)", label, re.M)
    return m.group(1) if m else default


def read_pds_image(path):
    """Devuelve (memmap, x0_centro, y0_centro, escala_m, etiqueta). Valores especiales ISIS como NaN solo al leer ventana."""
    label = pds_label(path)
    lines, samples, bits = int(pds_key(label, "LINES")), int(pds_key(label, "LINE_SAMPLES")), int(pds_key(label, "SAMPLE_BITS"))
    stype = pds_key(label, "SAMPLE_TYPE")
    dt = {("PC_REAL", 32): "<f4", ("IEEE_REAL", 32): ">f4", ("LSB_INTEGER", 16): "<i2", ("MSB_INTEGER", 16): ">i2", ("UNSIGNED_INTEGER", 8): "u1", ("LSB_UNSIGNED_INTEGER", 8): "u1"}[(stype, bits)]
    rb, iptr = int(pds_key(label, "RECORD_BYTES")), int(pds_key(label, r"\^IMAGE"))
    A = np.memmap(path, dtype=dt, mode="r", offset=rb * (iptr - 1), shape=(lines, samples))
    scale = float(re.search(r"MAP_SCALE\s*=\s*([\d.]+)", label).group(1))
    lo, so = float(re.search(r"LINE_PROJECTION_OFFSET\s*=\s*(-?[\d.]+)", label).group(1)), float(re.search(r"SAMPLE_PROJECTION_OFFSET\s*=\s*(-?[\d.]+)", label).group(1))
    return A, -so * scale, lo * scale, scale, label


def indices_mapa(x, y, px, line_off, sample_off):
    """Fila y columna 0-based de un punto del plano polar, segun PDS: el OFFSET se mide desde el centro del primer pixel."""
    return np.rint(line_off - np.asarray(y) / px).astype(int), np.rint(sample_off + np.asarray(x) / px).astype(int)


def otsu(v, bins=256):
    """Umbral de Otsu: no usa el modelo ni depende de la escala absoluta."""
    v = v[np.isfinite(v)]
    h, e = np.histogram(v, bins=bins)
    c = (e[:-1] + e[1:]) / 2
    w = np.cumsum(h)
    m = np.cumsum(h * c)
    with np.errstate(divide="ignore", invalid="ignore"):
        b = (m[-1] * w - m * w[-1]) ** 2 / (w * (w[-1] - w))
    return float(c[int(np.nanargmax(b))])


def metricas(m, r):
    m, r = np.asarray(m, float), np.asarray(r, float)
    d = m - r
    return dict(n=len(m), sesgo=float(d.mean()), mae=float(np.abs(d).mean()), r=float(np.corrcoef(m, r)[0, 1]), pendiente=float(np.polyfit(r, m, 1)[0]))


def binarias(pred, obs):
    pred, obs = np.asarray(pred, bool), np.asarray(obs, bool)
    tp, tn = int((pred & obs).sum()), int((~pred & ~obs).sum())
    fp, fn = int((pred & ~obs).sum()), int((~pred & obs).sum())
    ba = 0.5 * (tp / max(tp + fn, 1) + tn / max(tn + fp, 1))
    den = float(tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
    mcc = (tp * tn - fp * fn) / den ** 0.5 if den > 0 else 0.0
    return dict(acuerdo=(tp + tn) / len(pred), balanceada=ba, mcc=mcc, vp=tp, vn=tn, fp=fp, fn=fn)


def read_percent_map(path):
    """Lee un mapa de visibilidad y devuelve (lector, informe). Acepta fraccion o porcentaje solo con evidencia."""
    import rasterio
    with rasterio.open(path) as f:
        scale, offset, dtype, nod = f.scales[0], f.offsets[0], f.dtypes[0], f.nodata
        A = f.read(1, out_shape=(min(f.height, 2000), min(f.width, 2000))).astype(float)
        tags = f.tags()
        crs = f.crs
    if nod is not None:
        A[A == nod] = np.nan
    A = A * scale + offset
    A[A < -1e30] = np.nan
    v = A[np.isfinite(A)]
    hist, _ = np.histogram(v, bins=256)
    pico = hist[-1] > 5 * max(hist[-2], 1) and hist[-1] > 0.001 * len(v)
    info = dict(archivo=Path(path).name, dtype=dtype, escala=scale, offset=offset, nodata=nod, minimo=float(v.min()), maximo=float(v.max()), pico_en_el_tope=bool(pico), crs=str(crs)[:80], etiquetas=tags)
    if dtype == "uint8" and scale == 1.0:
        raise EscalaDudosa(f"{info['archivo']}: es uint8 sin escala en metadatos; puede ser un producto de navegacion estirado. Usa el IMG o el TIF cientifico.")
    if pico:
        raise EscalaDudosa(f"{info['archivo']}: hay un pico en el valor maximo, posible saturacion. Revisa la etiqueta antes de comparar.")
    if v.min() < -0.5 or v.max() > 100.5:
        raise EscalaDudosa(f"{info['archivo']}: rango {v.min():.3g} a {v.max():.3g}; no es fraccion ni porcentaje. Revisa la etiqueta.")
    if v.max() <= 1.0001:
        info["factor"] = 100.0
        info["nota"] = "Valores de 0 a 1 tratados como fraccion; confirma con la etiqueta PDS."
    elif v.max() > 1.5:
        info["factor"] = 1.0
        info["nota"] = "Valores hasta 100 tratados como porcentaje; confirma con la etiqueta PDS."
    else:
        raise EscalaDudosa(f"{info['archivo']}: maximo {v.max():.3g}, ambiguo entre fraccion y porcentaje.")
    return info
