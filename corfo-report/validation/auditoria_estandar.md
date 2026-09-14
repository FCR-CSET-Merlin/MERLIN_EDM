# Revisión del estándar de reportabilidad CORFO

Fecha: 14 de septiembre de 2026. Fuente: [estándar](https://github.com/FCR-CSET-Merlin/merlin-index/blob/a9b855f60c4ad207d7c2544a07e4f43d25356209/08-reportaje-corfo/estandar-estructura-corfo-report.md), commit `a9b855f60c4ad207d7c2544a07e4f43d25356209`.

## Dictamen

La estructura mínima estaba presente. Faltaban el índice tabular obligatorio, trazabilidad del compromiso y evidencia explícita del contraste contra el umbral KPI. Se añaden índice, ficha, manifiesto y generación automática del resumen KPI. La conformidad de la estructura no equivale al cumplimiento del compromiso HC2.

| Requisito | Evidencia / resultado |
|---|---|
| Rutas obligatorias | corfo-report/results/figures, results/tables, validation y README.md presentes |
| README con Main results, Validation, Reproducibility | Índice actualizado con archivo, proceso, fuente y descripción |
| Resultados finales pequeños | CSV KPI en results/tables; APE/MAPE en validation; sin datasets pesados |
| Figuras finales | Carpetas reservadas, sin figuras independientes existentes; no se fabrican evidencias |
| Procedencia y trazabilidad | Ficha, enlaces al código y manifiesto con hashes de entradas, salidas y scripts |
| Automatización | reportar_kpi.py ejecuta cálculo y genera KPI, resumen y manifiesto; documentación interpretativa manual declarada |
| Respeto del código y datos originales | No se mueve código ni datasets externos |
| Conservar carpetas previas | El traslado previo de resultados fue solicitado explícitamente por el usuario. Se conserva reportes/README.md como guía de migración; no se restauran copias manuales de tablas |
| Versionado | Checkpoint 2a35b6a antes de esta ampliación; commit final de evidencia y push conforme al estándar |
| Cumplimiento KPI explícito | Evaluación individual de cinco sectores; 4/5 cumplen umbral local; HC2 completo no acreditado |

## Brechas que no resuelve la organización de archivos

- Falta aceptación de MAPE espacial anual de consistencia como evidencia formal del indicador HC2-2.
- BRE participa en escalamiento: no es una validación independiente.
- Transporte está sobre el umbral; se preserva el resultado sin exclusiones.
- Falta evidencia de Alemania y demanda térmica en este paquete, y la matriz país–sector del proyecto.
- Falta fijar commit de inferencia/entrenamiento original, procedencia editorial/licencia de la referencia y revisión humana formal.

No se declara cumplimiento contractual global ni se calcula avance del proyecto a partir de la existencia de repositorios. Las comparaciones y valores previos se conservan; la única evaluación nueva es el contraste del MAPE 2024 ya calculado con el umbral comprometido.
