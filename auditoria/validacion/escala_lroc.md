# Escala del mapa LROC

## Estado: RESUELTO

La lectura anterior estaba equivocada. El GeoTIFF de 8 bits es un producto de navegacion con estiramiento de contraste, no porcentajes en la escala 255 = 100 %.

## Evidencia

Producto cientifico: `WAC_POLE_ILL_PCT_SOUTH_100M.IMG` (copia en esta carpeta), version v1.3 de LRO-L-LROC-5-RDR-V1.0.

Su etiqueta PDS incrustada indica:

- `SAMPLE_TYPE = PC_REAL`, `SAMPLE_BITS = 32`, 1214 x 1214 pixeles, 100 m/pixel, estereografica polar centrada en 90 S.
- La descripcion dice que el mapa "indicates the percentage (PCT) of observations where the surface was illuminated".
- No trae `SCALING_FACTOR` ni `OFFSET`: los valores ya son porcentajes. Rango valido: hasta 71,58 %.

Comparacion pixel a pixel con el GeoTIFF de 8 bits usado antes:

- IMG = 0,1778 x DN - 0,175, con residuo maximo de 0,09 % para DN entre 1 y 249.
- DN 255 equivale a unos 45,2 %, y por encima de eso el GeoTIFF satura: 5768 pixeles superan ese tope, con un maximo real de 71,58 %.
- La lectura anterior (100 x DN / 255) inflaba cada valor unas 2,2 veces y hacia que zonas de 45 a 72 % parecieran de 100 %.

Por eso `validar_ancho_v4.py` y los archivos derivados del GeoTIFF dan un sesgo que no existe. Quedan solo como historia.

## Efecto en la validacion

Configuracion de la app (5 m, Sol puntual, 360 azimuts, 200 km), 2010-2011. No se aplico ningun factor de calibracion: el IMG se lee tal como viene.

| Conjunto | Lectura | Sesgo | MAE | r | Pendiente |
|---|---|---|---|---|---|
| 121 celdas de Site04 | GeoTIFF, 100 x DN / 255 (equivocada) | -17,0 | 17,0 | 0,985 | 0,47 |
| 121 celdas de Site04 | IMG | -0,3 | 1,3 | 0,985 | 1,00 |
| 10 candidatos | GeoTIFF, 100 x DN / 255 (equivocada) | -7,5 | 11,4 | 0,90 | 0,47 |
| 10 candidatos | IMG | +7,4 | 7,4 | 0,90 | 1,04 |

Salida completa: `validacion_lroc_img.txt` y `validacion_lroc_img.csv`. Se regenera con `python auditoria/scripts_calculo/validar_lroc_img.py`.

## Lo que este producto no resuelve

- Mide el porcentaje de observaciones con el pixel iluminado, con "a conservative global threshold" y sin corregir el muestreo temporal no uniforme, segun su README.
- El mapa ponderado por tiempo (TWI) solo se comparo en su version de 8 bits, con la misma lectura equivocada. Falta su IMG.
- Su maximo de 71,6 % es menor que los 86 a 94 % publicados para puntos a pocos metros de altura (Speyerer y Robinson 2013; Glaser et al. 2014, 2017). Pixel de 100 m, umbral y metrica son distintos, asi que no son directamente comparables.
