# Ficha de evidencia — MERLIN EDM Chile 2024

- **ID:** `CORFO-MERLIN-EDM-CHILE-BRE2024`.
- **Estado:** reproducible pendiente de validación.
- **Responsable:** Raimundo, según matriz de evidencia de merlin-index; confirmar responsabilidad de cierre.
- **Revisor/aceptación formal:** pendiente de designación; no hay acta de aceptación en este paquete.
- **Fecha de corte:** 14 de septiembre de 2026.
- **Repositorio:** FCR-CSET-Merlin/MERLIN_EDM. Commit base y hashes de scripts: [manifiesto](manifiesto_edm_2024.json). Commit que produjo los pesos y la inferencia original: no establecido.
- **Aporte:** evidencia de consistencia anual regional y sectorial eléctrica; contribución parcial a HC2/OE2.

## Alcance y método

Chile, 16 regiones, 2024. Sectores Residencial, Comercial, Público, Industrial y Transporte. Salidas anuales en GWh, derivadas de predicciones horarias. No se evalúa demanda térmica ni Alemania. No se trata de demanda energética total de transporte ni de todos los combustibles.

APE = 100 × |modelo − BRE| / |BRE|. MAPE sectorial = media aritmética de los 16 APE. Meta: MAPE < 35 % en mayoría de sectores; mayoría se operacionaliza como al menos 3 de 5. Total se excluye del denominador. No hay ponderación energética ni exclusiones de regiones. No se usan datos extrapolados de 2025 para la decisión.

## Datos y procedencia

| Insumo | Fuente y transformación | Cobertura/unidades | Versión, acceso y limitación |
|---|---|---|---|
| GeoPackage regional | Salida de capa_regional.ipynb; agregado anual de predicciones | 16 regiones, 2024–2025, GWh | SHA-256 y ruta en manifiesto; no se usa geometría en la métrica |
| CSV BRE | wp2_elec_input_sector_shares_raw.csv; selección 2024 y suma por región/sector | Historia 2018–2024; valores tratados como GWh en el flujo | SHA-256 en manifiesto; falta vincular descarga oficial, versión editorial y licencia |
| Alias | reg_alias.json; cruce de nombres regionales | 16 regiones | SHA-256 en manifiesto |

Las fuentes permanecen en almacenamiento local externo. El paquete identifica los archivos usados; no acredita por sí solo su cadena completa de adquisición o licencia. No se transforma CRS para esta comparación tabular.

## Reproducción y resultados

`python analisis/ape_bre/reportar_kpi.py`, desde la raíz. Python 3, bibliotecas estándar; no requiere TensorFlow para las métricas. Sin semilla: cálculo determinista sobre artefactos existentes. Entradas y salidas: [manifiesto](manifiesto_edm_2024.json).

| Indicador | Valor | Evidencia |
|---|---|---|
| MAPE total regional | 1,11233 % | [MAPE 2024](ape_bre/mape_regional_bre_2024.csv) |
| Sectores con MAPE < 35 % | 4/5; 80 % | [KPI por sector](kpi_validation.csv) |
| Condición numérica de mayoría, Chile eléctrico 2024 | Satisfecha | [Evaluación](cumplimiento_kpi.md) |
| HC2 completo | No acreditado por este paquete | Brechas abajo |

## Verificación y límites

Se ejecuta la regeneración de métricas a partir del GeoPackage y CSV. El script comprueba 96 pares únicos de 2024, 16 regiones por sector, referencias positivas, APE recalculados, promedio MAPE y umbral estricto sin redondeo. Esto verifica el cálculo, no valida independientemente la inferencia.

BRE es una referencia usada en el escalamiento. El resultado respalda consistencia anual; no demuestra precisión horaria, desempeño fuera de muestra ni validación independiente. La agregación espacial anual debe ser aceptada por el responsable del KPI antes de presentar el indicador como logro contractual.

## Matriz de compromiso y brechas

| Compromiso | Evidencia disponible | Estado y acción de cierre |
|---|---|---|
| HC2-2, precisión | Chile eléctrico 2024: 4 de 5 sectores bajo 35 % | Condición numérica satisfecha en este alcance; revisión metodológica pendiente. Transporte no cumple (35,02915 %) |
| HC2-1, ≥1 modelo por sector y país | Modelo MLP común con cinco salidas sectoriales y artefactos Chile | Contribución parcial; no equiparar cinco salidas con cinco modelos independientes. Falta matriz completa y ejecución validada por país/sector |
| HC2, Chile y Alemania, demanda térmica y eléctrica | Este paquete aporta electricidad Chile | No acreditado globalmente; faltan Alemania y térmico y la integración con otros modelos |
| R2, modelos operativos en ciudades | Código y resultados regionales | No acredita por sí solo casos urbanos operativos exigidos |
| R1, R3–R7, HC1 y HC3 | Sin evaluación específica en este paquete | No se declara cumplimiento; requieren evidencia de otros casos o entregables |

No se incorporaron otras comparaciones; cualquier nueva referencia o ensayo deberá acordarse con el solicitante.

## Referencias

- [Compromiso HC2 y fecha 29-oct-2026](https://github.com/FCR-CSET-Merlin/merlin-index/blob/a9b855f60c4ad207d7c2544a07e4f43d25356209/05-roadmap/01-antecedentes/Resultados_Excel_CORFO.md).
- [Matriz de compromisos](https://github.com/FCR-CSET-Merlin/merlin-index/blob/a9b855f60c4ad207d7c2544a07e4f43d25356209/08-reportaje-corfo/matriz-compromisos-corfo.md).
- [Matriz de evidencia de modelos](https://github.com/FCR-CSET-Merlin/merlin-index/blob/a9b855f60c4ad207d7c2544a07e4f43d25356209/08-reportaje-corfo/matriz-evidencia-modelos.md).
- [Reporte detallado](ape_bre/resultados_modelo_bre_2024.md).

La matriz central distingue la fecha de cumplimiento HC2 (29 de octubre) de la entrega del reporte (29 de noviembre); confirmar el calendario formal antes del cierre.
