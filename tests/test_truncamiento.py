"""Terreno mas alla de 304 km del polo: la capa de 120 m se usa solo donde el DEM de 80 m no llega."""
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import horizon2 as hz

TR = ROOT / "auditoria" / "truncamiento"
IM2 = hz.xy_from_latlon(-84.7906, 29.1957)


def raster(half, d, value):
    n = int(2 * half / d)
    return (np.full((n, n), value, dtype=np.float32), -half, half, d)


def test_far_layer_is_used_only_outside_the_80_m_extent():
    wide = raster(304000.0, 8000.0, 100.0)
    wide[0][10, 10] = np.nan
    T = hz.Terrain(None, wide, raster(931200.0, 9600.0, 500.0))
    assert float(T.z(np.array([0.0]), np.array([0.0]))[0]) == 100
    assert float(T.z(np.array([340000.0]), np.array([0.0]))[0]) == 500
    hole_x = -304000.0 + 10.5 * 8000.0
    hole_y = 304000.0 - 10.5 * 8000.0
    assert np.isnan(T.z(np.array([hole_x]), np.array([hole_y]))[0])


def test_far_mountain_changes_the_horizon_only_with_the_far_layer():
    x, y = IM2
    wide = raster(304000.0, 8000.0, 0.0)
    far = raster(931200.0, 2400.0, 0.0)
    Z, x0, y0, d = far
    xs = x0 + d * (np.arange(Z.shape[1]) + .5)
    ys = y0 - d * (np.arange(Z.shape[0]) + .5)
    X, Y = np.meshgrid(xs, ys)
    u = math.hypot(x, y)
    Z[np.hypot(X - x * (1 + 196000 / u), Y - y * (1 + 196000 / u)) < 6000] = 40000.0  # a 196 km hacia afuera, fuera del mapa de 80 m
    _, without = hz.horizon(hz.Terrain(None, wide), x, y, 5.0)
    _, with_far = hz.horizon(hz.Terrain(None, wide, far), x, y, 5.0)
    assert with_far[0] > without[0] + 1
    assert np.array_equal(with_far[170:190], without[170:190])  # hacia el polo no cambia nada


def test_missing_far_file_fails_instead_of_truncating(tmp_path):
    with pytest.raises(FileNotFoundError, match="LDEM_60S_120MPP_ADJ"):
        hz.load_far(tmp_path, IM2, 215000)


def test_sites_near_the_pole_do_not_need_the_far_file(tmp_path):
    assert hz.load_far(tmp_path, (0.0, 0.0), 215000) is None
    assert not hz.needs_far((-1000.0, -7000.0), 215000)
    assert hz.needs_far(IM2, 215000)


def test_only_im2_needs_the_far_layer():
    data = json.loads((ROOT / "data" / "data.json").read_text(encoding="utf-8"))
    assert [s["id"] for s in data["sites"] if s["kind"] != "region" and hz.needs_far((s["x"], s["y"]), 215000)] == ["im2"]


def test_before_and_after_csv_match_and_describe_the_published_data():
    a = list(csv.DictReader(open(TR / "antes.csv", encoding="utf-8")))
    b = list(csv.DictReader(open(TR / "despues.csv", encoding="utf-8")))
    assert a == b and len(a) == 13
    data = json.loads((ROOT / "data" / "data.json").read_text(encoding="utf-8"))
    for row, s in zip(b, data["sites"]):
        assert row["id"] == s["id"] and row["hz_sha"] == hashlib.sha256(s["hz"].encode()).hexdigest()[:16]


def test_recorded_checks_are_within_limits():
    assert "Resultado: DENTRO" in (TR / "union_terreno.txt").read_text(encoding="utf-8")
    assert "define el horizonte: 0 con 120 m, 0 con 240 m" in (TR / "comprobacion_im2.txt").read_text(encoding="utf-8")
