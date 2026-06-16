import tensorflow as tf
import os

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

print("Versión de TF:", tf.__version__)
print("GPU Disponible:", tf.config.list_physical_devices('GPU'))

try:
    from tensorflow.python.keras import layers
    print("Keras importado exitosamente.")
except Exception as e:
    print("Error importando Keras:", e)