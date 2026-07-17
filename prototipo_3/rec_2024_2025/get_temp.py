import os
import xarray as xr
import rioxarray
import geopandas as gpd
import pandas as pd
from shapely.geometry import mapping
import warnings

# Suprimir warnings de proyecciones para mantener la consola limpia
warnings.filterwarnings("ignore")

# ==========================================
# 1. DEFINICIÓN DE RUTAS (Rutas Relativas Ancladas)
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)

RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
TEMP_DIR = os.path.join(RAW_DIR, "ERA5_Land_T2m_Chile")
OUT_DIR = os.path.join(BASE_DIR, "data", "rec_2024_2025") 
os.makedirs(OUT_DIR, exist_ok=True)

def main():
    print(f"Directorio base detectado: {BASE_DIR}")
    print("1. Cargando capas espaciales...")
    
    # Cargar y asegurar que los sistemas de coordenadas (CRS) sean EPSG:4326
    ruta_regiones = os.path.join(RAW_DIR, "capa_regional.gpkg")
    ruta_comunas = os.path.join(RAW_DIR, "capa_comunal.gpkg")
    ruta_urbano = os.path.join(RAW_DIR, "capa_limite_urbano.gpkg")
    
    gdf_regiones = gpd.read_file(ruta_regiones).to_crs("EPSG:4326")
    gdf_comunas = gpd.read_file(ruta_comunas).to_crs("EPSG:4326")
    gdf_urbano = gpd.read_file(ruta_urbano).to_crs("EPSG:4326")
    
    resultados_regionales = []
    resultados_comunales = []
    
    print("2. Iniciando extracción de temperaturas para 2024 y 2025...")
    for year in [2024, 2025]:
        for month in range(1, 13):
            archivo_nc = os.path.join(TEMP_DIR, f"era5land_t2m_chile_{year}_{month:02d}.nc")
            
            if not os.path.exists(archivo_nc):
                print(f"[!] Advertencia: Archivo {archivo_nc} no encontrado. Omitiendo...")
                continue
                
            print(f"Procesando: {year}-{month:02d}...")
            
            # Abrir el NetCDF y asignar CRS 
            ds = xr.open_dataset(archivo_nc)
            if not ds.rio.crs:
                ds = ds.rio.write_crs("EPSG:4326", inplace=True)
                
            da_temp = ds['t2m'] 
            
            # ---------------------------------------------------------
            # A) PROCESAMIENTO REGIONAL (Mantiene Lógica de Límite Urbano)
            # ---------------------------------------------------------
            for idx, row in gdf_regiones.iterrows():
                nombre_region = row['region'] 
                urbano = gdf_urbano[gdf_urbano['region'] == nombre_region]
                temp_region_series = None
                
                # INTENTO 1: Máscara espacial con Límite Urbano
                if not urbano.empty:
                    try:
                        clipped = da_temp.rio.clip(urbano.geometry.apply(mapping), urbano.crs, all_touched=True)
                        temp_region_series = clipped.mean(dim=["longitude", "latitude"]).to_series()
                        if temp_region_series.isna().all():
                            temp_region_series = None 
                    except Exception:
                        pass 
                
                # INTENTO 2 (FALLBACK): Centroide
                if temp_region_series is None:
                    poligono_base = urbano.geometry.iloc[0] if (not urbano.empty and not urbano.geometry.iloc[0].is_empty) else row.geometry
                    if poligono_base is None or poligono_base.is_empty:
                        continue 
                    
                    centroide = poligono_base.centroid
                    if centroide.is_empty: continue
                    
                    temp_region_series = da_temp.sel(longitude=centroide.x, latitude=centroide.y, method="nearest").to_series()
                    
                resultados_regionales.append(pd.DataFrame({
                    'fecha_hora': temp_region_series.index,
                    'region': nombre_region,
                    'temperatura': temp_region_series.values
                }))

            # ---------------------------------------------------------
            # B) PROCESAMIENTO COMUNAL (Centroide Directo, omitiendo límite urbano)
            # ---------------------------------------------------------
            for idx, row in gdf_comunas.iterrows():
                nombre_comuna = row['comuna'] # Asegúrate de que la columna se llame así en tu geopackage
                centroide = row.geometry.centroid
                
                if centroide.is_empty:
                    print(f"   [!] Centroide vacío para comuna {nombre_comuna}.")
                    continue
                
                # Método Nearest Neighbor usando el centroide
                temp_comuna_series = da_temp.sel(
                    longitude=centroide.x, 
                    latitude=centroide.y, 
                    method="nearest"
                ).to_series()

                resultados_comunales.append(pd.DataFrame({
                    'fecha_hora': temp_comuna_series.index,
                    'comuna': nombre_comuna,
                    'temperatura': temp_comuna_series.values
                }))
                
            ds.close() 
            
    print("3. Concatenando, estandarizando y validando datos...")
    df_regional = pd.concat(resultados_regionales, ignore_index=True)
    df_comunal = pd.concat(resultados_comunales, ignore_index=True)
    
    # Pasar de Kelvin a Celsius (si ERA5Land viene en Kelvin, estándar en Copernicus)
    df_regional['temperatura'] = df_regional['temperatura'] - 273.15
    df_comunal['temperatura'] = df_comunal['temperatura'] - 273.15
    
    # ==========================================
    # 4. VALIDACIÓN DE COBERTURA ESPACIAL (EL CHECK)
    # ==========================================
    total_regiones = df_regional['region'].nunique()
    total_comunas = df_comunal['comuna'].nunique()
    
    print("\n--- REPORTE DE VALIDACIÓN ---")
    print(f"Regiones procesadas: {total_regiones} / 16")
    if total_regiones == 16:
        print("✅ Check Regional: OK")
    else:
        print("❌ ALERTA: Faltan regiones en el cruce.")
        
    print(f"Comunas procesadas: {total_comunas} / 345")
    if total_comunas == 345:
        print("✅ Check Comunal: OK")
    else:
        # Mostrar cuáles faltan si no son 345
        comunas_esperadas = set(gdf_comunas['comuna'].unique())
        comunas_obtenidas = set(df_comunal['comuna'].unique())
        faltantes = comunas_esperadas - comunas_obtenidas
        print(f"❌ ALERTA: Faltan las siguientes comunas: {faltantes}")
    print("-----------------------------\n")

    # ==========================================
    # 5. EXPORTACIÓN A PARQUET
    # ==========================================
    ruta_salida_reg = os.path.join(OUT_DIR, "temperatura_regional_2024_2025.parquet")
    ruta_salida_com = os.path.join(OUT_DIR, "temperatura_comunal_2024_2025.parquet")
    
    df_regional.to_parquet(ruta_salida_reg, engine='pyarrow', index=False)
    df_comunal.to_parquet(ruta_salida_com, engine='pyarrow', index=False)
    
    print(f"¡Éxito! Datasets guardados en:")
    print(f" -> {ruta_salida_reg}")
    print(f" -> {ruta_salida_com}")

if __name__ == "__main__":
    main()