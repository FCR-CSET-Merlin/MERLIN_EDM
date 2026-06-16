import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import os 

def load_and_merge_data(temp_demand_path, calendar_path, shares_path): 
    print("1. Cargando datasets parciales")

    # Cargar datos
    df_temp = pd.read_parquet(temp_demand_path, engine="pyarrow")
    df_cal = pd.read_parquet(calendar_path, engine="pyarrow")
    df_shr = pd.read_parquet(shares_path, engine="pyarrow")

    # Asegurar formato datetime 
    for df in [df_temp, df_cal, df_shr]: 
        if "fecha_hora" in df.columns: 
            df["fecha_hora"] = pd.to_datetime(df["fecha_hora"])

    print("2. Fusionando todo en una gran matriz")
    # Cruce secuencial según hora y comuna
    df_merged = pd.merge(df_temp, df_cal, on=["fecha_hora", "comuna"], how="inner")

    # Si df_shr tiene "region" y df_merged también, cruzamos por las tres para evitar duplicidad de columnas
    merge_keys = ["fecha_hora", "comuna"]
    if "region" in df_merged.columns and "region" in df_shr.columns: 
        merge_keys.append("region")

    df_final = pd.merge(df_merged, df_shr, on=["fecha_hora", "comuna"], how="inner")

    # Ordenar cronológicamente 
    df_final = df_final.sort_values(by=["comuna", "fecha_hora"]).reset_index(drop=True)
    print(f"-> Dataset unificado creado con {len(df_final)} filas y {len(df_final.columns)} columnas.")
    
    return df_final