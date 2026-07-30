# Módulo de Inferencia y Desagregación (Forecast EDM)

Este directorio aloja el núcleo operativo (backend) de la fase de producción de **MERLIN_EDM**. Aquí residen los motores desacoplados encargados de procesar la entrada de datos, orquestar las predicciones masivas del **Modelo Global (MLP)** y ejecutar el pipeline matemático de desagregación física y espacial de la demanda eléctrica.

La arquitectura de este módulo fue diseñada priorizando la mantenibilidad, el manejo eficiente de la memoria (para evitar desbordamientos de RAM/VRAM al procesar millones de filas) y el rigor físico de las predicciones.

---

## Componentes del Sistema

El sistema de inferencia está dividido en cuatro sub-motores principales, los cuales son coordinados secuencialmente por el script orquestador (`main.py`):

### 1. `shares_engine.py` (Motor de Proporciones)
Se encarga de reconstruir y proyectar el tejido de metadatos espaciales y temporales que la red neuronal necesita para la inferencia. Sus funciones principales incluyen:
* **Extrapolación Temporal:** Proyecta la proporción de consumo sectorial (shares) hacia años futuros (ej. 2024-2025) utilizando regresiones lineales mes a mes para mantener la coherencia estacional.
* **Interpolación Espacial:** Rellena brechas geográficas (comunas sin datos) mediante técnicas SIG (Sistemas de Información Geográfica) como **IDW (Inverse Distance Weighting)** ponderado por área y distancia de los vecinos más cercanos, además de imputaciones basadas en perfiles macro-regionales.

### 2. `scaling_engine.py` (Motor de Escalamiento)
Implementa la matemática base propuesta por *Kusumoto et al.* para la estandarización local:
* Calcula dinámicamente el promedio ($\mu$) y la desviación estándar ($\sigma$) del consumo eléctrico a nivel anual para cada identificador espacial (región o comuna).
* Genera los parámetros $\mu_{sin~ sector}$ y $\sigma_{sin~ sector}$ que se utilizarán para escalar los inputs de la red, y los parámetros específicos que excluyen un sector objetivo, vitales para la etapa de desagregación.

### 3. `time_features.py` (Motor de Tiempo)
Módulo auxiliar de Feature Engineering que transforma estampas temporales (`timestamps`) en señales continuas que la red neuronal pueda interpretar. Incluye cálculos de transformadas trigonométricas (senos y cosenos) para capturar ciclos horarios, semanales y anuales, además de procesar variables binarias como días hábiles y feriados.

### 4. `inference.py` (Motor de Predicción y Filtros)
El ejecutor final del modelo en TensorFlow/Keras. Maneja la lógica de desagregación sectorial mediante la ecuación $L^{sector} = L^{all} - L^{w/o~sector}$.


* **Consumo sin sector**: La red neuronal recibe un vector de características con el share del sector deseado igual a $0.0$ para obtener la demanda de electricidad sin el sector.
* **Desescalamiento Local:** El resultado estandarizado de la red se reconvierte a Megavatios-hora (MWh) usando los parámetros del `scaling_engine`.
* **Desagregación sectorial**: Con las demandas en la escala original, se obtiene la demanda del sector usando $L^{sector} = L^{all} - L^{w/o~sector}$.

---

## Manejo de Memoria y Rendimiento (Batching)

Dado que este pipeline evalúa todas las horas del año para todo el país simultáneamente (más de 3 millones de filas), `inference.py` no procesa los tensores de golpe. 

El modelo Keras es invocado utilizando un tamaño de lote (`batch_size=2048`), y los dataframes gigantes se administran mediante clonación en memoria superficial (`.copy()`). Si se ejecuta el proceso completo en una máquina local, se recomienda forzar la inferencia por CPU para aprovechar la RAM clásica sobre las limitaciones de la VRAM de una tarjeta gráfica, evitando el error *Out Of Memory (OOM)*.