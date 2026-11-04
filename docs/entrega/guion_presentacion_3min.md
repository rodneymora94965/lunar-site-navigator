# Presentación de 3 minutos

**Borrador.**

## 0:00–0:30. El problema

*[Mostrar `renders/luna_portada_v5_sitio456.png`.]*

En el polo sur lunar el Sol oscila apenas unos 1,6° sobre el horizonte. Una loma puede dejar un sitio sin energía, y la Tierra sube y baja cada unos 27 días. Si una misión se retrasa, hay que reevaluar sitio y fecha, y las herramientas actuales no lo hacen rápido.

## 0:30–1:15. La herramienta

*[Abrir `final.html`: primera pantalla y calendario de ventanas.]*

Lunar Site Navigator es un solo archivo web. Al abrirlo responde: en este sitio y esta fecha, ¿hay Sol y línea de vista? Una misión de 14 días al sitio 456 que llega el 21 de junio de 2030 tiene Sol y Tierra juntos el 4 % del tiempo. Si llega el 7 de agosto, el 73 %. El calendario muestra eso para cada día del año. Y una sola cifra no basta: mover el lander 100 m deja el Sol del 456 entre 20 y 22 %; en el sitio 14, el de más luz, lo mueve de 33 a 58 %.

## 1:15–2:15. Qué tan confiable es

- Las posiciones de Sol y Tierra coinciden con JPL Horizons en 20 fechas y 3 sitios.
- Contra el producto IMG de LROC, en 121 celdas, el sesgo es −0,3 puntos y el MAE 1,3, sin calibrar.
- Contra NASA PGDA, el MAE es 1,6 en Sol y 3,1 en Tierra.
- En nuestros 10 candidatos, el modelo da unos 7 puntos de más de Sol frente a LROC y unos 3 frente a PGDA.
- Eso mide cuánta luz hay, no cuándo llega. Para eso fijamos de antemano otra prueba con 5 fotogramas de LROC con fecha: MCC medio 0,74 frente al mínimo de 0,5, y mejor que los tres controles en los 5.
- Sus límites: 5 fechas de 2009 y solo Site04. No valida la predicción de 2026 a 2045, el modelo marca más puntos con luz que la imagen, y el primer fotograma queda por debajo de 0,5.
- La línea de vista no es un enlace de comunicación.
- Los 9 puntos en regiones que nombra la NASA vienen de un estudio publicado y van fuera del ranking. Tres no tienen comparación, y de Gerlache Rim 2 difiere mucho de LROC, sin causa demostrada.

## 2:15–3:00. Qué concluimos y para qué sirve

*[Mostrar `renders/luna_comparacion_4_sitios_v2.png`.]*

El modelo pasó dos comprobaciones de cuánta luz hay y una de cuándo llega. El sitio 456 es robusto: 21 % en el modelo, 15 % en LROC y 23 % en PGDA, con un bolsón de 4,47 km². El sitio 14 tiene más luz, pero es frágil: 0,33 km² y sin confirmar a escala de píxel.

Sirve para comparar sitios y fechas rápido, y para enseñar por qué el polo es tan difícil. No certifica un aterrizaje. Falta probar otras fechas y zonas, y la Tierra. Las reglas y los límites están publicados.

## Las 3 preguntas más difíciles

### 1. "¿Por qué eligen el 456 si el 14 tiene más del doble de luz?"

Porque preferimos cifras que se sostienen. El 14 tiene Sol 49 % y Sol con Tierra 26 %, frente a 21 % y 14 % del 456, y eso lo mostramos. Pero al mover el 14 ±100 m el Sol va de 33 a 58 %, su bolsón mide 0,33 km², LROC da 39 % frente a 49 % del modelo, y en PGDA 8 de los 9 píxeles en un radio de 100 m valen 0, aunque LROC no muestra esos ceros. Ese moteado parece un artefacto, sin causa demostrada; el 0 % que vimos primero en su píxel fue un error de geometría nuestro, ya corregido.

El criterio es un juicio nuestro y lo fijamos después de ver los datos; está escrito en la app. Tampoco es el mejor sitio del polo: es el más robusto de 10 candidatos en un recorte de 16 km, sin considerar ciencia ni riesgos de aterrizaje. IM-2 tiene más tiempo con Sol y Tierra (37 %), aunque calculado con terreno más grueso.

### 2. "¿Cómo saben que el modelo acierta cuándo llega la luz, y no solo cuánta?"

Lo probamos en 5 fechas de 2009, y solo eso. LROC y PGDA son promedios: si invierto los azimuts a propósito, la comparación con LROC casi no cambia. Por eso fijamos el criterio antes de abrir las imágenes: 5 fotogramas de LROC con fecha, elegidos sin mirarlos, un umbral que no usa el modelo y tres controles falsos (azimut espejado, Sol girado 180° y fecha +14,77 días). Aprobó: MCC por fotograma de +0,474 a +0,877, media 0,737, y en los 5 superó a los controles, que van de −0,30 a +0,36.

Lo que no prueba: son 5 fechas de 2009 y solo Site04, y no valida la predicción de 2026 a 2045 ni la visibilidad de la Tierra. El primer fotograma queda por debajo de 0,5 por sí solo; el criterio era el promedio. Y el modelo marca más puntos con luz que la imagen en los 5, 7881 frente a 5135 en total, sin causa demostrada.

### 3. "Antes tenían un sesgo de −17 y ahora de −0,3. ¿No ajustaron hasta que diera bien?"

No. El modelo no cambió: las cifras de esas celdas se calcularon antes de tener el IMG. El error estaba en cómo leíamos LROC: usábamos un GeoTIFF de navegación de 8 bits, estirado y saturado cerca de 45 %, como si 255 fuera 100 %. La etiqueta PDS del IMG dice que son porcentajes y no trae factor de escala, y no aplicamos ninguno. La misma corrección dejó a la vista un problema que antes no se veía: los 7 puntos de más en los candidatos. También lo publicamos.
