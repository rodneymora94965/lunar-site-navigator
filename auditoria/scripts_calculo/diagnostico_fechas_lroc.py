#!/usr/bin/env python3
"""Diagnostico posterior (no forma parte del criterio) de los falsos positivos de la prueba de fechas.

Se escribio DESPUES de ver el resultado. No cambia fotogramas, umbral, modelo ni veredicto, y no explica la causa:
solo describe cuan oscuros son los puntos que el modelo marca con luz y la imagen no, y cuan lejos estan de la luz observada.
Uso: python auditoria/scripts_calculo/diagnostico_fechas_lroc.py   Salida: auditoria/validacion/diagnostico_fechas_lroc.txt
"""
import csv, os, sys
from pathlib import Path
import numpy as np
from scipy import ndimage as ni
sys.path.insert(0, str(Path(__file__).resolve().parent))
import modelo_lroc_fechas as m
import validar_fechas_lroc as v
from lectura_productos import otsu

T = m.hz.load_terrain(center=(-1000.0, -7000.0), radius_m=215000)
X, Y = m.grid(step=200.0)
s = (len(np.unique(Y)), len(np.unique(X)))
out = ["Diagnostico posterior: no forma parte del criterio ni cambia el veredicto.", "valor = I/F del fotograma; dist = distancia a un punto con luz observada, en la malla de 200 m"]
tot = np.zeros(4, int)
for r in csv.DictReader(open(v.LISTA, encoding="utf-8")):
    val, hora, _ = v.leer_valores(v.DIR / (r["producto"] + ".IMG"), X, Y)
    um = otsu(val[np.isfinite(val)])
    O = (val > um).reshape(s)
    M = m.lit_state(T, X, Y, m.sun_vector(hora))[0].reshape(s)
    V = val.reshape(s)
    vp, fp, fn, vn = M & O, M & ~O, ~M & O, ~M & ~O
    tot += [vp.sum(), fp.sum(), fn.sum(), vn.sum()]
    d1 = ni.binary_dilation(O, structure=np.ones((3, 3)), iterations=1)
    d2 = ni.binary_dilation(O, structure=np.ones((3, 3)), iterations=2)
    out.append(f"{hora[:10]}  precision {vp.sum()/(vp.sum()+fp.sum()):.2f}  sensibilidad {vp.sum()/(vp.sum()+fn.sum()):.2f}  luz modelo/imagen {M.mean()/O.mean():.2f}  mediana VP {np.median(V[vp]):.4f} FP {np.median(V[fp]):.4f} VN {np.median(V[vn]):.4f} umbral {um:.4f}  FP sobre medio umbral {(V[fp]>um/2).mean():.2f}  FP a 200 m o menos {d1[fp].mean():.2f}, a 400 m o menos {d2[fp].mean():.2f}")
out.append(f"Total: VP {tot[0]} FP {tot[1]} FN {tot[2]} VN {tot[3]}; puntos con luz modelo {tot[0]+tot[1]}, imagen {tot[0]+tot[2]}; precision {tot[0]/(tot[0]+tot[1]):.3f}, sensibilidad {tot[0]/(tot[0]+tot[2]):.3f}")
(Path(v.OUT) / "diagnostico_fechas_lroc.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
