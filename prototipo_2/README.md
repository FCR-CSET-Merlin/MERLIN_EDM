# [DEPRECADO] Prototipo 2: Iteraciones Iniciales y Pruebas de Concepto

> **ATENCIÓN:** El código, modelos y cuadernos contenidos en esta carpeta **se encuentran deprecados**. Han sido archivados exclusivamente con fines de trazabilidad histórica, académica y metodológica. Para consultar la versión estable, modularizada y en producción del modelo, por favor dirígete a la carpeta [`../prototipo_3`](../prototipo_3).

---

## Propósito de esta carpeta

Esta rama de desarrollo albergó las pruebas de concepto (PoC) originales para la estimación y desagregación de la demanda eléctrica en el marco del proyecto MERLIN_EDM. Durante esta fase se evaluaron diversas arquitecturas de redes neuronales, técnicas de escalamiento de datos y lógicas de preprocesamiento, lo que permitió cimentar las bases teóricas de la versión final.

Aunque el código aquí contenido no es apto para entornos de despliegue ni producción por falta de optimización para grandes volúmenes de datos, funciona como bitácora de la evolución científica y técnica del proyecto.

## Hitos y Aprendizajes (Historia del Desarrollo)

Los desarrollos experimentados en el **Prototipo 2** permitieron descubrir limitaciones críticas que guiaron el diseño de la arquitectura actual. Entre los principales enfoques testeados y superados destacan:

1. **MinMaxScaler vs. Estandarización Local:** En estas versiones tempranas se intentó escalar la demanda eléctrica utilizando `MinMaxScaler`. Durante las pruebas de desagregación sectorial se evidenció que este método limitaba matemáticamente la reconstrucción de curvas en "escenarios puros". Esto motivó la adopción del escalamiento mediante $\mu$ y $\sigma$ específico por zona y año (basado en la metodología empírica de *Kusumoto et al.*).
2. **Modelos Locales vs. Modelo Global:** Se experimentó entrenando redes neuronales de forma aislada para cada identificador geográfico (comuna/región). Se descubrió que la falta de varianza espacial provocaba que la red neuronal anulara (peso cercano a cero) la importancia de las proporciones sectoriales (*shares*). El aprendizaje de este fallo derivó directamente en la creación del **Modelo Global** del prototipo 3.
3. **Manejo de Memoria Limitado:** Los scripts originales de esta carpeta fueron diseñados para cargar toda la información en memoria simultáneamente, lo que causaba desbordamientos (OOM - Out of Memory) al intentar procesar todo el país.

## Estructura de Archivos Archivados

Dentro de esta carpeta podrás encontrar versiones antiguas de:

* `notebooks/`: Análisis exploratorio de datos (EDA) inicial, cruce básico de geometrías, y primeras validaciones algorítmicas.
* `models/`: Archivos `.keras` y `.pkl` de iteraciones de prueba (como los primeros intentos de MLP). **No utilizar estos modelos para realizar inferencias actuales**.
* **Scripts de extracción:** Códigos con lógica desfasada para el cálculo de variables trigonométricas (hora/semana/año) y rezagos de temperatura.

---
*💡 **Nota para nuevos investigadores:** Si estás tomando el relevo de este proyecto para generar nuevas proyecciones (ej. 2024-2025) o aplicar mejoras operativas, **puedes ignorar completamente esta carpeta** en tu flujo de trabajo diario y enfocarte de lleno en el orquestador de `prototipo_3`.*