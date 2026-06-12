import pandas as pd
import numpy as np 
import os
import json

def generate_temperature_lags(input_filepath, output_filepath, total_dimensions=8): 

    """
    Toma un .parquet de temperaturas en formato largo (fecha_hora, comuna, temperatura),
    y genera las columnas de retardo (lags).
    Para d=8, genera 7 rezagos (t-1, t-2, ..., t-7)
    """

    print(f"Cargando datos desde: {input_filepath}")
    df_long = pd.read_parquet(input_filepath, engine="pyarrow")

    # 2. Asegurar formato de fecha y ordenar
    # Ordenar primero por región y después por tiempo cronológico 
    df_long["fecha_hora"] = pd.to_datetime(df_long["fecha_hora"])
    df_long = df_long.sort_values(by=["comuna", "fecha_hora"]).reset_index(drop=True)
    
    # 3. Generar lags
    lags = total_dimensions - 1
    print(f"Generando {lags} horas de rezago para la temperatura agrupando por comuna...")

    for i in range(1, lags + 1): 

        col_name = f"temp_t - {i}"
        df_long[col_name] = df_long.groupby("comuna")["temperatura"].shift(i)
    
    # 4. Limpieza de valores nulos 
    filas_antes = len(df_long)
    df_long = df_long.dropna(subset=[f"temp_t - {i}" for i in range(1, lags + 1)])
    filas_despues = len(df_long)

    print(f"Limpieza: Se eliminaron {filas_antes - filas_despues} filas por falta de historial.")

    # 5. Exportar el dataset procesado 
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    df_long.to_parquet(output_filepath, engine="pyarrow", index=False)
    print(f"Dataset guardado exitosamente en: {output_filepath}")
    print(df_long.head())

# %% Pruebas
if __name__ == "__main__": 

    # Probar de acuerdo a las rutas
    input_file = "../data/interim/demanda_comunal_horaria_temperatura.parquet"
    output_file = "../data/processed/temperatura_comunal_lagged.parquet"

    generate_temperature_lags(input_file, output_file, total_dimensions=8)

