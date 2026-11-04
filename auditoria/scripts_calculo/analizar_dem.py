#!/usr/bin/env python3
"""
analizar_dem.py  -  Solaris Core / MHD-INT
Lee un recorte LOLA (GeoTIFF, estereografica polar sur, metros), calcula la pendiente
por celda, la compara con el mapa de pendiente oficial de la NASA y marca las celdas
"seguras" segun un umbral de pendiente.

Uso (desde luna_polo_sur):
    python analizar_dem.py
    python analizar_dem.py --dem datos/Site04_surf.tif --slp datos/Site04_slp.tif --umbral 10

Salida (carpeta salida/):
    <nombre>_pendiente_calculada.tif   (GeoTIFF, grados)
    <nombre>_mapas.png                 (elevacion, pendiente propia, pendiente NASA, celdas seguras)
    <nombre>_resumen.txt

NOTAS:
 - El umbral de pendiente es un parametro de ESTE prototipo (por defecto 10 grados),
   no un requisito oficial de la NASA. Ajustalo segun lo que pida el reto.
 - La pendiente se calcula con diferencias centrales a la resolucion del DEM (5 m).
 - Unidades de alturas: metros (segun la documentacion del PGDA).
"""
import argparse
import math
import os
import sys

import numpy as np
import rasterio

R_LUNA_M = 1737400.0  # radio de la esfera de referencia del CRS del GeoTIFF


def pendiente_grados(z, res_x, res_y):
    dzdy, dzdx = np.gradient(z, res_y, res_x)  # filas (y), columnas (x)
    return np.degrees(np.arctan(np.hypot(dzdx, dzdy)))


def xy_a_latlon(x, y, radio=R_LUNA_M):
    """Estereografica polar SUR (origen lat -90, meridiano central 0) -> lat, lon (grados)."""
    rho = np.hypot(x, y)
    c = 2.0 * np.arctan(rho / (2.0 * radio))
    lat = -90.0 + np.degrees(c)
    lon = np.degrees(np.arctan2(x, y))
    return lat, lon


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dem", default="datos/Site04_surf.tif")
    ap.add_argument("--slp", default="datos/Site04_slp.tif", help="pendiente oficial NASA (opcional)")
    ap.add_argument("--umbral", type=float, default=10.0, help="pendiente maxima 'segura' en grados")
    ap.add_argument("--out", default="salida")
    a = ap.parse_args()

    if not os.path.isfile(a.dem):
        print("ERROR: no existe", a.dem)
        sys.exit(1)
    os.makedirs(a.out, exist_ok=True)
    nombre = os.path.splitext(os.path.basename(a.dem))[0]

    with rasterio.open(a.dem) as d:
        z = d.read(1).astype("float64")
        perfil = d.profile
        res_x, res_y = d.res
        bounds = d.bounds
        if d.nodata is not None and not np.isnan(d.nodata):
            z[z == d.nodata] = np.nan
        transform = d.transform

    L = []
    L.append(f"DEM: {a.dem}  |  {z.shape[1]} x {z.shape[0]} px  |  resolucion {res_x} x {res_y} m")
    L.append(f"Limites (m): izq {bounds.left}, abajo {bounds.bottom}, der {bounds.right}, arriba {bounds.top}")
    L.append(f"Celdas sin dato: {100*np.mean(np.isnan(z)):.2f} %")
    L.append(f"Elevacion (m): min {np.nanmin(z):.1f}, max {np.nanmax(z):.1f}, desnivel {np.nanmax(z)-np.nanmin(z):.1f}")

    # esquinas -> lat/lon (verifica la geometria)
    for nom, (x, y) in {"centro": ((bounds.left+bounds.right)/2, (bounds.bottom+bounds.top)/2),
                        "esquina sup-izq": (bounds.left, bounds.top)}.items():
        la, lo = xy_a_latlon(x, y)
        L.append(f"  {nom}: x={x:.0f} y={y:.0f} -> lat {la:.4f}, lon {lo:.3f}")
    la0, lo0 = xy_a_latlon(0.0, 0.0)
    L.append(f"  (x=0,y=0) -> lat {la0:.3f} (debe ser -90)")

    pend = pendiente_grados(z, res_x, res_y)
    L.append(f"Pendiente propia (grados): media {np.nanmean(pend):.2f}, mediana {np.nanmedian(pend):.2f}, "
             f"p95 {np.nanpercentile(pend,95):.2f}, max {np.nanmax(pend):.2f}")
    seguro = (pend <= a.umbral + 1e-6) & ~np.isnan(pend)
    valido = ~np.isnan(pend)
    L.append(f"Celdas con pendiente <= {a.umbral:g} grados: {100*seguro.sum()/valido.sum():.1f} % de las validas")

    # comparacion con la pendiente oficial
    slp = None
    if a.slp and os.path.isfile(a.slp):
        with rasterio.open(a.slp) as s:
            slp = s.read(1).astype("float64")
            if s.nodata is not None and not np.isnan(s.nodata):
                slp[slp == s.nodata] = np.nan
        if slp.shape == pend.shape:
            m = ~np.isnan(slp) & ~np.isnan(pend)
            L.append(f"Pendiente NASA: min {np.nanmin(slp):.2f}, max {np.nanmax(slp):.2f}, media {np.nanmean(slp):.2f}")
            if np.nanmax(slp) > 90:
                L.append("  AVISO: la pendiente NASA supera 90 -> sus unidades NO parecen grados; revisar la documentacion.")
            else:
                dif = np.abs(pend[m] - slp[m])
                corr = np.corrcoef(pend[m], slp[m])[0, 1]
                L.append(f"  Diferencia absoluta propia vs NASA: media {dif.mean():.2f}, p95 {np.percentile(dif,95):.2f} grados; "
                         f"correlacion {corr:.3f}")
                seg_n = (slp <= a.umbral + 1e-6) & m
                coincide = (seguro & seg_n).sum() / max(1, (seguro | seg_n).sum())
                L.append(f"  Coincidencia de celdas seguras (propia vs NASA): {100*coincide:.1f} %")
        else:
            L.append("Pendiente NASA con otra forma de matriz: no se compara.")
    else:
        L.append("No se encontro la pendiente NASA: sin comparacion.")

    txt = "\n".join(L)
    print(txt)
    with open(os.path.join(a.out, f"{nombre}_resumen.txt"), "w", encoding="utf-8") as f:
        f.write(txt + "\n")

    # GeoTIFF de pendiente propia
    perfil.update(dtype="float32", count=1, nodata=np.nan)
    with rasterio.open(os.path.join(a.out, f"{nombre}_pendiente_calculada.tif"), "w", **perfil) as dst:
        dst.write(pend.astype("float32"), 1)

    # mapas
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        ext = [bounds.left/1000, bounds.right/1000, bounds.bottom/1000, bounds.top/1000]
        paneles = [("Elevacion (m)", z, "terrain", None),
                   ("Pendiente propia (grados)", pend, "magma", (0, 30))]
        if slp is not None and slp.shape == pend.shape:
            paneles.append(("Pendiente NASA", slp, "magma", (0, 30)))
        paneles.append((f"Celdas con pendiente <= {a.umbral:g} grados", seguro.astype(float), "Greens", (0, 1)))
        n = len(paneles)
        fig, ax = plt.subplots(1, n, figsize=(5.2 * n, 5.4))
        for axi, (tit, dat, cm, lim) in zip(np.atleast_1d(ax), paneles):
            kw = {} if lim is None else {"vmin": lim[0], "vmax": lim[1]}
            im = axi.imshow(dat, extent=ext, cmap=cm, **kw)
            axi.set_title(tit, fontsize=10)
            axi.set_xlabel("x (km)")
            axi.set_ylabel("y (km)")
            fig.colorbar(im, ax=axi, shrink=0.75)
        fig.suptitle(f"{nombre}  -  estereografica polar sur (el polo esta en x=0, y=0)")
        fig.tight_layout()
        fig.savefig(os.path.join(a.out, f"{nombre}_mapas.png"), dpi=110)
    except Exception as e:
        print("Aviso: no se pudo generar el grafico:", e)

    print("\nListo. Archivos en:", os.path.abspath(a.out))


if __name__ == "__main__":
    main()
