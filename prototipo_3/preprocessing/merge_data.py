import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import os 
import joblib
import numpy as np

def load_and_merge_data(temp_path, calendar_path, shares_path, demand_path, mu_sigma_path): 
    print("1. Cargando datasets regionales...")

    # Cargar datos procesados
    df_temp = pd.read_parquet(temp_path, engine="pyarrow")
    df_cal = pd.read_parquet(calendar_path, engine="pyarrow")
    df_shr = pd.read_parquet(shares_path, engine="pyarrow")
    df_demand = pd.read_parquet(demand_path, engine="pyarrow") # Asumiendo que ahora es parquet
    
    # Cargar parámetros mu y sigma guardados
    print(" -> Cargando parámetros de estandarización de demanda (mu, sigma)...")
    df_mu_sigma = pd.read_csv(mu_sigma_path) # Ajusta si lo guardaste como parquet

    # Renombrar 'valid_time' a 'fecha_hora' si es necesario
    if "valid_time" in df_demand.columns:
        df_demand = df_demand.rename(columns={"valid_time": "fecha_hora"})

    # --- ESTANDARIZAR STRINGS A NIVEL REGIONAL ---
    print("   -> Estandarizando nombres de regiones (Mayúsculas y sin espacios)...")
    for df in [df_temp, df_cal, df_shr, df_demand, df_mu_sigma]:
        # Si la columna se llama 'region_bne' o similar, la renombramos a 'region' para homogeneizar
        if "region_bne" in df.columns:
             df.rename(columns={"region_bne": "region"}, inplace=True)
                
        if "region" in df.columns:
            df["region"] = df["region"].str.upper().str.strip()

    # Asegurar formato datetime en las series temporales
    for df in [df_temp, df_cal, df_shr, df_demand]: 
        if "fecha_hora" in df.columns: 
            df["fecha_hora"] = pd.to_datetime(df["fecha_hora"])

    # Extraer el año en la demanda para facilitar el cruce con mu y sigma
    df_demand['year'] = df_demand['fecha_hora'].dt.year

    print("2. Fusionando todo en una gran matriz (Inner Join)...")
    
    # 2.1 Cruce secuencial Temp + Calendario + Shares + Demanda
    df_merged = pd.merge(df_temp, df_cal, on=["fecha_hora", "region"], how="inner")
    df_merged = pd.merge(df_merged, df_shr, on=["fecha_hora", "region"], how="inner")
    df_final = pd.merge(df_merged, df_demand, on=["fecha_hora", "region"], how="inner")
    
    # Limpieza de columnas duplicadas (_x, _y)
    cols_y = [col for col in df_final.columns if col.endswith('_y')]
    df_final = df_final.drop(columns=cols_y)
    df_final = df_final.rename(columns=lambda col: col[:-2] if col.endswith('_x') else col)

    # 2.2 Cruce con los parámetros Mu y Sigma por Año y Región
    # Asumimos que df_mu_sigma tiene columnas: ['year', 'region', 'mu', 'sigma']
    df_final = pd.merge(df_final, df_mu_sigma, on=["year", "region"], how="left")
    
    # Validar que no hayan quedado nulos en mu o sigma
    if df_final['mu'].isnull().any():
        print("   -> [ADVERTENCIA] Faltan parámetros mu/sigma para algunas regiones/años. Se eliminarán esas filas.")
        df_final = df_final.dropna(subset=['mu', 'sigma'])

    print(f"   -> Tras cruces (Final): {len(df_final)} filas")

    # Ordenar cronológicamente 
    df_final = df_final.sort_values(by=["region", "fecha_hora"]).reset_index(drop=True)
    
    anios_disponibles = df_final['year'].unique()
    print(f"-> Dataset unificado creado. Años disponibles: {sorted(anios_disponibles)}")

    return df_final


def create_case_dataset(df_master, case_name, train_years, val_years, test_years, out_dir):
    print(f"\n=============================================")
    print(f" PROCESANDO {case_name}")
    print(f"=============================================")
    
    # 1. Separar datos cronológicamente
    train_df = df_master[df_master['year'].isin(train_years)].copy()
    val_df   = df_master[df_master['year'].isin(val_years)].copy()
    test_df  = df_master[df_master['year'].isin(test_years)].copy() if test_years else pd.DataFrame()

    print(f"   -> Train: {len(train_df)} muestras | Años: {train_years}")
    print(f"   -> Val:   {len(val_df)} muestras | Años: {val_years}")
    print(f"   -> Test:  {len(test_df)} muestras | Años: {test_years}")

    # 2. Escalar Temperatura con MinMaxScaler (FIT SOLO EN TRAIN)
    temp_columns = [col for col in train_df.columns if 'temp' in col.lower()]
    temp_scaler = MinMaxScaler(feature_range=(0, 1))
    
    train_df[temp_columns] = temp_scaler.fit_transform(train_df[temp_columns])
    val_df[temp_columns] = temp_scaler.transform(val_df[temp_columns])
    if not test_df.empty: 
        test_df[temp_columns] = temp_scaler.transform(test_df[temp_columns])
    
    # Guardar el scaler de temperatura
    scaler_path = os.path.join(out_dir, f"scaler_temp_{case_name}.pkl")
    joblib.dump(temp_scaler, scaler_path)
    print(f"   -> Scaler de temperatura guardado en: {scaler_path}")

    # 3. Escalar la Demanda (Estandarización Kusumoto usando mu y sigma)
    # Se crea la variable objetivo que usará la red neuronal
    for df_part in [train_df, val_df, test_df]:
        if not df_part.empty and 'demanda_mwh' in df_part.columns:
            df_part['target_scaled'] = (df_part['demanda_mwh'] - df_part['mu']) / df_part['sigma']

    # 4. Guardar METADATOS (Mantienen fecha_hora, region, demanda real, mu y sigma)
    meta_cols = ['fecha_hora', 'region', 'year', 'demanda_mwh', 'mu', 'sigma', 'target_scaled']
    
    print(f"   -> Guardando metadatos para postprocesamiento...")
    train_df[meta_cols].to_parquet(os.path.join(out_dir, f"{case_name}_train_metadata.parquet"), index=False)
    val_df[meta_cols].to_parquet(os.path.join(out_dir, f"{case_name}_val_metadata.parquet"), index=False)
    if not test_df.empty:
        test_df[meta_cols].to_parquet(os.path.join(out_dir, f"{case_name}_test_metadata.parquet"), index=False)

    # 5. Generar y guardar DATASETS "CIEGOS" (Solo tensores numéricos para Keras)
    # Eliminamos columnas identificadoras y la demanda cruda/mu/sigma
    cols_to_drop = ['year', 'fecha_hora', 'region', 'demanda_mwh', 'mu', 'sigma']
    
    blind_train = train_df.drop(columns=cols_to_drop, errors='ignore').astype('float32')
    blind_val = val_df.drop(columns=cols_to_drop, errors='ignore').astype('float32')
    blind_test = test_df.drop(columns=cols_to_drop, errors='ignore').astype('float32') if not test_df.empty else pd.DataFrame()

    print(f"   -> Guardando matrices ciegas (TensorFlow Ready)...")
    blind_train.to_parquet(os.path.join(out_dir, f"{case_name}_train_blind.parquet"), index=False)
    blind_val.to_parquet(os.path.join(out_dir, f"{case_name}_val_blind.parquet"), index=False)
    if not blind_test.empty:
        blind_test.to_parquet(os.path.join(out_dir, f"{case_name}_test_blind.parquet"), index=False)


if __name__ == "__main__":
    # 1. Definición de Rutas
    DATA_DIR = "../data/interim"
    OUTPUT_DIR = "../data/processed"
    MODELS_DIR = "../models"
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)

    TEMP_FILE    = os.path.join(DATA_DIR, "temperatura_regional_lagged.parquet")
    CALENDAR_FILE= os.path.join(DATA_DIR, "calendario_regional.parquet")
    SHARES_FILE  = os.path.join(DATA_DIR, "sector_shares_regional.parquet")
    DEMAND_FILE  = os.path.join(DATA_DIR, "demanda_regional.parquet")
    
    # ATENCIÓN: Ruta al archivo que contiene mu y sigma por año y región
    MU_SIGMA_FILE = os.path.join(MODELS_DIR, "std_scale", "parametros_estandarizacion.csv")

    # Verificar que existan todos los archivos
    required_files = [TEMP_FILE, CALENDAR_FILE, SHARES_FILE, DEMAND_FILE, MU_SIGMA_FILE]
    if all(os.path.exists(f) for f in required_files):
        
        # 2. Cargar y Unificar toda la base de datos
        master_df = load_and_merge_data(TEMP_FILE, CALENDAR_FILE, SHARES_FILE, DEMAND_FILE, MU_SIGMA_FILE)
        
        # 3. Generar Caso 1 (Entrenamiento: 2018-2020 | Val: 2021 | Test: 2022 en adelante)
        # Identificamos el año máximo del dataset para el testeo
        max_year = master_df['year'].max()
        test_years_case1 = list(range(2022, max_year + 1))
        
        create_case_dataset(
            df_master=master_df,
            case_name="CASO_1",
            train_years=[2018, 2019, 2020],
            val_years=[2021],
            test_years=test_years_case1,
            out_dir=OUTPUT_DIR
        )

        # 4. Generar Caso 2 (Entrenamiento: 2020 | Val: 2021 | Test: Nada)
        create_case_dataset(
            df_master=master_df,
            case_name="CASO_2",
            train_years=[2020],
            val_years=[2021],
            test_years=[], # Vacío, ya que usarás otra base de datos
            out_dir=OUTPUT_DIR
        )

        print("\n¡Pipeline de preprocesamiento regional completado con éxito!")
    else:
        print("Error: Faltan archivos en las carpetas. Verifica las siguientes rutas:")
        for f in required_files:
            if not os.path.exists(f): print(f" -> FALTA: {f}")