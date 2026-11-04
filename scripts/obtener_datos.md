# Como obtener los datos externos

El repositorio no incluye DEM ni kernels por su tamano. Colocalos en una carpeta y apunta a ella con `LUNAR_SOURCE_DIR` (por defecto `../luna_polo_sur`):

```
luna_polo_sur/
  datos/    Site04_surf.tif  LDEM_80S_80MPP_ADJ.TIF  WAC_POLE_ILL_PCT_SOUTH_100M.TIF  WAC_POLE_ILL_TWI_SOUTH_100M.TIF
  kernels/  naif0012.tls  de440s.bsp  pck00011.tpc  moon_de440_250416.tf  moon_pa_de440_200625.bpc
  salida_2010/validacion_ancho.csv   (celdas de validacion; copia en auditoria/validacion/)
```

## Kernels SPICE (NAIF, JPL)
Directorio: https://naif.jpl.nasa.gov/pub/naif/generic_kernels/
- `lsk/naif0012.tls`, `spk/planets/de440s.bsp`, `pck/pck00011.tpc`
- `fk/satellites/moon_de440_250416.tf`, `pck/moon_pa_de440_200625.bpc`

Comprueba la subcarpeta en el directorio: estas rutas se escribieron sin poder abrirlo desde el entorno de trabajo.

## Elevacion LOLA
- `Site04_surf.tif` (5 m/pixel) y `LDEM_80S_80MPP_ADJ.TIF` (80 m/pixel): productos LOLA de LRO. Busca esos nombres en NASA PGDA (https://pgda.gsfc.nasa.gov/) o PDS Geosciences. Los archivos se descargaron en una sesion anterior y el proyecto no guardo su URL exacta; confirmala y anotala aqui antes de publicar.

- `LDEM_60S_120MPP_ADJ.TIF` (120 m/pixel, 785 MB): `https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_60S_120MPP_ADJ.TIF`. Va en `luna_polo_sur/datos/`. Solo lo necesitan los sitios cuyos rayos de 200 km salen del mapa de 80 m, a mas de 104 km del polo; sin el, el calculo de esos sitios falla con un mensaje.

## Regiones
- `Landing_Sites.zip` (11,9 MB, MD5 `fdd66337acc737beff5ce56cfd2b50c0`): `https://zenodo.org/records/17084058/files/Landing_Sites.zip?download=1`. Va en `auditoria/datos_externos/Regiones/`. Solo hace falta para repetir `auditoria/scripts_calculo/seleccionar_regiones.py`, que necesita `pyshp`.

## LROC WAC (producto cientifico)
- `https://pds.lroc.im-ldi.com/data/LRO-L-LROC-5-RDR-V1.0/LROLRC_2001/DATA/BDR/WAC_POLE/WAC_POLE_ILL_PCT_SOUTH/WAC_POLE_ILL_PCT_SOUTH_100M.IMG`
- Ya hay copia en `auditoria/validacion/`. Se valida con `python auditoria/scripts_calculo/validar_lroc_img.py`.
- No uses el TIF de `EXTRAS/BROWSE` para medir: es de 8 bits, esta estirado y satura cerca de 45 %.

## Para terminar la validacion: colocar en `auditoria/datos_externos/`
1. `AVGVISIB_85S_060M_201608.IMG` y `.LBL`, y `AVGVISIB_85S_060M_201608_EARTH.IMG` y `.LBL`:
   `http://imbrium.mit.edu/EXTRAS/ILLUMINATION/`
   Luego: `python auditoria/scripts_calculo/validar_pgda_img.py` (el modelo ya esta en `auditoria/validacion/validacion_pgda_modelo.csv`). Para los TIF existe la alternativa `validar_pgda.py comparar`.
2. Los 5 fotogramas WAC de `auditoria/validacion/prueba_fechas_lroc.md` (prueba ya ejecutada; solo hacen falta para repetirla), en `auditoria/datos_externos/fotogramas_lroc/`.
   Luego: `python auditoria/scripts_calculo/validar_fechas_lroc.py`

## Regenerar
```bash
python -m pip install -r requirements.txt
LUNAR_SOURCE_DIR=/ruta/a/luna_polo_sur bash scripts/make_all.sh
```
La malla de +-100 m tarda unos 20 minutos en una PC modesta; `src/precalc.py heat 0 2` y `heat 1 2` la dividen y se puede reanudar.
