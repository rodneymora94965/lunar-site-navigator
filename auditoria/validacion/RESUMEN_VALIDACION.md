# Resumen de validacion

| Que | Contra que | Resultado | Estado |
|---|---|---|---|
| Posicion de Sol y Tierra | JPL Horizons, 20 fechas, 3 sitios | Maximo 0,00003 grados en elevacion | Validado (`validacion_horizons.md`) |
| Trazado del horizonte | Soluciones analiticas sinteticas | Dentro de la tolerancia | Validado (`tests/test_project.py`) |
| JavaScript del navegador | Python y Horizons | Dentro de la tolerancia | Validado (`tests/`) |
| Escala del mapa LROC | Etiqueta PDS del IMG | Valores en porcentaje; el GeoTIFF de 8 bits estaba estirado y saturado | Resuelto (`escala_lroc.md`) |
| % de Sol, 121 celdas de Site04 | LROC IMG 2010-2011 | Sesgo -0,3, MAE 1,3, r 0,985, pendiente 1,00 | Validado en cuanto a cantidad de luz |
| % de Sol, 10 candidatos | LROC IMG 2010-2011 | Sesgo +7,4, MAE 7,4, r 0,90, pendiente 1,04 | Sobreestima unos 7 puntos |
| Hora y direccion de la luz del Sol | 5 fotogramas WAC con fecha, 2009 | MCC +0,474, +0,877, +0,815, +0,777, +0,743; media 0,737 (minimo 0,5); supera en los 5 a tres controles, que van de -0,30 a +0,36 (`prueba_fechas_lroc.md`) | Aprueba, con limites: 5 fechas de 2009, solo Site04, no valida la prediccion de 2026 a 2045, el modelo da mas luz que la imagen y el primer fotograma queda por debajo de 0,5 |
| % de Sol, terreno general (121 celdas) | PGDA IMG (promedio de 18,6 anos) | Sesgo -0,3, MAE 1,6, r 0,965, pendiente 0,95 | Validado en cantidad de luz |
| % de Tierra, terreno general (121 celdas) | PGDA IMG | Sesgo -1,3, MAE 3,1, r 0,961, pendiente 0,91 | Validado en cantidad |
| % de Sol, 10 candidatos | PGDA IMG | Sesgo +3,1, MAE 3,8, r 0,946, pendiente 1,02 | Sobreestima unos 3 puntos |
| % de Tierra, 10 candidatos | PGDA IMG | Sesgo -2,2, MAE 2,6, r 0,994, pendiente 0,97 | Validado en cantidad |
| Sitio 14 | LROC y PGDA | Sin confirmar: ver seccion propia | **No confirmado** |

Configuracion de la app: 5 m, Sol puntual, 360 azimuts, 200 km. Ningun factor de calibracion aplicado.

## Validacion contra PGDA

Producto: `AVGVISIB_85S_060M_201608` y su version `_EARTH` (IMG, 60 m/pixel). Escala de la etiqueta PDS3: DN x 0,00004. Script: `validar_pgda_img.py`. Salida: `validacion_pgda.txt` y `.csv`.

| Conjunto | Magnitud | 5 m, app (punto/centro): sesgo, MAE, r, pendiente | 5 m, como PGDA (cualquier parte del disco): sesgo, MAE, r, pendiente |
|---|---|---|---|
| 121 celdas | Sol | -0,3; 1,6; 0,965; 0,95 | +1,2; 1,3; 0,964; 1,03 |
| 121 celdas | Tierra | -1,3; 3,1; 0,961; 0,91 | +1,6; 1,8; 0,964; 1,00 |
| 10 candidatos | Sol | +3,1; 3,8; 0,946; 1,02 | +5,4; 5,4; 0,940; 1,12 |
| 10 candidatos | Tierra | -2,2; 2,6; 0,994; 0,97 | +1,7; 1,7; 0,997; 1,02 |

Mayores diferencias en Sol: celda -6050/-10050 (+35,5), celda -1050/-11050 (+15,7), celda -2950/-7950 (+14,5), candidato 1643 (+14,0), candidato 14 (+7,3).

**Correccion de geometria.** La primera version del script leia los mapas un pixel al oeste y otro al norte, unos 85 m, porque restaba 1 a un OFFSET que ya es 0-based: un mapa simetrico de 5058 pixeles tiene su centro 0-based en 2528,5, igual al OFFSET. Con esa lectura salian candidatos con r 0,37 en Sol y el sitio 14 en 0 %. La version original esta en `auditoria/antes/ronda_pgda_img/`.

**Comprobacion independiente de la lectura.** Con el disco como PGDA, en las 121 celdas: lectura de etiqueta r 0,964 (Sol) y 0,964 (Tierra); lectura anterior r 0,914 y 0,949. Sin usar el modelo, PGDA frente a LROC IMG en Site04: r 0,927 frente a 0,911.

**Desplazamiento residual, sin aplicar.** Una fila al norte (60 m) mejora las celdas a r 0,989 y 0,991, pero frente a LROC no hay diferencia clara (0,927 en varias posiciones). Puede ser una diferencia de registro de hasta un pixel entre el DEM de PGDA y el de 5 m. No se corrigio porque seria un ajuste a posteriori.

**Fechas.** 2009-2013 en la etiqueta corresponde a los datos LOLA. La pagina de PGDA indica que el mapa promedia 18,6 anos. El modelo usa 19 anos desde 2026, asi que ambos cubren un ciclo nodal completo, aunque en fechas distintas.

## Sitio 14: no confirmado

A 660 m del polo. Detalle en `diagnostico_sitio14_pgda.txt`.

- **No es un problema de tamano:** el bolson de 0,33 km2 equivale a 92 pixeles de 60 m y 33 de 100 m.
- **PGDA en su pixel exacto:** Sol 41,6 % y Tierra 55,5 %. El 0 % anterior venia del error de geometria.
- **Pero el entorno esta moteado:** en radio de 100 m, 8 de 9 pixeles de PGDA valen 0. Los que no valen 0 promedian 41,6 % y 55,5 %.
- **El moteado se concentra junto al polo:** pares vecinos con salto mayor a 25 puntos: 21 % a 0-1 km, 5 % a 1-2 km y hasta 2 % mas lejos. LROC no lo muestra: en +-300 m va de 22,1 a 45,5 %, sin ceros. El modelo tampoco, ni con DEM de 60 m. Parece un artefacto, pero su causa no esta demostrada.

| Fuente, ventana de +-300 m (disco como PGDA) | Sol en el centro | Sol, media | Sol, ceros | Tierra en el centro | Tierra, media | Tierra, ceros |
|---|---|---|---|---|---|---|
| PGDA | 41,6 | 9,5 | 75 % | 55,5 | 13,8 | 69 % |
| Modelo, DEM 5 m, 0 m | 40,7 | 30,2 | 1 % | 55,6 | 48,2 | 3 % |
| Modelo, DEM 5 m, 2 m | 47,1 | 38,5 | 0 % | 55,6 | 51,9 | 0 % |
| Modelo, DEM 5 m, 5 m | 54,5 | 44,7 | 0 % | 55,6 | 53,8 | 0 % |
| Modelo, DEM 60 m, 0 m | 40,7 | 34,3 | 0 % | 55,6 | 50,6 | 2 % |
| Modelo, DEM 60 m, 2 m | 46,6 | 41,1 | 0 % | 55,6 | 52,8 | 0 % |
| Modelo, DEM 60 m, 5 m | 56,7 | 46,4 | 0 % | 55,6 | 54,3 | 0 % |

- **Altura:** el Sol sube de 41 a 55-57 % de 0 a 5 m. La Tierra casi no cambia en este punto.
- **Resolucion del DEM:** pasar de 5 a 60 m cambia poco el punto central y no produce los ceros.
- **Posicion, +-100 m con la configuracion de la app:** Sol 33 a 58 %; Tierra 51 %.
- **LROC:** 38,8 % en su pixel de 100 m, frente a 48,7 % del modelo en 2010-2011.

Lectura: los tres coinciden en que el sitio tiene luz cerca del 40 % con poca altura, y el valor de 49 % a 5 m queda alto frente a LROC. PGDA no sirve para confirmarlo ni para descartarlo a escala de pixel.

## Candidatos con las tres fuentes

Tabla completa: `candidatos_tres_fuentes.csv`.

## Por altura y tratamiento del Sol (LROC IMG)

| Conjunto | 2 m, punto | 5 m, punto (app) | 5 m, con borde del disco | 10 m, punto |
|---|---|---|---|---|
| 121 celdas: sesgo / MAE / r | -0,7 / 1,3 / 0,977 | -0,3 / 1,3 / 0,985 | +1,2 / 1,6 / 0,987 | +0,3 / 1,4 / 0,986 |
| 10 candidatos: sesgo / MAE / r | +4,3 / 4,3 / 0,961 | +7,4 / 7,4 / 0,902 | +9,5 / 9,5 / 0,892 | +10,5 / 10,5 / 0,844 |

## Por que los candidatos dan unos 7 puntos de mas

Se probo en `auditoria/scripts_calculo/diagnostico_candidatos_img.py`; datos en `validacion_candidatos_diagnostico.csv`.

| Grupo | n | Centro | Media del pixel | Todo el pixel iluminado |
|---|---|---|---|---|
| 10 candidatos | 10 | +7,4 | +6,2 | +3,5 |
| Otros bolsones planos, al azar | 40 | +3,9 | +2,8 | -1,3 |
| Celdas de Site04, al azar | 40 | -0,5 | -0,5 | -1,4 |

Sesgo en puntos porcentuales frente al IMG; mallas de 5x5 en candidatos y 3x3 en los demas, con 120 azimuts.

- **Tipo de terreno (seleccion):** los 10 candidatos no se eligieron por tener mas luz, sino por ser los 10 bolsones planos de mayor area (`bolsones.py`). Otros bolsones planos tambien dan mas luz que LROC (+3,9), mientras que las celdas al azar no (-0,5). Elegir terreno plano explica una parte.
- **Sitio 14 (seleccion por luz):** si se eligio por tener mas tiempo con Sol y Tierra. Su diferencia es +9,9 (48,7 % frente a 38,8 %). Puede heredar un efecto de seleccion, pero con un solo punto no se puede demostrar.
- **Resolucion, 5 m frente a 100 m:** promediar el pixel baja el sesgo de +7,4 a +6,2. Contar solo instantes con todo el pixel iluminado lo baja a +3,5, que es un extremo porque el umbral real de LROC no se puede reproducir. El caso mas claro es el candidato 1643: 21,3 % en el punto, 11,3 % de media, 2,5 % con todo el pixel iluminado y 0,9 % en LROC.
- **Crestas:** en una ventana de 2x2 km sobre la cresta de Shackleton (2 m, con borde del disco) el sesgo medio es -0,8 y el MAE 4,0, pero el mejor punto del modelo da 90,4 % y su pixel en LROC 57,1 %. El modelo puntual da mas luz que un pixel de 100 m justo donde hay mas luz.
- **Sin explicar:** estas pruebas no cierran los 7 puntos, y ademas se solapan, asi que no se pueden sumar. Queda una parte sin atribuir.

## Terreno mas alla de 304 km del polo

El mapa de 80 m llega a 304 km del polo. Con rayos de 200 km, solo IM-2 (158,1 km del polo) se salia de el, en 68 de 360 azimuts y desde 166 km. Se agrego `LDEM_60S_120MPP_ADJ.TIF` (120 m), que se usa solo fuera de esa extension. Ver `auditoria/truncamiento/`.

- **Cifras:** no cambio ninguna. `antes.csv` y `despues.csv` son identicos en los 13 sitios, y `data.json` tambien.
- **IM-2:** el terreno lejano no define el horizonte en ningun azimut; el cercano queda al menos 2,3 grados por encima. No es una validacion nueva de IM-2: PGDA llega hasta 85 grados S.
- **Union de los mapas, 250 a 304 km:** mediana -0,07 m y percentil 95 de 4,69 m, dentro de los limites fijados antes de mirar (5 m y 50 m). No se aplico ningun ajuste.
- **Regresion:** al recalcular el modelo, LROC, PGDA y la prueba de fechas salieron iguales. Eso muestra que el cambio no rompio nada; no aporta validacion nueva.
- **Limite que sigue:** las coordenadas propias de la app usan un DEM reducido que llega a 304 km, asi que a mas de 104 km del polo su horizonte sigue truncado hacia afuera, con aviso.

## Puntos en regiones que la NASA nombra como candidatas

Nueve puntos fuera del ranking, publicados por Wueller et al. 2026. Regla, criterios y datos: `auditoria/regiones/`. Son comparaciones de un punto, sin aprobar ni reprobar.

- **Sin comparacion:** Peak near Cabeus B, Mons Mouton Plateau y Nobile Rim 2. El mapa de LROC cubre de 88 a 90 grados S y PGDA llega a 85 grados S.
- **Con PGDA:** Haworth, Malapert Massif, Mons Mouton, Nobile Rim 1, de Gerlache Rim 2 y Slater Plain. En Haworth, Sol 36,9 % frente a 47,7 % del modelo.
- **Con LROC:** solo de Gerlache Rim 2: 15,9 % frente a 56,5 % del modelo, con PGDA en 54,9 %. Causa sin demostrar. `diagnostico_lroc_borde.txt` muestra que LROC y PGDA coinciden a unos 4 puntos a esa distancia del polo, asi que el borde del mapa no lo explica.

## Limite que sigue vigente

Con los azimuts invertidos a proposito (2 m, con borde del disco), la comparacion con el IMG casi no cambia: MAE 1,7 frente a 1,8 y r 0,976 en ambos casos. El acuerdo valida cuanta luz hay, no cuando ni desde donde llega.

## Altura del observador en el sitio 14 (19 anos)

| Altura | Sol, punto | Sol, con borde del disco | Tierra |
|---|---|---|---|
| 2 m | 42,2 % | 47,1 % | 51,0 % |
| 5 m (app) | 49,1 % | 55,2 % | 51,0 % |
| 10 m | 57,2 % | 62,9 % | 51,0 % |

## DEM reducido para coordenadas propias (paso de 3 h, 19 anos, 5 m)

Referencia: DEM completo. Elegido: 20 m en el recorte Site04 y 480 m fuera.

| Sitio | DEM completo: Sol / Tierra / ambos / noche | DEM reducido | Error RMS del horizonte |
|---|---|---|---|
| 14 | 49,1 / 51,0 / 26,2 / 17,0 | 50,1 / 51,1 / 27,0 / 16,9 | 0,15 grados |
| 456 | 20,8 / 50,5 / 14,4 / 29,1 | 20,9 / 50,5 / 14,5 / 29,1 | 0,13 grados |
| 1358 | 28,8 / 51,6 / 16,8 / 25,8 | 29,0 / 51,7 / 16,9 / 25,6 | 0,05 grados |
| IM-2 | 45,5 / 81,2 / 37,4 / 19,1 | 45,2 / 81,3 / 37,2 / 19,1 | 0,23 grados |

Son solo 4 puntos. Fuera del recorte Site04 no hay terreno de 5 m para comparar la zona cercana a menos de 480 m.

## 19 anos

Calculado de 2026-11-01 a 2045-10-31, cada hora. Cubre el ciclo nodal lunar de 18,6 anos. Los resultados de 10 y 19 anos estan en `auditoria/resultados_sitios.csv`. La comparacion con LROC cubre solo 2010-2011.

## Archivos historicos

`validacion_ancho.txt`, `validacion_celda.txt`, `validacion_malla.txt`, `validacion_iluminacion.*` y `auditoria/entrega_anterior/` usan el GeoTIFF de 8 bits con la lectura equivocada. Sus metricas contra LROC ya no valen. En `validacion_config_app.*` son validas las cifras del modelo, pero no las columnas ni las metricas contra LROC.

## Sitio principal: 456 (decision del autor)

Criterio: (1) Sol y Tierra utiles: Tierra de al menos 40 % en todo +-100 m y ambos de al menos 10 % en el punto; (2) acuerdo entre modelo, LROC y PGDA, sin ceros en el entorno; (3) rangos estrechos al mover +-100 m; (4) bolson amplio; (5) noche mas corta como desempate.

Pasan el filtro (1): 14, 1358, 456 y 964.

| Sitio | Modelo / LROC 2010-2011, Sol | PGDA Sol: pixel / mediana 100 m / ceros | Sol +-100 m | Ambos +-100 m | Tierra PGDA | Noche +-100 m | Bolson km2 |
|---|---|---|---|---|---|---|---|
| 14 | 48,7 / 38,8 | 41,6 / 0,0 / 89 % | 33-58 | 20-29 | 55,5 pixel; 0 mediana | 17-23 | 0,33 |
| 1358 | 28,9 / 15,4 | 23,8 / 23,7 / 0 % | 19-34 | 7-19 | 49,7 | 13-27 | 0,21 |
| **456** | **20,8 / 15,0** | **23,0 / 22,8 / 0 %** | **20-22** | **14-15** | **55,1** | **29-29** | **4,47** |
| 964 | 18,5 / 8,2 | 17,5 / 18,2 / 0 % | 18-20 | 14-14 | 52,2 | 29-118 | 1,21 |

El 456 es el mas robusto: sus cifras casi no cambian y el bolson es 13 veces mayor que el del 14. No es el de mas luz: el 14 da mas en el modelo, en LROC y en los pixeles de PGDA distintos de cero. El 14 queda como contraste: mas luz, pero fragil y sin confirmar a escala de pixel. Este criterio se fijo despues de ver los datos; no cambia ninguna cifra ni calculo. El campo `rank` de `data.json` sigue siendo el orden numerico por tiempo con ambos, no la recomendacion.
