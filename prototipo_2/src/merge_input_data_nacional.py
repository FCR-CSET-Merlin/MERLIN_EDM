import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import os 
import joblib

def load_and_merge_data(temp_demand_path, calendar_path, shares_path, demand_path): 
    print("1. Cargando datasets parciales...")

    # Cargar datos procesados previamente
    df_temp = pd.read_parquet(temp_demand_path, engine="pyarrow")
    df_cal = pd.read_parquet(calendar_path, engine="pyarrow")
    df_shr = pd.read_parquet(shares_path, engine="pyarrow")
    
    # Cargar datos crudos de la demanda
    print(" -> Cargando datos de demanda eléctrica...")
    df_demand = pd.read_csv(demand_path)
    
    # Renombrar 'valid_time' a 'fecha_hora'
    if "valid_time" in df_demand.columns:
        df_demand = df_demand.rename(columns={"valid_time": "fecha_hora"})

    # --- CORRECCIÓN CLAVE: ESTANDARIZAR STRINGS ---
    print("   -> Estandarizando nombres de comunas (Mayúsculas y sin espacios)...")
    for df in [df_temp, df_cal, df_shr, df_demand]:
        if "comuna" in df.columns:
            df["comuna"] = df["comuna"].str.upper().str.strip()

    # Asegurar formato datetime
    for df in [df_temp, df_cal, df_shr, df_demand]: 
        if "fecha_hora" in df.columns: 
            df["fecha_hora"] = pd.to_datetime(df["fecha_hora"])

    print("2. Fusionando todo en la Gran Matriz Maestra (Inner Join)...")
    
    # Cruce secuencial según hora y comuna
    df_merged = pd.merge(df_temp, df_cal, on=["fecha_hora", "comuna"], how="inner")
    
    # Cruce con Shares
    merge_keys = ["fecha_hora", "comuna"]
    if "region" in df_merged.columns and "region" in df_shr.columns: 
        merge_keys.append("region")
    df_final = pd.merge(df_merged, df_shr, on=merge_keys, how="inner")
    
    # Cruce con Demanda
    df_final = pd.merge(df_final, df_demand, on=["fecha_hora", "comuna"], how="inner")
    
    # Limpieza de columnas duplicadas (_x, _y)
    cols_y = [col for col in df_final.columns if col.endswith('_y')]
    df_final = df_final.drop(columns=cols_y)
    df_final = df_final.rename(columns=lambda col: col[:-2] if col.endswith('_x') else col)
    
    # Ordenar cronológicamente 
    df_final = df_final.sort_values(by=["comuna", "fecha_hora"]).reset_index(drop=True)
    print(f"-> Matriz Maestra Nacional creada con {len(df_final)} filas y {len(df_final.columns)} columnas.")

    return df_final


def split_and_scale_data(df, comuna_name, output_models_dir, train_end_year=2021, val_end_year=2021): 
    # Extraer el año
    df['year'] = df['fecha_hora'].dt.year
    
    # Separar datos cronológicamente
    train_df = df[df['year'] < train_end_year].copy()
    train_df = train_df[train_df["year"] >= 2020]
    val_df   = df[df['year'] == val_end_year].copy()
    test_df  = df[df['year'] > val_end_year].copy() # 2023 en adelante

    # Para evitar problemas con los nombres de archivo (espacios, etc.)
    safe_comuna_name = comuna_name.replace(" ", "_")

    # Guardar metadata necesario para postproceso
    train_md = train_df.copy()
    val_md = val_df.copy()
    test_md = test_df.copy()
    
    # HACER EL DATASET "CIEGO" (Eliminar columnas no numéricas)
    cols_to_drop = ['year', 'fecha_hora', 'comuna', 'region', 'region_bne']
    train_df = train_df.drop(columns=[c for c in cols_to_drop if c in train_df.columns])
    val_df   = val_df.drop(columns=[c for c in cols_to_drop if c in val_df.columns])
    test_df  = test_df.drop(columns=[c for c in cols_to_drop if c in test_df.columns])
    
    # 1. Escalar Temperatura
    temp_columns = [col for col in train_df.columns if 'temp' in col.lower()]
    temp_scaler = MinMaxScaler(feature_range=(0, 1))
    
    train_df[temp_columns] = temp_scaler.fit_transform(train_df[temp_columns])
    
    # Guardar Scaler de Temperatura ESPECÍFICO de la comuna
    t_sc_dir = os.path.join(output_models_dir, f"scaler_temp_{safe_comuna_name}.pkl")
    joblib.dump(temp_scaler, t_sc_dir)
    
    val_df[temp_columns] = temp_scaler.transform(val_df[temp_columns])
    test_df[temp_columns] = temp_scaler.transform(test_df[temp_columns])
    
    # 2. Escalar Demanda
    if 'demanda_mwh' in train_df.columns:
        target_scaler = MinMaxScaler(feature_range=(0, 1))
        train_df[['demanda_mwh']] = target_scaler.fit_transform(train_df[['demanda_mwh']])
        
        # Guardar Scaler de Demanda ESPECÍFICO de la comuna
        d_sc_dir = os.path.join(output_models_dir, f"scaler_demand_{safe_comuna_name}.pkl")
        joblib.dump(target_scaler, d_sc_dir)
        
        val_df[['demanda_mwh']]   = target_scaler.transform(val_df[['demanda_mwh']])
        test_df[['demanda_mwh']]  = target_scaler.transform(test_df[['demanda_mwh']])
    
    # Conversión a float32 para TensorFlow
    train_df = train_df.astype('float32')
    val_df   = val_df.astype('float32')
    test_df  = test_df.astype('float32')
        
    return train_df, val_df, test_df, train_md, val_md, test_md


if __name__ == "__main__":
    # RUTAS DE ENTRADA
    TEMP_DEMAND_FILE = "../data/processed/temperatura_comunal_lagged.parquet"
    CALENDAR_FILE    = "../data/interim/calendario_comunal_features.parquet"
    SHARES_FILE      = "../data/interim/sector_shares_comunal.parquet"
    DEMAND_FILE      = "../data/raw/demanda_comunal_horaria.csv"
    
    # NUEVAS RUTAS DE SALIDA PARA EL ENFOQUE DE N MODELOS
    OUTPUT_DATA_DIR = "../data/processed/modelo_nacional/"
    OUTPUT_MODELS_DIR = "../models/modelo_nacional/scaler/"
    
    os.makedirs(OUTPUT_DATA_DIR, exist_ok=True)
    os.makedirs(OUTPUT_MODELS_DIR, exist_ok=True)

    if all(os.path.exists(f) for f in [TEMP_DEMAND_FILE, CALENDAR_FILE, SHARES_FILE, DEMAND_FILE]):
        
        # 1. Crear la matriz maestra con todas las comunas
        master_df = load_and_merge_data(TEMP_DEMAND_FILE, CALENDAR_FILE, SHARES_FILE, DEMAND_FILE)
        
        # 2. Identificar todas las comunas disponibles
        comunas_disponibles = master_df["comuna"].unique()
        print(f"\n3. Iniciando el particionado y escalado para {len(comunas_disponibles)} comunas...")

        # 3. Bucle Iterativo: Procesar cada comuna independientemente
        for i, comuna in enumerate(comunas_disponibles):
            safe_name = comuna.replace(" ", "_")
            print(f"   [{i+1}/{len(comunas_disponibles)}] Procesando: {comuna}...")
            
            # Aislar datos de la comuna
            df_comuna = master_df[master_df["comuna"] == comuna].copy()
            
            # Si una comuna no tiene datos en los años de train/val, se saltará para no dar error
            if df_comuna.empty:
                print(f"      -> Saltando {comuna}: Sin datos.")
                continue
                
            try:
                # Dividir, Escalar y Guardar Scalers
                train, val, test, md_train, md_val, md_test = split_and_scale_data(
                    df_comuna, 
                    comuna_name=comuna, 
                    output_models_dir=OUTPUT_MODELS_DIR,
                    train_end_year=2021, 
                    val_end_year=2021
                )
                
                # Guardar Parquets de la comuna
                train.to_parquet(os.path.join(OUTPUT_DATA_DIR, f"ml_data/train_{safe_name}.parquet"), index=False)
                val.to_parquet(os.path.join(OUTPUT_DATA_DIR, f"ml_data/val_{safe_name}.parquet"), index=False)
                test.to_parquet(os.path.join(OUTPUT_DATA_DIR, f"ml_data/test_{safe_name}.parquet"), index=False)
                md_train.to_parquet(os.path.join(OUTPUT_DATA_DIR, f"metadata/train_{safe_name}.parquet"), index=False)
                md_val.to_parquet(os.path.join(OUTPUT_DATA_DIR, f"metadata/val_{safe_name}.parquet"), index=False)
                md_test.to_parquet(os.path.join(OUTPUT_DATA_DIR, f"metadata/test_{safe_name}.parquet"), index=False)
                
            except Exception as e:
                print(f"      -> [ERROR] Falló el procesamiento de {comuna}: {e}")

        print("\n¡Pipeline de preprocesamiento completado! Tienes N datasets listos para entrenar N modelos.")
            
    else:
        print("Error: Faltan archivos en las carpetas especificadas. Verifica las rutas.")