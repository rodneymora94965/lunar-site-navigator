# Lunar Landing Site Navigator — Site04

## What this delivery contains

This package ranks ten existing candidate landing sites around Site04 on the Shackleton rim for a 10-year planning interval beginning 1 November 2026. The candidate table is `candidatos_finales.csv`. Candidate lighting metrics were recalculated with a combined terrain horizon: the 5 m LOLA DEM inside the Site04 cutout and the 80 m polar DEM beyond it, sampled out to 120 km.

The selection rule is explicit: maximize the percentage of time when both the Sun and Earth are visible; break ties by the shortest continuous Sun-less interval, then by lower mean slope. The recommended site is candidate 14. The next three rows are alternatives. The ranking only covers the ten candidates supplied in the project's existing evaluation table; it is not a search over every point in the wider polar DEM.

## Validation against LROC

The newer wide-terrain model (5 m + 80 m) was compared with the LROC WAC illumination map using 121 cells. The saved validation reports an absolute mean error (MAE) of **15.8 percentage points**, a bias of **−15.8 percentage points** (the model underestimates illumination on average), and Pearson and Spearman correlations of **0.99**. The earlier model using only the 5 m cutout reported an MAE of **24.8 percentage points**. These are spatial comparison statistics for the 2010–2011 validation period; they do not establish equivalent accuracy for future illumination forecasts.

## Data and credits

- **Terrain:** NASA Lunar Orbiter Laser Altimeter (LOLA), `Site04_surf.tif` at 5 m and `LDEM_80S_80MPP_ADJ.TIF` at 80 m. The 5 m cutout covers about 16 × 16 km; outside it, the wider, coarser DEM supplies the horizon.
- **Validation:** NASA Lunar Reconnaissance Orbiter Camera (LROC) Wide Angle Camera (WAC) south-pole illumination map, representing 15 February 2010 to 5 February 2011.
- **Ephemerides and orientation:** NAIF SPICE kernels in `kernels/`, including JPL DE440, leap seconds, lunar frame definitions, and lunar orientation. Positions are computed in the project's `MOON_ME` frame.

## Method

The evaluation reuses the project's `calcular_candidatos.py` geometry and SPICE functions and the wide-horizon ray sampler in `validar_ancho_v4.py`; neither original script was modified. Each candidate uses a 2 m observer height, a 0.27° solar-radius allowance for candidate Sun visibility, 90 horizon azimuth samples, and a 3-hour time step over 10 years (29,220 samples). Sun and Earth visibility are tested against the 5 m + 80 m terrain horizon. Earth visibility uses the Earth center. Percentages are sampled-time fractions; the longest continuous dark interval is resolved at the 3-hour sampling cadence.

The animation map uses an 80 × 80 rendering of the 16 km fine-DEM cutout (about 200 m per displayed pixel) and ray samples from the combined terrain to show changing direct shadows. The Sun and Earth positions and the selected site's visibility status come from SPICE and the wide terrain horizon. Animation map shading treats the Sun as a point source; candidate Sun percentages include the 0.27° radius allowance. The 60 images are sampled about every two months from 1 November 2026 through 30 October 2036.

## Limits

- Terrain outside the 80 m polar DEM is not represented. The wide horizon stops at 120 km, so more distant terrain can still change visibility.
- The 80 m terrain and 200 m animation map cannot resolve small rocks, local lander-scale hazards, or every narrow ridge. Candidate horizon azimuth sampling is 4°.
- The animation's sampled shadow map is a visualization at about 200 m per pixel; candidate statistics use the separate ray-based site horizon described above.
- The Sun is a point source in the map shadow visualization. Candidate sunlight statistics allow for a 0.27° solar radius but do not model penumbra or atmospheric effects.
- The LROC validation is based on one historical interval and has a −15.8 percentage-point bias for the new model. Correlation of 0.99 does not remove this systematic underestimation or guarantee future accuracy.
- The ten-site candidate pool is inherited from the project's existing candidate evaluation. The recommendation is conditional on that pool and the stated ranking criterion.

## Reproduce

Run from the project root, with the listed Python packages, the input DEMs, and SPICE kernels available:

```powershell
python entrega_spaceapps/generar_candidatos_ancho.py
python entrega_spaceapps/generar_animacion.py
```

The first command writes the candidate table. The second writes 60 PNG frames under `entrega_spaceapps/.frames`. Assemble those existing frames with FFmpeg (30-second, 1080p, H.264, `yuv420p`):

```powershell
C:\Users\RoneyMora\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe -y -nostdin -hide_banner -loglevel error -framerate 2 -i entrega_spaceapps\.frames\frame_%03d.png -vf "fps=30,scale=1920:1080:flags=lanczos,format=yuv420p" -c:v libx264 -preset medium -crf 20 -movflags +faststart entrega_spaceapps\animacion_10anios.mp4
```

The final assembly used the full FFmpeg path above with `-y -nostdin`, 2 input frames per second, 1920 × 1080 scaling, H.264, and `yuv420p`. It completed with exit code 0 and no FFmpeg error output. The resulting 30-second `animacion_10anios.mp4` is 2,167,664 bytes. An earlier attempt without `-nostdin` exceeded its 120-second limit; its partial MP4 was removed before the successful assembly.
