# Validacion de efemerides contra JPL Horizons

Comparacion directa de SPICE (DE440s, MOON_ME, LT+S; observador sobre la esfera de 1737,4 km) con la API de JPL Horizons (azimut y elevacion aparentes, sin atmosfera), en 20 fechas de 2026 a 2045.

| Sitio | Cuerpo | n | max abs d_elev (grados) | RMS d_elev | max abs d_azim | RMS d_azim |
|---|---|---|---|---|---|---|
| 14 | sol | 20 | 0.00000 | 0.00000 | 0.00000 | 0.00000 |
| 14 | tierra | 20 | 0.00003 | 0.00002 | 0.00000 | 0.00000 |
| 456 | sol | 20 | 0.00000 | 0.00000 | 0.00000 | 0.00000 |
| 456 | tierra | 20 | 0.00003 | 0.00002 | 0.00000 | 0.00000 |
| im2 | sol | 20 | 0.00000 | 0.00000 | 0.00000 | 0.00000 |
| im2 | tierra | 20 | 0.00003 | 0.00002 | 0.00000 | 0.00000 |

Las diferencias se redondean a 0,00001 grados; un 0,00000 significa menos que eso.
Alcance: valida la posicion de Sol y Tierra y nuestra conversion a azimut y elevacion. No valida el horizonte ni el terreno.
Limite: Horizons y los kernels vienen de la misma familia de efemerides de JPL. Es una implementacion independiente de la conversion, no una medicion independiente de la orbita lunar.
Datos crudos: tests/fixtures/horizons_sol_tierra.csv
