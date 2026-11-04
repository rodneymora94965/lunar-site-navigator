# De dónde sale cada cifra de los borradores

| Cifra | Fuente |
|---|---|
| Hora a hora, noviembre de 2026 a octubre de 2045 | `data/data.json` (`t0`, `n`, `step_h`) |
| Sitio 456: Sol 21 % (20–22), ambos 14 % (14–15), noche 29 días | `data/data.json` (`rng`) y `auditoria/resultados_sitios.csv` |
| Sitio 456: bolsón de 4,47 km²; sitio 14: 0,33 km² | `data/data.json` (`area`) |
| Sitio 456: modelo 21 %, LROC 15 %, PGDA 23 % | `auditoria/validacion/candidatos_tres_fuentes.csv` |
| Sitio 14: Sol 49 %, noche 17 días | `auditoria/resultados_sitios.csv` |
| Sitio 14: Sol 33–58 % al mover ±100 m | `data/data.json` (`rng.sun`, 32,9 a 58,2) |
| Sitio 14: ambos 26 %; IM-2: ambos 37 % | `auditoria/resultados_sitios.csv` (`both_19y`, 26,23 y 37,45) |
| Sitio 14 en 2010-2011: modelo 49 %, LROC 39 % | `auditoria/validacion/validacion_lroc_img.csv` (48,66 y 38,8) |
| Portada y comparación (renders nuevos): cifras del 456, 14, 1358 y 964 a 19 años | `auditoria/resultados_sitios.csv` (comprobadas contra los renders) |
| Video del 456: alturas de Sol y Tierra por fecha | Calculadas de `data/data.json` (comprobadas en 3 fechas) |
| 121 celdas: sesgo −0,3, MAE 1,3 | `auditoria/validacion/validacion_lroc_img.txt` |
| 10 candidatos: sesgo +7,4 ("unos 7 puntos") | `auditoria/validacion/validacion_lroc_img.txt` |
| Sesgo anterior de −17 | `auditoria/validacion/validacion_config_app.md` (lectura equivocada) |
| 121 celdas contra PGDA: MAE Sol 1,6 y Tierra 3,1; candidatos: Sol +3,1 ("unos 3") | `auditoria/validacion/validacion_pgda.txt` |
| Sitio 14 en PGDA: 41,6 %, 8 de 9 píxeles en 0; a 660 m del polo | `auditoria/validacion/diagnostico_sitio14_pgda.txt` |
| 20 fechas y 3 sitios con JPL Horizons | `auditoria/validacion/validacion_horizons.md` |
| GeoTIFF saturado cerca de 45 % | `auditoria/validacion/escala_lroc.md` |
| Sol ±1,6° en el polo | `auditoria/validacion/resumen_S90p00_0p00.txt` (−1,58 a 1,59, 10 años) |
| Ciclo de la Tierra de unos 27 días | Medido sobre `data/data.json`; prueba `test_earth_cycle_is_about_27_days` |
| Recorte de 16 km | `auditoria/validacion/Site04_surf_resumen.txt` |
| Video: sitio 456, misión de 14 días: llegada 21 jun 2030, 4 %; llegada 7 ago 2030, 73 % | Calendario de `final.html`; `scripts/hacer_demo.py` comprueba estos textos en pantalla y `tests/test_app_e2e.py` compara el calendario con el planificador |
| 9 puntos de región; sitios y coordenadas | `auditoria/regiones/puntos_representativos.csv`, de Wueller et al. 2026 |
| De Gerlache Rim 2: LROC 15,9 %, modelo 56,5 %, PGDA 54,9 %; tres puntos sin comparación | `auditoria/regiones/validacion_regiones.csv` |
| 5 fotogramas con fecha; Sol a 1,3–1,6° | `auditoria/validacion/fotogramas_lroc_seleccion.csv` (1,321 a 1,632°) |
| MCC por fotograma, media 0,737 ("0,74"), controles de −0,30 a +0,36, APRUEBA | `auditoria/validacion/validacion_fechas_lroc.txt` y `.csv` |
| 7881 y 5135 puntos con luz; 2797 falsos positivos y 51 falsos negativos | Suma de VP, FP y FN del modelo en `auditoria/validacion/validacion_fechas_lroc.csv` |
| 6400 puntos por fotograma, malla de 200 m | `auditoria/validacion/validacion_fechas_lroc.csv` y `prueba_fechas_lroc.md` |
