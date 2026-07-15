import pandas as pd
import numpy as np
import calendar

def _get_hours_in_year(year):
    """
    Determina la cantidad exacta de horas en un año (bisiesto o normal).
    """
    # Se emplea el método .isleap(year) que entrega un booleano si es bisiesto o no
    is_leap = calendar.isleap(year)
    return 8784 if is_leap else 8760


def calculate_scaling_parameters(total_anual_mwh, consumos_anuales_sectores, year, a, b):
    """
    Calcula mu y sigma global de la zona, así como los valores 'sin sector' 
    para la etapa de desagregación de la demanda.
    
    Args:
        total_anual_mwh (float): Consumo físico total proyectado para el año completo (MWh).
        consumos_anuales_sectores (dict): Diccionario con el consumo anual de cada sector.
                                          Ej: {'I': 1500.5, 'R': 2000.0, 'C': 500.0, ...}
        year (int): Año a evaluar (para definir 8760 vs 8784 horas).
        a (float): Parámetro 'a' de la curva de correlación empírica (sigma = a * mu^b).
        b (float): Parámetro 'b' de la curva de correlación empírica.
        
    Returns:
        dict: Diccionario que contiene mu_total, sigma_total, mu_sin_X, sigma_sin_X.
    """
    horas_anio = _get_hours_in_year(year)
    
    # 1. Parámetros Globales (Total de la Zona)
    mu_total = total_anual_mwh / horas_anio
    sigma_total = a * (mu_total ** b)
    
    resultados = {
        'mu_total': mu_total,
        'sigma_total': sigma_total
    }
    
    # 2. Parámetros "Sin Sector" para los Escenarios Puros (Desagregación)
    for sector, consumo_sector in consumos_anuales_sectores.items():
        # Restamos el consumo del sector al total. Aplicamos max(0.0) como filtro 
        # físico por si la matemática de proyección arrojara inconsistencias ínfimas.
        total_sin_sector = max(0.0, total_anual_mwh - consumo_sector)
        
        mu_sin = total_sin_sector / horas_anio
        
        # Omitimos cálculo de sigma si mu es 0 (ej. zona sin consumo) para evitar errores matemáticos
        if mu_sin > 0:
            sigma_sin = a * (mu_sin ** b)
        else:
            sigma_sin = 0.0
            
        resultados[f'mu_sin_{sector}'] = mu_sin
        resultados[f'sigma_sin_{sector}'] = sigma_sin
        
    return resultados


def scale_temperature_features(df_inputs, temp_columns, temp_scaler):
    """
    Aplica el escalado a las variables de temperatura utilizando 
    el scaler pre-entrenado del modelo.
    
    Args:
        df_inputs (pd.DataFrame): DataFrame que contiene los features del modelo.
        temp_columns (list): Lista de nombres de las columnas de temperatura 
                             (ej. ['temperatura', 'temp_t-1', ...]).
        temp_scaler (sklearn scaler): Objeto Scaler cargado vía joblib.
        
    Returns:
        pd.DataFrame: DataFrame con las temperaturas escaladas.
    """
    df_scaled = df_inputs.copy()
    
    # Se asegura de escalar solo las columnas indicadas y reemplazarlas in-place
    df_scaled[temp_columns] = temp_scaler.transform(df_scaled[temp_columns])
    
    return df_scaled