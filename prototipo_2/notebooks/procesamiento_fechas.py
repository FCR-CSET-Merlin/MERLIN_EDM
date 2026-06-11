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
