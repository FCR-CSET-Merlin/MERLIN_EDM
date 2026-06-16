import pandas as pd
import os

def prepare_sector_shares(sectorial_filepath, projection_years=[2017, 2025, 2026]):
    """
    Toma los datos sectoriales en formato largo (year | region | sector | valor),
    los pivota a formato ancho, calcula los porcentajes (shares) y proyecta 
    el último año hacia el futuro. Mientras que el primer año (2018) lo extiende al 2017.
    """
    print(f"1. Cargando datos sectoriales desde: {sectorial_filepath}")
    
    df_long = pd.read_csv(sectorial_filepath)
    
    # 1. Transformar de formato largo a ancho (Pivot)
    print("   Pivotando tabla a formato ancho (wide)...")
    df_sec = df_long.pivot_table(
        index=['año', 'región'], 
        columns='sector', 
        values='valor', 
        aggfunc='sum'
    ).reset_index()
    
    # Llenar posibles nulos con 0 (por si alguna región no tiene un sector específico)
    df_sec = df_sec.fillna(0)
    
    sectores = ['Industrial', 'Residencial', 'Comercial', 'Público', 'Transporte']
    sectores_alias = {'Industrial': "I", 'Residencial':"R", 'Comercial':"C", 'Público':"P", 'Transporte':"T"}
    
    # Verificación de seguridad: si un sector no existe en la tabla, lo creamos con 0
    for sec in sectores:
        if sec not in df_sec.columns:
            df_sec[sec] = 0.0

    # 2. Calcular el consumo total de la región en ese año
    df_sec['total_consumo_region'] = df_sec[sectores].sum(axis=1)
    
    # 3. Calcular el consumo total nacional por año
    df_nacional = df_sec.groupby('año')['total_consumo_region'].sum().reset_index()
    df_nacional.rename(columns={'total_consumo_region': 'total_consumo_nacional'}, inplace=True)
    
    # Unir el total nacional de vuelta al dataframe original
    df_sec = pd.merge(df_sec, df_nacional, on='año', how='left')
    
    # 4. Calcular la magnitud de la región (region_share)
    df_sec['region_share'] = df_sec['total_consumo_region'] / df_sec['total_consumo_nacional']
    
    # 5. Calcular el comportamiento interno (sector_share_by_region)
    share_cols = []
    for sec in sectores:
        aka = sectores_alias[sec]
        col_name = f'share_{aka}'
        df_sec[col_name] = df_sec[sec] / df_sec['total_consumo_region']
        share_cols.append(col_name)
        
    # Filtrar solo las columnas útiles para el modelo
    columnas_finales = ['año', 'región', 'region_share'] + share_cols
    df_shares = df_sec[columnas_finales].copy()
    
    # 6. Proyectar/Congelar datos para 2025 y 2026 basados en 2024
    df_2018 = df_shares[df_shares['año'] == 2018].copy()
    df_2024 = df_shares[df_shares['año'] == 2024].copy()
    
    projections = []
    for py in projection_years:
        if py == 2017:
            print(f"Proyectando configuración espacial de 2018 para el año {py}...")
            df_proj = df_2018.copy()
        else:
            print(f"Proyectando configuración espacial de 2024 para el año {py}...")
            df_proj = df_2024.copy()
        df_proj['año'] = py
        projections.append(df_proj)
        
    df_shares = pd.concat([df_shares] + projections, ignore_index=True)
    
    # Validación matemática
    check_sum = df_shares[df_shares['año'] == 2024]['region_share'].sum()
    print(f"Validación matemática: La suma de los region_shares en 2024 es {check_sum:.4f} (Debe ser ~1.0)")

    # Renombrar columnas para el cruce con el archivo Parquet
    df_shares = df_shares.rename(columns={"año": "year", "región": "region"})
    
    return df_shares

def merge_shares_to_hourly(hourly_filepath, df_shares, output_filepath):

    print(f"\n2. Cargando matriz horaria COMUNAL desde: {hourly_filepath}")
    # CAMBIO: Usar read_parquet para procesar el formato binario de forma eficiente
    df_hourly = pd.read_parquet(hourly_filepath)
    
    # Asegurar el formato datetime (Parquet lo suele mantener, pero es una buena práctica)
    df_hourly['fecha_hora'] = pd.to_datetime(df_hourly['fecha_hora'])
    df_hourly['year'] = df_hourly['fecha_hora'].dt.year
    
    print("   Haciendo broadcasting de las variables espaciales (Región -> Comunas) a resolución horaria...")
    # LA MAGIA OCURRE AQUÍ: Al hacer merge por 'year' y 'region', Pandas asigna 
    # automáticamente los shares a todas las comunas que comparten esa región.
    df_final = pd.merge(df_hourly, df_shares, on=['year', 'region'], how='left')
    df_final = df_final.drop(columns=['year'])
    
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    
    # CAMBIO: Guardar el dataset final en formato Parquet para el modelo ML
    df_final.to_parquet(output_filepath, index=False)
    print(f"3. ¡Dataset MERLIN final listo y guardado en: {output_filepath}!")
    
    return df_final

if __name__ == "__main__":
    
    SECTORIAL_FILE = "../data/raw/wp2_elec_input_sector_shares_raw.csv" 
    HOURLY_FILE = "../data/interim/calendario_comunal_features.parquet" 
    FINAL_OUTPUT = "../data/interim/sector_shares_comunal.parquet" 
    
    if os.path.exists(SECTORIAL_FILE) and os.path.exists(HOURLY_FILE):
        # 1. Preparar y proyectar los shares regionales
        df_shares_calc = prepare_sector_shares(SECTORIAL_FILE)
        
        # 2. Inyectar los shares regionales a cada comuna hora por hora
        df_ml_ready = merge_shares_to_hourly(HOURLY_FILE, df_shares_calc, FINAL_OUTPUT)
        
        print("\nMuestra de las nuevas variables espaciales (Nota cómo la comuna hereda la info de su región):")
        # Mostrar 'comuna' explícitamente para comprobar el éxito del script
        cols_to_show = ['valid_time', 'comuna', 'region', 'region_share', 'share_I', 'share_R']
        
        # Si la columna se llama diferente en tu parquet (ej. 'Comuna'), ajusta el nombre en cols_to_show
        if 'comuna' in df_ml_ready.columns:
            print(df_ml_ready[cols_to_show].head(10))
        else:
            print(df_ml_ready.head(10))
            
    else:
        print("Error: Faltan archivos de entrada. Verifica las rutas relativas.")