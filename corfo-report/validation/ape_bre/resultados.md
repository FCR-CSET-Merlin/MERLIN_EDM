# APE anual y MAPE entre regiones

Fuente: GeoPackage regional de resultados 2024–2025 y data/raw/wp2_elec_input_sector_shares_raw.csv.
Unidades: GWh. Cruce mediante data/raw/reg_alias.json.

2024: referencia BRE disponible. 2025: extrapolación lineal por región y sector de todos los años disponibles, con valores negativos truncados a cero, reproduciendo capa_regional.ipynb. Los sectores ausentes en años históricos se completan con cero, igual que en el notebook.

APE = 100 × |modelo − referencia| / |referencia|. MAPE: media aritmética de los APE de las 16 regiones, sin ponderación energética, por año y sector. Total usa demanda_total_GWh y la suma de los cinco sectores del BRE; no se obtiene promediando los APE sectoriales.

Si una referencia es cero, APE queda indefinido y no se publica un MAPE de 16 regiones para ese grupo. No se reemplaza por cero ni se excluye silenciosamente.

Estas comparaciones miden consistencia anual con las referencias que el flujo utiliza para escalar las predicciones; no son una validación independiente ni un MAPE horario. Para 2025 no constituyen error contra un BRE observado.

## 2024

| Región | Total | Residencial | Comercial | Público | Industrial | Transporte |
|---|---:|---:|---:|---:|---:|---:|
| TARAPACÁ | 2.34% | 10.42% | 4.91% | 8.00% | 1.19% | 13.69% |
| ANTOFAGASTA | 0.25% | 5.64% | 17.45% | 5.15% | 0.86% | 33.77% |
| ATACAMA | 2.41% | 13.13% | 14.83% | 4.98% | 2.45% | 238.90% |
| COQUIMBO | 0.32% | 7.08% | 0.51% | 2.22% | 1.06% | 218.89% |
| VALPARAÍSO | 0.19% | 0.13% | 0.82% | 8.71% | 2.32% | 6.05% |
| LIBERTADOR GENERAL BERNARDO O'HIGGINS | 0.94% | 1.89% | 3.45% | 7.72% | 0.32% | 0.71% |
| MAULE | 1.65% | 1.20% | 2.08% | 4.93% | 2.21% | 2.52% |
| BIOBÍO | 0.54% | 1.16% | 0.75% | 11.75% | 0.40% | 1.35% |
| LA ARAUCANÍA | 1.20% | 0.29% | 5.77% | 9.13% | 1.68% | 2.97% |
| LOS LAGOS | 1.16% | 4.00% | 5.79% | 10.39% | 3.51% | 1.28% |
| AYSÉN DEL GENERAL CARLOS IBÁÑEZ DEL CAMPO | 2.17% | 1.01% | 13.98% | 12.66% | 3.68% | 12.17% |
| MAGALLANES Y DE LA ANTÁRTICA CHILENA | 1.03% | 15.60% | 4.27% | 1.87% | 4.85% | 5.72% |
| METROPOLITANA DE SANTIAGO | 0.75% | 6.46% | 1.46% | 20.92% | 2.56% | 1.87% |
| LOS RÍOS | 1.08% | 0.86% | 7.95% | 7.64% | 0.32% | 9.43% |
| ARICA Y PARINACOTA | 0.72% | 5.85% | 3.84% | 9.22% | 0.28% | 4.61% |
| ÑUBLE | 1.06% | 0.26% | 6.05% | 8.70% | 0.12% | 6.53% |
| **MAPE 16 regiones** | **1.11%** | **4.69%** | **5.87%** | **8.37%** | **1.74%** | **35.03%** |

## 2025

| Región | Total | Residencial | Comercial | Público | Industrial | Transporte |
|---|---:|---:|---:|---:|---:|---:|
| TARAPACÁ | 2.22% | 10.44% | 5.14% | 7.78% | 1.12% | 14.32% |
| ANTOFAGASTA | 0.52% | 5.32% | 16.38% | 5.34% | 1.13% | 33.66% |
| ATACAMA | 2.03% | 14.38% | 11.26% | 5.73% | 1.94% | 28.03% |
| COQUIMBO | 0.08% | 8.67% | 3.39% | 0.34% | 1.54% | 6.75% |
| VALPARAÍSO | 0.11% | 1.40% | 1.96% | 8.08% | 1.91% | 7.55% |
| LIBERTADOR GENERAL BERNARDO O'HIGGINS | 0.37% | 4.90% | 1.44% | 6.58% | 0.39% | 1.95% |
| MAULE | 1.33% | 2.18% | 1.46% | 5.35% | 1.36% | 1.44% |
| BIOBÍO | 0.53% | 2.40% | 0.37% | 10.52% | 0.46% | 1.75% |
| LA ARAUCANÍA | 0.75% | 1.39% | 4.97% | 9.56% | 0.96% | 2.90% |
| LOS LAGOS | 0.69% | 2.10% | 4.49% | 11.43% | 3.03% | 0.36% |
| AYSÉN DEL GENERAL CARLOS IBÁÑEZ DEL CAMPO | 1.29% | 0.26% | 11.71% | 17.14% | 3.18% | 8.98% |
| MAGALLANES Y DE LA ANTÁRTICA CHILENA | 0.43% | 11.34% | 0.96% | 3.42% | 5.45% | 4.49% |
| METROPOLITANA DE SANTIAGO | 0.94% | 5.78% | 1.15% | 21.08% | 2.62% | 2.53% |
| LOS RÍOS | 0.24% | 2.34% | 6.29% | 8.81% | 0.85% | 7.96% |
| ARICA Y PARINACOTA | 0.76% | 5.70% | 2.80% | 10.94% | 0.01% | 8.17% |
| ÑUBLE | 0.81% | 1.47% | 4.66% | 8.69% | 0.45% | 5.11% |
| **MAPE 16 regiones** | **0.82%** | **5.00%** | **4.90%** | **8.80%** | **1.65%** | **8.50%** |
