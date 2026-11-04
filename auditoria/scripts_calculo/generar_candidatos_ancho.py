#!/usr/bin/env python3
"""Evaluate existing landing candidates with the project's wide-terrain horizon."""
import csv
import math
import os
import sys

import numpy as np
import rasterio
from scipy.ndimage import map_coordinates

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import calcular_candidatos as cc
import validar_ancho_v4 as va


def main():
    candidates_path = os.path.join(ROOT, "salida", "candidatos_evaluados.csv")
    fine_path = os.path.join(ROOT, "datos", "Site04_surf.tif")
    wide_path = os.path.join(ROOT, "datos", "LDEM_80S_80MPP_ADJ.TIF")
    kernels = os.path.join(ROOT, "kernels")
    with open(candidates_path, newline="", encoding="utf-8") as f:
        candidates = list(csv.DictReader(f))[:10]
    zf, trf, _, _, _, _ = va.cargar(fine_path, "float64")
    zw, trw, _, _, _, _ = va.cargar(wide_path, "float32")

    start = "2026-11-01"
    years = 10.0
    step_hours = 3.0
    height_m = 2.0
    solar_radius_deg = 0.27
    max_distance_km = 120.0
    distances = np.concatenate((np.arange(10.0, 20000.0, 10.0),
                                np.arange(20000.0, max_distance_km * 1000.0, 80.0)))

    print(f"Calculating SPICE positions: {start}, {years:g} years, {step_hours:g} h step")
    frame, sun, earth = cc.efemerides(kernels, start, years, step_hours)
    print(f"Frame {frame}; {len(sun)} time samples; {len(candidates)} candidates")

    results = []
    inv = ~trf
    for index, row in enumerate(candidates, 1):
        x, y = float(row["x_m"]), float(row["y_m"])
        lat, lon = cc.xy_a_latlon(x, y)
        lat_r, lon_r = math.radians(lat), math.radians(lon)
        east, north, up = cc.base_local(lat_r, lon_r)
        col, r = inv * (x, y)
        ground = map_coordinates(zf, [[r - 0.5], [col - 0.5]], order=1,
                                 mode="nearest")[0]
        azs, horizon = va.horizonte2(zf, trf, zw, trw, x, y, lon,
                                     height_m, distances, 90)
        site = np.array([math.cos(lat_r) * math.cos(lon_r),
                         math.cos(lat_r) * math.sin(lon_r),
                         math.sin(lat_r)]) * (cc.R_KM + (ground + height_m) / 1000.0)
        sun_elev, sun_az = cc.elev_az_vec(sun - site, east, north, up)
        earth_elev, earth_az = cc.elev_az_vec(earth - site, east, north, up)
        sun_h = np.interp(sun_az, np.append(azs, 360.0),
                          np.append(horizon, horizon[0]))
        earth_h = np.interp(earth_az, np.append(azs, 360.0),
                            np.append(horizon, horizon[0]))
        sun_visible = sun_elev + solar_radius_deg > sun_h
        earth_visible = earth_elev > earth_h
        results.append({
            "id": row["id"], "x_m": row["x_m"], "y_m": row["y_m"],
            "lat_deg": f"{lat:.5f}", "lon_east_deg": f"{lon:.4f}",
            "elevation_m": row["elev_m"], "area_centers_m2": row["area_centros_m2"],
            "mean_slope_deg": row["pend_media_deg"],
            "sun_time_pct": f"{100 * sun_visible.mean():.1f}",
            "earth_time_pct": f"{100 * earth_visible.mean():.1f}",
            "both_time_pct": f"{100 * (sun_visible & earth_visible).mean():.1f}",
            "longest_continuous_sunless_days": f"{cc.racha_maxima(~sun_visible, step_hours / 24):.1f}",
            "longest_continuous_earthless_days": f"{cc.racha_maxima(~earth_visible, step_hours / 24):.1f}",
            "wide_horizon_max_deg": f"{float(horizon.max()):.2f}",
        })
        print(f"  {index}/{len(candidates)} candidate {row['id']} complete")

    # Explicit selection rule: maximize simultaneous Sun+Earth availability;
    # break ties by shorter longest Sun-less interval, then lower mean slope.
    results.sort(key=lambda q: (-float(q["both_time_pct"]),
                                float(q["longest_continuous_sunless_days"]),
                                float(q["mean_slope_deg"])))
    for rank, result in enumerate(results, 1):
        result["selection_rank"] = rank
        result["selection"] = "Recommended" if rank == 1 else (f"Alternative {rank - 1}" if rank <= 4 else "Compared")
        result["selection_criterion"] = "Maximize both-time %, then minimize longest Sun-less interval, then mean slope"

    output_path = os.path.join(OUT, "candidatos_finales.csv")
    fields = list(results[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
