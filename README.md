# MERLIN EDM: Modelo de estimación y desagregación de demanda eléctrica con Machine Learning

Este repositorio contiene el pipeline completo de ingeniería de datos y machine learning diseñado para la predicción y desagregación espacial y sectorial de la demanda eléctrica en Chile. El enfoque permite estimar el consumo a escala regional y comunal, dividiéndolo en cinco sectores estratégicos: **Residencial (R), Comercial (C), Público (P), Industrial (I) y Transporte (T)**.

La metodología base de este proyecto está basada en las técnicas de desagregación (downscaling) espacial propuestas por *Kusumoto et al. (2024)*, adaptada a la disponibilidad de datos y metadatos territoriales del sector eléctrico chileno.

---

## Estado del Proyecto y Estructura

El repositorio está dividido en dos grandes ramas de desarrollo físico (carpetas):

* **`prototipo_2/` (Desactualizado):** Contiene las iteraciones iniciales, pruebas de concepto y los primeros acercamientos al modelo. **Esta versión está deprecada** y se mantiene únicamente por propósitos de historial y trazabilidad. No se recomienda su uso para nuevos desarrollos.
* **`prototipo_3/` (Versión Actual / Producción):** Contiene la arquitectura final, optimizada, modularizada y orientada a objetos para el preprocesamiento, entrenamiento e inferencia masiva.

### Árbol de Directorios Principal

```text
MERLIN_EDM/
│
├── prototipo_2/                 # [DEPRECADO] Iteraciones tempranas y scripts de prueba.
│
├── prototipo_3/                 # [ACTIVO] Modelo final y motores de inferencia.
│   ├── notebooks/               # Cuadernos interactivos para cruces, análisis BNE y evaluación de modelos.
│   ├── preprocessing/           # Scripts de extracción y limpieza (lags térmicos, fechas, variables físicas).
│   ├── rec_2024_2025/           # Pipeline de extrapolación e inferencia para reconstrucción 2024-2025.
│   └── src/                     # Código fuente central.
│       ├── forecast_edm/        # Motores modulares de inferencia (Shares, Scaling, Inference, Time Features).
│       └── train_mlp_v2.py      # Script principal para entrenamiento del modelo global.
│
├── .gitignore
├── README.md
└── requirements.txt             # Dependencias del proyecto.
```
---

## Arquitectura del Modelo (Modelo Global)

El núcleo predictivo es un **Perceptrón Multicapa (MLP)** entrenado bajo la arquitectura de un *Modelo Global*. En lugar de entrenar modelos aislados por comuna, una única red neuronal asimila la variabilidad de todo el país.

La desagregación sectorial se logra a través de la operación entre predicciones de la demanda eléctrica con todos los sectores activos (el output de la red con todas las caracterísitcas, $L^{all}$)  y predicción con el sector deseado "apagado" (definiendo el peso del sector a 0, $L^{w/o~ sector}$).

$$ L^{sector} = L^{all} - L^{w/o~ sector}$$

Ambas salidas tienen que estar estandarizadas  usando $\mu$ y $\sigma$ del caso correspondiente.

---

## Estructura de Salida (Artefactos Generados)

El pipeline de inferencia produce resultados listos para su ingesta en bases de datos espaciales y temporales (PostgreSQL/PostGIS). Los artefactos principales por año (ej. 2024-2025) son:

* **Series de Tiempo Horarias (`.parquet`):**
    * Ejemplo: `wp2_output_demanda_electrica_comunal_2024_2025_ts.parquet`
    * Contienen el `timestamp`, identificadores geográficos (comuna/región) y la demanda desagregada en **MWh** (Total y RCPIT).
* **Capas Geográficas Anuales (`.gpkg`):**
    * Ejemplo: `wp2_output_demanda_electrica_comunal_2024_2025.gpkg`
    * Agrupan las 8,760 horas del año, convierten las unidades a **GWh** y se acoplan con los polígonos territoriales de Chile para visualización de mapas de calor.

---

## Arquitectura Modular del Código

Para garantizar el procesamiento eficiente (por lotes/batches) y la escalabilidad, la inferencia está dividida en módulos:

* `shares_engine.py`: Motor de preprocesamiento, interpolación espacial (IDW por distancia y área) y extrapolación temporal de proporciones de consumo.
* `scaling_engine.py`: Calculador de parámetros de estandarización ($\mu$, $\sigma$) a nivel zonal.
* `inference.py`: Motor de predicciones que invoca al modelo en Keras, maneja los escenarios puros, el desescalamiento, y el filtro físico.
* `main.py`: Orquestador maestro que coordina los tres motores para procesar años y zonas geográficas a gran escala.

---

## Flujo Operativo Recomendado

Si necesitas regenerar las capas de un año nuevo o cargar todo el sistema desde cero, el orden de ejecución estricto es el siguiente:

1. **Extrapolación y Preparación (Notebooks):**
   * Ejecutar los notebooks `capa_comunal.ipynb` y `capa_regional.ipynb`. Estos cuadernos cargan los metadatos, ejecutan las extrapolaciones temporales/espaciales de datos faltantes e invocan al modelo de Machine Learning para generar las predicciones.
2. **Visualización y Control de Calidad:**
   * Utilizar el cuaderno `vis_capas.ipynb`. Este script permite auditar los mapas de calor estáticos antes de realizar el despliegue, asegurando que la desagregación sectorial posea coherencia espacial.
3. **Ingesta en Base de Datos:**
   * Ejecutar el script de despliegue `to_DB.ipynb`. Este cuaderno contiene la lógica de conexión (`SQLAlchemy` / `GeoPandas`) para subir de manera eficiente y limpia los archivos `.gpkg` y `.parquet` al servidor PostgreSQL (por ejemplo, al esquema `work.guest_resultados`).

*Desarrollado para la estimación avanzada de perfiles de consumo energético.*

---
# Instalación y Configuración del Entorno
Para ejecutar este proyecto, es estrictamente recomendable utilizar un entorno virtual (Virtual Environment) para no generar conflictos con las dependencias globales de Python de tu sistema.

1. **Clonar el repositorio**

```Bash
git clone https://github.com/FCR-CSET-Merlin/MERLIN_EDM.git
cd MERLIN_EDM
```

2. **Crear y activar el entorno virtual**
Usando `venv` (Python estándar):

```Bash
python -m venv venv

# En Windows:
venv\Scripts\activate
# En macOS / Linux:
source venv/bin/activate
```

Usando `conda` (Anaconda / Miniconda):

```Bash
conda create --name merlin_env python=3.10
conda activate merlin_env
```

3. **Instalar los requerimientos**

Asegúrate de estar en la raíz del proyecto (donde se encuentra el archivo requirements.txt) y ejecuta:

```Bash
pip install -r requirements.txt
```

*(Nota: Si planeas entrenar el modelo utilizando una GPU, asegúrate de tener instalados los drivers de NVIDIA y CUDA Toolkit correspondientes a la versión de TensorFlow especificada en el entorno).*