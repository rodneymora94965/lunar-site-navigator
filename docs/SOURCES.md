# Data and provenance / Datos y procedencia

The application uses precomputed data in `data/data.json`. To regenerate it, see `scripts/obtener_datos.md`.

La aplicacion usa los datos precalculados de `data/data.json`. Para regenerarlos, consulta `scripts/obtener_datos.md`.

- Ephemerides / Efemerides: NASA/JPL NAIF SPICE, DE440s, lunar orientation kernels (MOON_ME frame). Checked against JPL Horizons.
- Elevation / Elevacion: LOLA aboard Lunar Reconnaissance Orbiter (`Site04_surf.tif`, 5 m; `LDEM_80S_80MPP_ADJ.TIF`, 80 m; `LDEM_60S_120MPP_ADJ.TIF`, 120 m, only beyond 304 km from the pole). Barker et al. 2023, Planet. Sci. J. 4, 183 (https://pgda.gsfc.nasa.gov/products/90).
- Illumination comparison / Comparacion de iluminacion: LROC WAC `WAC_POLE_ILL_PCT_SOUTH_100M.IMG`, 32-bit percentages from the PDS RDR (Speyerer & Robinson 2013, Icarus 222). The 8-bit browse GeoTIFF is not used for science.
- IM-2 Athena coordinates / Coordenadas de IM-2 Athena: 84.7906 S, 29.1957 E, LROC featured image (https://www.lroc.im-ldi.com/images/1408).
- Candidate metadata / Metadatos de candidatos: `auditoria/entrega_anterior/candidatos_finales.csv` (area and slope), from `auditoria/scripts_calculo/bolsones.py`.
- Literature used for context only / Literatura usada solo como contexto: Mazarico et al. 2011, Icarus 211; Glaser et al. 2014, Icarus 243; Glaser et al. 2017, PSS 162.

## Reference sites left out / Sitios de referencia omitidos

Only sites with a primary-source coordinate inside DEM coverage (80S to 90S) are included. NASA's Artemis III list names regions without coordinates in the source reviewed, Apollo and Chandrayaan-3 are outside this DEM, and no other primary-source landing coordinate was verified.

Solo se incluyen sitios con coordenada de fuente primaria dentro de la cobertura del DEM (80S a 90S). La lista de Artemis III de la NASA nombra regiones sin coordenadas en la fuente revisada, Apollo y Chandrayaan-3 quedan fuera de este DEM, y no se verifico otra coordenada de aterrizaje de fuente primaria.

Credits / Creditos: **Solaris Core, Roney Rigg Mora**.
- Test tool only / Solo para pruebas: axe-core 4.10.2 (Deque Systems, MPL-2.0), `tests/fixtures/axe-4.10.2.min.js`. It is not part of the app.
- Region points / Puntos de region: Wueller et al. 2026, JGR Planets 131(3), e2025JE009434; dataset https://doi.org/10.5281/zenodo.17084058 (CC BY 4.0). Region names: NASA release 24-136, https://www.nasa.gov/news-release/nasa-provides-update-on-artemis-iii-moon-landing-regions/.
