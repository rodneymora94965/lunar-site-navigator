# Paquete de auditoria

- `README.md`, `docs/`, `src/`, `tests/`, `data/`, `final.html`: la aplicacion y su documentacion.
- `auditoria/validacion/RESUMEN_VALIDACION.md`: **empieza aqui**. Que esta validado y que no.
- `auditoria/validacion/`: Horizons, producto IMG de LROC y su validacion (`validacion_lroc_img.*`), escala, diagnostico de candidatos y resultados historicos.
- `auditoria/scripts_calculo/`: scripts que generan los numeros, incluidos `bolsones.py`, `validar_horizons.py`, `validar_config_app.py`, `validar_lroc_img.py`, `diagnostico_candidatos_img.py` y `validar_pgda.py`.
- `auditoria/regiones/`: puntos representativos de 9 regiones, su comparacion con LROC y PGDA, y diagnostico.
- `auditoria/truncamiento/`: terreno mas alla de 304 km: CSV antes y despues, union de mapas y comprobacion de IM-2.
- `auditoria/validacion/prueba_fechas_lroc.md`: prueba de cuando llega la luz: ejecutada, aprueba con su criterio fijado de antemano, con sus limites.
- `docs/entrega/`: borradores de la entrega y `fuentes_cifras.md`, que indica de donde sale cada cifra.
- `auditoria/validacion/validacion_pgda.txt`, `diagnostico_sitio14_pgda.txt`, `candidatos_tres_fuentes.csv`: validacion contra PGDA, sitio 14 y comparacion de candidatos. `validar_pgda_img.py` es el script vigente; `validar_pgda.py` queda como alternativo para TIF.
- `auditoria/resultados_sitios.csv`: cifras actuales de 10 y 19 anos con rangos de +-100 m.
- `auditoria/antes/`: copia de datos, CSV, HTML, README y renders anteriores a estos cambios.
- `auditoria/entrega_anterior/`: textos y candidatos de entregas previas (cifras antiguas y lectura equivocada de LROC, solo como historia).
- `auditoria/_to_delete/`: dos archivos temporales vacios que se pueden borrar a mano.
- `auditoria/datos_externos/`: IMG y README de LROC tal como se descargaron; lugar para los mapas de PGDA pendientes (ver `scripts/obtener_datos.md`).
- `auditoria/*.png`: portada, comparacion de 4 sitios y toma del sitio 14, version anterior. Los renders vigentes del sitio 456 estan en `renders/`; los del 14 quedan respaldados en `auditoria/antes/ronda_render_456/`.
