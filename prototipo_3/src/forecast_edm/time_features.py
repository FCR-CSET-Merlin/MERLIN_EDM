import pandas as pd 
import numpy as np 
import holidays

def build_temperature_lags(
        df_temp, 
        temp_col='temperatura', 
        tau=7
):
    """
    Toma un Dataframe anual de temperatura y genera los lags, 
    usando las últimas 'tau' horas para rellenar el inicio.
    """

    df = df_temp.copy()

    for i in range(1, tau + 1): 
        # np.roll desplaza los valores. Al desplazar hacia abajo, 
        # los últimos valores pasan automáticamente al principio
        df[f'temp_t - {i}'] = np.roll(df[temp_col], i)

    return df


def build_calendar_features(df, dt_col='fecha_hora', country='CL', subdiv=None):
    """
    Construye las variables trigonométricas y categóricas del calendario
    a partir de una columna de fecha y hora.
    
    Args:
        df (pd.DataFrame): DataFrame que contiene la serie temporal.
        dt_col (str): Nombre de la columna con las fechas (Datetime).
        country (str): Código ISO del país para buscar los feriados (Defecto: 'CL').
        subdiv (str): Código  ISO de la subdivisón (región) del país (Defecto: None)
        
    Returns:
        pd.DataFrame: DataFrame con las nuevas columnas de features temporales.
    """
    df = df.copy()
    
    # 0. Asegurar que la columna de entrada sea de tipo datetime de Pandas
    if not pd.api.types.is_datetime64_any_dtype(df[dt_col]):
        df[dt_col] = pd.to_datetime(df[dt_col])
        
    # 1. Extraer componentes base
    hour = df[dt_col].dt.hour
    day_of_week = df[dt_col].dt.dayofweek  # Lunes = 0, Domingo = 6
    day_of_year = df[dt_col].dt.dayofyear
    # Detectar años bisiestos para ajustar la longitud del ciclo anual
    days_in_year = df[dt_col].dt.is_leap_year.map({True: 366, False: 365})
    
    # 2. Transformaciones Trigonométricas (Ciclos)
    # Ciclo diario (24 horas)
    df['hour_sin'] = np.sin(2 * np.pi * hour / 24)
    df['hour_cos'] = np.cos(2 * np.pi * hour / 24)
    
    # Ciclo semanal (7 días)
    df['dow_sin'] = np.sin(2 * np.pi * day_of_week / 7)
    df['dow_cos'] = np.cos(2 * np.pi * day_of_week / 7)
    
    # Ciclo anual (365/366 días) - *Sugerido para complementar estacionalidad
    df['doy_sin'] = np.sin(2 * np.pi * day_of_year / days_in_year)
    df['doy_cos'] = np.cos(2 * np.pi * day_of_year / days_in_year)
    
    # 3. Flags Categóricos (Fines de semana y Festivos)
    df['is_weekend'] = df[dt_col].dt.dayofweek.isin([5, 6]).astype(int)
    
    # Obtener festivos del país para los años presentes en el DataFrame
    years = df[dt_col].dt.year.unique()
    cl_holidays = holidays.country_holidays(country, subdiv=subdiv, years=years)
    
    # Mapear si la fecha cae en un día festivo
    df['is_holiday'] = df[dt_col].dt.date.apply(lambda d: d in cl_holidays).astype(int)
    
    # 4. Día laboral (Es True solo si NO es fin de semana y NO es festivo)
    df['is_working_day'] = ((df['is_weekend'] == 0) & (df['is_holiday'] == 0)).astype(int)
    
    return df