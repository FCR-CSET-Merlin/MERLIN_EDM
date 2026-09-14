# Evidencia numérica del umbral HC2 — Chile, electricidad 2024

ID de evidencia: `CORFO-MERLIN-EDM-CHILE-BRE2024`. Fuente del compromiso: [HC2, indicador 2](https://github.com/FCR-CSET-Merlin/merlin-index/blob/a9b855f60c4ad207d7c2544a07e4f43d25356209/05-roadmap/01-antecedentes/Resultados_Excel_CORFO.md).

Meta: MAPE estrictamente inferior a 35 % en la mayoría de los sectores. Se interpreta mayoría como más de la mitad de los cinco sectores; el total agregado no es un sexto sector.

| Sector | MAPE entre 16 regiones | MAPE < 35 % |
|---|---:|---|
| Residencial | 4.68556 % | Sí |
| Comercial | 5.86904 % | Sí |
| Público | 8.37401 % | Sí |
| Industrial | 1.73917 % | Sí |
| Transporte | 35.02915 % | No |

**Resultado: 4/5 sectores (80 %) cumplen el umbral numérico en este caso.** La decisión usa valores sin redondear.

Estado: evidencia reproducible de consistencia anual, pendiente de aceptación como validación del KPI. El BRE 2024 interviene en el escalamiento del modelo; por tanto no es un comparador independiente. La meta no especifica que este MAPE espacial anual sea la agregación formal aceptada. La aceptación de la métrica, su frontera y su uso como evidencia de precisión requiere revisión del proyecto.

No se acredita HC2 completo: este paquete no demuestra demanda térmica, ejecución en Alemania ni cobertura validada de todos los modelos país–sector. Tampoco acredita R1–R7, HC1 o HC3. El diagnóstico para Alemania es factibilidad, no ejecución validada. 2025 se excluye del KPI porque su referencia es extrapolada.

Transporte no cumple el umbral en 2024. Los casos Atacama y Coquimbo se conservan íntegros; no se descartan ni se sustituye el indicador por otra métrica para obtener cumplimiento.

- [Datos KPI por sector](kpi_validation.csv).
- [APE y referencias por región](ape_bre/ape_region_sector_bre_2024.csv).
- [Ficha de evidencia y brechas](ficha_evidencia_edm_2024.md).
