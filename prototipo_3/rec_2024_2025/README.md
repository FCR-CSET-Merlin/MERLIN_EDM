# Reconstrucción y Despliegue 2024-2025

Este directorio alberga el flujo de trabajo final y operativo de MERLIN EDM. Su propósito es utilizar los motores de inferencia (`../src/forecast_edm/`) junto con el modelo MLP global entrenado para reconstruir las series históricas y futuras (2024 y 2025) de demanda eléctrica, tanto a nivel comunal como regional.

## Artefactos de Salida (Outputs)

Los scripts aquí contenidos procesan los datos por lotes (*batching*) y exportan dos formatos principales, preparados para ser integrados inmediatamente en sistemas de información geográfica (SIG) y bases de datos.

* **Capas Geográficas Anuales (`.gpkg`)**
  * Bases de datos espaciales OGC GeoPackage.
  * Contienen la geometría (polígonos de comunas/regiones) fusionada con los valores totales agregados anuales en GWh (demanda total y desagregada en RCPIT).
  * Ideales para visualización de mapas de calor dinámicos (ej. en QGIS).

* **Series de Tiempo Horarias (`.parquet`)**
  * Archivos columnares altamente comprimidos (Apache Parquet).
  * Contienen la resolución horaria (`timestamp`) en MWh para cada identificador espacial, asegurando un rápido procesamiento y una fácil ingesta.

## 🚀 Flujo Operativo Recomendado

Si necesitas regenerar las capas de un año nuevo o cargar todo en el sistema, el orden de ejecución es el siguiente:

1. **Extrapolación y Preparación (Notebooks):**
   * Ejecutar los notebooks de preparación (`capa_comunal.ipynb` / `capa_regional.ipynb`). Estos cuadernos cargan los metadatos, ejecutan las extrapolaciones de datos faltantes e invocan al modelo de Machine Learning.

2. **Visualización y Control de Calidad (`vis_capas.ipynb`):**
   * Utilizar este cuaderno para auditar mapas de calor estáticos antes del despliegue, asegurándose de que la desagregación (R, C, P, I, T) posea coherencia espacial.

3. **Ingesta en Base de Datos (`to_DB.ipynb`):**
   * Script final que contiene la lógica de conexión de SQLAlchemy / GeoPandas para cargar de manera eficiente los archivos `.gpkg` y `.parquet` al servidor PostgreSQL/PostGIS (ej. en el esquema `work.guest_resultados`).