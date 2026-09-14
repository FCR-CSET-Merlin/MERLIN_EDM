# Reportes CORFO — MERLIN EDM

Ubicación consolidada de resultados y comparaciones del modelo.

```text
corfo-report/
├── results/
│   ├── figures/          # Figuras de resultados simulados
│   └── tables/           # Tablas de resultados simulados
└── validation/
    ├── ape_bre/          # Reportes y tablas de comparación con BRE
    └── figures/          # Figuras que respaldan las comparaciones
```

## Validación disponible

- [Reporte interpretativo BRE 2024](validation/ape_bre/resultados_modelo_bre_2024.md).
- [Tablas de APE y MAPE 2024–2025](validation/ape_bre/resultados.md).
- [APE por región y sector, ambos años](validation/ape_bre/ape_region_sector.csv).
- [MAPE entre las 16 regiones, ambos años](validation/ape_bre/mape_16_regiones.csv).
- [Extracto APE 2024](validation/ape_bre/ape_region_sector_bre_2024.csv).
- [Extracto MAPE 2024](validation/ape_bre/mape_regional_bre_2024.csv).

2024 utiliza el BRE disponible; 2025 utiliza una extrapolación, no un balance observado. Estas comparaciones evalúan consistencia anual con las referencias usadas para escalar el modelo, no validación independiente ni precisión horaria.

## Regeneración

Desde la raíz del repositorio:

```bash
python analisis/ape_bre/calcular.py
```

El script escribe las tablas de ambos años, los extractos 2024 y el resumen `resultados.md` en `validation/ape_bre/`. El reporte interpretativo se mantiene manualmente y debe revisarse si se regeneran los datos. Las fuentes externas y su ruta local están definidas en el script.

Las carpetas `results/figures`, `results/tables` y `validation/figures` están reservadas para futuras exportaciones. No había figuras independientes que trasladar; las imágenes incrustadas en notebooks permanecen en sus cuadernos. Los Parquet y GeoPackage externos permanecen en su directorio de datos original.
