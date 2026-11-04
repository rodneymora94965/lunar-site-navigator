# Estado Space Apps (Lunar Landing Site Navigator) - cierre del 29-oct-2026

## Hecho
- Pipeline en esta carpeta (DEM LOLA 5 m Site04 + 80 m, SPICE, LROC). Validacion aceptada por Roney: error medio 15.8 pp, sesgo -15.8 pp, r=0.99 (modelo anterior solo 5 m: 24.8 pp). El modelo subestima la luz; presentar como estimaciones conservadoras.
- Codex (v0.164.0, se lanza con `codex` dentro de esta carpeta) recalculo los 10 candidatos con terreno ancho: entrega_spaceapps/candidatos_finales.csv. Recomendado: sitio 14 (Sol 48.5 %, Tierra 52.3 %, ambos 26.8 %, noche 17.4 dias, pendiente 4.93). Alternativas: 456, 1358, 964. Criterio: max % conjunto, luego noche mas corta, luego pendiente. Ojo: el bolsón del 14 es chico (0.33 km2; 456 tiene 4.47, 964 1.21, 1358 0.21) y el criterio no lo considera.
- v1: entrega_spaceapps/animacion_10anios.mp4 (30 s, 2 fps). v2: entrega_spaceapps/v2/ (animacion_10anios_v2.mp4, portada_v2.png): mejor, pero la interpolacion mezclo tambien los textos (fecha y lecturas borrosas/dobles).
- v3 EN CURSO: entrega_spaceapps/v3/ tiene portada_v3.png (vista amplia 60 km + detalle + tabla con area). NO hay aun video v3, README_v3 ni informe_codex_v3.

## Pendiente para manana
1. Pedir a Codex (misma carpeta, a mano, sin pegar) que corrija la portada v3: subtitulos superpuestos; mapa de detalle desalineado; etiquetas del mapa amplio amontonadas; areas con 2 decimales; nota en espanol cortada. Luego revisar la portada ANTES de generar el video.
2. Generar animacion_10anios_v3.mp4 con textos nitidos (dibujarlos despues de interpolar; solo el mapa se interpola), 30 fps, 30-40 s. ffmpeg: C:\Users\RoneyMora\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe con -y -nostdin y limite de tiempo (sin -y se cuelga).
3. Revisar el informe de Codex: dice que el anillo oscuro es sombra del relieve; verificarlo (hipotesis mia sin confirmar: borde del crater Shackleton).
4. Aclarar en el video que "visible" = sobre el horizonte local (4.89 grados para el sitio 14).
5. Armar la entrega oficial: descripcion, video, repositorio; limite 15 nov; evento 14-15 nov en TEC Cartago.
6. Pendientes de Roney: equipo o solo; respuesta de los organizadores (lista de espera y uso de herramientas propias).

## Briefs de Codex (en esta carpeta)
brief_codex_animacion.md (v1), brief_codex_pulido.md (v2), brief_codex_v3.md (v3, incluye correccion del texto borroso en el punto 7). Codex tropieza con comandos de una linea en PowerShell y con parches sobre archivos que cambiaron: pedirle que escriba .py y relea el archivo antes de editar.
