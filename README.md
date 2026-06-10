# MERLIN_EDM (Energy Demand Model)

Este repositorio contiene los módulos de estimación de demanda energética para el proyecto MERLIN, organizados en diferentes etapas de desarrollo y escalas de resolución espacial.

## Estructura del Repositorio

El proyecto se divide en dos bloques principales de desarrollo:

* **`prototipo_1/` (Versión Desactualizada - Base de Desarrollo):**
    * **Enfoque:** Estimación de demanda a **nivel regional**.
    * **Metodología:** Basado en la arquitectura y modelo de *Kusumoto et al.*
    * **Nota:** Se mantiene en el repositorio como el bloque base y línea base del desarrollo matemático y lógico del modelo.
* **`prototipo_2/` (Versión Actual - Desarrollo Activo):**
    * **Enfoque:** Estimación de demanda a **nivel comunal**.
    * **Metodología:** Evolución del modelo anterior, utilizando la misma arquitectura de *Kusumoto et al.* pero adaptada a una mayor resolución espacial.
    * **Contenido adicional:** Incluye los scripts y códigos de preprocesamiento de datos necesarios para la escala comunal.

---

## Gestión de Datos (`data/`)

Por motivos de peso y almacenamiento, las carpetas `data/` dentro de cada prototipo **están excluidas del control de versiones** (añadidas al `.gitignore`). 

Para ejecutar los modelos localmente, es necesario asegurar la siguiente estructura de directorios y posicionar los archivos correspondientes en cada ruta:

```text
MERLIN_EDM/
├── prototipo_1/
│   └── data/          <-- Insertar datos de entrada y salida regional aquí
└── prototipo_2/
    └── data/          <-- Insertar datos de entrada, preprocesamiento y salida comunal aquí