import pandas as pd
import os 
import numpy as np
import geopandas as gpd

# ==========================================
# 1. DEFINICIÓN DE RUTAS (Rutas Relativas Ancladas)
# ==========================================
# Detecta la carpeta donde está este script (prototipo_3/preprocessing)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Sube un nivel para llegar a la raíz del proyecto (prototipo_3)
BASE_DIR = os.path.dirname(SCRIPT_DIR)

# Define las rutas hacia los datos bajando desde BASE_DIR
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
DEMAND_DIR = os.path.join(RAW_DIR, "demanda_comunal_horaria.csv")
OUT_DIR = os.path.join(BASE_DIR, "data", "interim") # Aquí se guardará el resultado
os.makedirs(OUT_DIR, exist_ok=True)

def main(): 

    print("1. Cargando configuraciones y datos base")

    # Para construir la demanda regional, necesitamos referenciar los retiros con las regiones
    # usando geocapas
    # Demanda comunal
    ruta_demanda_comunal = os.path.join(RAW_DIR, "demanda_comunal_horaria.csv")
    df_comunas = pd.read_csv(ruta_demanda_comunal).rename(columns={"valid_time": "fecha_hora"})
    df_comunas["fecha_hora"] = pd.to_datetime(df_comunas["fecha_hora"])
    # Geocapas
    ruta_geo_comunal = os.path.join(RAW_DIR, "capa_comunal.gpkg")
    gdf_comunas = gpd.read_file(ruta_geo_comunal)

    print("2. Cruzar las comunas con regiones usando Geopackage")
    # Extraer sólo las columnas de cruce y eliminar duplicados
    df_mapa = gdf_comunas[["comuna", "region"]].drop_duplicates()
    # Unir para asignar la región a cada registro comunal 
    df_comunas = pd.merge(df_comunas, df_mapa, on="comuna", how="left")

    print("3. Generando sumas de la demanda por región")
    # Sumar los datos por región
    df_regional = df_comunas.groupby(["fecha_hora", "region"])["demanda_mwh"].sum().reset_index()
    df_regional = df_regional.sort_values(["region", "fecha_hora"]).reset_index(drop=True)
    
    print("4. Exportar resultados")
    ruta_salida = os.path.join(OUT_DIR, "demanda_regional_horaria.parquet")
    df_regional.to_parquet(ruta_salida, index=False, engine="pyarrow")

    print(f"Éxito! Demanda regional guardada en: \n{ruta_salida}")

if __name__ == "__main__": 

    main()

    