# Auditoria independiente del proyecto luna_polo_sur

NO modifiques ni borres ningun archivo existente. Solo lee y ejecuta analisis de lectura. Si quieres probar algo, escribe en una carpeta nueva llamada revision_codex.

## Contexto
Calculo el % de tiempo con Sol sobre el DEM LOLA de 5 m del sitio Site04 (borde de Shackleton, datos/Site04_surf.tif) usando efemerides SPICE (kernels/) y un horizonte por trazado de rayos (calcular_candidatos.py). Lo valido contra el mapa LROC WAC (datos/WAC_POLE_ILL_PCT_SOUTH_100M.TIF, periodo 15-feb-2010 a 5-feb-2011).

Resultado: sesgo ~0 pero error absoluto medio ~24 puntos, con compresion hacia el medio (zonas oscuras salen mas claras y crestas mas oscuras).

Ya descarte: orientacion del DEM (probar_orientaciones.py), registro espacial/desfase (probar_registro.py), resolucion del horizonte, y cercania al borde del recorte (diagnostico_error.py).

## Tareas
1. Lee calcular_candidatos.py, validar_malla.py y los demas scripts. Busca errores de geometria, unidades, marcos de referencia (MOON_ME vs PA), proyeccion estereografica (x=rho*sin(lon), y=rho*cos(lon)), curvatura, altura del observador o muestreo temporal.
2. Dime que hipotesis alternativas explicarian el error y cual es la mas probable, con evidencia de los CSV en salida_2010/.
3. Verifica independientemente la conversion xy_a_latlon y la base local este/norte/arriba.
4. Propon y, si es posible, ejecuta una prueba que distinga entre causas (por ejemplo, terreno fuera del recorte vs. error de modelo).

Entregame un informe corto con hallazgos ordenados por probabilidad y que evidencia tiene cada uno.
