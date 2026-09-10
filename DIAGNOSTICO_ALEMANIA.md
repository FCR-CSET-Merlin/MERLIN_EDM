**Factibilidad de transferir MERLIN_EDM a Alemania**

Fecha de revisión: 8 de septiembre de 2026. Diagnóstico basado en inspección del código, notebooks, metadatos del modelo local y documentación pública de las fuentes alemanas. No se ejecutó entrenamiento, inferencia alemana ni una auditoría estadística de las series completas. Las valoraciones de factibilidad son juicios técnicos, no resultados de un experimento.

**Dictamen**

La metodología es transferible como reconstrucción de demanda horaria condicionada por consumos territoriales y sectoriales. La arquitectura MLP también es reutilizable. Aplicar directamente los pesos chilenos a Alemania solo es defendible como experimento de referencia: no existe evidencia aquí que permita asumir precisión alemana. La opción recomendada es reentrenar con datos alemanes y comparar con ajuste de los pesos chilenos y métodos alemanes de desagregación.

El cuello de botella es la disponibilidad de etiquetas horarias territoriales comparables y la definición del consumo, más que el cómputo o TensorFlow. Una serie nacional y balances anuales no identifican por sí solos las curvas horarias de miles de municipios.

| Escala de salida | Factibilidad metodológica | Condición principal |
| --- | --- | --- |
| Alemania | Alta | Definir carga de red o consumo final; disponer de varios años coherentes. |
| Bundesland | Media-alta para estimación | Balances anuales accesibles; las zonas eléctricas no equivalen automáticamente a estados. |
| Kreis / kreisfreie Stadt | Media | Estadísticas territoriales y modelos de referencia; etiquetas horarias observadas fragmentarias. |
| Gemeinde / ciudad | Media en pilotos; condicionada para cobertura nacional | Energía anual local y correspondencia con redes de distribución. |
| Bezirk / barrio | Condicionada | Datos locales; mayor incertidumbre y posible secreto estadístico. |

“Distrito” debe fijarse antes de implementar: un Kreis y un Bezirk urbano son niveles diferentes. “Región” tampoco tiene una única traducción; puede ser una agrupación de municipios o una división administrativa. Usar códigos territoriales oficiales, jerarquía y año de límites, no nombres ni una simple bandera binaria.

**Qué hace realmente el repositorio**

La cadena activa combina demanda horaria comunal, agregación regional, temperatura ERA5-Land, calendario, balances energéticos y facturación. `prototipo_3/notebooks/se_shares.ipynb` lee facturación de clientes regulados y ventas a clientes libres; `process_all_data.ipynb` forma shares sectoriales mensuales y la proporción comunal respecto al total nacional mensual. `preprocessing/demanda_elec_regional.py` suma las series comunales por región.

La supervisión entra ya como `demanda_comunal_horaria.csv`. La procedencia declarada es CEN, pero el archivo `prototipo_2/preprocessing/retiros.py` está vacío: esta revisión no pudo reconstruir desde ese script la transformación barra → consumo comunal. Para homologarla hay que recuperar y auditar el cruce original, incluyendo cobertura de barras, clientes servidos, pérdidas y posibles duplicados. La ubicación física de una subestación no demuestra que sus retiros se consuman en su municipio.

`prototipo_3/src/train_mlp_v2.py` implementa un MLP con capas 256 → 128 → 64 → 32 → 1, activación ELU en capas ocultas, salida lineal, Adam con tasa 0,0005 y pérdida Huber. Dropout está comentado; BatchNormalization se importa pero no se utiliza. Se prepara ReduceLROnPlateau, pero no se incluye en los callbacks de `fit`.

Los artefactos no están dentro del checkout. Se localizaron en `/srv/compartido/inbox/datos_modelos_MERLIN_EDM_prot_3/`: `models/ds_comunal/best_merlin_mlp_global.keras`, `models/scaler_temp_global.pkl` y `data/rec_2024_2025/columns.txt`. El ZIP del modelo informa Keras 3.14.1 y fecha de guardado 2026-07-10; su arquitectura coincide con el script y recibe 24 entradas. Esto verifica metadatos, no la calidad predictiva ni la carga efectiva en el entorno actual.

| Grupo | Entradas |
| --- | --- |
| Calendario, 9 | Seno/coseno de hora, día semanal y día anual; laboral, festivo y fin de semana. |
| Participación espacial, 1 | `region_comuna_share`. |
| Sectores, 5 | `share_I`, `share_R`, `share_C`, `share_P`, `share_T`. |
| Escala territorial, 1 | `is_comuna`. |
| Temperatura, 8 | Temperatura contemporánea y rezagos de 1 a 7 horas. |

No es una red recurrente ni recibe rezagos de demanda en ese contrato. Aprende una forma de carga estandarizada. En inferencia:

`L(z,t) = mu(z,y) + sigma(z,y) * f(X(z,t))`

`scaling_engine.py` calcula `mu = energía_anual / horas_del_año` y `sigma = a * mu**b`. El notebook de reconstrucción comunal fija `a = exp(-1.1315)` y `b = 0.8988`. Esos coeficientes deben estimarse y validarse con datos alemanes. Poner un consumo anual como entrada de escala no garantiza que la integral de las predicciones lo reproduzca: la media anual de la salida de la red puede no ser cero.

El notebook global configura entrenamiento 2018–2019, validación 2020 y prueba 2021, mientras otros scripts contemplan particiones distintas. La configuración presente no prueba qué partición produjo cada archivo de pesos; hace falta un manifiesto del experimento.

**Limitaciones que afectan a la transferencia**

1. **Cambio de dominio.** Calendario anual en hemisferios opuestos, composición industrial, electrificación de calefacción/transporte, autoconsumo y hábitos pueden modificar la relación entre entradas y carga. Invertir seis meses el calendario o transformar temperaturas no garantiza una transferencia correcta. Estas diferencias deben medirse en el conjunto alemán.
2. **Normalización con información del año objetivo.** El preprocesamiento calcula medias y desviaciones de la demanda por territorio y año antes de evaluar. Es admisible para reconstrucción condicionada a estadísticas conocidas; no constituye validación de un pronóstico con información disponible al inicio del año. Además, la evaluación con sigma observada no mide el error de la sigma estimada en producción.
3. **Desagregación no identificada por etiquetas sectoriales.** `inference.py` resta la predicción sin un sector de la predicción total y recorta negativos. Al anular un share, los shares dejan de sumar uno y el escenario puede salir del dominio de entrenamiento. No se impone aditividad, conservación anual sectorial ni una interpretación causal de la resta.
4. **Dos reglas de escalamiento.** `mu_sigma_reg.py` y el notebook de entrenamiento calculan parámetros sin sector proporcionalmente a `1-share`; la inferencia modular aplica una potencia al consumo remanente. Para `b != 1`, ambas reglas difieren y deben reconciliarse.
5. **Rezagos circulares.** `time_features.py` usa `np.roll`: conecta el final del vector al principio. Para series anuales usa el final de diciembre como pasado de enero del mismo año; sin agrupación puede mezclar territorios. Usar horas previas reales, ordenadas por territorio, y comprobar continuidad horaria.
6. **Implementación y documentación divergentes.** `forecast_edm/main.py` está vacío. El motor espacial modular selecciona un donante cercano de área similar; no implementa el IDW ponderado descrito por el README, aunque los notebooks incluyen procedimientos espaciales más extensos. `shares_engine.py` devuelve `share_region_comuna`, distinto de `region_comuna_share` del modelo; se requiere un adaptador explícito.
7. **Escaladores.** `preprocessing/merge_data.py` serializa su MinMaxScaler antes del ajuste. El notebook global sí guarda su scaler después del ajuste; no corresponde extender el defecto a todos los artefactos. También debe verificarse que temperaturas regionales y comunales llegan en la misma escala física antes del reescalamiento global.
8. **Validación espacial pendiente.** Mezclar filas regionales y comunales no demuestra generalización a territorios nuevos. Una región y sus comunas contienen información agregada relacionada; un test espacial debe retirar también agregados que incluyan el territorio reservado.

**Dependencias y portabilidad**

| Bloque | Dependencias actuales | Diagnóstico |
| --- | --- | --- |
| Tablas y estadística | pandas, NumPy, SciPy, PyArrow | Reutilizable para Alemania; contratos de unidades y claves necesarios. |
| ML | TensorFlow/Keras, scikit-learn, joblib | Reutilizable; fijar versiones compatibles con los artefactos y verificar carga/inferencia. |
| Geografía y clima | GeoPandas, xarray, rioxarray, netCDF4; GDAL/GEOS/PROJ en Docker | Reutilizable; reemplazar capas, rutas y CRS chileno. |
| Calendario | holidays | La función acepta país/subdivisión; usar DE y calendario de cada Land, verificando festivos locales. |
| Selección de rezagos | nolitsa, numba | Útil para rehacer ingeniería térmica; no imprescindible para ejecutar un contrato fijo de ocho temperaturas. |
| Exploración/exportación | Jupyter, matplotlib, seaborn; SQLAlchemy, psycopg2 | Mantener separados del entorno mínimo de inferencia. |

`requirements.txt` utiliza mínimos abiertos y varias dependencias sin versión. `nolitsa` se descarga desde `master.zip`; tampoco está fijado a commit. Por tanto, el Dockerfile no garantiza reproducibilidad temporal. Su comando ejecuta `train_mlp.py`, no `train_mlp_v2.py`, y las rutas relativas de datos requieren comprobar el directorio de ejecución. Prioridad: fijar un entorno probado, rutas configurables, manifiesto de features, pruebas de carga y un comando integral. No se instaló ni compiló ese entorno en esta revisión.

**Fuentes homólogas alemanas y su función**

| Insumo chileno / necesidad | Fuente alemana verificada | Resolución y uso | Brecha relevante |
| --- | --- | --- | --- |
| Carga agregada CEN | [SMARD: descarga](https://www.smard.de/home/downloadcenter), [definición de consumo](https://www.smard.de/page/en/wiki-article/6078/6036/electricity-consumption) | Datos de mercado con intervalos de 15 minutos; referencia agregada y selección territorial del portal. | No es una base de retiros por barra ni una medición municipal. Diferenciar carga de red de carga residual. |
| Áreas eléctricas agregadas | [ENTSO-E: Total Load](https://transparency.entsoe.eu/load-domain/r2/totalLoadR2/show) | País, zona de oferta y área de control; resolución según serie. | Seleccionar dominio histórico correcto: no asumir que una zona de oferta representa exclusivamente Alemania o un Land. |
| Carga local observada | [Stromnetz Berlin: curvas de carga](https://www.stromnetz.berlin/uber-uns/veroffentlichungspflichten/energiewirtschaftsgesetz-enwg/) | Archivos Excel históricos de Lastverlauf y por nivel de tensión. | Auditar intervalos, límites y significado de cada curva; no sumar niveles de tensión sin evitar doble conteo. Publicación accesible; comprobar condiciones de reutilización. |
| Balance nacional BNE | [AG Energiebilanzen: tablas](https://ag-energiebilanzen.de/wp-content/uploads/EBD24e_Auswertungstabellen_deutsch.pdf) | Series anuales por portador y sectores; electricidad para energía anual y shares. | Seleccionar electricidad de consumo final, no energía primaria ni consumo total de todos los combustibles. |
| Balances regionales BRE | [Estadística oficial: energía y acceso al LAK](https://www.statistikportal.de/de/energie) | Balances por Land; sirven como restricciones anuales. | El portal LAK devolvió 403 en esta consulta; no se verificó exhaustivamente su cobertura descargable por año/estado. |
| Ejemplo concreto de balance regional | [Berlín-Brandenburgo: balances](https://www.statistik-berlin-brandenburg.de/e-iv-4-j/) | Series y reportes anuales; la página consultada publica 2023. | No inferir que todos los estados tienen el mismo último año disponible. |
| Energía anual comunal / facturación | [Berlín: consumo eléctrico Umweltatlas](https://daten.berlin.de/datensaetze/energieverbrauch-strom-umweltatlas-wfs-238921d9) | Consumo 2022 agregado por manzanas, distritos y códigos postales; acceso WFS. | Excluye autoconsumo y pérdidas; hay manzanas suprimidas por privacidad. No son curvas horarias ni garantiza separar cinco sectores. |
| Temperatura ambiente | [ERA5-Land](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=documentation), [DWD CDC](https://www.dwd.de/EN/ourservices/cdc/cdc.html?lsbId=646268) | ERA5-Land horario desde 1950; DWD aporta observaciones meteorológicas y productos climáticos. | ERA5-Land preserva la familia de datos chilena; estaciones DWD requieren cobertura e interpolación. Ponderar por población/actividad según objetivo. |
| Población, viviendas y calefacción | [Zensus 2022: datos GIS](https://www.destatis.de/zensus2022?nn=1344278) | Grillas de 100 m, 1 km y 10 km, según producto; datos censales. | Proxies espaciales, no consumo medido; actualizar años posteriores y gestionar supresiones. |
| Actividad económica sectorial | [Bundesagentur für Arbeit: empleo](https://statistik.arbeitsagentur.de/DE/Navigation/Statistiken/Fachstatistiken/Beschaeftigung/Beschaeftigte/Beschaeftigte-Nav.html), [Regionaldatenbank vía Statistikportal](https://www.statistikportal.de/de/energie) | Empleo por actividad y territorio; energía industrial en estadísticas regionales. | Detalle sectorial y territorial depende de tabla y confidencialidad. Empleo no equivale a MWh; requiere intensidades por rama. |
| Límites y jerarquía geográfica | [BKG: documentación VG250](https://sgx.geodatenzentrum.de/web_public/gdz/dokumentation/deu/vg250.pdf) | Divisiones administrativas hasta municipio. | Versionar límites y códigos AGS/ARS y su cruce con NUTS; barrios pueden necesitar capas municipales adicionales. |
| Perfiles sectoriales de referencia | [BDEW: actualización de perfiles 2025](https://www.bdew.de/media/documents/2025-03-17_AWH_Aktualisierte_SLP_Strom_2025_Ver%C3%B6ffentlichung.pdf) | Perfiles estándar para construir una referencia temporal. | Son perfiles representativos; una reconstrucción basada en ellos no es medición local independiente. |
| Desagregación alemana existente | [DemandRegio: informe](https://www.ffe.de/wp-content/uploads/2020/10/DemandRegio_Abschlussbericht.pdf), [disaggregator](https://github.com/DemandRegioTeam/disaggregator) | Modelación espacial a Kreis/NUTS-3 y temporal principalmente cuartohoraria; hogares, servicios e industria. | Útil como baseline, insumos o preentrenamiento; sus salidas son modeladas y no deben presentarse como verdad observada. |
| Generación distribuida/autoconsumo | [MaStR: exportación](https://www.marktstammdatenregister.de/mastrhilfe/subpages/datenexport.html) | Registro y exportaciones de instalaciones; covariables tecnológicas. | No proporciona por sí mismo demanda horaria ni autoconsumo horario medido. |

SMARD permite reutilización bajo CC BY 4.0 con atribución a Bundesnetzagentur | SMARD.de ([condiciones](https://www.smard.de/home/datennutzung)). La ficha Umweltatlas declara dl-de-zero-2.0. El código disaggregator declara GPLv3; las licencias de datasets deben registrarse por separado. Acceso público a una página no sustituye la revisión de licencia y metadatos de cada descarga.

**Homologación sectorial**

| MERLIN | Correspondencia inicial alemana | Decisión propuesta |
| --- | --- | --- |
| Residencial R | Haushalte | Correspondencia razonable; añadir proxies de vivienda y calefacción. |
| Industrial I | Industrie / Verarbeitendes Gewerbe | Verificar cobertura de minería, construcción y autoconsumo industrial. |
| Comercial C y Público P | GHD / CTS: comercio y servicios | Trabajar inicialmente con C+P; separarlos solo donde existan inventarios o consumos públicos identificables. |
| Transporte T | Verkehr | Usar únicamente electricidad; diferenciar tracción ferroviaria, recarga y asignación territorial. |
| Actividades sin correspondencia directa | Agricultura y otras ramas según balance | Documentar inclusión o crear categoría adicional, sin perder energía silenciosamente. |

La separación C/P no se obtiene automáticamente de un balance GHD. Si se cambia la taxonomía, debe cambiar el contrato del modelo y reentrenarse; conservar cinco columnas con un reparto arbitrario no hace equivalentes los datos.

**Diseño recomendado para Alemania**

Primero fijar el perímetro: consumo final eléctrico o retiro de red. Comparar el consumo final estadístico con carga de red exige un puente contable para autoconsumo, pérdidas, almacenamiento y cobertura. Las diferencias deben documentarse; no absorberlas todas en un factor estadístico.

Construir tablas separadas de carga observada, energía anual/mensual sectorial, clima, calendario y correspondencias geográficas. Guardar `timestamp_utc`, identificador territorial, nivel, territorio padre, año de límites, unidad, fuente, estado observado/modelado e indicador de imputación. Generar calendario en `Europe/Berlin`, con UTC para uniones; respetar las horas repetidas/ausentes por cambio horario y años bisiestos. Si la fuente expresa MW medios por cuarto de hora, multiplicar por 0,25 h y sumar a MWh horarios; si ya expresa energía por intervalo, sumar directamente.

Reutilizar ERA5-Land para un primer experimento comparable y DWD para contraste. Cambiar el CRS chileno EPSG:32719 por una proyección adecuada al análisis alemán/europeo; elegirla según si se calculan distancias o áreas. Sustituir imputación por cercanía/área por una distribución apoyada en población, empleo por rama y edificios, calibrada a consumos conocidos.

Comparar cuatro alternativas con las mismas particiones: perfil alemán estándar escalado; MERLIN chileno congelado; MERLIN ajustado con datos alemanes; MLP de la misma arquitectura entrenado desde cero en Alemania. En el modelo congelado se conserva el escalador chileno; ajustar un MinMaxScaler alemán manteniendo los pesos cambiaría el significado de las entradas. El ajuste fino debe tratar conjuntamente esa transformación y la red. Si la taxonomía cambia, el experimento con pesos originales pierde comparabilidad directa.

Imponer conservación donde los datos lo permitan: suma de sectores igual a total horario, suma territorial igual al agregado compatible y energía anual igual al balance correspondiente. Una opción es estimar perfiles sectoriales no negativos, normalizarlos por energía anual y reconciliarlos con las curvas agregadas. Estas restricciones mejoran coherencia, pero no crean información horaria local: persiste incertidumbre sobre la forma de cada perfil.

Validar años completos reservados y territorios no vistos. Separar métricas de forma horaria, energía anual, picos y cierre territorial/sectorial. Reportar MAE, RMSE normalizado por demanda media, sesgo energético, error de magnitud/hora de punta y error por estación/tipo de territorio. Evitar depender de MAPE en consumos cercanos a cero. Si un balance anual se usa para calibrar, el cierre frente a ese mismo balance es una restricción satisfecha, no una validación independiente.

Para un producto nacional municipal, procesar por territorio/año y escribir Parquet particionado. Como referencia de tamaño, 10.000 zonas implican 87,6 millones de filas por año y unos 8,4 GB solo para 24 features float32, sin DataFrames, metadatos ni copias. El batching de Keras no evita construir matrices completas en memoria.

**Piloto concreto propuesto**

Empezar por Berlín y usar 2022 como candidato para comprobar distribución anual por distritos, sujeto a verificar coincidencia con los archivos de carga y balances. La combinación disponible es: curvas de Stromnetz Berlin para el agregado, Umweltatlas 2022 para energía local, balance oficial para composición sectorial, Zensus para proxies y ERA5-Land/DWD para clima. Los datos de distrito permiten validar magnitudes espaciales; no validan por sí solos las curvas horarias distritales.

Primero reproducir y evaluar el agregado urbano en años reservados. Después desagregar a distritos con energía anual conocida y declarar los perfiles como estimaciones. Para demostrar precisión horaria distrital se requieren curvas independientes de distritos, alimentadores u otros conjuntos de clientes con correspondencia espacial verificable. Incorporar luego territorios de estructura industrial y rural para probar generalización; un único caso urbano no valida Alemania completa.

La decisión de expansión debe depender de superar los baselines alemanes, mantener cierre energético y explicar los errores de pico y la incertidumbre local. Con fuentes públicas puede construirse un modelo alemán de estimación territorial; para reclamar una réplica supervisada comunal/horaria del caso chileno aún es necesario cerrar la brecha de etiquetas locales y de correspondencia entre red y territorio.
