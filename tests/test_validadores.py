"""Prueba los lectores y validadores con datos sinteticos. No requiere los mapas de PGDA ni los fotogramas de LROC."""
import csv
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "auditoria" / "scripts_calculo"
sys.path.insert(0, str(SCRIPTS))
rasterio = pytest.importorskip("rasterio")
from lectura_productos import EscalaDudosa, binarias, indices_mapa, metricas, otsu, read_pds_image, read_percent_map  # noqa: E402

CRS = "+proj=stere +lat_0=-90 +lon_0=0 +k=1 +x_0=0 +y_0=0 +R=1737400 +units=m +no_defs"


def write_tif(path, Z, dtype="float32", scale=None, nodata=None):
    from rasterio.transform import from_origin
    with rasterio.open(path, "w", driver="GTiff", height=Z.shape[0], width=Z.shape[1], count=1, dtype=dtype, crs=CRS, transform=from_origin(-20000, 5000, 60, 60), nodata=nodata) as f:
        f.write(Z.astype(dtype), 1)
        if scale:
            f.scales = (scale,)
            f.offsets = (0.0,)


def field(max_value):
    y, x = np.mgrid[0:400, 0:600]
    return max_value * (0.5 + 0.5 * np.sin(x / 90.0) * np.cos(y / 70.0))


def test_binary_metrics_and_otsu():
    obs = np.array([1, 1, 0, 0, 1, 0], bool)
    assert binarias(obs, obs)["mcc"] == pytest.approx(1)
    assert binarias(~obs, obs)["mcc"] == pytest.approx(-1)
    lo, hi = np.random.default_rng(1).normal(0.01, 0.002, 3000), np.random.default_rng(2).normal(0.08, 0.005, 1000)
    t = otsu(np.r_[lo, hi])
    assert (lo < t).mean() > 0.999 and (hi > t).mean() > 0.999  # cualquier umbral entre los dos grupos es valido


def test_metrics_recover_known_bias_and_slope():
    r = np.linspace(0, 100, 50)
    q = metricas(r * 1.0 + 2.0, r)
    assert q["sesgo"] == pytest.approx(2)
    assert q["mae"] == pytest.approx(2)
    assert q["pendiente"] == pytest.approx(1)


def test_map_reader_accepts_only_confirmed_scales(tmp_path):
    write_tif(tmp_path / "pct.tif", field(90))
    assert read_percent_map(tmp_path / "pct.tif")["factor"] == 1.0
    write_tif(tmp_path / "frac.tif", field(0.9))
    assert read_percent_map(tmp_path / "frac.tif")["factor"] == 100.0
    write_tif(tmp_path / "esc.tif", field(9000), dtype="int16", scale=0.01)
    assert read_percent_map(tmp_path / "esc.tif")["factor"] == 1.0


def test_map_reader_refuses_browse_and_saturated_files(tmp_path):
    write_tif(tmp_path / "u8.tif", field(255), dtype="uint8")
    with pytest.raises(EscalaDudosa, match="uint8"):
        read_percent_map(tmp_path / "u8.tif")
    Z = field(120)
    Z[Z > 60] = 60
    write_tif(tmp_path / "sat.tif", Z)
    with pytest.raises(EscalaDudosa, match="saturacion"):
        read_percent_map(tmp_path / "sat.tif")
    write_tif(tmp_path / "rango.tif", field(300))
    with pytest.raises(EscalaDudosa):
        read_percent_map(tmp_path / "rango.tif")


def run_pgda(tmp_path, sun, earth, rows):
    write_tif(tmp_path / "AVGVISIB_85S_060M_201608.TIF", sun)
    write_tif(tmp_path / "AVGVISIB_85S_060M_201608_EARTH.TIF", earth)
    mfile = tmp_path / "modelo.csv"
    cols = ["tipo", "id", "x_m", "y_m", "h5_sol_punto", "h5_tierra_centro", "h5_sol_disco", "h5_tierra_limbo", "h2_sol_punto", "h2_tierra_centro", "h10_sol_punto", "h10_tierra_centro"]
    with open(mfile, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    env = dict(os.environ, PGDA_DIR=str(tmp_path), PGDA_MODELO=str(mfile), PGDA_OUT=str(tmp_path))
    return subprocess.run([sys.executable, str(SCRIPTS / "validar_pgda.py"), "comparar"], capture_output=True, text=True, env=env)


def synthetic_rows(sun, earth, n=40):
    from rasterio.transform import from_origin, rowcol
    tr = from_origin(-20000, 5000, 60, 60)
    rng = np.random.default_rng(5)
    rows = []
    for k in range(n):
        x, y = rng.uniform(-15000, 10000), rng.uniform(-18000, 3000)
        r, c = rowcol(tr, x, y)
        s, e = float(sun[r, c]) + 2.0, float(earth[r, c]) - 3.0
        rows.append(dict(tipo="celda" if k < 30 else "candidato", id=str(k), x_m=x, y_m=y, h5_sol_punto=s, h5_tierra_centro=e, h5_sol_disco=s, h5_tierra_limbo=e, h2_sol_punto=s, h2_tierra_centro=e, h10_sol_punto=s, h10_tierra_centro=e))
    return rows


def test_pgda_end_to_end_recovers_known_differences(tmp_path):
    sun, earth = field(80), field(95)
    p = run_pgda(tmp_path, sun, earth, synthetic_rows(sun, earth))
    assert p.returncode == 0, p.stderr
    txt = (tmp_path / "validacion_pgda.txt").read_text(encoding="utf-8")
    assert re.search(r"Sol\s+celda\s+5 m, punto \(app\)\s+30\s+\+2\.0\s+2\.0", txt)
    assert re.search(r"Tierra\s+candidato\s+5 m, centro \(app\)\s+10\s+-3\.0\s+3\.0", txt)
    assert "Mayores diferencias en Tierra" in txt


def test_pgda_stops_on_doubtful_scale(tmp_path):
    sun, earth = field(255), field(95)
    p = run_pgda(tmp_path, sun, earth, synthetic_rows(field(80), earth))
    assert p.returncode != 0 and "DETENIDO" in p.stderr
    assert not (tmp_path / "validacion_pgda.txt").exists()


def test_pds_index_convention_is_symmetric():
    """Un mapa de N pixeles centrado en el polo: pixeles opuestos deben quedar a la misma distancia del origen."""
    N, off = 5058, 2528.5
    assert off == (N - 1) / 2
    r, c = indices_mapa(np.array([-off * 60, off * 60]), np.array([off * 60, -off * 60]), 60.0, off, off)
    assert r.tolist() == [0, N - 1] and c.tolist() == [0, N - 1]


PGDA = ROOT / "auditoria" / "datos_externos" / "AVGVISIB_85S_060M_201608.IMG"


@pytest.mark.skipif(not PGDA.exists(), reason="faltan los IMG de PGDA")
def test_pgda_site14_pixel_values():
    S = np.memmap(PGDA, dtype="<i2", mode="r", shape=(5058, 5058))
    T = np.memmap(str(PGDA).replace(".IMG", "_EARTH.IMG"), dtype="<i2", mode="r", shape=(5058, 5058))
    r, c = indices_mapa(204.0, 625.0, 60.0, 2528.5, 2528.5)
    assert S[r, c] * 4e-3 == pytest.approx(41.6, abs=0.1) and T[r, c] * 4e-3 == pytest.approx(55.5, abs=0.1)


IMG = ROOT / "auditoria" / "validacion" / "WAC_POLE_ILL_PCT_SOUTH_100M.IMG"


@pytest.mark.skipif(not IMG.exists(), reason="falta el IMG de LROC")
def test_pds_reader_on_real_lroc_product():
    A, x0, y0, sc, label = read_pds_image(IMG)
    assert (x0, y0, sc) == (-60650.0, 60650.0, 100.0)
    assert A.shape == (1214, 1214) and np.nanmax(A) == pytest.approx(71.58, abs=0.01)
    assert "percentage (PCT)" in label.replace("\n", " ") or "percentage" in label


def test_preselected_frames_are_fixed_and_spread_in_azimuth():
    rows = list(csv.DictReader(open(ROOT / "auditoria" / "validacion" / "fotogramas_lroc_seleccion.csv", encoding="utf-8")))
    assert len(rows) == 5
    az = [float(r["az_sol_deg"]) for r in rows]
    for i, a in enumerate(az):
        for b in az[i + 1:]:
            assert min(abs(a - b), 360 - abs(a - b)) >= 50
    assert all(0.15 <= float(r["frac_luz_modelo"]) <= 0.75 for r in rows)


def test_submission_draft_limits_and_figures():
    d = (ROOT / "docs" / "entrega" / "descripcion_entrega_EN.md").read_text(encoding="utf-8")
    assert len(d.split()) <= 250
    txt = (ROOT / "auditoria" / "validacion" / "validacion_lroc_img.txt").read_text(encoding="utf-8")
    assert re.search(r"celda\s+h5_punto\s+121\s+-0\.3\s+1\.3", txt) and "bias −0.3 points and MAE 1.3" in d
    assert re.search(r"candidato\s+h5_punto\s+10\s+\+7\.4", txt) and "about 7 points" in d
    assert "33–58 %" in d
