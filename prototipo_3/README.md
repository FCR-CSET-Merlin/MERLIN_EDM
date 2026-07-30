## Descripción del Flujo de Trabajo 

El pipeline actual (``/prototipo_3``) está diseñado para ser altamente modular. A grandes rasgos, el flujo se divide en:

1. Preprocesamiento (``preprocessing/`` y ``notebooks/``):
    - Construcción de factores temporales (series trigonométricas de hora, semana, año).
    - Generación de matrices de rezagos térmicos (lags de temperatura).
    - Cálculo de proporciones (shares) territoriales y sectoriales a partir de los balances regionales (BRE) y facturaciones.
    - Cálculo de variables de estandarización físicas ($\mu$ y $\sigma$) por año y zona.

2. Entrenamiento (``src/train_mlp_v2.py``):
    - Configuración y entrenamiento de un Modelo Global (que ve simultáneamente datos de todas las regiones y comunas) para evitar el sesgo espacial.

3. Inferencia y Downscaling (``src/forecast_edm/``):
    - Utiliza la metodología de "apagado de sector", forzando el share del sector deseado a $0.0$ para obtener la demanda eléctrica sin ese sector. Finalmente se resta el resultado de esa inferencia a la predicción con todas las características.
    - El motor de escalamiento (scaling_engine.py) devuelve las predicciones a valores físicos en MWh aplicando los parámetros locales.

4. Reconstrucción y Despliegue (``rec_2024_2025/``):
    - Scripts dedicados a predecir las capas geográficas (GeoPackages ``.gpkg``) y series de tiempo horarias (``.parquet``) para los años 2024 y 2025.
    - Módulos de ingesta y exportación para bases de datos espaciales (PostgreSQL/PostGIS).