import pandas as pd
import tensorflow as tf
import joblib
import glob
import os

# 0. Configuración de rutas y columnas
METADATA_DIR = "../data/processed/modelo_nacional/metadata"
MODELS_DIR = "../models/modelo_nacional"
metadata_cols = ["year", "fecha_hora", "region", "comuna", "region_bne"]

# Usamos glob para encontrar todos los archivos de validación. 
# Asume que guardaste como "val_{COMUNA}_metadata.parquet"
archivos_val = glob.glob(os.path.join(METADATA_DIR, "val_*.parquet"))

# Lista para ir guardando los DataFrames individuales
lista_resultados = []

print(f"Se encontraron {len(archivos_val)} archivos de validación. Iniciando procesamiento...\n")

for filepath in archivos_val:
    # 1. Extraer el identificador (comuna o región) del nombre del archivo
    # Ej: "val_SANTIAGO_metadata.parquet" -> "SANTIAGO"
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
        
        X_val_scaled = df_scaled.drop(columns=['demanda_mwh'] + metadata_cols).values
        
        # 5. Hacer predicciones (silenciando la salida de Keras para no inundar la consola)
        y_pred_scaled = model.predict(X_val_scaled, verbose=0)
        
        # 6. Devolver a la escala original
        y_pred_real = scaler_y.inverse_transform(y_pred_scaled).flatten()
        
        # 7. Reconstruir el DataFrame para esta comuna
        df_res_local = df_metadata.copy()
        df_res_local['demanda_real_mwh'] = y_val_real
        df_res_local['demanda_pred_mwh'] = y_pred_real
        
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
    
    # Opcional: Guardar este DataFrame gigante para graficar o calcular métricas sin tener que predecir de nuevo
    ruta_guardado = os.path.join(MODELS_DIR, "results/resultados_modelo_nacional.parquet")
    df_validacion_global.to_parquet(ruta_guardado)
    print(f"Resultados guardados en: {ruta_guardado}")
    
    # Muestra rápida
    print("\nMuestra de resultados globales:")
    print(df_validacion_global.head())
else:
    print("\nNo se pudo procesar ningún archivo. Revisa las rutas y nombres.")