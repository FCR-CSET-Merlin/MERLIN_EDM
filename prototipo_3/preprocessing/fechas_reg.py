import os
import json
import pandas as pd
import numpy as np
import holidays
import geopandas as gpd

# ==========================================
# 1. DEFINICIÓN DE RUTAS (Dinámicas)
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
INTERIM_DIR = os.path.join(BASE_DIR, "data", "interim")

def main():
    print("1. Cargando configuraciones y datos base...")
    
    # Cargar el mapeo de alias regionales desde el JSON
    alias_path = os.path.join(RAW_DIR, "reg_alias.json")
    if not os.path.exists(alias_path):
        raise FileNotFoundError(f"No se encontró el archivo de alias en: {alias_path}")
        
    with open(alias_path, 'r', encoding='utf-8') as f:
        MAPEO_REGIONES_HOLIDAYS = json.load(f)

    # Para construir el calendario, necesitamos la combinación exacta de Fechas y Regiones.
    # Leeremos el dataset de temperatura SOLO para extraer su estructura base (fecha y region),
    # ignorando la columna de temperatura en la carga para ahorrar memoria.
    ruta_base = os.path.join(INTERIM_DIR, "temperatura_regional_horaria.parquet")
    df = pd.read_parquet(ruta_base, columns=['fecha_hora', 'comuna'], engine="pyarrow")
    df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])

    print("2. Generando Señales Periódicas (Seno/Coseno) de Kusumoto...")
    # ==========================================
    # TRANSFORMACIONES TRIGONOMÉTRICAS
    # ==========================================
    # Variabilidad Diaria (Ciclo de 24 horas)
    horas = df['fecha_hora'].dt.hour
    df['hour_sin'] = np.sin(2 * np.pi * horas / 24)
    df['hour_cos'] = np.cos(2 * np.pi * horas / 24)
    
    # Variabilidad Semanal (Ciclo de 7 días, Lunes=0, Domingo=6)
    dias_semana = df['fecha_hora'].dt.dayofweek
    df['dow_sin'] = np.sin(2 * np.pi * dias_semana / 7)
    df['dow_cos'] = np.cos(2 * np.pi * dias_semana / 7)
    
    # Variabilidad Anual (Manejo dinámico de años bisiestos)
    dias_ano = df['fecha_hora'].dt.dayofyear
    days_in_year = df['fecha_hora'].dt.is_leap_year.map({True: 366, False: 365})
    df['doy_sin'] = np.sin(2 * np.pi * dias_ano / days_in_year)
    df['doy_cos'] = np.cos(2 * np.pi * dias_ano / days_in_year)

    print("3. Evaluando Días Laborales y Feriados Regionales vectorizados...")
    # ==========================================
    # DETERMINACIÓN DE DÍA (Workday / Holiday / Weekend)
    # ==========================================
    df['fecha_date'] = df['fecha_hora'].dt.date
    
    # Aislar combinaciones únicas para optimizar las llamadas a la librería `holidays`
    fechas_unicas = df[['fecha_date', 'region']].drop_duplicates().dropna()
    
    def check_holiday(row):
        fecha = row['fecha_date']
        region_nombre = row['region']
        
        # Buscar el alias en el JSON precargado
        cod_subdiv = MAPEO_REGIONES_HOLIDAYS.get(region_nombre, None)
        
        if cod_subdiv:
            cl_holidays = holidays.CL(years=fecha.year, subdiv=cod_subdiv)
        else:
            cl_holidays = holidays.CL(years=fecha.year)
            
        return int(fecha in cl_holidays)

    # Aplicar la búsqueda solo a los pares (Fecha-Región) únicos
    fechas_unicas['is_holiday'] = fechas_unicas.apply(check_holiday, axis=1)
    
    # Reintegrar la etiqueta de feriado al dataset maestro
    df = pd.merge(df, fechas_unicas, on=['fecha_date', 'region'], how='left')
    
    # Definir fines de semana y días laborales
    df['is_weekend'] = (df['fecha_hora'].dt.dayofweek >= 5).astype(int)
    df['is_working_day'] = ((df['is_weekend'] == 0) & (df['is_holiday'] == 0)).astype(int)
    
    # Limpieza de columna pivote
    df = df.drop(columns=['fecha_date'])

    print("4. Exportando Calendario Maestro Comunal...")
    # Restringir estrictamente el output a la información temporal y espacial requerida
    columnas_finales = [
        'fecha_hora', 'region', 
        'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos', 'doy_sin', 'doy_cos',
        'is_working_day', 'is_holiday', 'is_weekend'
    ]
    df_final = df[columnas_finales]
    
    ruta_salida = os.path.join(INTERIM_DIR, "calendario_regional.parquet")
    df_final.to_parquet(ruta_salida, index=False, engine="pyarrow")
    
    print(f"¡Éxito! Base de tiempo guardada en:\n{ruta_salida}")

if __name__ == "__main__":
    main()