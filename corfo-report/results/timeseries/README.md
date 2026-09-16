# Series horarias de resultados

Este directorio reúne localmente las series horarias de reconstrucción del modelo. Son artefactos pesados y quedan excluidos de Git mediante el `.gitignore` local; el repositorio versiona el índice con su procedencia, cobertura, tamaño y SHA-256.

| Nivel | Archivo | Cobertura | Fuente original |
|---|---|---|---|
| Regional | `regional/demanda_regional_2023_horaria.parquet` | 2023, 16 regiones, 140.160 filas | `prototipo_3/data/rec_historica/2023/` |
| Regional | `regional/demanda_regional_2024_2025_horaria.parquet` | 2024–2025, 16 regiones, 280.704 filas | `/srv/compartido/inbox/datos_modelos_MERLIN_EDM_prot_3/data/rec_2024_2025/results/capas_regionales/` |
| Comunal | `comunal/demanda_comunal_2024_2025_horaria.parquet` | 2024–2025, 345 comunas, 6.052.680 filas | `/srv/compartido/inbox/datos_modelos_MERLIN_EDM_prot_3/data/rec_2024_2025/results/capas_comunales/` |

El archivo 2023 proviene del piloto ejecutado en `feature/validacion-bre-2023`. Los archivos regional y comunal de 2024–2025 son copias de los resultados operativos existentes; sus fuentes originales no se mueven ni se sobrescriben. Los datos se expresan en MWh y conservan las columnas sectoriales propias de cada salida. Para conocer hashes, tamaños y fecha de copia, consultar `manifest_timeseries.json`.

Las series horarias no son necesarias para leer los APE/MAPE publicados; se incluyen para permitir auditorías de agregación y trazabilidad de los resultados simulados. No se añaden bases horarias directamente al commit, porque los binarios comunales superan el tamaño razonable para GitHub.
