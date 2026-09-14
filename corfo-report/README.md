# CORFO Report Results

## Main results

MERLIN EDM aporta evidencia de demanda **eléctrica de Chile, año 2024, 16 regiones y cinco sectores**. El MAPE del total es 1,11 %. Cuatro de cinco sectores quedan bajo 35 % (80 %); Transporte registra 35,03 %. Este resultado cumple la condición numérica local de mayoría del indicador HC2-2, pero **no acredita el cumplimiento global de HC2**. La métrica es espacial sobre energía anual y el BRE interviene en el escalamiento; su aceptación como evidencia de precisión está pendiente de revisión.

| Resultado | Archivo | Script/proceso | Fuente | Descripción |
|---|---|---|---|---|
| Resumen numérico HC2 Chile 2024 | [kpi_summary.csv](results/tables/kpi_summary.csv) | [reportar_kpi.py](../analisis/ape_bre/reportar_kpi.py) | MAPE de las 16 regiones y meta HC2 | Conteo de sectores bajo 35 %, excluyendo Total |
| Reporte interpretativo 2024 | [Reporte BRE](validation/ape_bre/resultados_modelo_bre_2024.md) | Redacción revisada a partir de calcular.py | GeoPackage regional y BRE 2024 | APE, MAPE y limitaciones |

## Validation

| Validación | Archivo | Referencia | Descripción |
|---|---|---|---|
| Umbral comprometido y estado | [Cumplimiento KPI](validation/cumplimiento_kpi.md), [CSV](validation/kpi_validation.csv) | [HC2-2](https://github.com/FCR-CSET-Merlin/merlin-index/blob/a9b855f60c4ad207d7c2544a07e4f43d25356209/05-roadmap/01-antecedentes/Resultados_Excel_CORFO.md) | Resultado por sector, sin redondear para la decisión |
| APE regional y sectorial 2024 | [CSV APE](validation/ape_bre/ape_region_sector_bre_2024.csv) | BRE disponible 2024 | 96 pares: 16 regiones × cinco sectores y Total |
| MAPE espacial 2024 | [CSV MAPE](validation/ape_bre/mape_regional_bre_2024.csv) | Media de los 16 APE por categoría | Sin ponderación por energía |
| Comparaciones 2024–2025 | [Resumen](validation/ape_bre/resultados.md), [APE](validation/ape_bre/ape_region_sector.csv), [MAPE](validation/ape_bre/mape_16_regiones.csv) | BRE 2024; extrapolación para 2025 | 2025 no se usa para acreditar el KPI |
| Trazabilidad y alcance | [Ficha](validation/ficha_evidencia_edm_2024.md), [manifiesto](validation/manifiesto_edm_2024.json) | Entradas identificadas por SHA-256 | Distingue generación de métricas de inferencia original |
| Cumplimiento del estándar | [Auditoría](validation/auditoria_estandar.md) | [Estándar CORFO](https://github.com/FCR-CSET-Merlin/merlin-index/blob/a9b855f60c4ad207d7c2544a07e4f43d25356209/08-reportaje-corfo/estandar-estructura-corfo-report.md) | Requisitos satisfechos, excepciones y brechas |

## Reproducibility

Desde la raíz, con Python 3 y bibliotecas estándar:

```bash
python analisis/ape_bre/reportar_kpi.py
```

Este comando ejecuta `calcular.py`, regenera los CSV de ambos años, los extractos 2024, el resumen de errores y la evidencia KPI (CSV, Markdown y manifiesto). Verifica fórmulas, cobertura y el umbral estricto. No ejecuta entrenamiento ni inferencia. El informe interpretativo y la ficha son documentación revisada manualmente; deben revisarse si cambian las cifras.

Los archivos de entrada se leen de `/srv/compartido/inbox/datos_modelos_MERLIN_EDM_prot_3/data/`:

- `rec_2024_2025/results/capas_regionales/wp2_output_demanda_electrica_regional.gpkg`: totales anuales modelados en GWh, procedentes de [capa_regional.ipynb](../prototipo_3/rec_2024_2025/capa_regional.ipynb).
- `raw/wp2_elec_input_sector_shares_raw.csv`: valores sectoriales BRE; se filtra 2024 para el KPI.
- `raw/reg_alias.json`: homologación de regiones.

Las rutas están definidas en `calcular.py`. La reproducción requiere acceso a esos insumos externos; el manifiesto permite comprobar su identidad. No se distribuyen datasets pesados en Git. Los Parquet horarios y GeoPackage comunales/regionales permanecen en ese directorio externo. El procedimiento original de inferencia está descrito en [Reconstrucción 2024–2025](../prototipo_3/rec_2024_2025/README.md); su entorno ML y sus artefactos son necesarios para repetir la inferencia, no para recalcular estas métricas.

## Estructura y alcance documental

```text
corfo-report/
├── results/
│   ├── figures/
│   └── tables/
└── validation/
    ├── ape_bre/
    └── figures/
```

Las carpetas de figuras están reservadas para futuras exportaciones; no hay figuras independientes trasladadas. Las imágenes incrustadas en notebooks permanecen allí. El código se mantiene en sus directorios originales. Los resultados comparativos se consolidaron por petición expresa del usuario; `reportes/README.md` conserva una referencia a su nueva ubicación. No se incorporaron comparadores nuevos ni escenarios adicionales.

La fuente del compromiso se consultó en merlin-index, commit `a9b855f60c4ad207d7c2544a07e4f43d25356209`. La meta documental no prueba por sí misma el logro. Revisar [ficha de evidencia](validation/ficha_evidencia_edm_2024.md) antes de declarar cumplimiento contractual.
