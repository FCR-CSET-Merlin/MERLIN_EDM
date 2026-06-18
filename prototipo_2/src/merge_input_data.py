import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import os 
import joblib

def load_and_merge_data(temp_demand_path, calendar_path, shares_path, demand_path, prototype=True): 
    print("1. Cargando datasets parciales...")

    # Cargar datos procesados previamente
    df_temp = pd.read_parquet(temp_demand_path, engine="pyarrow")
    df_cal = pd.read_parquet(calendar_path, engine="pyarrow")
    df_shr = pd.read_parquet(shares_path, engine="pyarrow")
    
    # Cargar datos crudos de la demanda
    print(" -> Cargando datos de demanda eléctrica...")
    df_demand = pd.read_csv(demand_path)
    
    # Renombrar 'valid_time' a 'fecha_hora' para que todas las tablas compartan la misma llave temporal
    if "valid_time" in df_demand.columns:
        df_demand = df_demand.rename(columns={"valid_time": "fecha_hora"})

    # --- CORRECCIÓN CLAVE: ESTANDARIZAR STRINGS ---
    print("   -> Estandarizando nombres de comunas (Mayúsculas y sin espacios)...")
    for df in [df_temp, df_cal, df_shr, df_demand]:
        if "comuna" in df.columns:
            # Convertimos a mayúsculas y quitamos espacios residuales
            df["comuna"] = df["comuna"].str.upper().str.strip()

    # Asegurar formato datetime en todas las matrices
    for df in [df_temp, df_cal, df_shr, df_demand]: 
        if "fecha_hora" in df.columns: 
            df["fecha_hora"] = pd.to_datetime(df["fecha_hora"])

    # --- DIAGNÓSTICO INICIAL ---
    print(f"   -> Filas originales: Temp: {len(df_temp)} | Cal: {len(df_cal)} | Shr: {len(df_shr)} | Demanda: {len(df_demand)}")

    print("2. Fusionando todo en una gran matriz (Inner Join)...")
    
    # Cruce secuencial según hora y comuna
    df_merged = pd.merge(df_temp, df_cal, on=["fecha_hora", "comuna"], how="inner")
    print(f"   -> Tras cruzar Temp + Calendario quedan: {len(df_merged)} filas")

    # Si df_shr tiene "region" y df_merged también, cruzamos por las tres para evitar duplicidad de columnas
    merge_keys = ["fecha_hora", "comuna"]
    if "region" in df_merged.columns and "region" in df_shr.columns: 
        merge_keys.append("region")
    df_final = pd.merge(df_merged, df_shr, on=merge_keys, how="inner")
    
    print(f"   -> Tras cruzar con Shares quedan: {len(df_final)} filas")
    
    # Finalmente cruzamos con la demanda. 
    # Al ser 'inner', automáticamente descarta las horas/comunas que no tienen datos de demanda
    df_final = pd.merge(df_final, df_demand, on=["fecha_hora", "comuna"], how="inner")
    # Eliminar las columnas duplicadas que terminan en '_y'
    cols_y = [col for col in df_final.columns if col.endswith('_y')]
    df_final = df_final.drop(columns=cols_y)

    # Quitarle el '_x' a las que quedaron para que el nombre quede limpio
    df_final = df_final.rename(columns=lambda col: col[:-2] if col.endswith('_x') else col)
    print(f"   -> Tras cruzar con Demanda (Final): {len(df_final)} filas")

    # --- DIAGNÓSTICO DE AÑOS ---
    if len(df_final) > 0:
        anios_disponibles = df_final['fecha_hora'].dt.year.unique()
        print(f"   -> Años que sobrevivieron en el dataset final: {anios_disponibles}")
    else:
        print("   -> ¡ALERTA! El dataset final quedó vacío después de los cruces.")

    # Ordenar cronológicamente 
    df_final = df_final.sort_values(by=["comuna", "fecha_hora"]).reset_index(drop=True)
    print(f"-> Dataset unificado creado con {len(df_final)} filas y {len(df_final.columns)} columnas.")

    if prototype: 
        print("-> Extrayendo datos de la comuna de Santiago")
        df_santiago = df_final.loc[df_final["comuna"] == "SANTIAGO"].copy()
        df_santiago = df_santiago.sort_values(by=["fecha_hora"]).reset_index(drop=True)

        return df_final, df_santiago

    else: 

        return df_final


def split_and_scale_data(df, train_end_year=2021, val_end_year=2021, is_prototype=True): 

    print("\n3. Realizando División Cronológica (Train / Val / Test)...")
    
    # Extraer el año para facilitar el corte
    df['year'] = df['fecha_hora'].dt.year
    
    # Separar datos
    train_df = df[df['year'] < train_end_year].copy()
    train_df = train_df[train_df["year"] >= 2020]
    val_df   = df[df['year'] == val_end_year].copy()
    test_df  = df[df['year'] > val_end_year].copy() # 2023 en adelante
    
    # --- HACER EL DATASET "CIEGO" ---
    # Eliminamos strings y datetimes para que la red neuronal solo vea tensores numéricos
    cols_to_drop = ['year', 'fecha_hora', 'comuna']
    if 'region' in train_df.columns:
        cols_to_drop.append('region')

    if "region_bne" in train_df.columns:
        cols_to_drop.append("region_bne")
        
    train_df = train_df.drop(columns=cols_to_drop, errors='ignore')
    val_df   = val_df.drop(columns=cols_to_drop, errors='ignore')
    test_df  = test_df.drop(columns=cols_to_drop, errors='ignore')
    
    print(f"   -> Train: {len(train_df)} muestras (hasta {train_end_year})")
    print(f"   -> Val:   {len(val_df)} muestras (año {val_end_year})")
    print(f"   -> Test:  {len(test_df)} muestras ({val_end_year + 1} en adelante)")

    print("\n4. Escalando variables (MinMaxScaler)...")
    
    # 4.1 Identificar y escalar columnas de Temperatura (actual y lags)
    temp_columns = [col for col in train_df.columns if 'temp' in col.lower()]
    print(f"   -> Escalando temperaturas: {temp_columns}")
    
    temp_scaler = MinMaxScaler(feature_range=(0, 1))
    # FIT SOLAMENTE EN TRAIN (Regla de oro)
    train_df[temp_columns] = temp_scaler.fit_transform(train_df[temp_columns])
    t_sc_dir = "../models/scaler_temp_santiago.pkl" if is_prototype else "../models/scaler_temp.pkl"
    print(f"        -> Guardando parámetros de escalamiento de la temperatura en {t_sc_dir}")
    joblib.dump(temp_scaler, t_sc_dir)
    val_df[temp_columns] = temp_scaler.transform(val_df[temp_columns])
    test_df[temp_columns] = temp_scaler.transform(test_df[temp_columns])
    
    # 4.2 Escalar la Demanda Objetivo (Recomendado para estabilizar gradientes en MLP)
    if 'demanda_mwh' in train_df.columns:
        print("   -> Escalando variable objetivo: ['demanda_mwh']")
        target_scaler = MinMaxScaler(feature_range=(0, 1))
        # Se requiere doble corchete para mantener la estructura 2D de pandas que pide sklearn
        train_df[['demanda_mwh']] = target_scaler.fit_transform(train_df[['demanda_mwh']])
        d_sc_dir = "../models/scaler_demand_santiago.pkl" if is_prototype else "../models/scaler_demand.pkl"
        print(f"        -> Guardando parámetros de escalamiento de la demanda en {d_sc_dir}")
        joblib.dump(target_scaler, d_sc_dir)
        val_df[['demanda_mwh']]   = target_scaler.transform(val_df[['demanda_mwh']])
        test_df[['demanda_mwh']]  = target_scaler.transform(test_df[['demanda_mwh']])
    else:
        target_scaler = None
    
    print("\n -> Verificación final y conversión a float32 (TensorFlow Ready)...")
    try:
        train_df = train_df.astype('float32')
        val_df   = val_df.astype('float32')
        test_df  = test_df.astype('float32')
        print("   -> ¡Éxito! Matrices convertidas a float32 puro.")
    except ValueError as e:
        print("\n[ERROR CRÍTICO] Quedó una columna residual con texto en tu dataset. Revisa los tipos de datos:")
        print(train_df.dtypes)
        raise e
        
    return train_df, val_df, test_df, temp_scaler, target_scaler

if __name__ == "__main__":
    # Ajusta estas rutas a tu estructura de directorios
    TEMP_DEMAND_FILE = "../data/processed/temperatura_comunal_lagged.parquet"
    CALENDAR_FILE    = "../data/interim/calendario_comunal_features.parquet"
    SHARES_FILE      = "../data/interim/sector_shares_comunal.parquet"
    DEMAND_FILE      = "../data/raw/demanda_comunal_horaria.csv"
    
    OUTPUT_DIR = "../data/processed/"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Definimos si habrá o no dataset para prototipo
    prototype = True  #### MODIFICAR EN CASO QUE SEA NECESARIO
    
    # Validamos que existan todos los inputs, incluyendo la nueva demanda
    if all(os.path.exists(f) for f in [TEMP_DEMAND_FILE, CALENDAR_FILE, SHARES_FILE, DEMAND_FILE]):
        
        if prototype:
            # 1. Unificar (Ahora incluye la demanda filtrando "huecos")
            master_df, stgo_df = load_and_merge_data(TEMP_DEMAND_FILE, CALENDAR_FILE, SHARES_FILE, DEMAND_FILE, prototype=True)
            
            # 2. Dividir y Escalar (Train: hasta 2021, Val: 2022, Test: 2023+)
            # Retorna datasets 100% numéricos ("ciegos")
            # Primero, escalamos y separamos el dataset del conjunto completo
            train, val, test, temp_scaler, target_scaler = split_and_scale_data(master_df, train_end_year=2021, val_end_year=2021, is_prototype=False)
            # Segundo, escalamos y separamos el dataset del subconjunto del prototipo 
            train_stgo, val_stgo, test_stgo, _, _ = split_and_scale_data(stgo_df, train_end_year=2021, val_end_year=2021, is_prototype=True)

            # 3. Guardar matrices finales listas para la Red Neuronal
            print("\n5. Guardando particiones en data/processed/ ...")
            train.to_parquet(os.path.join(OUTPUT_DIR, "train_merlin.parquet"), index=False)
            val.to_parquet(os.path.join(OUTPUT_DIR, "val_merlin.parquet"), index=False)
            test.to_parquet(os.path.join(OUTPUT_DIR, "test_merlin.parquet"), index=False)
            train_stgo.to_parquet(os.path.join(OUTPUT_DIR, "train_merlin_stgo.parquet"), index=False)
            val_stgo.to_parquet(os.path.join(OUTPUT_DIR, "val_merlin_stgo.parquet"), index=False)
            test_stgo.to_parquet(os.path.join(OUTPUT_DIR, "test_merlin_stgo.parquet"), index=False)
            
            print("\n¡Pipeline de preprocesamiento completado! Los datos están listos para TensorFlow/Keras.")
            
        else:
            print("Error: Faltan archivos en las carpetas especificadas. Verifica las rutas.")