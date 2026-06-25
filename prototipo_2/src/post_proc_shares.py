import pandas as pd
import numpy as np  # <-- Agregado para el np.maximum()
import tensorflow as tf
import joblib
import glob
import os

# 0. Configuración de rutas y columnas
METADATA_DIR = "../data/processed/modelo_nacional/metadata"
MODELS_DIR = "../models/modelo_nacional"
metadata_cols = ["year", "fecha_hora", "region", "comuna", "region_bne"]

# ==============================================================================
# ¡IMPORTANTE! Define los índices de las columnas de los shares en X_val_scaled.
# Ajusta estos números a la posición exacta que tienen en tu matriz de features.
# Ejemplo: 18=Industrial, 19=Residencial, 20=Comercial, 21=Público, 22=Transporte
idx_shares = {'I': 18, 'R': 19, 'C': 20, 'P': 21, 'T': 22} 
# ==============================================================================

# Usamos glob para encontrar todos los archivos de validación. 
archivos_val = glob.glob(os.path.join(METADATA_DIR, "val_*.parquet"))

# Lista para ir guardando los DataFrames individuales
lista_resultados = []

print(f"Se encontraron {len(archivos_val)} archivos de validación. Iniciando procesamiento...\n")

for filepath in archivos_val:
    # 1. Extraer el identificador (comuna o región) del nombre del archivo
    basename = os.path.basename(filepath)
    identificador = basename.replace("val_", "").replace(".parquet", "")
    
    print(f"Procesando: {identificador}...")
    
    try:
        # 2. Cargar los metadatos y variables reales de esta comuna
        df_val_md = pd.read_parquet(filepath)
        df_metadata = df_val_md[metadata_cols].copy()
        y_val_real = df_val_md['demanda_mwh'].values
        
        # 3. Cargar el modelo y scalers específicos de esta comuna
        model_path = os.path.join(MODELS_DIR, f"ml_models/best_mlp_{identificador}.keras")
        scaler_y_path = os.path.join(MODELS_DIR, f"scaler/scaler_demand_{identificador}.pkl")
        scaler_temp_path = os.path.join(MODELS_DIR, f"scaler/scaler_temp_{identificador}.pkl")
        
        model = tf.keras.models.load_model(model_path)
        scaler_y = joblib.load(scaler_y_path)
        temp_scaler = joblib.load(scaler_temp_path)
        
        # 4. Escalar los datos de entrada (X)
        df_scaled = df_val_md.copy()
        temp_columns = [col for col in df_scaled.columns if 'temp' in col.lower()]
        df_scaled[temp_columns] = temp_scaler.transform(df_scaled[temp_columns])
        
        # Extraemos la matriz de features (X)
        X_val_scaled = df_scaled.drop(columns=['demanda_mwh'] + metadata_cols).values
        
        # 5. Hacer predicción de la demanda TOTAL
        y_pred_scaled = model.predict(X_val_scaled, verbose=0)
        
        # 6. Devolver a la escala original
        y_pred_real = scaler_y.inverse_transform(y_pred_scaled).flatten()
        
        # 7. Inicializar el DataFrame para esta comuna con totales
        df_res_local = df_metadata.copy()
        df_res_local['demanda_real_mwh'] = y_val_real
        df_res_local['demanda_pred_mwh'] = y_pred_real
        
        # ==============================================================================
        # 7.5. DESAGREGACIÓN SECTORIAL (MÉTODO KUSUMOTO)
        # ==============================================================================
        predicciones_puras = {}

        for sector, idx in idx_shares.items():
            # a) Crear copia de la matriz de entrada para el escenario "puro"
            X_val_puro = X_val_scaled.copy()
            
            # b) Forzar a 0 todos los shares excepto el del sector actual
            for other_sector, other_idx in idx_shares.items():
                if other_sector != sector:
                    X_val_puro[:, other_idx] = 0.0
            X_val_puro[:, idx] = 1.0
                    
            # c) Predecir bajo el escenario alterado (silenciado)
            pred_escenario = model.predict(X_val_puro, verbose=0)
            
            # d) Des-escalar la predicción a MWh y aplanar el arreglo
            pred_mwh = scaler_y.inverse_transform(pred_escenario).flatten()
            
            # e) Aplicar Clipping para evitar valores negativos
            pred_mwh = np.maximum(0.0, pred_mwh)

            # f) Guardar en un diccionario
            predicciones_puras[sector] = pred_mwh
            
            # f) Guardar el sector en el dataframe local
            # df_res_local[f'demanda_pred_{sector}'] = pred_mwh
        # ==============================================================================
        # Pasar a dataframe el resultado
        df_puras = pd.DataFrame(predicciones_puras)

        # Calcular la suma de las predicciones puras 
        sectores = list(idx_shares.keys())
        df_puras["suma_puras"] = df_puras[sectores].sum(axis=1)

        # Calcular fracción horaria
        df_fracciones = pd.DataFrame()
        for sector in sectores: 
            df_fracciones[f'fraccion_{sector}'] = df_puras[sector] / (df_puras['suma_puras'] + 1e-9)
        
        # Re-escalar con la demanda total
        for sector in sectores: 
            df_res_local[f'demanda_pred_{sector}'] = df_fracciones[f"fraccion_{sector}"] * df_res_local["demanda_pred_mwh"]

        # Guardar en la lista maestra
        lista_resultados.append(df_res_local)
        
    except Exception as e:
        # Si algo falla (ej. un scaler no existe), imprime el error y pasa a la siguiente comuna
        print(f" [!] Error al procesar {identificador}: {e}")
        continue

# 8. Concatenar todo en un solo gran DataFrame de validación
if lista_resultados:
    df_validacion_global = pd.concat(lista_resultados, ignore_index=True)
    
    # Ordenar por fecha_hora y comuna para mayor legibilidad
    df_validacion_global = df_validacion_global.sort_values(by=['fecha_hora', 'comuna'])
    
    print("\n¡Procesamiento exitoso!")
    print(f"Dimensiones del DataFrame Global: {df_validacion_global.shape}")
    
    # Opcional: Guardar este DataFrame gigante para graficar o calcular métricas
    # Asegurarse de que exista la carpeta results
    results_dir = os.path.join(MODELS_DIR, "results")
    os.makedirs(results_dir, exist_ok=True)
    
    ruta_guardado = os.path.join(results_dir, "resultados_modelo_nacional_desagregado.parquet")
    df_validacion_global.to_parquet(ruta_guardado)
    print(f"Resultados guardados en: {ruta_guardado}")
    
    # Muestra rápida
    print("\nMuestra de resultados globales:")
    print(df_validacion_global.head())
else:
    print("\nNo se pudo procesar ningún archivo. Revisa las rutas y nombres.")