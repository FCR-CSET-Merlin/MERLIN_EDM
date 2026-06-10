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
# Detecta la carpeta donde está este script (prototipo_2/preprocessing)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Sube un nivel para llegar a la raíz del proyecto (prototipo_2)
BASE_DIR = os.path.dirname(SCRIPT_DIR)

# Define las rutas hacia los datos bajando desde BASE_DIR
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
TEMP_DIR = os.path.join(RAW_DIR, "ERA5_Land_T2m_Chile")
OUT_DIR = os.path.join(BASE_DIR, "data", "interim") # Aquí se guardará el resultado
os.makedirs(OUT_DIR, exist_ok=True)

def main():
    print(f"Directorio base detectado: {BASE_DIR}")
    print("1. Cargando capas espaciales...")
    
    # Cargar y asegurar que los sistemas de coordenadas (CRS) sean EPSG:4326
    ruta_comunas = os.path.join(RAW_DIR, "capa_comunal.gpkg")
    ruta_urbano = os.path.join(RAW_DIR, "capa_limite_urbano.gpkg")
    
    gdf_comunas = gpd.read_file(ruta_comunas).to_crs("EPSG:4326")
    gdf_urbano = gpd.read_file(ruta_urbano).to_crs("EPSG:4326")
    
    resultados = []
    
    print("2. Iniciando iteración de archivos de temperatura...")
    for year in range(2017, 2018):
        # Manejar la excepción del año 2026 (solo hasta mayo)
        meses = range(1, 2) if year < 2026 else range(1, 6)
        
        for month in meses:
            archivo_nc = os.path.join(TEMP_DIR, f"era5land_t2m_chile_{year}_{month:02d}.nc")
            
            if not os.path.exists(archivo_nc):
                print(f"[!] Advertencia: Archivo {archivo_nc} no encontrado. Omitiendo...")
                continue
                
            print(f"Procesando: {year}-{month:02d}...")
            
            # Abrir el NetCDF y asignar CRS 
            ds = xr.open_dataset(archivo_nc)
            if not ds.rio.crs:
                ds = ds.rio.write_crs("EPSG:4326", inplace=True)
                
            # Extraer la variable de temperatura a 2 metros 
            da_temp = ds['t2m'] 
            
            for idx, row in gdf_comunas.iterrows():
                nombre_comuna = row['comuna'] 
                
                # Buscar el límite urbano correspondiente a esta comuna
                urbano = gdf_urbano[gdf_urbano['comuna'] == nombre_comuna]
                temp_comuna_series = None
                
                # INTENTO 1: Máscara espacial con Límite Urbano
                if not urbano.empty:
                    try:
                        clipped = da_temp.rio.clip(urbano.geometry.apply(mapping), urbano.crs, all_touched=True)
                        temp_comuna_series = clipped.mean(dim=["longitude", "latitude"]).to_series()
                        
                        if temp_comuna_series.isna().all():
                            temp_comuna_series = None 
                    except Exception:
                        pass # Si no hay intersección o hay un error geométrico, va al Fallback
                
                # INTENTO 2 (FALLBACK): Centroide + Nearest Neighbor
                if temp_comuna_series is None:
                    # 1. Definir qué polígono usar (priorizar urbano, luego comunal)
                    if not urbano.empty and not urbano.geometry.iloc[0].is_empty:
                        poligono_base = urbano.geometry.iloc[0]
                    else:
                        poligono_base = row.geometry
                    
                    # 2. Validar que el polígono base finalmente no esté vacío o sea nulo
                    if poligono_base is None or poligono_base.is_empty:
                        print(f"   [!] Error espacial: La comuna {nombre_comuna} no tiene geometría válida. Se omitirá.")
                        continue # Salta esta comuna para este mes
                        
                    # 3. Calcular centroide
                    centroide = poligono_base.centroid
                    
                    # 4. Validar que el centroide se haya generado correctamente
                    if centroide.is_empty:
                        print(f"   [!] Error espacial: Centroide vacío para {nombre_comuna}. Se omitirá.")
                        continue

                    # 5. Extraer temperatura con Nearest Neighbor
                    temp_comuna_series = da_temp.sel(
                        longitude=centroide.x, 
                        latitude=centroide.y, 
                        method="nearest"
                    ).to_series()
                    
                # Guardar el resultado
                df_temp = pd.DataFrame({
                    'fecha_hora': temp_comuna_series.index,
                    'comuna': nombre_comuna,
                    'temperatura': temp_comuna_series.values
                })
                
                resultados.append(df_temp)
                
            ds.close() 
            
    print("3. Concatenando y guardando datos...")
    df_final = pd.concat(resultados, ignore_index=True)
    
    # Opcional: Pasar de Kelvin a Celsius (descomentar si ERA5 está en Kelvin)
    df_final['temperatura'] = df_final['temperatura'] - 273.15
    
    ruta_salida = os.path.join(OUT_DIR, "demanda_comunal_horaria_temperatura.csv")
    df_final.to_csv(ruta_salida, index=False)
    print(f"¡Éxito! Dataset guardado en:\n{ruta_salida}")

if __name__ == "__main__":
    main()