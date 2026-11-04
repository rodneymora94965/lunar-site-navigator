# Prueba de cuándo y desde dónde llega la luz

## Estado: ejecutada, aprueba

El autor la ejecutó en su PC con los 5 fotogramas reales. Salida: `validacion_fechas_lroc.txt` y `.csv`. **Aprueba con el criterio fijado de antemano.** No se cambiaron fotogramas, umbral ni criterio: el script y la selección son anteriores a la descarga de las imágenes.

| Fotograma | Hora del archivo (UTC) | MCC modelo | MCC espejo | MCC giro 180° | MCC fecha +14,77 d | VP | VN | FP | FN |
|---|---|---|---|---|---|---|---|---|---|
| `WAC_MOVIE_S20091022T0306` | 2009-10-22 03:09:57 | +0,474 | −0,160 | −0,197 | −0,195 | 479 | 4763 | 1139 | 19 |
| `WAC_MOVIE_S20091106T2212` | 2009-11-06 22:16:04 | +0,877 | −0,222 | −0,302 | −0,303 | 1639 | 4422 | 338 | 1 |
| `WAC_MOVIE_S20091101T2323` | 2009-11-01 23:27:05 | +0,815 | +0,042 | −0,231 | −0,235 | 1618 | 4247 | 520 | 15 |
| `WAC_MOVIE_S20091116T0257` | 2009-11-16 03:00:42 | +0,777 | +0,361 | −0,222 | −0,212 | 611 | 5452 | 329 | 8 |
| `WAC_MOVIE_S20090927T2014` | 2009-09-27 20:17:56 | +0,743 | −0,125 | −0,123 | −0,137 | 737 | 5184 | 471 | 8 |

MCC medio del modelo: 0,737, frente al mínimo de 0,5. Supera a los tres controles en los 5 fotogramas; los controles van de −0,303 a +0,361. Cada fotograma usa 6400 puntos. VP, VN, FP y FN son las cuentas del modelo.

**Comprobación:** al volver a ejecutar el script sobre los mismos archivos, fotograma por fotograma, salieron el `.csv` idéntico y el `.txt` idéntico salvo los finales de línea. Esto confirma que el resultado se reproduce; no es una medición independiente.

## Qué no demuestra

- **Solo 5 fechas de 2009 y solo Site04.** El Sol estaba a unos 1,3–1,6° de altura en todas, así que no prueba el Sol más bajo.
- **No valida la predicción de 2026 a 2045.** Prueba terreno y geometría en esas fechas.
- **Solo prueba el Sol.** Ninguna prueba con imágenes cubre la visibilidad de la Tierra.
- **El primer fotograma queda por debajo de 0,5** por sí solo (MCC +0,474). El criterio era el promedio, y aprobar no borra ese dato.
- **El modelo tiende a dar más luz que la imagen.** En total marca más puntos con luz: 7881 frente a 5135 de la imagen, con 2797 falsos positivos y 51 falsos negativos.
- **Usa un rayo exacto por punto**, no las tablas de horizonte de 360 azimuts de la app.
- **Los fotogramas se eligieron donde el Sol y sus controles más se diferencian.** Eso da potencia a la prueba, pero también facilita superar a los controles. Lo que exige más es el MCC medio.

## Diagnóstico posterior de los falsos positivos

Se hizo después de ver el resultado, no forma parte del criterio y no cambia el veredicto. Script: `diagnostico_fechas_lroc.py`. Salida: `diagnostico_fechas_lroc.txt`.

- De los puntos con luz en el modelo, la imagen confirma el 64,5 %. De los puntos con luz en la imagen, el modelo marca el 99,0 %.
- En el fotograma del 2009-10-22 el modelo marca 3,25 veces la luz de la imagen; en los otros, de 1,21 a 1,62 veces.
- Los falsos positivos no son oscuros del todo: su valor mediano es de unas 8 a 25 veces el de los verdaderos negativos, aunque queda bajo el umbral. El umbral de Otsu puede estar dejando terreno tenue como sombra, o puede ser luz dispersa.
- En 3 fotogramas, de 81 a 86 % de los falsos positivos están a 400 m o menos de luz observada. En el del 2009-10-22 son 19 %, y en el del 2009-09-27, 44 %: ahí no se explican por el borde de las sombras.
- La causa no está demostrada. También influyen, sin cuantificar aquí, el observador a 5 m del modelo y la resolución de la imagen.

## Criterio fijado antes de ver las imágenes

1. **Fotogramas:** los elige `seleccionar_fotogramas_lroc.py` sin abrir ninguna imagen, entre 79 nombres publicados de `WAC_POLE_MOVIE_SOUTH`. Exige de 15 a 75 % de puntos con luz según el modelo y 50° de separación en azimut solar, y prefiere los que más distinguen el Sol real de sus controles.
2. **Observación:** cada imagen se separa en luz y sombra con un umbral de Otsu, calculado solo sobre el recorte Site04. No usa el modelo.
3. **Modelo:** 5 m, Sol puntual, DEM 5 m + 80 m, 200 km, un rayo por punto hacia el azimut exacto del Sol. Malla de 200 m. Sin ajustar nada.
4. **Controles:** azimut espejado, Sol girado 180° y fecha desplazada 14,77 días.
5. **Aprueba** solo si en todos los fotogramas el MCC del modelo supera a los tres controles y el MCC medio es de al menos 0,5.

Si no aprueba, se publica igual. No se cambian fotogramas, umbral ni criterio después de ver el resultado.

## Archivos usados

Guardar en `auditoria/datos_externos/fotogramas_lroc/`. Cada IMG pesa unos 141 MB.

| Producto | Fecha (UTC, del nombre) | Azimut solar | Elev. solar |
|---|---|---|---|
| `WAC_MOVIE_S20091022T0306.IMG` | 2009-10-22 03:06 | 297,5° | 1,63° |
| `WAC_MOVIE_S20091106T2212.IMG` | 2009-11-06 22:12 | 105,4° | 1,39° |
| `WAC_MOVIE_S20091101T2323.IMG` | 2009-11-01 23:23 | 165,5° | 1,32° |
| `WAC_MOVIE_S20091116T0257.IMG` | 2009-11-16 02:57 | 353,3° | 1,52° |
| `WAC_MOVIE_S20090927T2014.IMG` | 2009-09-27 20:14 | 233,4° | 1,32° |

Ruta: `https://pds.lroc.im-ldi.com/data/LRO-L-LROC-5-RDR-V1.0/LROLRC_2001/DATA/BDR/WAC_POLE/WAC_POLE_MOVIE_SOUTH/<producto>`

Esa ruta se confirmó en la página de un fotograma (`WAC_MOVIE_S20090920T0850`); para estos 5 se dedujo del mismo patrón.

Después: `python auditoria/scripts_calculo/validar_fechas_lroc.py`. Tarda varios minutos y escribe `validacion_fechas_lroc.txt` y `.csv`.

## Prueba del script con datos sintéticos

Se crearon dos IMG falsos con etiqueta PDS, a partir del modelo, con 5 % de píxeles invertidos. Malla de 400 m.

| Fotograma sintético | MCC modelo | MCC espejo | MCC giro 180° | MCC fecha +14,77 d |
|---|---|---|---|---|
| Hora correcta | +0,826 | −0,126 | −0,257 | −0,259 |
| Hora equivocada a propósito | −0,258 | +0,624 | +0,866 | +0,874 |

El script detecta el fotograma con la hora equivocada y da "NO APRUEBA". Esto demuestra que la prueba distingue los casos, no que el modelo acierte con imágenes reales.

## Límites de la prueba

- Son 5 fechas de 2009, todas con el Sol sobre el horizonte matemático, y solo en el recorte Site04.
- Pone a prueba el terreno y la geometría, no la predicción de 2026 a 2045.
- La luz dispersa o el brillo de la Tierra pueden afectar el umbral en zonas oscuras.
