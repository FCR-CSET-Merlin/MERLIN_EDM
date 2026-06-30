import os
import json
import pandas as pd
import numpy as np

# ==========================================
# 1. DEFINICIÓN DE RUTAS (Rutas Relativas Ancladas)
# ==========================================
# Detecta la carpeta donde está este script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Sube un nivel para llegar a la raíz del proyecto
BASE_DIR = os.path.dirname(SCRIPT_DIR)

# Archivos de entrada
INTERIM_DIR = os.path.join(BASE_DIR, "data", "interim")
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")

CEN_PARQUET_PATH = os.path.join(INTERIM_DIR, "demanda_regional_horaria.parquet")
BRE_CSV_PATH = os.path.join(RAW_DIR, "wp2_elec_input_sector_shares_raw.csv")
ALIAS_JSON_PATH = os.path.join(RAW_DIR, "reg_alias.json")

# Archivos de salida
OUT_DIR = os.path.join(BASE_DIR, "data", "models", "std_scale")
os.makedirs(OUT_DIR, exist_ok=True) # Crea la carpeta si no existe

def main():
    print("1. Cargando datos y configuraciones...")
    
    # Cargar alias de regiones
    with open(ALIAS_JSON_PATH, 'r', encoding='utf-8') as f:
        dict_alias = json.load(f)

    # Cargar demanda del CEN
    df_reg = pd.read_parquet(CEN_PARQUET_PATH, engine="pyarrow")
    
    # Cargar datos del BRE
    df_bre = pd.read_csv(BRE_CSV_PATH)
    
    print("2. Procesando parámetros globales del CEN (Mu y Sigma Totales)...")
    # Homologar nombres de regiones del CEN hacia los del BRE
    df_reg["region"] = df_reg["region"].replace(dict_alias)
    df_reg = df_reg.rename(columns={"region": "región"}) # Igualar nombre de columna
    
    # Extraer el año de la fecha_hora
    df_reg["fecha_hora"] = pd.to_datetime(df_reg["fecha_hora"])
    df_reg["año"] = df_reg["fecha_hora"].dt.year
    
    # Calcular promedios y desviaciones estándar por región y por año
    df_params = df_reg.groupby(["región", "año"]).agg(
        mu_total=("demanda_mwh", "mean"),
        sigma_total=("demanda_mwh", "std")
    ).reset_index()

    print("3. Procesando participaciones (shares) del BRE...")
    # Definir los sectores y sus alias para las columnas de salida
    sectores = ['Industrial', 'Residencial', 'Comercial', 'Público', 'Transporte']
    sectores_alias = {'Industrial': "I", 'Residencial': "R", 'Comercial': "C", 'Público': "P", 'Transporte': "T"}
    
    # Filtrar solo los sectores de interés (por precaución)
    df_bre = df_bre[df_bre["sector"].isin(sectores)].copy()
    
    # Pivotear de formato largo a ancho
    df_sec = df_bre.pivot_table(
        index=["año", "región"], 
        columns="sector", 
        values="valor", 
        aggfunc="sum"
    ).reset_index()

    # Llenar posibles nulos con 0 (por si alguna región no tiene un sector específico)
    df_sec = df_sec.fillna(0)

    # Verificación de seguridad: si un sector no existe en la tabla, lo creamos con 0
    for sec in sectores:
        if sec not in df_sec.columns:
            df_sec[sec] = 0.0
    
    # Calcular el total del BRE por región y año (suma de la fila de los 5 sectores)
    df_sec["total_BRE"] = df_sec[sectores].sum(axis=1)
    
    # Calcular las proporciones (shares) de cada sector (0 a 1)
    for sector in sectores:
        df_sec[f"share_{sector}"] = df_sec[sector] / df_sec["total_BRE"]

    print("4. Cruzando datos y calculando parámetros 'Sin Sector'...")
    # Unir parámetros del CEN con los shares del BRE
    # Usamos inner merge para asegurar que solo queden los años/regiones que existen en ambos
    df_final = pd.merge(df_params, df_sec, on=["región", "año"], how="inner")
    
    # Aplicar método Kusumoto
    for sector, alias in sectores_alias.items():
        # Fracción remanente tras "apagar" el sector
        fraccion_restante = 1.0 - df_final[f"share_{sector}"]
        
        # Calcular los nuevos mu y sigma
        df_final[f"mu_sin_{alias}"] = df_final["mu_total"] * fraccion_restante
        df_final[f"sigma_sin_{alias}"] = df_final["sigma_total"] * fraccion_restante

    print("5. Limpiando y exportando resultados...")
    # Seleccionar solo las columnas necesarias para el modelo
    columnas_exportar = ["región", "año", "mu_total", "sigma_total"]
    for alias in sectores_alias.values():
        columnas_exportar.extend([f"mu_sin_{alias}", f"sigma_sin_{alias}"])
        
    df_export = df_final[columnas_exportar].copy()
    
    # Ordenar para mayor legibilidad
    df_export = df_export.sort_values(["año", "región"]).reset_index(drop=True)
    
    # Exportar a CSV
    ruta_salida = os.path.join(OUT_DIR, "parametros_estandarizacion_regional.csv")
    df_export.to_csv(ruta_salida, index=False, encoding="utf-8")
    
    print(f"¡Éxito! Parámetros de estandarización guardados en:\n{ruta_salida}")

if __name__ == "__main__":
    main()