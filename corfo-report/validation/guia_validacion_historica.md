# Factibilidad y guía para extender la comparación BRE a 2018–2023

Fecha de revisión: 14 de septiembre de 2026. Base del repositorio: `603de6f`. Estado: diagnóstico y plan de ejecución; no se ejecutó una nueva inferencia ni se generaron métricas históricas en esta revisión.

## Dictamen y orden recomendado

**La reconstrucción regional de años anteriores a 2024 es factible con el modelo global existente. Recomiendo empezar por 2023**, porque el BRE contiene los 80 registros región–sector y la temperatura tiene cobertura horaria completa para las 16 regiones. No hace falta reentrenar para ejecutar esta reconstrucción condicionada al balance.

Luego se puede abordar 2022, resolviendo dos referencias de Transporte ausentes, y finalmente 2021–2018. La reconstrucción 2017 tiene temperatura, pero no BRE observado del mismo año en el CSV disponible; no es candidata a este contraste sin una fuente adicional.

Extender el período no convierte automáticamente la comparación en validación independiente. En el flujo regional, los consumos del BRE del año reconstruido determinan los shares y el escalamiento. Por ello, compararlos luego con las predicciones mide consistencia anual con el balance de entrada. Para medir capacidad de pronóstico fuera de muestra se necesita otro diseño, descrito como alternativa pendiente de acuerdo al final.

## Qué se inspeccionó

- Estructura del repositorio, scripts de los dos prototipos, notebooks de preparación y evaluación y capa de reportabilidad. `prototipo_2` es antecedente de desarrollo; parte del preprocesamiento comunal global todavía referencia datos de ese directorio.
- Modelo global, contrato de columnas y metadatos Keras; particiones Parquet de entrenamiento, validación y prueba.
- Cobertura temporal y espacial de temperatura, rezagos, demanda regional, shares comunales y BRE en el directorio externo.
- Código de calendario, escalamiento, desagregación, exportación y cálculo APE/MAPE/KPI.

La inspección no cargó el modelo para inferencia, no ajustó pesos, no modificó los datos originales ni evaluó exhaustivamente cada salida incrustada en notebooks. La carpeta NetCDF original devolvió permiso denegado al inventariarla; los Parquet climáticos procesados sí fueron leídos y bastan para la ruta regional propuesta.

## Inventario verificado por año

| Año | BRE: regiones / registros sectoriales | Temperatura con 7 rezagos | Uso en particiones globales disponibles | Factibilidad del contraste |
|---|---|---|---|---|
| 2018 | 16 / 75 de 80 | 8.760 horas por región | Entrenamiento, desde agosto en los metadatos | Reconstrucción posible; faltan cinco referencias de Transporte; no es prueba fuera de muestra |
| 2019 | 16 / 75 de 80 | 8.760 horas por región | Entrenamiento | Posible con las mismas reservas; faltan cinco referencias de Transporte |
| 2020 | 16 / 76 de 80 | 8.784 horas por región | Validación utilizada para selección/early stopping | Posible; faltan cuatro referencias de Transporte; no es prueba final independiente |
| 2021 | 16 / 75 de 80 | 8.760 horas por región | Prueba | Posible; faltan cinco referencias de Transporte; comparar BRE sigue siendo consistencia condicionada |
| 2022 | 16 / 78 de 80 | 8.760 horas por región | Ausente de las tres particiones globales inspeccionadas | Buen segundo caso, tras aclarar dos faltantes |
| 2023 | 16 / 80 de 80 | 8.760 horas por región | Ausente de las tres particiones globales inspeccionadas | Mejor primer caso: referencia y clima completos |

Las particiones verificadas son `data/processed/ds_comunal/{train,val,test}_metadata_global.parquet`: 2018–2019, 2020 y 2021, respectivamente. Coinciden con `process_all_data.ipynb`. Esto describe los archivos presentes, pero no demuestra qué versión exacta de ellos produjo los pesos: falta el manifiesto de entrenamiento. Por tanto, 2022–2023 son candidatos fuera de las particiones disponibles, no años certificados como nunca vistos por el modelo.

El modelo archivado tiene 24 entradas, metadatos Keras 3.14.1 y fecha de guardado 2026-07-10. No se verificó su carga en un entorno de inferencia durante esta tarea. En el entorno `h2integrate`, usado solo para leer Parquet, están pandas/PyArrow y no se encontraron TensorFlow/Keras ni holidays; deberá localizarse o preparar un entorno MERLIN compatible.

### Referencias sectoriales ausentes

| Año | Regiones sin fila de Transporte en el CSV BRE |
|---|---|
| 2018 | Arica y Parinacota, Atacama, Coquimbo, Magallanes, Tarapacá |
| 2019 | Aysén, Arica y Parinacota, Atacama, Magallanes, Tarapacá |
| 2020 | Arica y Parinacota, Atacama, Magallanes, Tarapacá |
| 2021 | Aysén, Arica y Parinacota, Atacama, Magallanes, Tarapacá |
| 2022 | Aysén, Los Ríos |

Las filas presentes tienen valores positivos. **Ausencia no equivale a consumo cero.** El código actual de shares rellena ausencias con cero y `calcular.py` utiliza un `defaultdict` que también puede devolver cero. Ese comportamiento no debe heredarse silenciosamente al ampliar la evaluación. Si la fuente oficial confirma un cero real, APE es indefinido con denominador cero; si el dato falta, se debe recuperar o declarar cobertura parcial. En ninguno de esos casos corresponde publicar un “MAPE de 16 regiones” excluyendo registros sin indicarlo. La falta de Transporte también condiciona la suma regional y los shares usados en inferencia, aunque los otros cuatro sectores estén completos.

## Insumos para la reconstrucción regional

Raíz externa utilizada: `/srv/compartido/inbox/datos_modelos_MERLIN_EDM_prot_3/`.

| Insumo | Archivo o procedimiento existente | Para qué se requiere | Estado |
|---|---|---|---|
| Pesos de la red global | `models/ds_comunal/best_merlin_mlp_global.keras` | Forma horaria total y escenarios sin sector | Disponible; falta prueba de carga |
| Escalador de temperatura | `models/scaler_temp_global.pkl` | Transformación consistente con entrenamiento | Disponible; usar transform, no volver a ajustar |
| Contrato de entrada | `data/rec_2024_2025/columns.txt` | Nombres y orden de 24 variables | Disponible |
| Temperatura regional física y rezagos | `data/interim/temperatura_regional_lagged.parquet` | Temperatura contemporánea y siete horas previas | Disponible, completo 2018–2023, sin nulos; continuidad horaria comprobada |
| Temperatura regional física original | `data/interim/temperatura_regional_horaria.parquet` | Regenerar rezagos y controles | Disponible desde 2017; unidades coherentes con °C en código y rangos inspeccionados |
| Energía anual regional y sectorial | `data/raw/wp2_elec_input_sector_shares_raw.csv` | Shares, intensidad regional y parámetros físicos | Disponible 2018–2024; faltantes históricos detallados arriba |
| Alias de regiones | `data/raw/reg_alias.json` | Cruzar clima, balance y regiones | Disponible, 16 regiones |
| Calendario y festivos | `time_features.py`, fechas horarias, holidays CL/subdivisión | Nueve variables de calendario | Generables; fijar convención temporal y versión de festivos |
| Parámetros físicos | `A_PARAM=exp(-1.1315)`, `B_PARAM=0.8988`; `scaling_engine.py` | Escalamiento anual total y sin sectores | En el flujo; conservar para el caso comparable y documentar procedencia/calibración pendiente |
| Geometría regional | `data/raw/capa_regional.gpkg` | Exportar GeoPackage/mapas y homologar límites | Disponible; no es necesaria para calcular solo tablas |

No se necesita la demanda horaria real para ejecutar la ruta de reconstrucción regional condicionada al BRE. Sí se necesita para reentrenar y para una eventual evaluación horaria de referencia. La facturación comunal y las ventas a clientes libres tampoco son necesarias para este primer caso regional.

### Contrato de 24 entradas

1. Calendario: `hour_sin`, `hour_cos`, `dow_sin`, `dow_cos`, `doy_sin`, `doy_cos`, `is_working_day`, `is_holiday`, `is_weekend`.
2. Participación territorial: `region_comuna_share`.
3. Sectores: `share_I`, `share_R`, `share_C`, `share_P`, `share_T`.
4. Escala territorial: `is_comuna=0` para la salida regional.
5. Clima: `temperatura`, `temp_t - 1`, …, `temp_t - 7`.

El orden exacto debe leerse de `columns.txt`. No entran rezagos de demanda. Metadatos como región, año, fecha, mu y sigma se conservan fuera de X para identificar y desescalar las predicciones.

## Paso a paso propuesto

### 1. Fijar el primer experimento y preservar el caso 2024

Caso recomendado: **reconstrucción regional condicionada al BRE 2023, cinco sectores, modelo global congelado**. Mantener intactos los resultados y KPI de 2024. Registrar hashes de modelo, scaler, columnas, BRE, temperatura, alias y parámetros; identificar commit y entorno. No usar los modelos `caso_1/2/3` en sustitución del global porque pertenecen a otra cadena de preparación.

Producto: configuración y manifiesto del caso 2023. El identificador debe distinguir año, modelo y referencia de escalamiento.

### 2. Preparar un entorno de inferencia compatible

Identificar primero el entorno utilizado en la ejecución original. Comprobar carga del `.keras`, ajuste del scaler y correspondencia de sus ocho entradas climáticas. Fijar versiones de TensorFlow/Keras, scikit-learn/joblib, NumPy, pandas/PyArrow y holidays; GeoPandas solo es necesaria si se exporta la capa geográfica. No basta con asumir que `requirements.txt`, con versiones abiertas, reproduce el entorno del modelo archivado.

Producto: entorno documentado y prueba pequeña de carga/predicción con forma de entrada `(n, 24)`. No se ha realizado todavía.

### 3. Parametrizar el flujo sin sobrescribir 2024–2025

Usar [capa_regional.ipynb](../../prototipo_3/rec_2024_2025/capa_regional.ipynb) como referencia ejecutable del proceso. Para una implementación repetible conviene extraer un punto de entrada con parámetros de año, raíz de datos y directorio de salida. Ese comando histórico **todavía no existe**; `forecast_edm/main.py` está vacío.

En una copia de trabajo del notebook, los cambios mínimos son `AÑOS_TARGET=[2023]`, rutas absolutas al modelo/scaler/columnas/BRE/clima y `OUT_DIR` distinto. Sustituir también el `open` literal de `columns.txt`, no solo `COLUMNS_PATH`. Filtrar la temperatura al año objetivo: cambiar `AÑOS_TARGET` por sí solo no controla todas las filas que llegan a inferencia.

Salida pesada propuesta, externa al repositorio: `data/rec_historica/2023/results/capas_regionales/`. Es una ruta propuesta, aún no creada ni poblada.

### 4. Preparar clima y calendario completos

Reutilizar el Parquet con rezagos físicos y filtrar a 2023 **después** de disponer de los rezagos. Para 2023 deben quedar 140.160 filas, una por región y hora. El archivo histórico contiene horas anteriores para generar correctamente los primeros rezagos de enero.

Evitar ejecutar de nuevo el bloque `build_temperature_lags` basado en `np.roll` sobre el año filtrado: conectaría diciembre del año objetivo con su comienzo. `calc_lags_reg.py` utiliza `groupby(region).shift`, y el archivo existente ya tiene esos rezagos. Construir el calendario con la convención temporal que usó el entrenamiento; los timestamps inspeccionados son sin zona explícita, por lo que no se debe convertir a hora local o UTC sin verificar su origen. Mantener tratamiento de años bisiestos y festivos regionales.

Aplicar **una sola vez** `scaler_temp_global.transform` a temperatura y sus siete rezagos. Los metadatos globales `train/val/test` ya están escalados y no deben transformarse otra vez. El notebook global recupera temperaturas físicas regionales antes del escalamiento común; usar los Parquet climáticos físicos evita mezclar escalas.

### 5. Construir los shares del año objetivo

Filtrar BRE a 2023, pivotar por región/sector y verificar 80 combinaciones únicas con referencia positiva. Calcular:

`E_region = suma_s E_region,s`; `share_s = E_region,s / E_region`; `region_comuna_share = E_region / suma_regiones E_region`.

No hace falta extrapolar 2023: el balance de ese año está presente. Unir por año y alias regional, exigir relación muchos-a-uno desde horas a referencia anual y fallar ante duplicados/faltantes en vez de continuar con advertencias.

### 6. Calcular parámetros y ejecutar la red

Convertir GWh del BRE a MWh para el escalamiento. Con H horas del año:

`mu_total = E_region_MWh / H`; `sigma_total = exp(-1.1315) * mu_total**0.8988`.

Para cada sector, calcular los parámetros sobre el consumo regional sin dicho sector, como en `calculate_scaling_parameters`. Ejecutar [predict_and_disaggregate](../../prototipo_3/src/forecast_edm/inference.py): una predicción total y cinco escenarios con el share del sector apagado; desescalar, restar y aplicar los recortes existentes. No imponer a posteriori cierre exacto al BRE antes de medir el error, pues eliminaría la discrepancia que se quiere evaluar.

Producto: serie horaria total y sectorial con región, año y timestamp. Verificar finitud, no negatividad, filas esperadas y ausencia de duplicados. La suma de sectores no está garantizada por esta arquitectura; conservar el total propio de la red.

### 7. Agregar y contrastar con el BRE del mismo año

Sumar MWh horarios por región/sector y dividir por 1.000 para obtener GWh. Comparar el total modelado con la suma regional BRE; comparar cada sector con su referencia correspondiente. Para 2023 completo se esperan 96 APE y seis MAPE (cinco sectores y Total).

Generalizar [calcular.py](../../analisis/ape_bre/calcular.py): hoy fija raíz y archivo 2024–2025, exige 32 filas e itera solo `[2024, 2025]`. Debe recibir archivo/años de evaluación, validar `16 × número de años`, rechazar referencias faltantes y separar el modo BRE observado de la extrapolación. El reporte `reportar_kpi.py` también fija 2024; debe ampliarse por año sin reemplazar la evidencia existente.

APE regional = `100 * abs(pred - BRE) / abs(BRE)`. MAPE sectorial anual = media de los 16 APE. Si se desea además un MAPE temporal por región, sería el promedio de sus APE entre años comparables y debe identificarse como otra agregación; no mezclarlo con el MAPE entre regiones.

### 8. Incorporar la evidencia CORFO y ampliar años

Guardar comparaciones, gráficos de error y manifiesto bajo `corfo-report/validation/`, separados por año o con columna explícita. Guardar tablas de simulación sin comparación en `results/tables` y figuras de simulación en `results/figures`; las series pesadas quedan fuera de Git. Actualizar índice y ficha.

Para cada año, evaluar el KPI de cinco sectores con umbral **estricto MAPE < 35 %**, sin contar Total como sexto sector. Reportar denominador y referencias disponibles, sectores que no cumplen y estado de aceptación del comparador. No anunciar cumplimiento histórico hasta ejecutar la inferencia y calcular las métricas. No seleccionar solamente años/sectores favorables.

Después del piloto 2023, abordar 2022 y los faltantes de Transporte; continuar 2021–2018 según cobertura y finalidad. Conservar las etiquetas entrenamiento/validación/prueba/candidato no usado en las particiones.

## Qué cambia si se reconstruye desde comunas

La ruta comunal requiere además temperatura horaria comunal del año, consumos mensuales comunales por sector, mapa comuna–región, geometrías y reglas de imputación para comunas sin datos. `shares_comunales.parquet` contiene 2018–2021, 212 comunas por año y 14 regiones; no demuestra cobertura completa mensual para todas las comunas. No contiene 2022–2023.

Para reconstruir esos últimos años por comunas habría que recuperar facturación de regulados y ventas de clientes libres contemporáneas, o acordar una imputación/proyección explícita. Sus predicciones agregadas a región podrían contrastarse con BRE, previa homologación del perímetro y sin reutilizar el balance evaluado para corregir el resultado. Esta ruta es más exigente que usar las salidas regionales directas y no se recomienda como primer paso.

## Alternativas para una validación más independiente — requieren acuerdo

1. **BRE reservado del año objetivo:** generar inputs de energía y shares sin usar ese BRE (por ejemplo, fuentes independientes o solo balances de años previos), y usarlo exclusivamente como referencia. Para un pronóstico estricto también deben congelarse entrenamiento, parámetros y todos los insumos a la fecha de corte. No ajustar la extrapolación con 2024 para evaluar 2023. Si se usa clima observado del año, describir el experimento como retrospectivo condicionado al clima, no como pronóstico meteorológico ex ante.
2. **Contraste horario con demanda CEN:** existe `demanda_regional_horaria.parquet` para 2018–2023, pero cubre 14 regiones; Aysén y Magallanes no están. En 2018 empieza en agosto; 2022 tiene entre 7.320 y 8.040 registros por región; en 2023 hay 8.759 horas en 13 regiones y 8.760 en Maule. No sumar esas observaciones parciales y compararlas como si fueran energía anual completa. Homologar timestamps y cobertura antes de evaluar perfiles horarios. La correspondencia entre retiros y consumo final sigue requiriendo trazabilidad.

Estas alternativas no se ejecutaron ni se añadieron a los KPI. Deben acordarse antes de introducir otro comparador o una metodología diferente de la reconstrucción BRE condicionada solicitada.

## Decisión de inicio

El siguiente trabajo concreto es implementar y ejecutar el piloto **regional 2023 con modelo congelado**, conservando la etiqueta de consistencia anual BRE. Los pasos pendientes son prueba del entorno ML, parametrización del flujo, generalización del evaluador y ejecución. El inventario ya confirma que no se necesita una nueva descarga climática para ese piloto. El diagnóstico no asegura un determinado MAPE antes de ejecutar el modelo.

## Evidencia de esta revisión

- [Inventario de insumos y particiones](inventario_historico.json).
- [Particiones globales y recuperación de temperaturas](../../prototipo_3/notebooks/process_all_data.ipynb).
- [Preparación de rezagos regionales](../../prototipo_3/preprocessing/calc_lags_reg.py).
- [Reconstrucción regional existente](../../prototipo_3/rec_2024_2025/capa_regional.ipynb).
- [Método de escalamiento](../../prototipo_3/src/forecast_edm/scaling_engine.py).
- [Desagregación](../../prototipo_3/src/forecast_edm/inference.py).
- [Evidencia KPI actual](cumplimiento_kpi.md).
