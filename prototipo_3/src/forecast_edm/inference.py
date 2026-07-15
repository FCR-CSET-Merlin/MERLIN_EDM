import pandas as pd
import numpy as np

def predict_and_disaggregate(model, df_inputs, df_metadata, feature_cols, sectores=['I', 'R', 'C', 'P', 'T']):
    """
    Realiza la estimación de demanda eléctrica total y la desagregación sectorial 
    mediante el método de resta de escenarios.
    
    Args:
        model (keras.Model): Modelo MLP global pre-entrenado.
        df_inputs (pd.DataFrame): DataFrame solo con los features (X) numéricos y escalados.
        df_metadata (pd.DataFrame): DataFrame con metadatos asociados a las filas de df_inputs 
                                    (debe contener mu_total, sigma_total, mu_sin_X, sigma_sin_X).
        feature_cols (list): Lista con el orden exacto de las columnas que traga el modelo.
        sectores (list): Lista de los identificadores de los sectores.
        
    Returns:
        pd.DataFrame: df_metadata enriquecido con las curvas de demanda total y por sector en MWh.
    """
    df_res = df_metadata.copy()
    
    # Aseguramos el orden estricto de las columnas para la red neuronal
    X_total = df_inputs[feature_cols].values

    # ---------------------------------------------------------
    # PASO 1: PREDICCIÓN TOTAL
    # ---------------------------------------------------------
    print("-> Calculando demanda total...")
    y_pred_scaled = model.predict(X_total, batch_size=2048).flatten()
    
    # Desescalamiento con parámetros globales
    df_res['demanda_total_pred'] = (y_pred_scaled * df_res['sigma_total']) + df_res['mu_total']
    df_res['demanda_total_pred'] = df_res['demanda_total_pred'].clip(lower=0.0) # Filtro físico

    # ---------------------------------------------------------
    # PASO 2: DESAGREGACIÓN SECTORIAL (MÉTODO DE RESTA)
    # ---------------------------------------------------------
    for sector in sectores:
        print(f"-> Desagregando sector: {sector}")
        df_sim = df_inputs.copy()
        
        # 1. Apagar el sector objetivo (llevar su share a cero)
        col_share = f'share_{sector}'
        df_sim[col_share] = 0.0

        # 2. Predecir el escenario "Sin el Sector"
        X_sim = df_sim[feature_cols].values
        y_pred_sin_scaled = model.predict(X_sim, batch_size=2048).flatten()

        # 3. Desescalar utilizando mu y sigma SIN el sector
        col_mu_sin = f'mu_sin_{sector}'
        col_sigma_sin = f'sigma_sin_{sector}'
        
        demanda_sin_pred = (y_pred_sin_scaled * df_res[col_sigma_sin]) + df_res[col_mu_sin]
        demanda_sin_pred = demanda_sin_pred.clip(lower=0.0)

        # 4. Obtener demanda del sector por diferencia (Total - Predicción sin el sector)
        col_demanda_sector = f'demanda_pred_{sector}'
        df_res[col_demanda_sector] = df_res['demanda_total_pred'] - demanda_sin_pred
        df_res[col_demanda_sector] = df_res[col_demanda_sector].clip(lower=0.0)

    return df_res