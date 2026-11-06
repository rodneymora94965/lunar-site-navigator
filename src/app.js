const T0 = Date.parse(DATA.t0), N = DATA.n, HOUR = 3600000, T_END = T0 + (N - 1) * HOUR;
const YEARS_TXT = Math.round(N / (365.25 * 24));

/* ---------- textos ---------- */
const I18N = {
 es:{
  title:"Navegador de Sitios Lunares",
  eyebrow:"NASA Space Apps 2026 · Reto Lunar Landing Site Navigator",
  h1:"Navegador de Sitios Lunares",
  sub:"Compara sitios de aterrizaje del polo sur lunar y fechas: cuándo hay Sol para generar energía y cuándo hay línea de vista a la Tierra, con el horizonte calculado desde el terreno LOLA.",
  loading:"Cargando efemérides y horizontes…",
  errNoDS:"Este navegador no puede descomprimir los datos (falta DecompressionStream). Abre la página en una versión reciente de Chrome, Edge, Safari o Firefox.",
  tSites:"Sitios (elige hasta 3)", grpCand:"10 candidatos del recorte Site04 (análisis propio, no selección de la NASA)", grpReal:"Aterrizaje real", grpRef:"Referencias educativas", grpCustom:"Tus coordenadas",
  hintSites:"Toca un sitio para añadirlo o quitarlo.", maxSites:"Ya hay 3 sitios. Quita uno antes de añadir otro.", minSites:"Debe quedar al menos un sitio.",
  tCustom:"Coordenadas propias", lLat:"Latitud (°, de −90 a −80)", lLon:"Longitud este (°)", add:"Añadir sitio",
  hintCustom:"Se calcula aquí mismo con un DEM reducido (20 m en el recorte Site04, 480 m fuera). En 4 sitios de prueba el resultado difirió hasta cerca de 1 punto del DEM completo. Es orientativo.",
  errCoord:"Coordenadas fuera de la cobertura del DEM (80°S a 90°S).", computing:"Calculando horizonte y malla de ±100 m…", edge:"Atención: a menos de 200 km del borde del DEM, el horizonte queda truncado hacia afuera.",
  customName:(n)=>`Personalizado ${n}`,
  tWhen:"Fecha y hora (UTC)", hintWhen:(a,b)=>`Datos horarios de ${a} a ${b}. Costa Rica es UTC−6.`,
  vidMain:"▶ Ver video explicativo (3:38, voz en español, subtítulos ES/EN)",vidAlt:"Versión con voz en inglés (3:28)",vidNote:"Video aparte: la app no lo necesita para funcionar. Las escenas 3D del video son ilustrativas.",
  tAns:"¿Hay Sol y Tierra aquí y ahora?",lAnsSite:"Sitio",lAnsAt:"Fecha elegida",ansGo:"Ver calendario de ventanas",
  ansNow:{both:"Hay Sol para generar energía y línea de vista a la Tierra.",onlySun:"Hay Sol para generar energía, pero sin línea de vista a la Tierra.",onlyEar:"Hay línea de vista a la Tierra, pero sin Sol.",none:"No hay Sol ni línea de vista a la Tierra."},
  ansEnds:(t)=>`Con ambos, esta ventana termina en ${t}.`,ansNext:(d,t)=>`Próxima ventana con ambos: ${d}, dentro de ${t}.`,ansNoNext:"No hay otra ventana con ambos en los datos.",ansNote:"Salida del modelo en este punto. Sirve para comparar, no certifica un aterrizaje.",
  tCal:"Calendario de ventanas",lCal:"Si la misión se mueve, ¿qué fechas siguen sirviendo? Cada celda es una misión: día de llegada (horizontal) y días que dura (vertical). Más intenso es más tiempo. Toca una celda.",lCalSite:"Sitio",lCalYear:"Año de llegada",lCalMet:"Mostrar tiempo con",calMets:["Sol y Tierra","Sol","Tierra"],calX:"Día de llegada",calY:"Días",calUse:"Ver esta fecha en los sitios",
  calRead:(d,n,x,ng)=>`Llegada ${d}, ${n} días: Sol ${x.sun} %, Tierra ${x.los} %, ambos ${x.both} %. Noche más larga dentro de la misión: ${ng}.`,calMax:(m,n,d,v)=>`Mayor tiempo con ${m} en misiones de ${n} días este año: llegada ${d}, ${v} %.`,calHint:"Misma cuenta del planificador, desde las 00:00 UTC del día de llegada y con la elevación mínima de la Tierra elegida arriba. Son cifras de un punto, sin el rango de ±100 m. Una fecha con mucho tiempo no garantiza nada más: no incluye temperatura, polvo ni riesgos de aterrizaje.",calAria:(s,y)=>`Calendario de ${s} en ${y}. Usa las flechas para moverte por las celdas.`,
  grpRegion:"Regiones que la NASA nombra como candidatas: punto representativo, fuera del ranking (no es una selección de la NASA)",
  regBadge:"Punto representativo · fuera del ranking",
  regNote:(s)=>`Sitio ${s.pub} publicado por Wueller et al. 2026, el más cercano al centro de los sitios que ese estudio propone en la región. No es una selección de la NASA ni describe toda la región: esos sitios abarcan unos ${dec(s.spread,0)} km. Terreno ${s.res}, sin 5 m.`,
  regPgda:(v)=>`PGDA en este píxel: Sol ${dec(v.pgda_sol,1)} % frente a ${dec(v.modelo_sol,1)} % del modelo; Tierra ${dec(v.pgda_tierra,1)} % frente a ${dec(v.modelo_tierra,1)} %.`,
  regLroc:(v)=>`LROC: ${dec(v.lroc,1)} % frente a ${dec(v.modelo_sol_2010,1)} % del modelo en 2010-2011.`,
  regBig:"Hay una diferencia grande, sin causa demostrada.",
  regNone:"Sin comparación: LROC cubre de 88 a 90°S y PGDA hasta 85°S, y este punto queda fuera. Estas cifras no están validadas.",
  regTime:"La prueba de hora y dirección de la luz solo cubre Site04, no este punto.",
  warnMix:"Aviso: esta tabla mezcla resoluciones. Los puntos de región usan terreno de 80 m y 120 m, y no compiten con los candidatos de 5 m, así que aquí no se marca el mejor valor.",
  play:"▶ Reproducir",pause:"⏸ Pausa",share:"Copiar enlace",copied:"Enlace copiado. Guarda sitios, fecha y ajustes.",copyFail:"No se pudo copiar solo. Selecciona y copia el enlace:",csvBtn:"Exportar CSV",lCsv:"Días a exportar",csvHint:"Datos por hora de los sitios elegidos, desde la fecha actual. Son salidas del modelo, no mediciones.",csvDone:(n)=>`CSV listo: ${n} filas.`,
  tDates:"Mismo sitio, dos fechas",lDates:"Compara qué cambia si la misión llega en otra fecha, con el mismo sitio y los mismos ajustes.",lDsSite:"Sitio",lDsA:"Fecha A (UTC)",lDsB:"Fecha B (UTC)",dsA:"Fecha A",dsB:"Fecha B",dsPano:"Panorama",dsNextSun:"Próximo cambio del Sol",dsNextEar:"Próximo cambio de la Tierra",dsSun30:(d)=>`Sol en los ${d} días siguientes`,dsEar30:(d)=>`Tierra en los ${d} días siguientes`,dsBoth30:(d)=>`Sol y Tierra en los ${d} días siguientes`,dsNight30:(d)=>`Noche más larga en esos ${d} días`,
  nav:{m29:"◀ día lunar",m1:"◀ 1 día",p1:"1 día ▶",p29:"día lunar ▶",win:"Próxima ventana con Sol y Tierra",ex:"Ejemplo 21-jun-2030"},
  lMargin:"Elevación mínima sobre el terreno para la Tierra", lArea:"Área de panel (m²)", lEff:"Eficiencia del panel (%)",
  hintPower:"Modelo simple de potencia: 1361 W/m² a 1 UA, panel vertical que sigue al Sol en azimut, fracción de disco visible sobre un horizonte recto. No incluye temperatura, polvo, baterías ni cableado. Área y eficiencia son supuestos ilustrativos que puedes cambiar; no es un diseño de misión.",
  sun:"Sol (centro del disco)", earth:"Línea de vista a la Tierra", visible:"VISIBLE", hidden:"TAPADO", noLos:"SIN LÍNEA DE VISTA",
  endsIn:"Termina en", startsIn:"Vuelve en", beyond:(y)=>`no ocurre antes de ${y}`,
  elSun:"Elevación real del Sol", mSun:"Margen del Sol sobre el terreno", frac:"Disco visible", pow:"Potencia del modelo",
  elEarth:"Elevación real de la Tierra", mEarth:"Margen de la Tierra sobre el terreno", azSun:"Azimut Sol", azEarth:"Azimut Tierra",
  pano:(ex)=>`Horizonte visto desde el sitio (azimut 0° = norte). El eje vertical está exagerado unas ${ex} veces respecto al horizontal. Los discos del Sol y la Tierra tienen tamaño mínimo visible y no están a escala.`,
  sunS:"Sol", earthS:"Tierra",
  tl:"Línea de tiempo de 60 días: 10 antes y 50 después (toca para saltar)", tlRows:["Sol","Tierra","Ambos"],
  ten:(y)=>`Resumen de ${y} años, en este punto (entre paréntesis, el rango si el punto se mueve ±100 m)`,
  sunPct:"Sol", earthPct:"Tierra", bothPct:"Ambos", night:"Noche más larga", noearth:"Más tiempo sin Tierra", pmean:"Potencia media del modelo",
  days:"d", hrs:"h", yrsGE:(y)=>`≥ ${y} años`,
  tCompare:"Comparación lado a lado", lCompare:"Misma fecha, hora y supuestos. En verde, el mejor valor de cada fila. Los porcentajes se redondean porque mover el punto unos metros los cambia mucho.",
  rows:{vis:"Estado ahora",solEl:"Elevación real del Sol",solM:"Margen del Sol sobre el terreno",frac:"Disco solar visible",pow:"Potencia del modelo ahora",tieEl:"Elevación real de la Tierra",tieM:"Margen de la Tierra sobre el terreno",sunP:(y)=>`Sol visible, ${y} años (±100 m)`,earP:(y)=>`Tierra visible, ${y} años (±100 m)`,bothP:(y)=>`Ambos, ${y} años (±100 m)`,night:"Noche más larga, días (±100 m)",noear:"Más tiempo sin Tierra, días",pm:"Potencia media del modelo",win60:"Horas con ambos, en la línea de tiempo",hz:"Horizonte local máximo (°)",area:"Área del bolsón (km²)",slope:"Pendiente media (°)"},
  both:"Sol y Tierra", onlySun:"Solo Sol", onlyEar:"Solo Tierra", none:"Ninguno",
  warn14:"Frágil y sin confirmar a escala de píxel: mover ±100 m da 33–58 % de Sol, y en PGDA sus vecinos valen 0 %, aunque LROC no muestra esos ceros. Para 2010-2011, LROC da 39 % y el modelo 49 %.",
  best:"Mejor de los 10 candidatos del recorte Site04, por robustez", contrast:"Contraste: más luz, pero frágil y sin confirmar a escala de píxel", passes:"Pasa el filtro de Sol y Tierra; menos robusto que el 456", fails:"No pasa el filtro de Sol y Tierra",
  tChoice:"Sitio principal y contraste", lChoice:"La recomendación premia las cifras que se sostienen, no la mayor cantidad de luz. Las cifras y los cálculos son los mismos para todos los sitios.",
  tMain:"Sitio 456: el más robusto", main:["<b>Se sostiene:</b> Sol 21 % (20–22 al mover ±100 m) y Sol con Tierra 14 % (14–15), en un bolsón de 4,47 km².","<b>Las fuentes se acercan:</b> Sol de 21 % en el modelo, 15 % en LROC (2010-2011) y 23 % en PGDA.","<b>Su costo:</b> menos luz que el 14 y una noche más larga, de 29 días."],
  tContrast:"Sitio 14: contraste, más luz pero frágil", contrastL:["<b>Su ventaja:</b> más luz y más tiempo con Sol y Tierra: Sol 49 %, ambos 26 %, noche de 17 días.","<b>Su debilidad:</b> bolsón de 0,33 km² y Sol de 33 a 58 % al mover ±100 m.","<b>Sin confirmar a escala de píxel:</b> en PGDA, 8 de los 9 píxeles en un radio de 100 m valen 0 %, aunque LROC no muestra esos ceros."],
  tCrit:"Criterio de selección", critList:["<b>Filtro:</b> Tierra de al menos 40 % en todo ±100 m, y Sol y Tierra juntos de al menos 10 % en el punto. Lo pasan 456, 14, 1358 y 964.","<b>Acuerdo</b> entre modelo, LROC y PGDA.","<b>Rango estrecho</b> al mover ±100 m.","<b>Bolsón amplio.</b>","<b>Noche corta,</b> solo como desempate."], critNote:"Este criterio es un juicio nuestro, fijado después de ver los datos. No es un requisito de la NASA y no considera ciencia ni riesgos de aterrizaje.",
  terrain:"terreno",
  tPlan:"Planificador de retraso", lPlan:"Mismo sitio, fechas distintas: ¿qué pasa si la misión se retrasa? Las cifras cubren desde el aterrizaje hasta el final de la misión.",
  lPsite:"Sitio", lLaunch:"Lanzamiento (UTC)", lCruise:"Días de viaje (supuesto)", lDur:"Duración en superficie (días)", lDelay:"Retraso (días)",
  planCols:["","Plan base","Con retraso"], planRows:{land:"Aterrizaje (UTC)",ls:"Al aterrizar",sun:"Sol visible",los:"Línea de vista a la Tierra",both:"Ambos",night:"Noche más larga",noe:"Más tiempo sin Tierra",en:"Energía del modelo",pm:"Potencia media del modelo"},
  capDelay:"Tiempo con Sol y Tierra a la vez durante la misión, según los días de retraso (toca para elegir)",
  planBest:(d,v,b)=>`En los próximos 60 días de retraso, el máximo es ${v} % con ${d} días de retraso. Plan base: ${b} %.`,
  outRange:"La misión se sale del rango de datos; ajusta la fecha o la duración.",
  tHeat:"Si muevo el lander 100 m", lHeat:"Cuánto cambia cada resultado al mover el punto hasta ±100 m. Una sola cifra no describe un sitio: esto muestra el rango.",
  lHsite:"Sitio", lHmet:"Métrica", mets:["Sol (%)","Tierra (%)","Ambos (%)","Noche más larga (días)"], heatMin:"Mínimo", heatPt:"En el punto", heatMax:"Máximo",
  heatNote:"Malla de 9×9 cada 25 m en el plano polar (+y arriba, +x derecha), observador a 5 m, paso de 3 h, sin margen de Tierra. El recuadro marca el punto central.",
  heat80:"Este sitio usa terreno de 80 m cerca del punto, que no resuelve cambios de 100 m: el mapa solo interpola.",
  heatRed:"Calculado con DEM reducido: solo orientativo.",
  t3d:"Vista 3D ilustrativa", l3d:"Escenas hechas con el relieve LOLA y las posiciones calculadas con SPICE. El lander, los continentes de la Tierra, las estrellas, las rocas y el micro-relieve son inventados. Las estrellas no se verían con esta exposición. Escenas y texturas creadas con apoyo de IA.",
  cap3d:(s)=>`Sitio ${s} · 21 jun 2030 11:00 UTC · relieve LOLA 5/80 m · rocas y micro-relieve ilustrativos`,
  capHero:"Toma ilustrativa del sitio 456 a 4,5 m de altura, 21 jun 2030, 11:00 UTC, con un módulo de aterrizaje ilustrativo. Las rocas, el micro-relieve, las estrellas y los continentes de la Tierra son inventados.",
  capVideo:"Un día lunar en el sitio 456, del 8 jun al 7 jul de 2030. Render ilustrativo, con textos en inglés; las alturas de Sol y Tierra sobre el horizonte son las del modelo.",
  tWhy:"Por qué un cambio pequeño lo cambia todo",
  why:[["El Sol casi no sube","En el polo el Sol oscila unos ±1,6° sobre el horizonte matemático a lo largo del año. Una loma de 5° basta para taparlo."],["La Tierra se mece","La libración mueve la Tierra unos ±7° con un ciclo de 27,3 días: cerca de 14 días arriba y 14 abajo en el polo."],["Pocos metros cuentan","Subir los paneles de 2 a 5 m en el sitio 14 pasa el Sol visible de unos 42 % a unos 49 % del tiempo en nuestros cálculos."],["El cráter lo decide",(y)=>`El centro de Shackleton no recibe Sol ni ve la Tierra en ${y} años, según este modelo: el horizonte local siempre queda más alto que ambos.`]],
  tAbout:"Cómo funciona y qué no hace", tMethod:"Método", tValid:"Qué está validado", tLimits:"Límites declarados",
  method:["Sol y Tierra: SPICE (NAIF/JPL), efemérides DE440 y marco lunar MOON_ME, cada hora desde el 1 nov 2026 durante 19 años.","Horizonte: trazado de rayos sobre DEM LOLA hacia 360 azimuts y hasta 200 km, con curvatura lunar, sin refracción, con observador a 5 m. Usa 5 m dentro del recorte Site04 (16×16 km), 80 m fuera y, más allá de 304 km del polo, 120 m.","Sol visible significa que el centro del disco está sobre ese horizonte. La energía del modelo sí usa la fracción de disco visible.","Las cifras se calculan en esta página a partir de esos datos."],
  valid:["<b>Efemérides:</b> coinciden con JPL Horizons en 20 fechas y 3 sitios (diferencia máxima menor a 0,0001°). Valida la posición de Sol y Tierra, no el terreno.","<b>Horizonte:</b> la app reproduce soluciones analíticas sintéticas en las pruebas automáticas.","<b>Cantidad de luz contra LROC WAC</b> (producto IMG, 2010-2011, 100 m/píxel, umbral conservador de iluminación), con la configuración de la app y sin calibrar: en 121 celdas de Site04, sesgo −0,3 puntos, MAE 1,3, correlación 0,985, pendiente 1,00.","<b>En los 10 candidatos el modelo sobreestima unos 7 puntos</b> (sesgo +7,4, MAE 7,4, correlación 0,90). Una parte viene del tipo de terreno elegido: son bolsones planos, y otros 40 bolsones no elegidos también dan más luz (+3,9). Otra parte viene de comparar un punto con terreno de 5 m contra un píxel de 100 m: promediar el píxel baja a +6,2. El resto sigue sin explicar.","<b>Hora y dirección de la luz del Sol:</b> aprueba una prueba fijada de antemano, contra 5 fotogramas LROC WAC con fecha, sin calibrar. MCC (0 = azar, 1 = perfecto) por fotograma: +0,474, +0,877, +0,815, +0,777 y +0,743; media 0,737 frente al mínimo de 0,5. En los 5 supera a tres controles (azimut espejado, Sol girado 180° y fecha +14,77 días), cuyo MCC va de −0,30 a +0,36.","<b>Sol y Tierra contra NASA PGDA</b> (cálculo separado con datos LOLA, la misma fuente de nuestro terreno; 60 m/píxel, promedio de 18,6 años, sin calibrar), configuración de la app. En 121 celdas: Sol sesgo −0,3, MAE 1,6, correlación 0,965; Tierra sesgo −1,3, MAE 3,1, correlación 0,961. En 10 candidatos: Sol sesgo +3,1, MAE 3,8, correlación 0,946; Tierra sesgo −2,2, MAE 2,6, correlación 0,994."],
  limits:["<b>La prueba de hora y dirección es acotada:</b> abarca 5 fechas de 2009 y solo Site04, con el Sol a unos 1,3–1,6° de altura. No valida la predicción de 2026 a 2045, y ninguna prueba con imágenes cubre la visibilidad de la Tierra.","<b>El modelo tiende a dar más luz que la imagen:</b> marca más puntos con luz en los 5 fotogramas (7881 frente a 5135 en total; 2797 falsos positivos y 51 falsos negativos), sin causa demostrada. El primer fotograma (2009-10-22) queda por debajo de 0,5 por sí solo (MCC +0,474); el criterio era el promedio.","<b>Los promedios de LROC y PGDA</b> miden cuánta luz hay, no cuándo llega: esa comparación casi no cambia al invertir los azimuts.","<b>El sitio 14 es frágil y no está confirmado a escala de píxel.</b> Está a unos 660 m del polo. PGDA da 41,6 % de Sol y 55,5 % de Tierra en su píxel exacto; un 0 % anterior fue un error de geometría nuestro, ya corregido. Lo que persiste: 8 de los 9 píxeles en un radio de 100 m valen 0 % en PGDA y LROC no muestra esos ceros, lo que parece un artefacto sin causa demostrada; además, mover ±100 m da 33–58 % de Sol, y LROC da 39 % frente a 49 % del modelo en 2010-2011.","<b>Línea de vista no es comunicación:</b> no modela estaciones en Tierra, antena ni enlace.","<b>El Sol cuenta como punto</b> en los porcentajes. Contar su borde sube los valores (en el sitio 14, unos 6 puntos).","<b>Un punto no es un sitio:</b> en el sitio 14, mover ±100 m cambia mucho el Sol visible. Usa los rangos.","<b>El observador a 5 m</b> es un supuesto; 2 m o 10 m dan cifras distintas.","<b>Los candidatos</b> son nuestro análisis dentro de un recorte de 16 km. No son selecciones de la NASA ni consideran ciencia o riesgos de aterrizaje.","<b>IM-2:</b> coordenadas de LROC; aterrizó dentro de un cráter de unos 20 m que el terreno de 80 m no resuelve.","<b>Las referencias:</b> Shackleton e IM-2 usan 80 m cerca del punto; el Polo Sur usa 5 m cerca y 80 m lejos.","<b>Herramienta educativa y de exploración:</b> sirve para comparar sitios, no para certificarlos."],
  foot:"Solaris Core · Roney Rigg Mora. Datos: NASA SPICE/NAIF (DE440), LOLA/LRO y LROC (PDS). Desarrollado con apoyo de IA, declarado en el README. Sin red funciona con fuentes de respaldo.",
  kinds:{region:"Región",cand:"Candidato",real:"Aterrizaje real",ref:"Referencia",custom:"Personalizado"}
 },
 en:{
  title:"Lunar Site Navigator",
  eyebrow:"NASA Space Apps 2026 · Lunar Landing Site Navigator challenge",
  h1:"Lunar Site Navigator",
  sub:"Compare lunar south pole landing sites and dates: when there is Sun for power and when there is line of sight to Earth, with the horizon computed from LOLA terrain.",
  loading:"Loading ephemerides and horizons…",
  errNoDS:"This browser cannot decompress the data (DecompressionStream is missing). Open the page in a recent Chrome, Edge, Safari or Firefox.",
  tSites:"Sites (pick up to 3)", grpCand:"10 candidates in the Site04 tile (our analysis, not a NASA selection)", grpReal:"Actual landing", grpRef:"Educational references", grpCustom:"Your coordinates",
  hintSites:"Tap a site to add or remove it.", maxSites:"3 sites are already selected. Remove one before adding another.", minSites:"At least one site must remain.",
  tCustom:"Custom coordinates", lLat:"Latitude (°, −90 to −80)", lLon:"East longitude (°)", add:"Add site",
  hintCustom:"Computed here with a reduced DEM (20 m in the Site04 tile, 480 m elsewhere). In 4 test sites the result differed from the full DEM by up to about 1 point. Treat it as indicative.",
  errCoord:"Coordinates outside DEM coverage (80°S to 90°S).", computing:"Computing horizon and ±100 m grid…", edge:"Warning: within 200 km of the DEM edge the horizon is truncated outward.",
  customName:(n)=>`Custom ${n}`,
  tWhen:"Date and time (UTC)", hintWhen:(a,b)=>`Hourly data from ${a} to ${b}. Costa Rica is UTC−6.`,
  vidMain:"▶ Watch the explainer video (3:28, English voice, EN/ES subtitles)",vidAlt:"Spanish-voice version (3:38)",vidNote:"Separate file: the app does not need it to work. The 3D scenes in the video are illustrative.",
  tAns:"Is there Sun and Earth here and now?",lAnsSite:"Site",lAnsAt:"Chosen date",ansGo:"See window calendar",
  ansNow:{both:"There is Sun for power and line of sight to Earth.",onlySun:"There is Sun for power, but no line of sight to Earth.",onlyEar:"There is line of sight to Earth, but no Sun.",none:"There is no Sun and no line of sight to Earth."},
  ansEnds:(t)=>`With both, this window ends in ${t}.`,ansNext:(d,t)=>`Next window with both: ${d}, in ${t}.`,ansNoNext:"There is no other window with both in the data.",ansNote:"Model output at this point. Use it to compare; it does not certify a landing.",
  tCal:"Window calendar",lCal:"If the mission moves, which dates still work? Each cell is a mission: arrival day (across) and days it lasts (up). Stronger color means more time. Tap a cell.",lCalSite:"Site",lCalYear:"Arrival year",lCalMet:"Show time with",calMets:["Sun and Earth","Sun","Earth"],calX:"Arrival day",calY:"Days",calUse:"See this date in the sites",
  calRead:(d,n,x,ng)=>`Arrival ${d}, ${n} days: Sun ${x.sun} %, Earth ${x.los} %, both ${x.both} %. Longest night during the mission: ${ng}.`,calMax:(m,n,d,v)=>`Most time with ${m} in ${n}-day missions this year: arrival ${d}, ${v} %.`,calHint:"Same count as the planner, from 00:00 UTC on the arrival day and with the minimum Earth elevation chosen above. These are single-point figures, without the ±100 m range. A date with a lot of time guarantees nothing else: temperature, dust and landing risks are not included.",calAria:(s,y)=>`Calendar for ${s} in ${y}. Use the arrow keys to move across cells.`,
  grpRegion:"Regions NASA names as candidates: representative point, outside the ranking (not a NASA selection)",
  regBadge:"Representative point · outside the ranking",
  regNote:(s)=>`Site ${s.pub} published by Wueller et al. 2026, the closest to the center of the sites that study proposes in the region. It is not a NASA selection and does not describe the whole region: those sites span about ${dec(s.spread,0)} km. Terrain ${s.res}, no 5 m.`,
  regPgda:(v)=>`PGDA at this pixel: Sun ${dec(v.pgda_sol,1)} % against the model's ${dec(v.modelo_sol,1)} %; Earth ${dec(v.pgda_tierra,1)} % against ${dec(v.modelo_tierra,1)} %.`,
  regLroc:(v)=>`LROC: ${dec(v.lroc,1)} % against the model's ${dec(v.modelo_sol_2010,1)} % for 2010-2011.`,
  regBig:"There is a large difference, with no proven cause.",
  regNone:"No comparison: LROC covers 88 to 90°S and PGDA reaches 85°S, and this point lies outside both. These figures are not validated.",
  regTime:"The test of time and direction of light covers only Site04, not this point.",
  warnMix:"Warning: this table mixes resolutions. Region points use 80 m and 120 m terrain and do not compete with the 5 m candidates, so no best value is marked here.",
  play:"▶ Play",pause:"⏸ Pause",share:"Copy link",copied:"Link copied. It keeps sites, date and settings.",copyFail:"Could not copy automatically. Select and copy the link:",csvBtn:"Export CSV",lCsv:"Days to export",csvHint:"Hourly data for the chosen sites, from the current date. These are model outputs, not measurements.",csvDone:(n)=>`CSV ready: ${n} rows.`,
  tDates:"Same site, two dates",lDates:"Compare what changes if the mission arrives on another date, with the same site and settings.",lDsSite:"Site",lDsA:"Date A (UTC)",lDsB:"Date B (UTC)",dsA:"Date A",dsB:"Date B",dsPano:"Panorama",dsNextSun:"Next Sun change",dsNextEar:"Next Earth change",dsSun30:(d)=>`Sun in the next ${d} days`,dsEar30:(d)=>`Earth in the next ${d} days`,dsBoth30:(d)=>`Sun and Earth in the next ${d} days`,dsNight30:(d)=>`Longest night in those ${d} days`,
  nav:{m29:"◀ lunar day",m1:"◀ 1 day",p1:"1 day ▶",p29:"lunar day ▶",win:"Next Sun and Earth window",ex:"Example 21 Jun 2030"},
  lMargin:"Minimum Earth elevation above terrain", lArea:"Panel area (m²)", lEff:"Panel efficiency (%)",
  hintPower:"Simple power model: 1361 W/m² at 1 AU, vertical panel tracking the Sun in azimuth, visible disc fraction over a straight horizon. It excludes temperature, dust, batteries and wiring. Area and efficiency are illustrative assumptions you can change; this is not a mission design.",
  sun:"Sun (disc center)", earth:"Line of sight to Earth", visible:"VISIBLE", hidden:"BLOCKED", noLos:"NO LINE OF SIGHT",
  endsIn:"Ends in", startsIn:"Returns in", beyond:(y)=>`does not occur before ${y}`,
  elSun:"True Sun elevation", mSun:"Sun margin above terrain", frac:"Visible disc", pow:"Model power",
  elEarth:"True Earth elevation", mEarth:"Earth margin above terrain", azSun:"Sun azimuth", azEarth:"Earth azimuth",
  pano:(ex)=>`Horizon seen from the site (azimuth 0° = north). The vertical axis is exaggerated about ${ex} times relative to the horizontal. Sun and Earth discs have a minimum visible size and are not to scale.`,
  sunS:"Sun", earthS:"Earth",
  tl:"60-day timeline: 10 before and 50 after (tap to jump)", tlRows:["Sun","Earth","Both"],
  ten:(y)=>`${y}-year summary at this point (in parentheses, the range if the point moves ±100 m)`,
  sunPct:"Sun", earthPct:"Earth", bothPct:"Both", night:"Longest night", noearth:"Longest time without Earth", pmean:"Mean model power",
  days:"d", hrs:"h", yrsGE:(y)=>`≥ ${y} years`,
  tCompare:"Side-by-side comparison", lCompare:"Same date, time and assumptions. Green marks the best value in each row. Percentages are rounded because moving the point a few meters changes them a lot.",
  rows:{vis:"State now",solEl:"True Sun elevation",solM:"Sun margin above terrain",frac:"Visible solar disc",pow:"Model power now",tieEl:"True Earth elevation",tieM:"Earth margin above terrain",sunP:(y)=>`Sun visible, ${y} years (±100 m)`,earP:(y)=>`Earth visible, ${y} years (±100 m)`,bothP:(y)=>`Both, ${y} years (±100 m)`,night:"Longest night, days (±100 m)",noear:"Longest time without Earth, days",pm:"Mean model power",win60:"Hours with both, on the timeline",hz:"Max local horizon (°)",area:"Landing pocket area (km²)",slope:"Mean slope (°)"},
  both:"Sun and Earth", onlySun:"Sun only", onlyEar:"Earth only", none:"Neither",
  warn14:"Fragile and not confirmed at pixel scale: moving ±100 m gives 33–58 % Sun, and in PGDA its neighbors read 0 %, although LROC does not show those zeros. For 2010-2011, LROC gives 39 % and the model 49 %.",
  best:"Best of the 10 candidates in the Site04 tile, for robustness", contrast:"Contrast: more light, but fragile and not confirmed at pixel scale", passes:"Passes the Sun and Earth filter; less robust than 456", fails:"Does not pass the Sun and Earth filter",
  tChoice:"Main site and contrast", lChoice:"The recommendation rewards figures that hold up, not the most light. Figures and calculations are the same for every site.",
  tMain:"Site 456: the most robust", main:["<b>It holds up:</b> Sun 21 % (20–22 when moved ±100 m) and Sun with Earth 14 % (14–15), in a 4.47 km² pocket.","<b>Sources come close:</b> Sun of 21 % in the model, 15 % in LROC (2010-2011) and 23 % in PGDA.","<b>Its cost:</b> less light than 14 and a longer night, 29 days."],
  tContrast:"Site 14: contrast, more light but fragile", contrastL:["<b>Its advantage:</b> more light and more time with Sun and Earth: Sun 49 %, both 26 %, night of 17 days.","<b>Its weakness:</b> a 0.33 km² pocket and Sun from 33 to 58 % when moved ±100 m.","<b>Not confirmed at pixel scale:</b> in PGDA, 8 of the 9 pixels within 100 m read 0 %, although LROC does not show those zeros."],
  tCrit:"Selection criterion", critList:["<b>Filter:</b> Earth of at least 40 % throughout ±100 m, and Sun and Earth together at least 10 % at the point. 456, 14, 1358 and 964 pass.","<b>Agreement</b> among model, LROC and PGDA.","<b>Narrow range</b> when moved ±100 m.","<b>Large pocket.</b>","<b>Short night,</b> only as a tiebreaker."], critNote:"This criterion is our own judgment, set after seeing the data. It is not a NASA requirement and ignores science and landing risks.",
  terrain:"terrain",
  tPlan:"Delay planner", lPlan:"Same site, different dates: what happens if the mission slips? Figures cover landing through end of mission.",
  lPsite:"Site", lLaunch:"Launch (UTC)", lCruise:"Cruise days (assumption)", lDur:"Surface duration (days)", lDelay:"Delay (days)",
  planCols:["","Base plan","With delay"], planRows:{land:"Landing (UTC)",ls:"At landing",sun:"Sun visible",los:"Line of sight to Earth",both:"Both",night:"Longest night",noe:"Longest time without Earth",en:"Model energy",pm:"Mean model power"},
  capDelay:"Time with both Sun and Earth during the mission, by days of delay (tap to choose)",
  planBest:(d,v,b)=>`Over the next 60 days of delay, the maximum is ${v} % with ${d} days of delay. Base plan: ${b} %.`,
  outRange:"The mission falls outside the data range; adjust the date or duration.",
  tHeat:"If I move the lander 100 m", lHeat:"How much each result changes when the point moves up to ±100 m. A single figure does not describe a site: this shows the range.",
  lHsite:"Site", lHmet:"Metric", mets:["Sun (%)","Earth (%)","Both (%)","Longest night (days)"], heatMin:"Minimum", heatPt:"At the point", heatMax:"Maximum",
  heatNote:"9×9 grid every 25 m in the polar plane (+y up, +x right), observer at 5 m, 3-hour step, no Earth margin. The outlined cell is the center point.",
  heat80:"This site uses 80 m terrain near the point, which does not resolve 100 m moves: the map only interpolates.",
  heatRed:"Computed with the reduced DEM: indicative only.",
  t3d:"Illustrative 3D view", l3d:"Scenes built from LOLA relief and SPICE positions. The lander, Earth's continents, stars, rocks and micro-relief are invented. Stars would not be visible at this exposure. Scenes and textures made with AI assistance.",
  cap3d:(s)=>`Site ${s} · 21 Jun 2030 11:00 UTC · LOLA relief 5/80 m · rocks and micro-relief illustrative`,
  capHero:"Illustrative shot of site 456 from 4.5 m above ground, 21 Jun 2030, 11:00 UTC, with an illustrative lander. The rocks, micro-relief, stars and Earth's continents are invented.",
  capVideo:"One lunar day at site 456, 8 Jun to 7 Jul 2030. Illustrative render; the Sun and Earth heights above the horizon are the model's.",
  tWhy:"Why a small change changes everything",
  why:[["The Sun barely rises","At the pole the Sun swings about ±1.6° around the mathematical horizon during the year. A 5° ridge is enough to hide it."],["Earth wobbles","Libration moves Earth about ±7° with a 27.3-day cycle: about 14 days up and 14 down at the pole."],["A few meters matter","Raising the panels from 2 to 5 m at site 14 moves Sun visibility from about 42 % to about 49 % of the time in our calculations."],["The crater decides",(y)=>`In this model, the center of Shackleton gets no Sun and sees no Earth in ${y} years: the local horizon always stays above both.`]],
  tAbout:"How it works and what it does not do", tMethod:"Method", tValid:"What is validated", tLimits:"Stated limits",
  method:["Sun and Earth: SPICE (NAIF/JPL), DE440 ephemerides and the MOON_ME lunar frame, hourly from 1 Nov 2026 for 19 years.","Horizon: ray tracing over the LOLA DEM toward 360 azimuths out to 200 km, with lunar curvature, no refraction and a 5 m observer. It uses 5 m inside the Site04 tile (16×16 km), 80 m outside and, beyond 304 km from the pole, 120 m.","Sun visible means the disc center is above that horizon. Model energy does use the visible disc fraction.","Figures are computed on this page from those data."],
  valid:["<b>Ephemerides:</b> match JPL Horizons at 20 dates and 3 sites (maximum difference below 0.0001°). This validates Sun and Earth position, not terrain.","<b>Horizon:</b> the code reproduces synthetic analytic solutions in the automated tests.","<b>Amount of light against LROC WAC</b> (IMG product, 2010-2011, 100 m/pixel, conservative illumination threshold), with the app's configuration and no calibration: in 121 Site04 cells, bias −0.3 points, MAE 1.3, correlation 0.985, slope 1.00.","<b>In the 10 candidates the model overestimates by about 7 points</b> (bias +7.4, MAE 7.4, correlation 0.90). Part comes from the terrain chosen: they are flat pockets, and 40 other unselected pockets also show more light (+3.9). Part comes from comparing a point on 5 m terrain with a 100 m pixel: averaging the pixel lowers it to +6.2. The rest remains unexplained.","<b>Time and direction of sunlight:</b> passes a test fixed in advance, against 5 dated LROC WAC frames, with no calibration. MCC (0 = chance, 1 = perfect) by frame: +0.474, +0.877, +0.815, +0.777 and +0.743; mean 0.737 against the required 0.5. In all 5 it beats three controls (mirrored azimuth, Sun turned 180°, date +14.77 days), whose MCC runs from −0.30 to +0.36.","<b>Sun and Earth against NASA PGDA</b> (a separate calculation from LOLA data, the same source as our terrain; 60 m/pixel, 18.6-year average, no calibration), app configuration. In 121 cells: Sun bias −0.3, MAE 1.6, correlation 0.965; Earth bias −1.3, MAE 3.1, correlation 0.961. In 10 candidates: Sun bias +3.1, MAE 3.8, correlation 0.946; Earth bias −2.2, MAE 2.6, correlation 0.994."],
  limits:["<b>The test of time and direction is narrow:</b> it covers 5 dates in 2009 and only Site04, with the Sun about 1.3–1.6° high. It does not validate the 2026–2045 prediction, and no image test covers Earth visibility.","<b>The model tends to give more light than the images:</b> it marks more lit points in all 5 frames (7,881 against 5,135 in total; 2,797 false positives and 51 false negatives), with no proven cause. The first frame (2009-10-22) stays below 0.5 on its own (MCC +0.474); the criterion applied to the mean.","<b>LROC and PGDA averages</b> measure how much light there is, not when it arrives: that comparison barely changes when azimuths are mirrored.","<b>Site 14 is fragile and not confirmed at pixel scale.</b> It lies about 660 m from the pole. PGDA gives 41.6 % Sun and 55.5 % Earth at its exact pixel; an earlier 0 % was our own geometry error, now corrected. What remains: 8 of the 9 pixels within 100 m read 0 % in PGDA and LROC does not show those zeros, which looks like an artifact with no proven cause; also, moving ±100 m gives 33–58 % Sun, and LROC gives 39 % against the model's 49 % for 2010-2011.","<b>Line of sight is not communication:</b> ground stations, antenna and link are not modeled.","<b>The Sun counts as a point</b> in the percentages. Counting its limb raises the values (about 6 points at site 14).","<b>A point is not a site:</b> at site 14, moving ±100 m changes Sun visibility a lot. Use the ranges.","<b>The 5 m observer</b> is an assumption; 2 m or 10 m give different figures.","<b>The candidates</b> are our own analysis inside a 16 km tile. They are not NASA selections and ignore science and landing risks.","<b>IM-2:</b> LROC coordinates; it landed inside a crater about 20 m wide that 80 m terrain does not resolve.","<b>References:</b> Shackleton and IM-2 use 80 m near the point; the South Pole uses 5 m near and 80 m far.","<b>Educational and exploratory tool:</b> use it to compare sites, not to certify them."],
  foot:"Solaris Core · Roney Rigg Mora. Data: NASA SPICE/NAIF (DE440), LOLA/LRO and LROC (PDS). Developed with AI assistance, declared in the README. Offline it works with fallback fonts.",
  kinds:{region:"Region",cand:"Candidate",real:"Actual landing",ref:"Reference",custom:"Custom"}
 }
};
let lang = (navigator.language||'es').toLowerCase().startsWith('en') ? 'en' : 'es';
try{ const s=localStorage.getItem('nav-lang'); if(s==='es'||s==='en') lang=s; }catch(e){}
const L = ()=>I18N[lang];
const $ = (id)=>document.getElementById(id);
const END_YEAR = new Date(T_END).getUTCFullYear();

/* ---------- datos ---------- */
function b64bytes(s){const b=atob(s);const u=new Uint8Array(b.length);for(let i=0;i<b.length;i++)u[i]=b.charCodeAt(i);return u;}
async function inflate(bytes){const ds=new DecompressionStream('deflate');const w=ds.writable.getWriter();w.write(bytes);w.close();return new Uint8Array(await new Response(ds.readable).arrayBuffer());}
async function series(pair,scale){const raw=await inflate(b64bytes(pair[1]));const d=new Int16Array(raw.buffer,raw.byteOffset,raw.byteLength>>1);const out=new Float64Array(d.length+1);let a=pair[0];out[0]=a/scale;for(let i=0;i<d.length;i++){a+=d[i];out[i+1]=a/scale;}return out;}
async function grid(g){const raw=await inflate(b64bytes(g.z));const d=new Int16Array(raw.buffer,raw.byteOffset,raw.byteLength>>1);const Z=new Float32Array(d.length);for(let r=0,k=0;r<g.h;r++)for(let c=0;c<g.w;c++,k++)Z[k]=d[k]+(r?Z[k-g.w]:0);return {x0:g.x0,y0:g.y0,d:g.d,h:g.h,w:g.w,Z};}
const EPH={}; let DEM=null;
async function loadEph(){const e=DATA.eph;EPH.slat=await series(e.slat,1000);EPH.slon=await series(e.slon,1000);EPH.sd=await series(e.sd,1e5);EPH.elat=await series(e.elat,1000);EPH.elon=await series(e.elon,1000);EPH.ed=await series(e.ed,1);}
async function loadDEM(){if(!DEM)DEM={fine:await grid(DATA.dem.fine),wide:await grid(DATA.dem.wide)};return DEM;}
const AU=149597870.7;

function prep(s){
  if(s.ready)return;
  if(!s.H){const hzb=b64bytes(s.hz);const h16=new Int16Array(hzb.buffer);s.H=new Float32Array(360);for(let i=0;i<360;i++)s.H[i]=h16[i]/100;}
  const b=CORE.basis(s.lat,s.lon);
  s.SA=new Float32Array(N);s.SE=new Float32Array(N);s.TA=new Float32Array(N);s.TE=new Float32Array(N);s.rs=new Float32Array(N);s.rt=new Float32Array(N);s.f=new Float32Array(N);s.pw=new Float32Array(N);
  s.pE=new Float64Array(N+1);
  for(let i=0;i<N;i++){
    const sd=EPH.sd[i],sv=CORE.azEl(b,EPH.slat[i],EPH.slon[i],sd*AU),ev=CORE.azEl(b,EPH.elat[i],EPH.elon[i],EPH.ed[i]);
    s.SA[i]=sv[0];s.SE[i]=sv[1];s.TA[i]=ev[0];s.TE[i]=ev[1];
    const m=sv[1]-CORE.interpHz(s.H,sv[0]);s.rs[i]=m;s.rt[i]=ev[1]-CORE.interpHz(s.H,ev[0]);
    const f=CORE.discFraction(m,CORE.sunRadiusDeg(sd));s.f[i]=f;const p=CORE.powerW(sd,f,sv[1],1,1);s.pw[i]=p;s.pE[i+1]=s.pE[i]+p;
  }
  s.hzmax=Math.max(...s.H);s.sv=new Uint8Array(N);s.tv=new Uint8Array(N);s.pS=new Int32Array(N+1);s.pT=new Int32Array(N+1);s.pB=new Int32Array(N+1);s.ready=true;
  s.mDone=null;masks(s);
}
function masks(s){
  if(s.mDone===S.margin)return;
  for(let i=0;i<N;i++){const a=s.rs[i]>0?1:0,c=s.rt[i]>S.margin?1:0;s.sv[i]=a;s.tv[i]=c;s.pS[i+1]=s.pS[i]+a;s.pT[i+1]=s.pT[i]+c;s.pB[i+1]=s.pB[i]+(a&c);}
  s.stat={sun:100*s.pS[N]/N,earth:100*s.pT[N]/N,both:100*s.pB[N]/N,night:CORE.longestFalse(s.sv,0,N)/24,noearth:CORE.longestFalse(s.tv,0,N)/24,pm:s.pE[N]/N};
  s.mDone=S.margin;
}
function site(id){const s=S.sites[id];prep(s);masks(s);return s;}

/* ---------- estado ---------- */
const MAIN_SITE='456', CONTRAST_SITE='14';
const S = {sel:[MAIN_SITE,CONTRAST_SITE,'1358'], idx:0, sites:{}, margin:0, area:1, eff:.30, nCustom:0, heatId:MAIN_SITE, heatMet:0, planSite:MAIN_SITE, dl:7, playing:false, dsSite:MAIN_SITE, dsA:0, dsB:0, ansSite:MAIN_SITE, calSite:MAIN_SITE, cal:{year:2030,met:0,day:171,len:14}};
const PASS_FILTER=['1358','964'];
function orderSites(list){const w=(s)=>s.id===MAIN_SITE?0:s.id===CONTRAST_SITE?1:2;return list.slice().sort((a,b)=>w(a)-w(b));}
function idxFromDate(d){return Math.round((d.getTime()-T0)/HOUR);}
function dateFromIdx(i){return new Date(T0+i*HOUR);}
function fmt(i){const d=dateFromIdx(i);return d.toISOString().slice(0,16).replace('T',' ')+' UTC';}
function setIdx(i,fromPlay){if(!fromPlay)stopPlay();S.idx=Math.max(0,Math.min(N-1,Math.round(i)));$('slider').value=S.idx;$('dt').value=dateFromIdx(S.idx).toISOString().slice(0,16);$('dtbig').textContent=fmt(S.idx);update();}
const EXAMPLE = Math.round((Date.UTC(2030,5,21,11,0)-T0)/HOUR);

function dur(h){ if(h==null) return L().beyond(END_YEAR); const d=Math.floor(h/24), hh=Math.round(h%24); return d>0?`${d} ${L().days} ${hh} ${L().hrs}`:`${Math.max(1,Math.round(h))} ${L().hrs}`; }
function nextChange(arr,i){const v=arr[i];for(let j=i+1;j<N;j++){if(arr[j]!==v) return j-i;}return null;}
function nextBoth(s,i){for(let j=i+1;j<N;j++){if(s.sv[j]&&s.tv[j]&&!(s.sv[j-1]&&s.tv[j-1])) return j;}return -1;}
function signed(x){return (x>=0?'+':'−')+Math.abs(x).toFixed(2)+'°';}
function sname(s){return lang==='es'?s.es:s.en;}
function css(v){return getComputedStyle(document.documentElement).getPropertyValue(v).trim();}
function dec(v,n){const t=v.toFixed(n);return lang==='es'?t.replace('.',','):t;}
function pct(v){return Math.round(v)+' %';}
function rngTxt(s,k){const r=s.rng&&s.rng[k];if(!r||S.margin&&(k==='earth'||k==='both'))return '';const a=Math.round(r[0]),b=Math.round(r[1]);return a===b?'':` (${a}–${b})`;}
function watts(p){const v=p*S.area*S.eff;return dec(v,v<10&&v>0?1:0)+' W';}
function daysTxt(v){const lim=(N/24)-1;return v>=lim?L().yrsGE(YEARS_TXT):(v<10?dec(v,1):String(Math.round(v)))+' '+L().days;}


/* ---------- reproducir ---------- */
const PLAY_STEP=6,PLAY_MS=120;
function playLabel(){const b=$('play');if(b){b.textContent=S.playing?L().pause:L().play;b.setAttribute('aria-pressed',S.playing?'true':'false');}}
function stopPlay(){if(S.playing){clearTimeout(S.playT);S.playing=false;playLabel();renderDates();}}
function playTick(){if(!S.playing)return;const j=S.idx+PLAY_STEP;if(j>=N-1){setIdx(N-1,true);stopPlay();return;}setIdx(j,true);S.playT=setTimeout(playTick,PLAY_MS);}
function togglePlay(){if(S.playing){stopPlay();return;}if(S.idx>=N-1)setIdx(0,true);S.playing=true;playLabel();playTick();}

/* ---------- mismo sitio, dos fechas ---------- */
const DS_DAYS=30;
function stateTxt(s,i){const T=L();return s.sv[i]&&s.tv[i]?T.both:s.sv[i]?T.onlySun:s.tv[i]?T.onlyEar:T.none;}
function winStats(s,i){const b=Math.min(N,i+DS_DAYS*24),h=Math.max(1,b-i);return {sun:100*(s.pS[b]-s.pS[i])/h,earth:100*(s.pT[b]-s.pT[i])/h,both:100*(s.pB[b]-s.pB[i])/h,night:CORE.longestFalse(s.sv,i,b)/24,days:Math.round(h/24)};}
function renderDates(){
  if(S.playing||!$('ds-tbl'))return;
  const T=L(),s=site(S.dsSite),a=S.dsA,b=S.dsB,wa=winStats(s,a),wb=winStats(s,b),R=T.rows,d=Math.min(wa.days,wb.days);
  const dd=(v)=>v>=d?`≥ ${d} ${T.days}`:dec(v,1)+' '+T.days;
  const rows=[[R.vis,i=>stateTxt(s,i)],[R.solEl,i=>signed(s.SE[i])],[R.solM,i=>signed(s.rs[i])],[R.frac,i=>Math.round(100*s.f[i])+' %'],[R.pow,i=>watts(s.pw[i])],[T.dsNextSun,i=>dur(nextChange(s.sv,i))],[R.tieEl,i=>signed(s.TE[i])],[R.tieM,i=>signed(s.rt[i])],[T.dsNextEar,i=>dur(nextChange(s.tv,i))],
    [T.dsSun30(d),(i,w)=>pct(w.sun)],[T.dsEar30(d),(i,w)=>pct(w.earth)],[T.dsBoth30(d),(i,w)=>pct(w.both)],[T.dsNight30(d),(i,w)=>dd(w.night)]];
  $('ds-tbl').innerHTML=`<thead><tr><th></th><th>${T.dsA}<br>${fmt(a)}</th><th>${T.dsB}<br>${fmt(b)}</th></tr></thead><tbody>`+rows.map(([n,g])=>`<tr><td>${n}</td><td data-ds="a">${g(a,wa)}</td><td data-ds="b">${g(b,wb)}</td></tr>`).join('')+'</tbody>';
  $('ds-meta').innerHTML=`${L().kinds[s.kind]} · ${s.lat.toFixed(3)}°, ${s.lon.toFixed(3)}° · ${T.terrain} ${s.res}`+(s.id===CONTRAST_SITE?`<p class="warn">${T.warn14}</p>`:'')+(s.kind==='region'?regionHtml(s):'');
  $('ds-cap-a').textContent=`${T.dsA}: ${fmt(a)}`;$('ds-cap-b').textContent=`${T.dsB}: ${fmt(b)}`;
  drawPano($('ds-pano-a'),s,a);drawPano($('ds-pano-b'),s,b);
}
function dsSet(k,v){const d=new Date(v+':00Z');if(isNaN(d))return;S[k]=Math.max(0,Math.min(N-1,idxFromDate(d)));$(k==='dsA'?'ds-a':'ds-b').value=dateFromIdx(S[k]).toISOString().slice(0,16);renderDates();}

/* ---------- enlace para compartir ---------- */
const hourTxt=(i)=>dateFromIdx(i).toISOString().slice(0,13);
const hourIdx=(t)=>{const d=new Date(t+':00:00Z');return isNaN(d)?null:Math.max(0,Math.min(N-1,idxFromDate(d)));};
const siteToken=(id)=>{const s=S.sites[id];return s.kind==='custom'?`c:${s.lat}:${s.lon}`:id;};
function shareHash(){const p=[['s',S.sel.map(siteToken).join(',')],['t',hourTxt(S.idx)],['m',S.margin],['a',S.area],['e',Math.round(S.eff*100)],['ds',siteToken(S.dsSite)],['da',hourTxt(S.dsA)],['db',hourTxt(S.dsB)],['as',siteToken(S.ansSite)],['cs',siteToken(S.calSite)],['cy',S.cal.year],['cm',S.cal.met],['cd',S.cal.day],['cl',S.cal.len]];return '#'+p.map(([k,v])=>k+'='+v).join('&');}
function shareUrl(){return location.href.split('#')[0]+shareHash();}
async function doShare(){
  const u=shareUrl(),T=L(),inp=$('share-url'),msg=$('share-msg');
  try{history.replaceState(null,'',shareHash());}catch(e){}
  inp.value=u;inp.hidden=false;
  try{await navigator.clipboard.writeText(u);msg.textContent=T.copied;}catch(e){msg.textContent=T.copyFail;inp.focus();inp.select();}
}
function parseHash(){const o={};location.hash.slice(1).split('&').forEach(kv=>{const k=kv.indexOf('=');if(k>0)o[kv.slice(0,k)]=decodeURIComponent(kv.slice(k+1));});return o;}
async function customToken(t,memo){
  if(memo[t])return memo[t];
  const [,la,lo]=t.split(':'),lat=parseFloat(la),lon=parseFloat(lo);
  if(!(lat>=-90&&lat<=-80)||!(lon>=-180&&lon<=360))return null;
  $('c-lat').value=lat;$('c-lon').value=lon;const before=S.nCustom;await addCustom();
  return S.nCustom>before?(memo[t]='c'+S.nCustom):null;
}
async function applyHash(){
  const o=parseHash(),memo={};if(!Object.keys(o).length)return;
  if(['0','3','5'].includes(o.m)){S.margin=+o.m;$('margin').value=o.m;}
  if(+o.a>0){S.area=+o.a;$('p-area').value=o.a;}
  if(+o.e>=1&&+o.e<=100){S.eff=+o.e/100;$('p-eff').value=o.e;}
  const res=async(t)=>t.startsWith('c:')?customToken(t,memo):(S.sites[t]?t:null);
  if(o.s){const ids=[];for(const t of o.s.split(',').slice(0,3)){const id=await res(t);if(id&&!ids.includes(id))ids.push(id);}if(ids.length)S.sel=ids;}
  if(o.ds){const id=await res(o.ds);if(id){S.dsSite=id;}}
  if(o.da){const i=hourIdx(o.da);if(i!=null)S.dsA=i;}
  if(o.db){const i=hourIdx(o.db);if(i!=null)S.dsB=i;}
  if(o.as){const id=await res(o.as);if(id)S.ansSite=id;}
  if(o.cs){const id=await res(o.cs);if(id)S.calSite=id;}
  if(+o.cy>=2027&&+o.cy<=2044){S.cal.year=Math.floor(+o.cy);$('cal-year').value=S.cal.year;}
  if(['0','1','2'].includes(o.cm))S.cal.met=+o.cm;
  if(+o.cl>=1&&+o.cl<=CAL_MAX)S.cal.len=Math.floor(+o.cl);
  if(o.cd!=null&&+o.cd>=0&&+o.cd<=365)S.cal.day=Math.floor(+o.cd);
  const i=o.t?hourIdx(o.t):null;
  $('ds-a').value=dateFromIdx(S.dsA).toISOString().slice(0,16);$('ds-b').value=dateFromIdx(S.dsB).toISOString().slice(0,16);
  $('warn-sites').textContent='';
  buildChips();fillSelects();build();setIdx(i==null?S.idx:i);
}

/* ---------- exportar CSV ---------- */
function csvText(days){
  const a=S.idx,b=Math.min(N,a+days*24),n3=(v)=>v.toFixed(3),q=(t)=>'"'+String(t).replace(/"/g,'""')+'"';
  const sel=S.sel.map(id=>site(id));
  const out=['# Lunar Site Navigator. Model output, not measurements. For comparing sites, not certifying them.',`# Time step 1 h, observer ${DATA.hobs} m. Earth line of sight needs margin above ${S.margin} deg. Power uses area ${S.area} m2 and efficiency ${Math.round(S.eff*100)} %.`,'# Line of sight is not a communications link.'];
  sel.forEach(s=>out.push(`# ${s.id}: terrain ${s.res}`));
  out.push('utc,site_id,site_name,lat_deg,lon_east_deg,sun_elevation_deg,sun_azimuth_deg,sun_margin_deg,sun_visible,solar_disc_pct,power_w,earth_elevation_deg,earth_azimuth_deg,earth_margin_deg,earth_line_of_sight');
  for(const s of sel)for(let i=a;i<b;i++)out.push([dateFromIdx(i).toISOString().slice(0,16)+'Z',s.id,q(s.en),s.lat,s.lon,n3(s.SE[i]),n3(s.SA[i]),n3(s.rs[i]),s.sv[i],(100*s.f[i]).toFixed(1),(s.pw[i]*S.area*S.eff).toFixed(2),n3(s.TE[i]),n3(s.TA[i]),n3(s.rt[i]),s.tv[i]].join(','));
  return {text:out.join('\r\n')+'\r\n',rows:(b-a)*sel.length};
}
function doCsv(){
  const v=Math.max(1,Math.min(366,Math.round(+$('csv-days').value)||30));$('csv-days').value=v;
  const {text,rows}=csvText(v);
  const u=URL.createObjectURL(new Blob([text],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');
  a.href=u;a.download=`lunar_site_navigator_${hourTxt(S.idx).replace(/[-:]/g,'')}_${v}d.csv`;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),2000);
  $('share-msg').textContent=L().csvDone(rows);
}

/* ---------- contraste del mapa de calor ---------- */
function hexRgb(h){const t=h.replace('#','');return [0,2,4].map(k=>parseInt(t.slice(k,k+2),16));}
function lumin(c){const f=c.map(v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4);});return .2126*f[0]+.7152*f[1]+.0722*f[2];}
function cellStyle(col,t){const a=hexRgb(css(col)),b=hexRgb(css('--panel2')),p=(10+t*70)/100,c=a.map((v,k)=>Math.round(v*p+b[k]*(1-p))),l=lumin(c),fg=(1.05)/(l+.05)>=(l+.05)/.05?'#ffffff':'#000000';return `background:rgb(${c.join(',')});color:${fg}`;}


/* ---------- respuesta rápida ---------- */
function siteWarn(s){return (s.id===CONTRAST_SITE?`<p class="warn">${L().warn14}</p>`:'')+(s.kind==='region'?regionHtml(s):'');}
function renderAnswer(){
  const T=L(),s=site(S.ansSite),i=S.idx,sv=s.sv[i],tv=s.tv[i];
  $('ans-at').textContent=fmt(i);$('ans-ks').textContent=T.sun;$('ans-kt').textContent=T.earth;
  document.querySelector('.callegend i').style.background=`linear-gradient(to right,var(--panel2),var(${CAL_COL[S.cal.met]}))`;
  $('ans-sv').textContent=sv?T.visible:T.hidden;$('ans-sv').className='v '+(sv?'on':'off');
  $('ans-tv').textContent=tv?T.visible:T.noLos;$('ans-tv').className='v '+(tv?'on':'off');
  $('ans-sd').textContent=`${sv?T.endsIn:T.startsIn} ${dur(nextChange(s.sv,i))}`;$('ans-td').textContent=`${tv?T.endsIn:T.startsIn} ${dur(nextChange(s.tv,i))}`;
  let next;
  if(sv&&tv){let j=i+1;while(j<N&&s.sv[j]&&s.tv[j])j++;next=T.ansEnds(dur(j-i));}
  else{const j=nextBoth(s,i);next=j>=0?T.ansNext(fmt(j),dur(j-i)):T.ansNoNext;}
  $('ans-text').textContent=T.ansNow[sv&&tv?'both':sv?'onlySun':tv?'onlyEar':'none']+' '+next;
  $('ans-warn').innerHTML=siteWarn(s);
}

/* ---------- calendario de ventanas ---------- */
const CAL_MAX=28,CAL_PREF=['pB','pS','pT'],CAL_COL=['--ok','--sun','--earth'];
const calStart=(y,d)=>idxFromDate(new Date(Date.UTC(y,0,1)+d*86400000));
const calDays=(y)=>Math.round((Date.UTC(y+1,0,1)-Date.UTC(y,0,1))/86400000);
function calVal(s,a,n,m){const p=s[CAL_PREF[m]];return 100*(p[a+n*24]-p[a])/(n*24);}
function renderCal(force){
  if(S.playing||!$('cal-cv'))return;
  const T=L(),s=site(S.calSite),C=S.cal,cv=$('cal-cv'),W=cv.clientWidth||320,col=css(CAL_COL[C.met]),key=[S.calSite,C.year,C.met,C.day,C.len,S.margin,lang,W,col,css('--panel2')].join('|');
  if(!force&&S.calKey===key)return;S.calKey=key;
  const days=calDays(C.year);C.day=Math.min(C.day,days-1);
  const dpr=window.devicePixelRatio||1,Hh=250,pl=34,pr=8,pt=8,pb=38,w=W-pl-pr,h=Hh-pt-pb;
  cv.width=W*dpr;cv.height=Hh*dpr;cv.style.height=Hh+'px';
  const c=cv.getContext('2d');c.setTransform(dpr,0,0,dpr,0,0);c.fillStyle=css('--panel2');c.fillRect(0,0,W,Hh);
  const A=hexRgb(col),B=hexRgb(css('--panel2')),cw=w/days,ch=h/CAL_MAX;
  for(let d=0;d<days;d++){const a=calStart(C.year,d);for(let n=1;n<=CAL_MAX;n++){const v=calVal(s,a,n,C.met)/100;c.fillStyle=`rgb(${A.map((x,k)=>Math.round(x*v+B[k]*(1-v))).join(',')})`;c.fillRect(pl+d*cw,pt+(CAL_MAX-n)*ch,Math.ceil(cw),Math.ceil(ch));}}
  c.fillStyle=css('--muted');c.font='11px '+css('--fm');c.textAlign='right';
  for(const n of [1,7,14,21,28])c.fillText(String(n),pl-6,pt+(CAL_MAX-n+.5)*ch+4);
  c.textAlign='center';
  for(let m=0;m<12;m++){const d=Math.round((Date.UTC(C.year,m,1)-Date.UTC(C.year,0,1))/86400000),x=pl+d*cw;c.fillRect(x,pt+h,1,4);if(W>=420||m%2===0)c.fillText(new Date(Date.UTC(2000,m,1)).toLocaleDateString(lang==='es'?'es':'en',{month:'short',timeZone:'UTC'}).replace('.',''),x+cw*14,pt+h+16);}
  c.fillText(T.calX,pl+w/2,Hh-5);
  c.save();c.translate(10,pt+h/2);c.rotate(-Math.PI/2);c.fillText(T.calY,0,0);c.restore();
  c.strokeStyle=css('--fg');c.lineWidth=2;c.strokeRect(pl+C.day*cw-1,pt+(CAL_MAX-C.len)*ch-1,Math.max(cw,2)+2,ch+2);
  cv._g={pl,pt,w,h,days};
  cv.setAttribute('aria-label',T.calAria(sname(s),C.year));
  const a=calStart(C.year,C.day),x=mission(s,a,C.len*24),r={sun:Math.round(x.sun),los:Math.round(x.los),both:Math.round(x.both)};
  $('cal-read').textContent=T.calRead(fmt(a).slice(0,10),C.len,r,dec(CORE.longestFalse(s.sv,a,a+C.len*24)/24,1)+' '+T.days);
  let bd=0,bv=-1;for(let d=0;d<days;d++){const v=calVal(s,calStart(C.year,d),C.len,C.met);if(v>bv+1e-9){bv=v;bd=d;}}
  $('cal-max').textContent=T.calMax(T.calMets[C.met],C.len,fmt(calStart(C.year,bd)).slice(0,10),Math.round(bv));
  $('cal-warn').innerHTML=siteWarn(s);
  $('cal-meta').textContent=`${T.kinds[s.kind]} · ${s.lat.toFixed(3)}°, ${s.lon.toFixed(3)}° · ${T.terrain} ${s.res}`;
}
function calPick(ev){const cv=$('cal-cv'),g=cv._g;if(!g)return;const r=cv.getBoundingClientRect(),d=Math.floor((ev.clientX-r.left-g.pl)/g.w*g.days),n=CAL_MAX-Math.floor((ev.clientY-r.top-g.pt)/g.h*CAL_MAX);if(d<0||d>=g.days||n<1||n>CAL_MAX)return;S.cal.day=d;S.cal.len=n;renderCal();}
function calKeys(ev){const C=S.cal,mv={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,1],ArrowDown:[0,-1]}[ev.key];if(!mv)return;ev.preventDefault();C.day=Math.max(0,Math.min(calDays(C.year)-1,C.day+mv[0]));C.len=Math.max(1,Math.min(CAL_MAX,C.len+mv[1]));renderCal();}
function calInit(){
  const y0=new Date(T0).getUTCFullYear()+1,y1=new Date(T_END).getUTCFullYear()-1;let h='';for(let y=y0;y<=y1;y++)h+=`<option value="${y}">${y}</option>`;$('cal-year').innerHTML=h;$('cal-year').value=S.cal.year;
  $('cal-site').onchange=(e)=>{S.calSite=e.target.value;renderCal();};$('cal-year').onchange=(e)=>{S.cal.year=+e.target.value;renderCal();};$('cal-met').onchange=(e)=>{S.cal.met=+e.target.value;renderCal();};
  $('cal-cv').addEventListener('click',calPick);$('cal-cv').addEventListener('keydown',calKeys);
  $('cal-use').onclick=()=>{setIdx(calStart(S.cal.year,S.cal.day));$('cards').scrollIntoView({behavior:'auto'});};
  $('ans-site').onchange=(e)=>{S.ansSite=e.target.value;renderAnswer();};
}

/* ---------- panorama ---------- */
function drawPano(cv,s,i){
  const dpr=window.devicePixelRatio||1,W=cv.clientWidth||320,Hh=210;cv.width=W*dpr;cv.height=Hh*dpr;cv.style.height=Hh+'px';
  const c=cv.getContext('2d');c.setTransform(dpr,0,0,dpr,0,0);
  const ymin=-3,ymax=Math.max(6,Math.ceil(s.hzmax+2)),pl=34,pr=8,pt=8,pb=22;
  const X=(az)=>pl+((((az%360)+360)%360)/360)*(W-pl-pr), Y=(el)=>pt+(1-(el-ymin)/(ymax-ymin))*(Hh-pt-pb);
  c.fillStyle=css('--sky');c.fillRect(0,0,W,Hh);
  c.strokeStyle=css('--line');c.fillStyle=css('--muted');c.font='11px '+css('--fm');c.lineWidth=1;
  for(let a=0;a<=360;a+=45){c.beginPath();c.moveTo(X(a===360?359.999:a),pt);c.lineTo(X(a===360?359.999:a),Hh-pb);c.globalAlpha=.35;c.stroke();c.globalAlpha=1;}
  const lbl={0:'N',90:'E',180:'S',270:lang==='es'?'O':'W'};
  for(const a in lbl){c.textAlign='center';c.fillText(lbl[a],X(+a)+(+a===0?6:0),Hh-6);}
  for(let e=0;e<=ymax;e+=Math.ceil(ymax/4)){c.textAlign='right';c.fillStyle=css('--muted');c.fillText(e+'°',pl-6,Y(e)+4);c.beginPath();c.moveTo(pl,Y(e));c.lineTo(W-pr,Y(e));c.globalAlpha=.25;c.stroke();c.globalAlpha=1;}
  const objs=[{az:s.SA[i],el:s.SE[i],rel:s.rs[i],r:0.2665,col:css('--sun'),name:L().sunS},{az:s.TA[i],el:s.TE[i],rel:s.rt[i]-S.margin,r:0.95,col:css('--earth'),name:L().earthS}];
  const ppd=(Hh-pt-pb)/(ymax-ymin);
  c.beginPath();c.moveTo(pl,Y(ymin));
  for(let px=pl;px<=W-pr;px+=1){const az=((px-pl)/(W-pl-pr))*360;c.lineTo(px,Y(Math.max(ymin,CORE.interpHz(s.H,az))));}
  c.lineTo(W-pr,Y(ymin));c.closePath();
  const g=c.createLinearGradient(0,Y(ymax*0.2),0,Y(ymin));g.addColorStop(0,css('--ground'));g.addColorStop(1,css('--ground2'));c.fillStyle=g;c.fill();
  c.strokeStyle=css('--muted');c.lineWidth=1.2;c.beginPath();
  for(let px=pl;px<=W-pr;px+=1){const az=((px-pl)/(W-pl-pr))*360;const y=Y(Math.max(ymin,CORE.interpHz(s.H,az)));px===pl?c.moveTo(px,y):c.lineTo(px,y);}c.stroke();
  for(const o of objs){
    const clamped=o.el<ymin+.2,x=X(o.az),y=Y(Math.max(o.el,ymin+0.2)),r=Math.max(o.r*ppd,5),vis=o.rel>0;
    c.save();
    if(!vis){c.globalAlpha=.55;}
    if(vis){const gr=c.createRadialGradient(x,y,r*.4,x,y,r*3);gr.addColorStop(0,o.col+'aa');gr.addColorStop(1,o.col+'00');c.fillStyle=gr;c.beginPath();c.arc(x,y,r*3,0,7);c.fill();}
    c.fillStyle=o.col;c.beginPath();c.arc(x,y,r,0,7);c.fill();
    if(!vis){c.strokeStyle=css('--bg');c.lineWidth=2;c.setLineDash([3,3]);c.beginPath();c.arc(x,y,r+3,0,7);c.stroke();}
    c.restore();
    c.fillStyle=css('--fg');c.font='600 11px '+css('--fm');c.textAlign='center';
    c.fillText(o.name+(clamped?` ↓${dec(o.el,1)}°`:''),Math.min(Math.max(x,pl+26),W-pr-26),Math.max(pt+10,y-r-6));
  }
  cv.setAttribute('role','img');cv.setAttribute('aria-label',`${sname(s)}: ${L().elSun} ${signed(s.SE[i])}; ${L().elEarth} ${signed(s.TE[i])}`);
  return Math.max(1,Math.round(ppd/((W-pl-pr)/360)));
}

/* ---------- línea de tiempo ---------- */
const TL_BACK=10*24, TL_SPAN=60*24;
function drawTL(cv,s,i){
  const dpr=window.devicePixelRatio||1,W=cv.clientWidth||320,Hh=96;cv.width=W*dpr;cv.height=Hh*dpr;cv.style.height=Hh+'px';
  const c=cv.getContext('2d');c.setTransform(dpr,0,0,dpr,0,0);
  const pl=44, pr=6, rowH=20, top=6;
  c.fillStyle=css('--panel2');c.fillRect(0,0,W,Hh);
  const rows=[[s.sv,css('--sun')],[s.tv,css('--earth')],[null,css('--ok')]];
  c.font='11px '+css('--fm');c.fillStyle=css('--muted');c.textAlign='right';
  for(let r=0;r<3;r++){c.fillText(L().tlRows[r],pl-6,top+r*(rowH+4)+14);}
  const x0=i-TL_BACK; const w=W-pl-pr;
  for(let r=0;r<3;r++){
    const y=top+r*(rowH+4);
    c.fillStyle=css('--bg');c.globalAlpha=.55;c.fillRect(pl,y,w,rowH);c.globalAlpha=1;
    c.fillStyle=rows[r][1];
    for(let px=0;px<w;px++){
      const a=Math.floor(x0+px/w*TL_SPAN), b=Math.max(a+1,Math.floor(x0+(px+1)/w*TL_SPAN));
      let on=false;for(let k=a;k<b;k++){if(k<0||k>=N)continue;const v=r<2?rows[r][0][k]:(s.sv[k]&s.tv[k]);if(v){on=true;break;}}
      if(on)c.fillRect(pl+px,y,1.2,rowH);
    }
  }
  c.fillStyle=css('--muted');c.textAlign='center';
  for(let d=0;d<=60;d+=10){const t=dateFromIdx(x0+d*24);const x=pl+(d/60)*w;if(W>=300||d%20===0)c.fillText((t.getUTCMonth()+1)+'/'+t.getUTCDate(),Math.min(Math.max(x,pl+8),W-14),Hh-6);c.globalAlpha=.4;c.fillRect(x,top,1,3*(rowH+4)-4);c.globalAlpha=1;}
  const cx=pl+(TL_BACK/TL_SPAN)*w;c.fillStyle=css('--fg');c.fillRect(cx-1,top-2,2,3*(rowH+4));
  cv._geom={pl,w,x0,span:TL_SPAN};
  cv.setAttribute('role','img');cv.setAttribute('aria-label',L().tl);
}


/* ---------- puntos de region ---------- */
function regionHtml(s){
  const T=L(),v=s.val||{},big=(a,b)=>a!=null&&b!=null&&Math.abs(a-b)>=10;
  let t=T.regNote(s)+' ';
  if(v.pgda_sol==null&&v.lroc==null)t+=T.regNone;
  else{if(v.pgda_sol!=null)t+=T.regPgda(v)+' ';if(v.lroc!=null)t+=T.regLroc(v)+' ';if(big(v.pgda_sol,v.modelo_sol)||big(v.pgda_tierra,v.modelo_tierra)||big(v.lroc,v.modelo_sol_2010))t+=T.regBig;}
  return `<p class="warn" data-r="warnreg">${t} ${T.regTime}</p>`;
}
const mixedRes=(sel)=>sel.some(s=>s.kind==='region')&&sel.some(s=>s.kind!=='region');

/* ---------- tarjetas ---------- */
function badge(s){
  if(s.kind==='region')return `<div class="badge">${L().regBadge}</div>`+regionHtml(s);
  if(s.kind!=='cand')return '';
  if(s.id===MAIN_SITE)return `<div class="badge top">${L().best}</div>`;
  if(s.id===CONTRAST_SITE)return `<div class="badge">${L().contrast}</div><p class="warn" data-r="warn14">${L().warn14}</p>`;
  return `<div class="badge">${PASS_FILTER.includes(s.id)?L().passes:L().fails}</div>`;
}
function build(){
  const cards=$('cards');cards.innerHTML='';
  S.sel.forEach((id)=>{
    const s=site(id);
    const el=document.createElement('article');el.className='card';
    el.innerHTML=`<h3>${sname(s)}</h3>${badge(s)}<div class="meta">${L().kinds[s.kind]} · ${s.lat.toFixed(3)}°, ${s.lon.toFixed(3)}° · ${s.z0.toFixed(0)} m · ${L().terrain} ${s.res}</div>
    <canvas class="pano" data-id="${id}" tabindex="0"></canvas><div class="cap" data-r="pcap"></div>
    <div class="status"><div class="st sun"><div class="k">${L().sun}</div><div class="v" data-r="sv"></div><div class="d" data-r="sd"></div></div><div class="st earth"><div class="k">${L().earth}</div><div class="v" data-r="tv"></div><div class="d" data-r="td"></div></div></div>
    <div class="nums n8"><div>${L().elSun}<b data-r="n1"></b></div><div>${L().mSun}<b data-r="n5"></b></div><div>${L().frac}<b data-r="n6"></b></div><div>${L().pow}<b data-r="n7"></b></div><div>${L().elEarth}<b data-r="n2"></b></div><div>${L().mEarth}<b data-r="n8"></b></div><div>${L().azSun}<b data-r="n3"></b></div><div>${L().azEarth}<b data-r="n4"></b></div></div>
    <div class="cap">${L().tl}</div><canvas class="tl" data-id="${id}" tabindex="0"></canvas>
    <div class="legend"><span style="--c:var(--sun)">${L().tlRows[0]}</span><span style="--c:var(--earth)">${L().tlRows[1]}</span><span style="--c:var(--ok)">${L().tlRows[2]}</span></div>
    <div class="cap" style="margin-top:12px">${L().ten(YEARS_TXT)}</div>
    <div class="bars" data-r="bars"></div>
    <div class="cap" style="margin-top:10px" data-r="sum"></div>`;
    cards.appendChild(el);
  });
  cards.querySelectorAll('canvas.tl').forEach(cv=>{
    cv.addEventListener('click',(ev)=>{const g=cv._geom;if(!g)return;const r=cv.getBoundingClientRect();const f=(ev.clientX-r.left-g.pl)/g.w;if(f<0||f>1)return;setIdx(g.x0+f*g.span);});
  });
}
function update(){
  const i=S.idx;
  S.sel.forEach(id=>site(id));
  $('cards').querySelectorAll('.card').forEach((card,k)=>{
    const s=S.sites[S.sel[k]];
    const sv=s.sv[i],tv=s.tv[i],T=L();
    const q=(r)=>card.querySelector(`[data-r="${r}"]`);
    q('sv').textContent=sv?T.visible:T.hidden;q('sv').className='v '+(sv?'on':'off');
    q('tv').textContent=tv?T.visible:T.noLos;q('tv').className='v '+(tv?'on':'off');
    q('sd').textContent=`${sv?T.endsIn:T.startsIn} ${dur(nextChange(s.sv,i))}`;
    q('td').textContent=`${tv?T.endsIn:T.startsIn} ${dur(nextChange(s.tv,i))}`;
    q('n1').textContent=signed(s.SE[i]);q('n2').textContent=signed(s.TE[i]);q('n5').textContent=signed(s.rs[i]);q('n8').textContent=signed(s.rt[i]);
    q('n6').textContent=Math.round(100*s.f[i])+' %';q('n7').textContent=watts(s.pw[i]);
    q('n3').textContent=dec(s.SA[i],1)+'°';q('n4').textContent=dec(s.TA[i],1)+'°';
    q('pcap').textContent=T.pano(drawPano(card.querySelector('canvas.pano'),s,i));drawTL(card.querySelector('canvas.tl'),s,i);
    const bar=(lab,v,col,key)=>`<div class="bar"><span>${lab}</span><i><u style="width:${v}%;background:var(${col})"></u></i><span>${pct(v)}${rngTxt(s,key)}</span></div>`;
    q('bars').innerHTML=bar(T.sunPct,s.stat.sun,'--sun','sun')+bar(T.earthPct,s.stat.earth,'--earth','earth')+bar(T.bothPct,s.stat.both,'--ok','both');
    q('sum').textContent=`${T.night}: ${daysTxt(s.stat.night)}${rngTxt(s,'night')} · ${T.noearth}: ${daysTxt(s.stat.noearth)} · ${T.pmean}: ${watts(s.stat.pm)}`;
  });
  const T=L(),rows=T.rows,sel=S.sel.map(id=>S.sites[id]);
  const inTL=(s)=>{const a=Math.max(0,i-TL_BACK),b=Math.min(N,i-TL_BACK+TL_SPAN);return s.pB[b]-s.pB[a];};
  const state=(s)=>s.sv[i]&&s.tv[i]?T.both:s.sv[i]?T.onlySun:s.tv[i]?T.onlyEar:T.none;
  const defs=[
    [rows.vis,s=>state(s),null],
    [rows.solEl,s=>s.SE[i],null,v=>signed(v)],
    [rows.solM,s=>s.rs[i],'max',v=>signed(v)],
    [rows.frac,s=>s.f[i],'max',v=>Math.round(v*100)+' %'],
    [rows.pow,s=>s.pw[i],'max',v=>watts(v)],
    [rows.tieEl,s=>s.TE[i],null,v=>signed(v)],
    [rows.tieM,s=>s.rt[i],'max',v=>signed(v)],
    [rows.sunP(YEARS_TXT),s=>s.stat.sun,'max',(v,s)=>pct(v)+rngTxt(s,'sun')],
    [rows.earP(YEARS_TXT),s=>s.stat.earth,'max',(v,s)=>pct(v)+rngTxt(s,'earth')],
    [rows.bothP(YEARS_TXT),s=>s.stat.both,'max',(v,s)=>pct(v)+rngTxt(s,'both')],
    [rows.night,s=>s.stat.night,'min',(v,s)=>daysTxt(v)+rngTxt(s,'night')],
    [rows.noear,s=>s.stat.noearth,'min',v=>daysTxt(v)],
    [rows.pm,s=>s.stat.pm,'max',v=>watts(v)],
    [rows.win60,s=>inTL(s),'max',v=>String(v)],
    [rows.hz,s=>s.hzmax,'min',v=>dec(v,1)],
    [rows.area,s=>s.area,'max',v=>v==null?'—':dec(v,2)],
    [rows.slope,s=>s.slope,'min',v=>v==null?'—':dec(v,1)]
  ];
  let h='<thead><tr><th></th>'+sel.map(s=>`<th>${sname(s)}</th>`).join('')+'</tr></thead><tbody>';
  for(const [lab,f,mode,fm] of defs){
    const vals=sel.map(f);let best=null;
    if(mode&&!mixedRes(sel)){const nums=vals.filter(v=>v!=null);if(nums.length>1){best=mode==='max'?Math.max(...nums):Math.min(...nums);if(nums.every(v=>v===best))best=null;}}
    h+=`<tr><td>${lab}</td>`+vals.map((v,k)=>`<td class="num ${best!=null&&v===best?'best':''}">${fm?fm(v,sel[k]):v}</td>`).join('')+'</tr>';
  }
  $('tbl').innerHTML=h+'</tbody>';
  $('warn-mix').textContent=mixedRes(sel)?T.warnMix:'';
  renderPlan();
  renderDates();
  renderAnswer();
  renderCal();
}

/* ---------- planificador ---------- */
function mission(s,a,hrs){
  const b=a+hrs;if(a<0||b>N)return null;
  return {sun:100*(s.pS[b]-s.pS[a])/hrs,los:100*(s.pT[b]-s.pT[a])/hrs,both:100*(s.pB[b]-s.pB[a])/hrs,night:CORE.longestFalse(s.sv,a,b)/24,noe:CORE.longestFalse(s.tv,a,b)/24,e:(s.pE[b]-s.pE[a])*S.area*S.eff/1000,pm:(s.pE[b]-s.pE[a])/hrs,sv:s.sv[a],tv:s.tv[a]};
}
function planInputs(){const launch=idxFromDate(new Date($('p-launch').value+':00Z'));return {launch,cruise:Math.max(0,+$('p-cruise').value||0),durH:Math.max(1,Math.round((+$('p-dur').value||1)*24)),delay:Math.max(0,Math.min(60,Math.round(+$('p-delay').value||0)))};}
function renderPlan(){
  const T=L(),s=site(S.planSite),p=planInputs();
  if(Number.isNaN(p.launch)){$('warn-plan').textContent=T.outRange;return;}
  const a0=p.launch+Math.round(p.cruise*24),A=mission(s,a0,p.durH),B=mission(s,a0+p.delay*24,p.durH);
  $('warn-plan').textContent=(A&&B)?'':T.outRange;
  const R=T.planRows,lands=(x)=>x?(x.sv&&x.tv?T.both:x.sv?T.onlySun:x.tv?T.onlyEar:T.none):'—',f=(x,fn)=>x?fn(x):'—';
  const rows=[[R.land,fmt(a0),fmt(a0+p.delay*24)],[R.ls,lands(A),lands(B)],[R.sun,f(A,x=>pct(x.sun)),f(B,x=>pct(x.sun))],[R.los,f(A,x=>pct(x.los)),f(B,x=>pct(x.los))],[R.both,f(A,x=>pct(x.both)),f(B,x=>pct(x.both))],[R.night,f(A,x=>dec(x.night,1)+' '+T.days),f(B,x=>dec(x.night,1)+' '+T.days)],[R.noe,f(A,x=>dec(x.noe,1)+' '+T.days),f(B,x=>dec(x.noe,1)+' '+T.days)],[R.en,f(A,x=>dec(x.e,1)+' kWh'),f(B,x=>dec(x.e,1)+' kWh')],[R.pm,f(A,x=>watts(x.pm)),f(B,x=>watts(x.pm))]];
  $('plan-tbl').innerHTML='<thead><tr>'+T.planCols.map(c=>`<th>${c}</th>`).join('')+'</tr></thead><tbody>'+rows.map(r=>`<tr><td>${r[0]}</td><td class="num">${r[1]}</td><td class="num">${r[2]}</td></tr>`).join('')+'</tbody>';
  $('cap-delay').textContent=T.capDelay;
  drawDelay(s,a0,p);
}
function drawDelay(s,a0,p){
  const cv=$('delay-cv'),dpr=window.devicePixelRatio||1,W=cv.clientWidth||320,Hh=150;cv.width=W*dpr;cv.height=Hh*dpr;
  const c=cv.getContext('2d');c.setTransform(dpr,0,0,dpr,0,0);c.fillStyle=css('--panel2');c.fillRect(0,0,W,Hh);
  const pl=34,pr=6,pt=8,pb=20,w=W-pl-pr,h=Hh-pt-pb,vals=[];
  for(let d=0;d<=60;d++){const m=mission(s,a0+d*24,p.durH);vals.push(m?m.both:null);}
  c.font='11px '+css('--fm');c.fillStyle=css('--muted');c.textAlign='right';
  for(const v of [0,50,100]){const y=pt+h*(1-v/100);c.fillText(v+'%',pl-4,y+4);c.globalAlpha=.3;c.fillRect(pl,y,w,1);c.globalAlpha=1;}
  const bw=w/61;
  vals.forEach((v,d)=>{if(v==null)return;c.fillStyle=d===p.delay?css('--sun'):css('--ok');c.fillRect(pl+d*bw,pt+h*(1-v/100),Math.max(1,bw-1),h*v/100);});
  c.fillStyle=css('--muted');c.textAlign='center';for(let d=0;d<=60;d+=10)c.fillText(d+(d===60?' '+L().days:''),Math.min(pl+d*bw+bw/2,W-20),Hh-6);
  cv._d={pl,bw};
  const ok=vals.map((v,d)=>[v,d]).filter(x=>x[0]!=null);
  if(ok.length){const b=ok.reduce((m,x)=>x[0]>m[0]?x:m,ok[0]);$('plan-best').textContent=L().planBest(b[1],Math.round(b[0]),Math.round(ok[0][0]));cv.setAttribute('aria-label',$('plan-best').textContent);}else $('plan-best').textContent='';
}

/* ---------- mapa de calor ---------- */
function renderHeat(){
  const T=L(),s=S.sites[S.heatId],m=S.heatMet,o=DATA.offs,n=o.length;
  if(!s.heat){$('h-grid').innerHTML='';$('h-stat').innerHTML='';$('h-note').textContent=T.computing;return;}
  const vals=s.heat.map(c=>c[m]),lo=Math.min(...vals),hi=Math.max(...vals),col=['--sun','--earth','--ok','--muted'][m],ctr=s.heat[Math.floor(n/2)*n+Math.floor(n/2)][m];
  const f=(v)=>m===3?dec(v,1):String(Math.round(v));
  $('h-stat').innerHTML=[[T.heatMin,lo],[T.heatPt,ctr],[T.heatMax,hi]].map(([a,b])=>`<div class="st"><div class="k">${a}</div><div class="v">${f(b)}</div></div>`).join('');
  let h='';
  for(let r=n-1;r>=0;r--){h+=`<div class="lab">${o[r]>0?'+':''}${o[r]}</div>`;for(let c=0;c<n;c++){const v=s.heat[r*n+c][m],t=hi>lo?(v-lo)/(hi-lo):.5,center=(r===Math.floor(n/2)&&c===Math.floor(n/2));h+=`<div class="${center?'c0':''}" style="${cellStyle(col,t)}">${f(v)}</div>`;}}
  h+='<div class="lab"></div>'+o.map(v=>`<div class="lab">${v>0?'+':''}${v}</div>`).join('');
  const g=$('h-grid');g.innerHTML=h;g.setAttribute('aria-label',`${sname(s)}, ${T.mets[m]}: ${f(lo)} – ${f(hi)}`);
  $('h-note').textContent=T.heatNote+(s.res.startsWith('80 m')?' '+T.heat80:'')+(s.kind==='custom'?' '+T.heatRed:'');
}
function fillSelects(){
  const opt=(id,cur)=>{$(id).innerHTML=orderSites(DATA.sites).concat(Object.values(S.sites).filter(s=>s.kind==='custom')).map(s=>`<option value="${s.id}" ${s.id===cur?'selected':''}>${sname(s)}</option>`).join('');};
  opt('p-site',S.planSite);opt('h-site',S.heatId);opt('ds-site',S.dsSite);opt('ans-site',S.ansSite);opt('cal-site',S.calSite);
  $('cal-met').innerHTML=L().calMets.map((m,k)=>`<option value="${k}" ${k===S.cal.met?'selected':''}>${m}</option>`).join('');
  $('h-met').innerHTML=L().mets.map((m,k)=>`<option value="${k}" ${k===S.heatMet?'selected':''}>${m}</option>`).join('');
}

/* ---------- coordenadas propias ---------- */
async function addCustom(){
  const T=L(),lat=parseFloat($('c-lat').value),lon=parseFloat($('c-lon').value);$('warn-custom').textContent='';
  if(!(lat>=-90&&lat<=-80)||!(lon>=-180&&lon<=360)){$('warn-custom').textContent=T.errCoord;return;}
  $('warn-custom').textContent=T.computing;$('c-add').disabled=true;
  await new Promise(r=>setTimeout(r,20));
  const dem=await loadDEM(),[x,y]=CORE.xyFromLatLon(lat,lon),z0=CORE.zAt(dem,x,y);
  if(Number.isNaN(z0)){$('warn-custom').textContent=T.errCoord;$('c-add').disabled=false;return;}
  const H=CORE.horizon(dem,x,y,DATA.hobs,360,200000);
  S.nCustom++;
  const inTile=!Number.isNaN(CORE.bil(dem.fine,x,y));
  const s={id:'c'+S.nCustom,es:I18N.es.customName(S.nCustom),en:I18N.en.customName(S.nCustom),lat,lon,x,y,kind:'custom',res:inTile?'20 m + 480 m (DEM reducido)':'480 m (DEM reducido)',area:null,slope:null,z0,H};
  S.sites[s.id]=s;prep(s);masks(s);
  if(S.sel.length<3)S.sel.push(s.id);else $('warn-sites').textContent=T.maxSites;
  S.heatId=s.id;S.planSite=s.id;
  buildChips();fillSelects();build();update();renderHeat();
  const edge=Math.hypot(x,y)>104000;
  $('warn-custom').textContent=edge?T.edge:'';
  await customHeat(s,dem);
  $('c-add').disabled=false;
}
async function customHeat(s,dem){
  const o=DATA.offs,cells=[];
  for(const dy of o){for(const dx of o){
    const x=s.x+dx,y=s.y+dy,[la,lo]=CORE.latLonFromXY(x,y),H=CORE.horizon(dem,x,y,DATA.hobs,180,200000),b=CORE.basis(la,lo);
    let ns=0,nt=0,nb=0,cur=0,best=0,n=0;
    for(let i=0;i<N;i+=3){
      const v=CORE.azEl(b,EPH.slat[i],EPH.slon[i],EPH.sd[i]*AU),e=CORE.azEl(b,EPH.elat[i],EPH.elon[i],EPH.ed[i]);
      const a=v[1]>CORE.interpHz(H,v[0]),c=e[1]>CORE.interpHz(H,e[0]);
      n++;ns+=a;nt+=c;nb+=(a&&c);cur=a?0:cur+1;if(cur>best)best=cur;
    }
    cells.push([100*ns/n,100*nt/n,100*nb/n,best/8]);
  }
  await new Promise(r=>setTimeout(r,0));}
  s.heat=cells;
  const mm=(k)=>[Math.min(...cells.map(c=>c[k])),Math.max(...cells.map(c=>c[k]))];
  s.rng={sun:mm(0),earth:mm(1),both:mm(2),night:mm(3)};
  if(S.heatId===s.id)renderHeat();
  update();
}

/* ---------- interfaz ---------- */
const TXT={'t-choice':'tChoice','l-choice':'lChoice','t-main':'tMain','t-contrast':'tContrast','t-crit':'tCrit','crit-note':'critNote',eyebrow:'eyebrow',h1:'h1',sub:'sub',loading:'loading','t-sites':'tSites','hint-sites':'hintSites','t-custom':'tCustom','l-lat':'lLat','l-lon':'lLon','c-add':'add','hint-custom':'hintCustom','t-when':'tWhen','l-margin':'lMargin','l-area':'lArea','l-eff':'lEff','hint-power':'hintPower','t-compare':'tCompare','l-compare':'lCompare','t-plan':'tPlan','l-plan':'lPlan','l-psite':'lPsite','l-launch':'lLaunch','l-cruise':'lCruise','l-dur':'lDur','l-delay':'lDelay','t-heat':'tHeat','l-heat':'lHeat','l-hsite':'lHsite','l-hmet':'lHmet','t-3d':'t3d','l-3d':'l3d','cap-hero':'capHero','cap-video':'capVideo','t-why':'tWhy','t-about':'tAbout','t-method':'tMethod','t-valid':'tValid','t-limits':'tLimits',foot:'foot'};
function setText(){
  const T=L();document.documentElement.lang=lang;document.title=T.title;
  for(const id in TXT)$(id).textContent=T[TXT[id]];
  const fd=(t)=>new Date(t).toISOString().slice(0,10);
  $('hint-when').textContent=T.hintWhen(fd(T0),fd(T_END));
  $('main-list').innerHTML=T.main.map(x=>`<li>${x}</li>`).join('');$('contrast-list').innerHTML=T.contrastL.map(x=>`<li>${x}</li>`).join('');$('crit-list').innerHTML=T.critList.map(x=>`<li>${x}</li>`).join('');
  $('method').innerHTML=T.method.map(x=>`<li>${x}</li>`).join('');$('valid').innerHTML=T.valid.map(x=>`<li>${x}</li>`).join('');$('limits').innerHTML=T.limits.map(x=>`<li>${x}</li>`).join('');
  $('why').innerHTML=T.why.map(([a,b])=>`<div class="box"><h3>${a}</h3><p>${typeof b==='function'?b(YEARS_TXT):b}</p></div>`).join('');
  $('lang').textContent=lang==='es'?'EN':'ES';
  const nv=$('nav');nv.innerHTML='';
  [['m29',-709],['m1',-24],['p1',24],['p29',709]].forEach(([k,dh])=>{const b=document.createElement('button');b.className='btn';b.textContent=T.nav[k];b.onclick=()=>setIdx(S.idx+dh);nv.appendChild(b);});
  const w=document.createElement('button');w.className='btn primary';w.textContent=T.nav.win;w.onclick=()=>{const s=site(S.sel[0]);const j=nextBoth(s,S.idx);if(j>=0)setIdx(j);};nv.appendChild(w);
  const e=document.createElement('button');e.className='btn';e.textContent=T.nav.ex;e.onclick=()=>setIdx(EXAMPLE);nv.appendChild(e);
  const pl=document.createElement('button');pl.className='btn';pl.id='play';pl.onclick=togglePlay;nv.insertBefore(pl,nv.firstChild);playLabel();
  for(const [id,k] of [['share','share'],['csv','csvBtn'],['l-csv','lCsv'],['hint-csv','csvHint'],['t-ans','tAns'],['l-ans-site','lAnsSite'],['l-ans-at','lAnsAt'],['ans-go','ansGo'],['ans-note','ansNote'],['t-cal','tCal'],['l-cal','lCal'],['l-cal-site','lCalSite'],['l-cal-year','lCalYear'],['l-cal-met','lCalMet'],['cal-use','calUse'],['cal-hint','calHint'],['t-dates','tDates'],['l-dates','lDates'],['l-ds-site','lDsSite'],['l-ds-a','lDsA'],['l-ds-b','lDsB']])$(id).textContent=T[k];
  $('share-url').setAttribute('aria-label',T.share);
  {const es=lang==='es',m=$('vid-main'),a=$('vid-alt');m.textContent=T.vidMain;a.textContent=T.vidAlt;$('vid-note').textContent=T.vidNote;m.href='videos/lsn_explicativo_'+(es?'es':'en')+'.mp4';a.href='videos/lsn_explicativo_'+(es?'en':'es')+'.mp4';}
  document.querySelectorAll('.tablewrap').forEach(w=>{const h=w.closest('section').querySelector('h2');if(h)w.setAttribute('aria-label',h.textContent);});
  $('gal').innerHTML=['456','14','1358','964'].map(id=>`<figure><img alt="${T.cap3d(id)}" src="data:image/jpeg;base64,${IMG[id]}"><figcaption>${T.cap3d(id)}</figcaption></figure>`).join('');
  $('hero').alt=T.capHero;$('dt').setAttribute('aria-label',T.tWhen);$('slider').setAttribute('aria-label',T.tWhen);
  buildChips();
}
function buildChips(){
  const T=L();const all=DATA.sites.concat(Object.values(S.sites).filter(s=>s.kind==='custom'));const groups=[['cand',T.grpCand],['real',T.grpReal],['ref',T.grpRef],['region',T.grpRegion],['custom',T.grpCustom]];
  let h='';
  for(const [k,name] of groups){const list=orderSites(all.filter(s=>s.kind===k));if(!list.length)continue;h+=`<div class="grp">${name}</div><div class="chips">`+list.map(s=>`<button class="chip" data-id="${s.id}" aria-pressed="${S.sel.includes(s.id)}">${sname(s)}</button>`).join('')+'</div>';}
  $('chips').innerHTML=h;
  $('chips').querySelectorAll('.chip').forEach(b=>b.onclick=()=>{
    const id=b.dataset.id,k=S.sel.indexOf(id);$('warn-sites').textContent='';
    if(k>=0){if(S.sel.length>1)S.sel.splice(k,1);else{$('warn-sites').textContent=L().minSites;return;}}
    else{if(S.sel.length>=3){$('warn-sites').textContent=L().maxSites;return;}S.sel.push(id);}
    buildChips();build();update();
  });
}
function ticks(){const span=T_END-T0;$('ticks').innerHTML=[2027,2030,2033,2036,2039,2042,2045].map(v=>`<span style="left:${Math.min(96,Math.max(4,100*(Date.UTC(v,0,1)-T0)/span))}%">${v}</span>`).join('');}

async function main(){
  if(typeof DecompressionStream==='undefined'){$('loading').hidden=true;$('error').hidden=false;$('error').textContent=I18N[lang].errNoDS;return;}
  for(const s of DATA.sites)S.sites[s.id]=s;
  $('loading').textContent=L().loading;
  try{await loadEph();}catch(e){$('loading').hidden=true;$('error').hidden=false;$('error').textContent='Error: '+e.message;return;}
  setText();fillSelects();
  $('loading').hidden=true;$('app').hidden=false;
  $('slider').max=N-1;ticks();
  $('p-launch').value=new Date(Date.UTC(2030,5,15,0,0)).toISOString().slice(0,16);
  $('p-launch').min=new Date(T0).toISOString().slice(0,16);$('p-launch').max=new Date(T_END).toISOString().slice(0,16);
  $('slider').oninput=(e)=>setIdx(+e.target.value);
  $('dt').onchange=(e)=>{const d=new Date(e.target.value+':00Z');if(!isNaN(d))setIdx(idxFromDate(d));};
  $('margin').onchange=(e)=>{S.margin=+e.target.value;update();};
  $('p-area').oninput=(e)=>{const v=+e.target.value;if(v>0){S.area=v;update();}};
  $('p-eff').oninput=(e)=>{const v=+e.target.value;if(v>0){S.eff=v/100;update();}};
  ['p-launch','p-cruise','p-dur','p-delay'].forEach(id=>$(id).addEventListener('input',renderPlan));
  $('p-site').onchange=(e)=>{S.planSite=e.target.value;renderPlan();};
  $('h-site').onchange=(e)=>{S.heatId=e.target.value;renderHeat();};
  $('h-met').onchange=(e)=>{S.heatMet=+e.target.value;renderHeat();};
  $('c-add').onclick=()=>addCustom();
  calInit();
  $('share').onclick=doShare;$('csv').onclick=doCsv;
  $('ds-site').onchange=(e)=>{S.dsSite=e.target.value;renderDates();};
  $('ds-a').onchange=(e)=>dsSet('dsA',e.target.value);$('ds-b').onchange=(e)=>dsSet('dsB',e.target.value);
  for(const id of ['ds-a','ds-b']){$(id).min=new Date(T0).toISOString().slice(0,16);$(id).max=new Date(T_END).toISOString().slice(0,16);}
  $('delay-cv').addEventListener('click',(ev)=>{const g=$('delay-cv')._d;if(!g)return;const r=$('delay-cv').getBoundingClientRect(),d=Math.floor((ev.clientX-r.left-g.pl)/g.bw);if(d>=0&&d<=60){$('p-delay').value=d;renderPlan();}});
  $('lang').onclick=()=>{lang=lang==='es'?'en':'es';try{localStorage.setItem('nav-lang',lang)}catch(e){}setText();fillSelects();build();update();renderHeat();};
  $('theme').onclick=()=>{const r=document.documentElement;const cur=r.dataset.theme||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');r.dataset.theme=cur==='dark'?'light':'dark';update();renderHeat();};
  S.dsA=EXAMPLE;S.dsB=Math.min(N-1,EXAMPLE+15*24);$('ds-a').value=dateFromIdx(S.dsA).toISOString().slice(0,16);$('ds-b').value=dateFromIdx(S.dsB).toISOString().slice(0,16);
  build();setIdx(EXAMPLE);renderHeat();
  await applyHash();
  let rt;addEventListener('resize',()=>{clearTimeout(rt);rt=setTimeout(update,120);});
  matchMedia('(prefers-color-scheme: dark)').addEventListener?.('change',()=>{update();renderHeat();});
}
main();
