import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Input, BatchNormalization
from tensorflow.keras.losses import Huber
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
import os
import glob

def load_and_split_xy(filepath, target_col='demanda_mwh'):
    print(f"  Cargando {filepath}...")
    df = pd.read_parquet(filepath, engine='pyarrow')
    
    # Separar variables predictoras (X) de la variable objetivo (y)
    y = df[target_col].values
    X = df.drop(columns=[target_col]).values
    
    return X, y

def build_mlp_model(input_dim):
    """
    Construye la arquitectura del Perceptrón Multicapa (MLP).
    Los hiperparámetros (neuronas, capas) se pueden ajustar iterativamente.
    """
    model = Sequential([
        Input(shape=(input_dim,)),
        Dense(256, activation='elu'),
        # Dropout(0.2), # Previene el sobreajuste apagando neuronas aleatoriamente
        Dense(128, activation='elu'),
        # Dropout(0.2),
        Dense(64, activation='elu'),
        Dense(32, activation='elu'),
        Dense(1, activation='linear') # Capa de salida (1 valor numérico)
    ])
    
    # Compilar usando el optimizador Adam y la pérdida Huber
    optimizer = tf.keras.optimizers.Adam(learning_rate=0.0005)
    model.compile(optimizer=optimizer, loss=Huber(delta=1.0), metrics=['mae'])
    return model

if __name__ == "__main__":
    print("Iniciando entrenamiento iterativo por comuna...")

    # 1. Definir directorios base (Nuevas rutas según lo solicitado)
    DATA_DIR = "../data/processed/modelo_nacional/ml_data"
    MODEL_DIR = "../models/modelo_nacional/ml_models/"
    
    # Asegurarse de que el directorio de modelos exista
    os.makedirs(MODEL_DIR, exist_ok=True)

    # 0. Parámetros generales del entrenamiento
    patience = 10
    epochs = 150
    # Batch size pequeño/medio es recomendable a nivel comunal
    batch_size = 64 

    # 2. Identificar todas las comunas disponibles
    # Asumimos el patrón de nombre "train_{comuna_name}.parquet"
    search_pattern = os.path.join(DATA_DIR, "train_*.parquet")
    train_files = glob.glob(search_pattern)
    
    comunas = []
    for file in train_files:
        filename = os.path.basename(file)
        # Limpiar el nombre para quedarnos solo con el identificador de la comuna
        comuna_name = filename.replace("train_", "").replace(".parquet", "")
        comunas.append(comuna_name)
        
    print(f"Se encontraron {len(comunas)} comunas para entrenar en la carpeta de datos.")

    # 3. Bucle Iterativo de Entrenamiento
    for comuna in comunas:
        print(f"\n{'='*50}")
        print(f"Entrenando modelo para la comuna: {comuna}")
        print(f"{'='*50}")
        
        # Construir rutas específicas para esta iteración
        TRAIN_FILE = os.path.join(DATA_DIR, f"train_{comuna}.parquet")
        VAL_FILE   = os.path.join(DATA_DIR, f"val_{comuna}.parquet")
        MODEL_PATH = os.path.join(MODEL_DIR, f"best_mlp_{comuna}.keras")
        
        # Validar existencia de datos de validación
        if not os.path.exists(VAL_FILE):
            print(f"  [ADVERTENCIA] No se encontró el archivo de validación para {comuna}. Saltando...")
            continue
            
        try:
            # A. Cargar datos
            X_train, y_train = load_and_split_xy(TRAIN_FILE)
            X_val, y_val     = load_and_split_xy(VAL_FILE)
            
            print(f"  -> Shape Train: X={X_train.shape}, y={y_train.shape}")
            print(f"  -> Shape Val:   X={X_val.shape}, y={y_val.shape}")
            
            # B. Construir modelo
            input_dimension = X_train.shape[1]
            model = build_mlp_model(input_dimension)
            
            # C. Configurar Callbacks (IMPORTANTE: El Checkpoint ahora apunta a MODEL_PATH)
            early_stop = EarlyStopping(monitor='val_loss', patience=patience, restore_best_weights=True, verbose=1)
            checkpoint = ModelCheckpoint(MODEL_PATH, monitor='val_loss', save_best_only=True, verbose=1)
            reduce_lr  = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=0.00001, verbose=1)
            
            # D. ¡Entrenar!
            history = model.fit(
                X_train, y_train,
                validation_data=(X_val, y_val),
                epochs=epochs,
                batch_size=batch_size,
                callbacks=[early_stop, checkpoint, reduce_lr],
                verbose=2  # verbose=2 para un output más limpio por época. Usa 1 si prefieres ver la barra de progreso
            )
            
            print(f"  [ÉXITO] Modelo de {comuna} guardado correctamente en {MODEL_PATH}")
            
        except Exception as e:
            # Si ocurre algún problema matemático, de OOM (Out of Memory), o archivos vacíos,
            # el script lo atrapa aquí, te informa y pasa a la siguiente comuna.
            print(f"  [ERROR] Falló el entrenamiento para {comuna}. Detalles: {e}")
            continue

    print("\n¡Proceso global finalizado!")