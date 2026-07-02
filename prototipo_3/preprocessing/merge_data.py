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
    df_demand = pd.read_parquet(demand_path, engine="pyarrow")

    # Renombrar 'valid_time' a 'fecha_hora' para que todas las tablas compartan la misma llave temporal
    if "valid_time" in df_demand.columns:
        df_demand = df_demand.rename(columns={"valid_time": "fecha_hora"})

    # --- CORRECCIÓN CLAVE: ESTANDARIZAR STRINGS ---
    print("   -> Estandarizando nombres de comunas (Mayúsculas y sin espacios)...")
    for df in [df_temp, df_cal, df_shr, df_demand]:
        if "region" in df.columns:
            # Convertimos a mayúsculas y quitamos espacios residuales
            df["region"] = df["region"].str.upper().str.strip()

    # Asegurar formato datetime en todas las matrices
    for df in [df_temp, df_cal, df_shr, df_demand]:
        if "fecha_hora" in df.columns:
            df["fecha_hora"] = pd.to_datetime(df["fecha_hora"])

    # --- DIAGNÓSTICO INICIAL ---
    print(
        f"   -> Filas originales: Temp: {len(df_temp)} | Cal: {len(df_cal)} | Shr: {len(df_shr)} | Demanda: {len(df_demand)}"
    )

    print("2. Fusionando todo en una gran matriz (Inner Join)...")

    # Cruce secuencial según hora y comuna
    df_merged = pd.merge(df_temp, df_cal, on=["fecha_hora", "region"], how="inner")
    print(f"   -> Tras cruzar Temp + Calendario quedan: {len(df_merged)} filas")

    # Si df_shr tiene "region" y df_merged también, cruzamos por las tres para evitar duplicidad de columnas
    merge_keys = ["fecha_hora", "region"]
    if "region" in df_merged.columns and "region" in df_shr.columns:
        merge_keys.append("region")
    df_final = pd.merge(df_merged, df_shr, on=merge_keys, how="inner")

    print(f"   -> Tras cruzar con Shares quedan: {len(df_final)} filas")

    # Finalmente cruzamos con la demanda.
    # Al ser 'inner', automáticamente descarta las horas/comunas que no tienen datos de demanda
    df_final = pd.merge(df_final, df_demand, on=["fecha_hora", "region"], how="inner")
    # Eliminar las columnas duplicadas que terminan en '_y'
    cols_y = [col for col in df_final.columns if col.endswith("_y")]
    df_final = df_final.drop(columns=cols_y)

    # Quitarle el '_x' a las que quedaron para que el nombre quede limpio
    df_final = df_final.rename(
        columns=lambda col: col[:-2] if col.endswith("_x") else col
    )
    print(f"   -> Tras cruzar con Demanda (Final): {len(df_final)} filas")

    # --- DIAGNÓSTICO DE AÑOS ---
    if len(df_final) > 0:
        anios_disponibles = df_final["fecha_hora"].dt.year.unique()
        print(f"   -> Años que sobrevivieron en el dataset final: {anios_disponibles}")
    else:
        print("   -> ¡ALERTA! El dataset final quedó vacío después de los cruces.")

    # Ordenar cronológicamente
    df_final = df_final.sort_values(by=["region", "fecha_hora"]).reset_index(drop=True)
    print(
        f"-> Dataset unificado creado con {len(df_final)} filas y {len(df_final.columns)} columnas."
    )

    return df_final


def split_and_scale_data(df, train_years, val_years, test_years, case_name):
    print("--- Iniciando preparación de datasets para el modelo ---")

    # 1. Separar por años
    train = df[df["año"].isin(train_years)].copy()
    val = df[df["año"].isin(val_years)].copy()
    test = df[df["año"].isin(test_years)].copy()

    # 2. Escalar Temperatura (MinMaxScaler)
    temp_cols = [c for c in train.columns if "temp" in c.lower()]
    scaler_temp = MinMaxScaler(feature_range=(0, 1))

    # Guardar el scaler
    t_sc_dir = f"../models/scaler_temp_{case_name}.pkl"
    print(f"Guardando parámetros de escalamiento de la temperatura en {t_sc_dir}")
    joblib.dump(scaler_temp, t_sc_dir)

    # Ajustamos scaler en train y transformamos los tres sets
    train[temp_cols] = scaler_temp.fit_transform(train[temp_cols])
    val[temp_cols] = scaler_temp.transform(val[temp_cols])
    test[temp_cols] = scaler_temp.transform(test[temp_cols]) if not test.empty else None

    # Guardar metadatos
    train_md = train.copy()
    train_md.to_parquet(f"../data/processed/train_md_{case_name}.parquet", index=False)
    val_md = val.copy()
    val_md.to_parquet(f"../data/processed/val_md_{case_name}.parquet", index=False)
    test_md = test.copy()
    test_md.to_parquet(f"../data/processed/test_md_{case_name}.parquet", index=False)

    # 3. Estandarizar Demanda (Método Kusumoto)
    # Usamos las columnas mu_total y sigma_total que ya deben estar en tu df_final
    for df_split in [train, val, test]:
        if not df_split.empty:
            df_split["target_scaled"] = (
                df_split["demanda_mwh"] - df_split["mu_total"]
            ) / df_split["sigma_total"]

    # 4. Crear datasets "ciegos" (Solo tensores numéricos para Keras)
    # Eliminamos columnas identificadoras, de tiempo, y las originales de demanda/estandarización
    cols_to_drop = [
        "año",
        "fecha_hora",
        "region",
        "demanda_mwh",
        "mu_total",
        "sigma_total",
        "region_bne",
    ]

    # Filtramos las columnas, convertimos a float32 y eliminamos cualquier residuo no numérico
    blind_train = train.drop(columns=cols_to_drop, errors="ignore").astype("float32")
    blind_val = val.drop(columns=cols_to_drop, errors="ignore").astype("float32")
    blind_test = (
        test.drop(columns=cols_to_drop, errors="ignore").astype("float32")
        if not test.empty
        else None
    )

    print(
        f"Dataset listo: {len(blind_train)} filas de entrenamiento, {len(blind_val)} de validación."
    )

    return blind_train, blind_val, blind_test


if __name__ == "__main__":

    # Rutas a directorios
    TEMP_DEMAND_FILE = "../data/interim/temperatura_regional_lagged.parquet"
    CALENDAR_FILE = "../data/interim/calendario_regional.parquet"
    SHARES_FILE = "../data/interim/sector_shares_regional.parquet"
    DEMAND_FILE = "../data/interim/demanda_regional_horaria.parquet"

    OUTPUT_DIR = "../data/processed/"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Genera el dataframe final de datos
    df_final = load_and_merge_data(
        TEMP_DEMAND_FILE, CALENDAR_FILE, SHARES_FILE, DEMAND_FILE
    )

    # Agrega columna de año en df_final para el merge
    df_final["año"] = df_final["fecha_hora"].dt.year

    # Carga los datos de parámetros de estandarización
    df_std = pd.read_csv(
        "../data/models/std_scale/parametros_estandarizacion_regional.csv",
        usecols=["región", "año", "mu_total", "sigma_total"],
    )
    df_std.rename(columns={"región": "region_bne"}, inplace=True)

    # Junta los dataframes para tener todos los datos
    df_completo = pd.merge(df_final, df_std, on=["año", "region_bne"])

    # Procesa y guarda los datos
    # Caso 1: 
    #   train = 2018, 2019, 2020
    #   val = 2021
    #   test = 2022, 2023
    # Caso 2: 
    #   train = 2020
    #   val = 2021
    #   test = 2022
    
    case_1 = "caso_1"
    train_c1, val_c1, test_c1 = split_and_scale_data(
        df_completo, train_years=[2018, 2019, 2020], val_years=[2021], test_years=[2022, 2023], case_name=case_1
    )
    train_c1.to_parquet(f"../data/processed/train_{case_1}.parquet", index=False)
    val_c1.to_parquet(f"../data/processed/val_{case_1}.parquet", index=False)
    test_c1.to_parquet(f"../data/processed/test_{case_1}.parquet", index=False)


    case_2 = "caso_2"
    train_c2, val_c2, test_c2 = split_and_scale_data(
        df_completo, train_years=[2020], val_years=[2021], test_years=[2022], case_name=case_2
    )
    
    train_c2.to_parquet(f"../data/processed/train_{case_2}.parquet", index=False)
    val_c2.to_parquet(f"../data/processed/val_{case_2}.parquet", index=False)
    test_c2.to_parquet(f"../data/processed/test_{case_2}.parquet", index=False)
