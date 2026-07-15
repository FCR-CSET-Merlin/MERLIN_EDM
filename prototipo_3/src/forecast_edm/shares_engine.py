import pandas as pd
import numpy as np
import geopandas as gpd

# Definimos las columnas de los sectores
SECTOR_COLS = ['share_I', 'share_R', 'share_C', 'share_P', 'share_T']

def _project_temporal_shares(df_hist, target_year, is_comuna):
    """
    Proyecta los consumos físicos hacia un año futuro usando una tendencia lineal simple
    y luego normaliza los resultados para que los shares sectoriales sumen exactamente 1.0.
    """
    df_proj = df_hist.copy()
    
    # Si el año ya existe en la historia, lo retornamos tal cual
    if target_year in df_proj['año'].values:
        return df_proj[df_proj['año'] == target_year]

    # Función interna para proyectar un set de datos (1 fila por año)
    def extrapolate_1d(df_sub):
        years = df_sub['año'].values
        
        # Si hay un solo año histórico, no podemos hacer tendencia, repetimos el último
        if len(years) < 2:
            row = df_sub.iloc[-1].copy()
            row['año'] = target_year
            return row
            
        future_row = df_sub.iloc[-1].copy()
        future_row['año'] = target_year
        
        # 1. Proyectar 'share_region_comuna' directamente
        z_src = np.polyfit(years, df_sub['share_region_comuna'].values, 1)
        p_src = np.poly1d(z_src)
        future_row['share_region_comuna'] = np.clip(p_src(target_year), 0.0, 1.0)
            
        # 2. Proyectar los consumos físicos (MWh) para obtener shares orgánicos
        total_proyectado = 0.0
        consumos_pred = {}
        
        for col_share in SECTOR_COLS:
            sector = col_share.split('_')[1] # Extrae 'I', 'R', 'C', 'P', 'T'
            
            # NOTA: Asumimos que las columnas físicas existen en df_hist.
            # Cambia el nombre aquí si en tu base se llaman diferente.
            col_mwh = f'consumo_{sector}_MWh' 
            
            # Ajuste lineal simple sobre los MWh
            z_mwh = np.polyfit(years, df_sub[col_mwh].values, 1)
            p_mwh = np.poly1d(z_mwh)
            pred_mwh = p_mwh(target_year)
            
            # Filtro físico: el consumo no puede ser negativo
            pred_mwh = max(0.0, pred_mwh)
            
            consumos_pred[col_share] = pred_mwh
            total_proyectado += pred_mwh
            
            # (Opcional) Guardamos el MWh proyectado en la fila por si fuera útil después
            future_row[col_mwh] = pred_mwh
                
        # 3. Calcular y re-normalizar los shares orgánicamente (Suma = 1.0)
        for col_share, mwh in consumos_pred.items():
            if total_proyectado > 0:
                future_row[col_share] = mwh / total_proyectado
            else:
                future_row[col_share] = 0.0
                
        return future_row

    # Aplicar la proyección
    if not is_comuna:
        # A nivel regional es 1 sola fila proyectada
        return extrapolate_1d(df_proj).to_frame().T
    else:
        # A nivel comunal, proyectamos la tendencia de CADA MES por separado
        projected_months = []
        for month in range(1, 13):
            df_month = df_proj[df_proj['mes'] == month]
            if not df_month.empty:
                projected_months.append(extrapolate_1d(df_month))
        return pd.DataFrame(projected_months)


def _interpolate_spatial_comuna(comuna_id, gdf_mapa, available_comunas, area_tolerance=0.3):
    """
    Encuentra la comuna más cercana geográficamente que tenga un área similar
    y que exista en nuestra base de datos histórica.
    """
    # 1. Obtener la geometría de la comuna objetivo
    target_geom = gdf_mapa[gdf_mapa['comuna_id'] == comuna_id]
    if target_geom.empty:
        raise ValueError(f"La comuna {comuna_id} no existe en la geocapa.")
    
    target_centroid = target_geom.geometry.centroid.iloc[0]
    target_area = target_geom.geometry.area.iloc[0]
    
    # 2. Filtrar el mapa solo con las comunas que SÍ tienen datos históricos
    gdf_available = gdf_mapa[gdf_mapa['comuna_id'].isin(available_comunas)].copy()
    
    # 3. Filtro de Área: Descartar comunas monstruosamente más grandes o pequeñas
    min_area = target_area * (1 - area_tolerance)
    max_area = target_area * (1 + area_tolerance)
    gdf_filtered = gdf_available[(gdf_available.geometry.area >= min_area) & 
                                 (gdf_available.geometry.area <= max_area)].copy()
    
    # Si el filtro de área es muy estricto y elimina todo, relajamos el filtro
    if gdf_filtered.empty:
        print(f"Advertencia: No se encontraron comunas con área similar para {comuna_id}. Relajando filtro de área.")
        gdf_filtered = gdf_available.copy()

    # 4. Calcular distancia desde el centroide objetivo a todos los centroides candidatos
    gdf_filtered['distance'] = gdf_filtered.geometry.centroid.distance(target_centroid)
    
    # 5. Obtener la comuna con la distancia mínima
    nearest_comuna = gdf_filtered.loc[gdf_filtered['distance'].idxmin(), 'comuna_id']
    print(f"-> Interpolación Espacial: Usando perfil de '{nearest_comuna}' para simular '{comuna_id}'.")
    
    return nearest_comuna


def get_shares(loc_id, is_comuna, year, df_shares, gdf_mapa=None):
    """
    Función principal para obtener el DataFrame de shares de una Región o Comuna.
    """
    # Filtrar el histórico para la localidad
    df_loc = df_shares[df_shares['id'] == loc_id].copy()
    
    # --- INTERPOLACIÓN ESPACIAL (Solo Comunas) ---
    if df_loc.empty:
        if not is_comuna:
            raise ValueError(f"Faltan datos para la región {loc_id}. No se interpola a nivel regional.")
        if gdf_mapa is None:
            raise ValueError(f"Comuna {loc_id} no tiene datos. Se requiere gdf_mapa para interpolar.")
            
        # Obtener lista de comunas que sí tienen datos
        comunas_con_datos = df_shares['id'].unique()
        
        # Encontrar la comuna "donante" de perfil
        donor_id = _interpolate_spatial_comuna(loc_id, gdf_mapa, comunas_con_datos)
        
        # Extraer los datos de la comuna donante y disfrazarlos como nuestra localidad
        df_loc = df_shares[df_shares['id'] == donor_id].copy()
        df_loc['id'] = loc_id
        df_loc['is_interpolated'] = True 
    else:
        df_loc['is_interpolated'] = False

    # --- PROYECCIÓN TEMPORAL ---
    # Revisar si tenemos el año exacto
    if year in df_loc['año'].values:
        res = df_loc[df_loc['año'] == year]
    else:
        print(f"-> Proyección Temporal: Estimando shares de {loc_id} para el año {year}.")
        res = _project_temporal_shares(df_loc, year, is_comuna)
        
    # Limpieza final de columnas para asegurar el formato esperado de salida
    if is_comuna:
        return res[['id', 'año', 'mes', 'share_region_comuna'] + SECTOR_COLS].sort_values('mes').reset_index(drop=True)
    else:
        return res[['id', 'año', 'share_region_comuna'] + SECTOR_COLS].reset_index(drop=True)