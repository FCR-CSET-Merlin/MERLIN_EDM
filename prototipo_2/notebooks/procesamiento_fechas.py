import pandas as pd 
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
INTERIM_DIR = os.path.join(BASE_DIR, "data", "interim")

# 1. Cargar SOLO las columnas necesarias para validar
# (Asegúrate de poner los nombres exactos de tus columnas)
data = os.path.join(INTERIM_DIR, "calendario_comunal_features.csv")
df_validacion = pd.read_csv(
    data, 
    usecols=['fecha_hora', 'comuna'] # O 'region' dependiendo de tu cruce
)

# 2. Ver un resumen rápido
print("Fecha inicio:", df_validacion['fecha_hora'].min())
print("Fecha fin:", df_validacion['fecha_hora'].max())
print("Total de horas únicas:", df_validacion['fecha_hora'].nunique())
print("Comunas/Regiones únicas:", df_validacion['comuna'].nunique())

# 3. Mostrar una pequeña muestra visual
print(df_validacion.head())
print(df_validacion.tail())


## OUTPUT
# Fecha inicio: 2017-01-01 00:00:00
# Fecha fin: 2026-05-11 23:00:00
# Total de horas únicas: 82032
# Comunas/Regiones únicas: 345
#             fecha_hora   comuna
# 0  2017-01-01 00:00:00  IQUIQUE
# 1  2017-01-01 01:00:00  IQUIQUE
# 2  2017-01-01 02:00:00  IQUIQUE
# 3  2017-01-01 03:00:00  IQUIQUE
# 4  2017-01-01 04:00:00  IQUIQUE
#                    fecha_hora       comuna
# 28301035  2026-05-11 19:00:00  SAN NICOLÁS
# 28301036  2026-05-11 20:00:00  SAN NICOLÁS
# 28301037  2026-05-11 21:00:00  SAN NICOLÁS
# 28301038  2026-05-11 22:00:00  SAN NICOLÁS
# 28301039  2026-05-11 23:00:00  SAN NICOLÁS