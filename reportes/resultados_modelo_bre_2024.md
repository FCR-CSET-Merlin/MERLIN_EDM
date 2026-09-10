# MERLIN EDM — Resultados regionales y sectoriales frente al BRE 2024

Fecha de elaboración: 10 de septiembre de 2026.

## Principales resultados

La demanda anual total estimada por el modelo presenta un MAPE de **1,11 % entre las 16 regiones** respecto al Balance Regional de Energía (BRE) 2024. Los APE del total regional se sitúan entre **0,19 % (Valparaíso)** y **2,41 % (Atacama)**. Las 16 regiones presentan un APE total inferior al 2,5 %.

La desagregación sectorial muestra discrepancias mayores: el MAPE es **1,74 % en Industrial**, **4,69 % en Residencial**, **5,87 % en Comercial**, **8,37 % en Público** y **35,03 % en Transporte**. El buen ajuste del total anual no implica el mismo ajuste en cada sector.

Estos indicadores describen la consistencia de los resultados anuales con el BRE utilizado por el flujo para construir entradas y parámetros de escalamiento. No constituyen una validación independiente del modelo ni evalúan el perfil horario.

## Alcance y procedencia

El desarrollo de `prototipo_3` utiliza un modelo MLP global con variables temporales, temperatura, participaciones territoriales y sectoriales, y parámetros de escalamiento físico. La desagregación sectorial se obtiene mediante diferencias entre la predicción total y escenarios de apagado de sector.

El directorio de resultados contiene capas regionales y comunales en GeoPackage y series de tiempo en Parquet para 2024–2025. Este reporte analiza la **capa regional de 2024**: 16 regiones, cinco sectores y demanda total; 96 comparaciones región–sector, contando el total como categoría adicional. Los resultados comunales no se agregaron ni se mezclaron con la salida regional.

La fuente de predicciones es `wp2_output_demanda_electrica_regional.gpkg`, con columnas `año`, `region`, `cod_region`, `demanda_total_GWh` y `demanda_R_GWh`, `demanda_C_GWh`, `demanda_P_GWh`, `demanda_I_GWh`, `demanda_T_GWh`. El GeoPackage contiene 32 registros en total: 16 regiones por dos años. Los totales anuales se producen sumando las predicciones horarias en MWh y dividiendo por 1.000.

La referencia es `wp2_elec_input_sector_shares_raw.csv`, filtrada a 2024, cruzada mediante `reg_alias.json`. Se mantienen las unidades en GWh. Para cada región, la referencia total corresponde a la suma de Residencial, Comercial, Público, Industrial y Transporte. La demanda total modelada se toma de su columna propia; no se sustituye por la suma de las predicciones sectoriales.

No se incluyen comparaciones de 2025, contra otras fuentes, entre escalas territoriales ni métricas horarias. Su incorporación requiere acordar el alcance con el solicitante.

## Método de cálculo

Para cada región r y sector s (o demanda total):

$$APE_{r,s}=100\frac{|\widehat E_{r,s}-E^{BRE}_{r,s}|}{|E^{BRE}_{r,s}|}$$

El MAPE sectorial es la media aritmética de los 16 errores regionales:

$$MAPE_s=\frac{1}{16}\sum_{r=1}^{16}APE_{r,s}$$

Cada región tiene igual peso, independientemente de su consumo. El MAPE del total no es el promedio de los MAPE sectoriales ni el error del consumo nacional agregado. El valor absoluto elimina el signo: el APE por sí solo no distingue sobreestimación de subestimación.

Se verificaron 96 pares únicos región–categoría, 16 regiones por categoría, referencias positivas y concordancia de cada APE con su fórmula. No se excluyeron regiones. Los cálculos conservan la precisión del CSV; las tablas redondean a dos decimales.

## MAPE entre las 16 regiones

| Categoría | MAPE 2024 | Regiones incluidas |
|---|---:|---:|
| Total | 1,11 % | 16 |
| Residencial | 4,69 % | 16 |
| Comercial | 5,87 % | 16 |
| Público | 8,37 % | 16 |
| Industrial | 1,74 % | 16 |
| Transporte | 35,03 % | 16 |

## APE por región y sector

| Región | Total | Residencial | Comercial | Público | Industrial | Transporte |
|---|---:|---:|---:|---:|---:|---:|
| TARAPACÁ | 2,34 % | 10,42 % | 4,91 % | 8,00 % | 1,19 % | 13,69 % |
| ANTOFAGASTA | 0,25 % | 5,64 % | 17,45 % | 5,15 % | 0,86 % | 33,77 % |
| ATACAMA | 2,41 % | 13,13 % | 14,83 % | 4,98 % | 2,45 % | 238,90 % |
| COQUIMBO | 0,32 % | 7,08 % | 0,51 % | 2,22 % | 1,06 % | 218,89 % |
| VALPARAÍSO | 0,19 % | 0,13 % | 0,82 % | 8,71 % | 2,32 % | 6,05 % |
| LIBERTADOR GENERAL BERNARDO O'HIGGINS | 0,94 % | 1,89 % | 3,45 % | 7,72 % | 0,32 % | 0,71 % |
| MAULE | 1,65 % | 1,20 % | 2,08 % | 4,93 % | 2,21 % | 2,52 % |
| BIOBÍO | 0,54 % | 1,16 % | 0,75 % | 11,75 % | 0,40 % | 1,35 % |
| LA ARAUCANÍA | 1,20 % | 0,29 % | 5,77 % | 9,13 % | 1,68 % | 2,97 % |
| LOS LAGOS | 1,16 % | 4,00 % | 5,79 % | 10,39 % | 3,51 % | 1,28 % |
| AYSÉN DEL GENERAL CARLOS IBÁÑEZ DEL CAMPO | 2,17 % | 1,01 % | 13,98 % | 12,66 % | 3,68 % | 12,17 % |
| MAGALLANES Y DE LA ANTÁRTICA CHILENA | 1,03 % | 15,60 % | 4,27 % | 1,87 % | 4,85 % | 5,72 % |
| METROPOLITANA DE SANTIAGO | 0,75 % | 6,46 % | 1,46 % | 20,92 % | 2,56 % | 1,87 % |
| LOS RÍOS | 1,08 % | 0,86 % | 7,95 % | 7,64 % | 0,32 % | 9,43 % |
| ARICA Y PARINACOTA | 0,72 % | 5,85 % | 3,84 % | 9,22 % | 0,28 % | 4,61 % |
| ÑUBLE | 1,06 % | 0,26 % | 6,05 % | 8,70 % | 0,12 % | 6,53 % |

## Lectura de las discrepancias sectoriales

Transporte concentra las mayores discrepancias relativas: Atacama alcanza **238,90 %** y Coquimbo **218,89 %**. Las magnitudes de referencia de estos casos se muestran a continuación para interpretar el denominador del APE. Ambas regiones se mantienen en el MAPE, sin recorte ni exclusión.

| Región — Transporte | Modelo (GWh) | BRE 2024 (GWh) | APE |
|---|---:|---:|---:|
| ATACAMA | 0,0368 | 0,0109 | 238,90 % |
| COQUIMBO | 0,0230 | 0,0072 | 218,89 % |

En Público destaca la Región Metropolitana con **20,92 %**. En Comercial, Antofagasta alcanza **17,45 %**; en Residencial, Magallanes alcanza **15,60 %**. Estos casos permiten localizar las discrepancias de la desagregación anual sin atribuirlas, a partir de esta comparación sola, a una causa específica.

## Límites de interpretación

El notebook de reconstrucción conserva los consumos del BRE cuando el año ya está disponible y extrapola los años faltantes. Para 2024, el CSV contiene datos del mismo año. El flujo utiliza los consumos para calcular participaciones y parámetros como `mu_total`, que intervienen al devolver las predicciones a unidades físicas. Por ello, la cercanía al BRE debe interpretarse como consistencia con una referencia empleada en el proceso de generación.

La agregación anual permite compensaciones entre errores horarios positivos y negativos. Estos resultados no permiten inferir precisión en puntas, estacionalidad, forma horaria o generalización a años no utilizados. Tampoco establecen un umbral de desempeño aceptable: no se definió uno para este reporte.

La revisión corresponde a los artefactos disponibles y al código del flujo; no se reentrenó ni se volvió a ejecutar la inferencia. La correspondencia exacta entre la versión del código y la ejecución que generó los archivos no se verificó mediante un registro de ejecución.

## Archivos y trazabilidad

- [APE por región y sector, con predicciones y referencias en GWh](ape_region_sector_bre_2024.csv).
- [MAPE entre las 16 regiones](mape_regional_bre_2024.csv).
- [Script del cálculo original](../analisis/ape_bre/calcular.py). Este script genera ambos años; el presente reporte selecciona exclusivamente 2024.
- [Descripción de prototipo_3](../prototipo_3/README.md).
- [Flujo de reconstrucción regional](../prototipo_3/rec_2024_2025/capa_regional.ipynb).
- [Descripción de los artefactos de salida](../prototipo_3/rec_2024_2025/README.md).

Fuentes de datos locales:

- [GeoPackage regional](../../datos_modelos_MERLIN_EDM_prot_3/data/rec_2024_2025/results/capas_regionales/wp2_output_demanda_electrica_regional.gpkg).
- [BRE disponible](../../datos_modelos_MERLIN_EDM_prot_3/data/raw/wp2_elec_input_sector_shares_raw.csv).
- [Alias regionales](../../datos_modelos_MERLIN_EDM_prot_3/data/raw/reg_alias.json).
