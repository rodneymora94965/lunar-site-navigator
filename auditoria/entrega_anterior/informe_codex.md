# Codex execution report

## Completed

- Read `brief_codex_animacion.md` and inspected the existing DEMs, kernels, candidate tables, and validation reports without modifying existing project files.
- Reused `calcular_candidatos.py` and `validar_ancho_v4.py` from a new delivery script. Recalculated 10 candidates for 1 November 2026 through 1 November 2036 at 3-hour intervals (29,220 samples), using the combined 5 m + 80 m terrain horizon to 120 km for both Sun and Earth visibility.
- Wrote `candidatos_finales.csv`. Candidate 14 ranks first under the documented rule: highest simultaneous Sun/Earth visibility, then shortest Sun-less interval, then lowest mean slope. Candidates 456, 1358, and 964 are the three alternatives.
- Rendered 60 bilingual 1080p PNG frames in `.frames`, sampled approximately every two months across the ten-year period.
- Wrote this report, the English README, and the bilingual submission description.

## Validation figures cited

The existing `salida_2010/validacion_ancho.txt` reports the new combined-terrain model at MAE 15.8 percentage points, bias −15.8 percentage points, Pearson 0.99, and Spearman 0.99 across 121 cells. It reports MAE 24.8 percentage points for the earlier 5 m-only model. The README and animation include the requested MAE, bias, Pearson correlation, and older-model MAE.

## Video assembly result

The first FFmpeg attempt did not finish within 120 seconds and left a partial file. At the user's direction, only that partial MP4 was removed. The 60 existing PNG frames were assembled using the full FFmpeg path with `-y -nostdin`, input framerate 2, 1920×1080 scaling, H.264, and `yuv420p`, under a 180-second process limit. FFmpeg completed with exit code 0 and no error output. The resulting 30-second `animacion_10anios.mp4` is 2,167,664 bytes. No frames were re-rendered.

The selected candidate values are estimates at a 3-hour cadence. Candidate horizons use 90 azimuth samples and a 120 km terrain extent; the wide DEM is 80 m outside the 5 m cutout. The animation map is downsampled to about 200 m per pixel. The validation is historical and exhibits −15.8 percentage points of bias, so its correlation does not imply unbiased future forecasts. The ten-candidate ranking depends on the existing candidate pool and does not search the entire wide DEM.
