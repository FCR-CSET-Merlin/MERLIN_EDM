import os
import pandas as pd
import geopandas as gpd
import xarray as xr 
from pathlib import Path
from scipy.spatial import cKDTree

def main(): 
    # 1. Definición de las rutas de trabajo 
    BASE_DIR = Path(__file__).parent.parent  # directorio a prototipo_2
    INTERIM_DIR = BASE_DIR / "data" / "interim"  # directorio a interim
    RAW_DIR = BASE_DIR / "data" / "raw"  # directorio a raw
    ERA5_DIR = RAW_DIR / "ERA5_Land_T2m_Chile"  # directorio a los datos de temperatura

    ruta_parquet = INTERIM_DIR / "demanda_comunal_horaria_temperatura.parquet"
    ruta_comunas = RAW_DIR / "capa_comunal.gpkg"  

    print("1. Cargando el dataset Parquet principal...")
    # Cargar el dataset completo 
    df = pd.read_parquet(ruta_parquet, engine="pyarrow")

    # 2. Identificar las 13 comunas con missing values (NaN) en la columna de temperaturas
    comunas_con_nan = df[df["temperatura"].isna()]["comuna"].unique()
    print(f"Se detectaron {len(comunas_con_nan)} comunas con datos faltantes: {comunas_con_nan}")

    # 2. EXTRA: Identificar comunas con temperaturas en kelvin
    comunas_en_kelvin = df[df["temperatura"] > 100]["comuna"].unique()
    print(f"Se detectaron {len(comunas_en_kelvin)} comunas en unidades Kelvin: {comunas_en_kelvin}")

    if len(comunas_con_nan) == 0 and len(comunas_en_kelvin) == 0: 
        print("No hay datos faltantes. El dataset está completo")
        return 
    
    if len(comunas_en_kelvin) > 0: 

        print("\n2. Convirtiendo valores de temperatura de Kelvin a Celsius")
        # Convertir Kelvin a Celsius
        df.loc[df["temperatura"] > 100, "temperatura"] = df["temperatura"] - 273.15

        print("\n3. Sobrescribiendo el archivo Parquet original...")
        df.to_parquet(ruta_parquet, engine='pyarrow', index=False)
        
        kelvin_restantes = (df["temperatura"] > 100).sum()
        print(f"¡Proceso finalizado! Valores nulos restantes en el dataset: {kelvin_restantes}")

   
    elif len(comunas_con_nan) > 0:
    
        print("\n2. Cargando polígonos comunales y calculando centroides...")
        gdf_comunas = gpd.read_file(ruta_comunas)
        # Filtrar sólo las comunas problemáticas
        gdf_faltantes = gdf_comunas[gdf_comunas["comuna"].isin(comunas_con_nan)].copy()
        # Calcular centroides
        gdf_faltantes = gdf_faltantes.to_crs(epsg=32719)
        gdf_faltantes["centroid"] = gdf_faltantes.geometry.centroid
        # Devolver el polígono y la columna del centroide al CRS geográfico de ERA5 (Lat/Lon)
        gdf_faltantes = gdf_faltantes.to_crs(epsg=4326)
        gdf_faltantes['centroid'] = gdf_faltantes['centroid'].to_crs(epsg=4326)

        print("\n3. Abriendo dataset de ERA5-Land...")
        ds_era5 = xr.open_mfdataset(str(ERA5_DIR / "*.nc"))
        if not ds_era5.rio.crs:
            ds_era5.rio.write_crs("EPSG:4326", inplace=True)
            
        ds_era5 = ds_era5['t2m'] - 273.15# Seleccionar solo la variable de temperatura

        print("\n4. Extrayendo temperatura (Nearest Valid Pixel) e inyectando al DataFrame...")
        
        print("   -> Construyendo mapa de píxeles válidos (tierra firme)...")
        
        # 1. Detectar cómo se llama la dimensión de tiempo ('time', 'valid_time', etc.)
        dim_tiempo = [d for d in ds_era5.dims if 'time' in d.lower()][0]
        
        # 2. Extraer el mapa base usando el nombre correcto dinámicamente
        mapa_base = ds_era5.isel({dim_tiempo: 0}).compute()
        
        df_grid = mapa_base.to_dataframe().reset_index()
        
        # Filtramos eliminando los píxeles del océano (NaN)
        df_validos = df_grid.dropna(subset=['t2m']).copy()
        
        # Construimos un árbol espacial con las coordenadas que SÍ tienen datos
        arbol_espacial = cKDTree(df_validos[['longitude', 'latitude']].values)

        for _, row in gdf_faltantes.iterrows():
            nombre_comuna = row['comuna']
            lon_original = row['centroid'].x
            lat_original = row['centroid'].y
            
            # Usamos el árbol para encontrar el píxel VÁLIDO más cercano a la isla/costa
            distancia, indice = arbol_espacial.query([[lon_original, lat_original]])
            
            # Extraemos las coordenadas reales del píxel de tierra firme
            lon_tierra = df_validos.iloc[indice[0]]['longitude']
            lat_tierra = df_validos.iloc[indice[0]]['latitude']
            
            print(f"   Procesando {nombre_comuna}: Centroide ({lon_original:.2f}, {lat_original:.2f}) -> Movido a tierra en ({lon_tierra:.2f}, {lat_tierra:.2f})")
            
            # Ahora sí, extraemos la serie de tiempo usando las coordenadas garantizadas
            serie_temp = ds_era5.sel(longitude=lon_tierra, latitude=lat_tierra, method='nearest').compute()
            s_temp = serie_temp.to_series()
            
            # Filtramos e inyectamos
            mask_comuna = df['comuna'] == nombre_comuna
            nuevo_mapeo = dict(zip(s_temp.index, s_temp.values))
            df.loc[mask_comuna, 'temperatura'] = df.loc[mask_comuna, 'fecha_hora'].map(nuevo_mapeo)

        print("\n5. Sobrescribiendo el archivo Parquet original...")
        df.to_parquet(ruta_parquet, engine='pyarrow', index=False)
        
        nans_restantes = df['temperatura'].isna().sum()
        print(f"¡Proceso finalizado! Valores nulos restantes en el dataset: {nans_restantes}")

if __name__ == "__main__": 

    main()