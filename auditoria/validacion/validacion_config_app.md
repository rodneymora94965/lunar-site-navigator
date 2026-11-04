> **OBSOLETO contra LROC:** estas metricas usan el GeoTIFF de 8 bits con la lectura equivocada 100 x DN / 255. Las cifras del modelo siguen validas. La comparacion correcta esta en `validacion_lroc_img.txt`.

# Validacion con la configuracion de la app (360 azimuts, alcance 200 km, DEM 5 m + 80 m)

Periodo: 15-feb-2010, 0,972 anos, cada hora, igual que el mapa LROC WAC.
LROC: GeoTIFF de navegacion de 8 bits leido con la conversion nominal 100 x DN / 255. Esa conversion NO esta confirmada: ver escala_lroc.md.

| Conjunto | n | Observador | Sol | Mapa LROC | Sesgo (pp) | MAE (pp) | Pearson | Pendiente |
|---|---|---|---|---|---|---|---|---|
| 121 celdas Site04 | 121 | 2 m | punto | PCT | -17.5 | 17.5 | 0.985 | 0.45 |
| 121 celdas Site04 | 121 | 2 m | disco | PCT | -16.1 | 16.1 | 0.987 | 0.49 |
| 121 celdas Site04 | 121 | 5 m | punto | PCT | -17.0 | 17.0 | 0.985 | 0.47 |
| 121 celdas Site04 | 121 | 5 m | punto | TWI | -18.3 | 18.3 | 0.984 | 0.45 |
| 121 celdas Site04 | 121 | 5 m | disco | PCT | -15.6 | 15.6 | 0.987 | 0.51 |
| 121 celdas Site04 | 121 | 10 m | punto | PCT | -16.5 | 16.5 | 0.976 | 0.50 |
| 121 celdas Site04 | 121 | 10 m | disco | PCT | -15.1 | 15.1 | 0.979 | 0.54 |
| 121 celdas Site04 (solo con luz) | 73 | 2 m | punto | PCT | -28.8 | 28.8 | 0.968 | 0.47 |
| 121 celdas Site04 (solo con luz) | 73 | 2 m | disco | PCT | -26.5 | 26.5 | 0.969 | 0.49 |
| 121 celdas Site04 (solo con luz) | 73 | 5 m | punto | PCT | -28.0 | 28.0 | 0.969 | 0.50 |
| 121 celdas Site04 (solo con luz) | 73 | 5 m | punto | TWI | -30.1 | 30.1 | 0.968 | 0.48 |
| 121 celdas Site04 (solo con luz) | 73 | 5 m | disco | PCT | -25.6 | 25.6 | 0.972 | 0.53 |
| 121 celdas Site04 (solo con luz) | 73 | 10 m | punto | PCT | -27.1 | 27.1 | 0.954 | 0.53 |
| 121 celdas Site04 (solo con luz) | 73 | 10 m | disco | PCT | -24.7 | 24.7 | 0.955 | 0.56 |
| 10 candidatos | 10 | 2 m | punto | PCT | -10.5 | 12.2 | 0.960 | 0.46 |
| 10 candidatos | 10 | 2 m | disco | PCT | -8.5 | 10.8 | 0.952 | 0.49 |
| 10 candidatos | 10 | 5 m | punto | PCT | -7.5 | 11.4 | 0.901 | 0.47 |
| 10 candidatos | 10 | 5 m | punto | TWI | -8.1 | 12.0 | 0.902 | 0.45 |
| 10 candidatos | 10 | 5 m | disco | PCT | -5.3 | 10.6 | 0.891 | 0.51 |
| 10 candidatos | 10 | 10 m | punto | PCT | -4.4 | 11.3 | 0.844 | 0.50 |
| 10 candidatos | 10 | 10 m | disco | PCT | -2.3 | 10.6 | 0.844 | 0.54 |
| 10 candidatos (solo con luz) | 8 | 2 m | punto | PCT | -13.1 | 15.2 | 0.964 | 0.41 |
| 10 candidatos (solo con luz) | 8 | 2 m | disco | PCT | -10.5 | 13.4 | 0.958 | 0.43 |
| 10 candidatos (solo con luz) | 8 | 5 m | punto | PCT | -9.2 | 14.1 | 0.891 | 0.39 |
| 10 candidatos (solo con luz) | 8 | 5 m | punto | TWI | -10.1 | 15.0 | 0.895 | 0.38 |
| 10 candidatos (solo con luz) | 8 | 5 m | disco | PCT | -6.5 | 13.1 | 0.878 | 0.42 |
| 10 candidatos (solo con luz) | 8 | 10 m | punto | PCT | -5.4 | 14.0 | 0.808 | 0.39 |
| 10 candidatos (solo con luz) | 8 | 10 m | disco | PCT | -2.8 | 13.1 | 0.811 | 0.42 |

La configuracion que publica la app es 5 m con Sol puntual.
Datos por punto: validacion_config_app.csv
