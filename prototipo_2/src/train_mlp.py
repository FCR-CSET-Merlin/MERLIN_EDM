import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Input, BatchNormalization # <- Añadido BatchNormalization
from tensorflow.keras.losses import Huber # <- Añadida la pérdida de Huber
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
import os

def load_and_split_xy(filepath, target_col='demanda_mwh'):
    print(f"Cargando {filepath}...")
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
    
    # Compilar usando el optimizador Adam y Error Cuadrático Medio (MSE)
    optimizer = tf.keras.optimizers.Adam(learning_rate=0.0005)
    model.compile(optimizer=optimizer, loss=Huber(delta=1.0), metrics=['mae'])
    return model

if __name__ == "__main__":
    
    prototype_S = False  ##### MODIFICAR ESTO SI ES NECESARIO
    prototype_RM = True

    if prototype_S:

        print("Cargando datos de comuna de Santiago")

        # 0. Parámetros
        patience = 10
        epochs = 150
        batch_size = 64

        # 1. Definir rutas
        TRAIN_FILE = "../data/processed/train_merlin_stgo.parquet"
        VAL_FILE   = "../data/processed/val_merlin_stgo.parquet"
        MODEL_DIR  = "../models/"
        NAME = "best_merlin_mlp_stgo.keras"
        os.makedirs(MODEL_DIR, exist_ok=True)

    if prototype_RM: 

        print("Cargando datos de Región Metropolitana")

        # 0. Parámetros
        patience = 10
        epochs = 100
        batch_size = 256

        # 1. Definir rutas
        TRAIN_FILE = "../data/processed/train_merlin_RM.parquet"
        VAL_FILE   = "../data/processed/val_merlin_RM.parquet"
        MODEL_DIR  = "../models/"
        NAME = "best_merlin_mlp_RM.keras"
        os.makedirs(MODEL_DIR, exist_ok=True)

    
    elif not (prototype_S or prototype_RM):

        print("Cargando datos de todas las comunas")

        # 0. Parámetros
        patience = 10
        epochs = 100
        batch_size = 8192

        # 1. Definir rutas
        TRAIN_FILE = "../data/processed/train_merlin.parquet"
        VAL_FILE   = "../data/processed/val_merlin.parquet"
        MODEL_DIR  = "../models/"
        NAME = "best_merlin_mlp.keras"
        os.makedirs(MODEL_DIR, exist_ok=True)

    
    # 2. Cargar datos
    X_train, y_train = load_and_split_xy(TRAIN_FILE)
    X_val, y_val     = load_and_split_xy(VAL_FILE)
    
    print(f"-> Shape de Entrenamiento: X={X_train.shape}, y={y_train.shape}")
    print(f"-> Shape de Validación:  X={X_val.shape}, y={y_val.shape}")
    
    # 3. Construir modelo
    input_dimension = X_train.shape[1]
    model = build_mlp_model(input_dimension)
    model.summary()
    
    # 4. Configurar Callbacks
    # EarlyStopping: Detiene el entrenamiento si el error de validación no mejora en 10 épocas
    early_stop = EarlyStopping(monitor='val_loss', patience=patience, restore_best_weights=True, verbose=1)
    
    # ModelCheckpoint: Guarda automáticamente la mejor versión del modelo
    checkpoint = ModelCheckpoint(os.path.join(MODEL_DIR, NAME), 
                                 monitor='val_loss', save_best_only=True, verbose=1)
    
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=0.00001, verbose=1)
    
    # 5. ¡Entrenar la Red Neuronal!
    print("\nIniciando entrenamiento...")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,           # Máximo de épocas (EarlyStopping cortará antes si es necesario)
        batch_size=batch_size,      # Lotes grandes para acelerar el procesamiento
        callbacks=[early_stop, checkpoint],
        verbose=1
    )
    
    print("\n¡Entrenamiento finalizado y modelo guardado!")