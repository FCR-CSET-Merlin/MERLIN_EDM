import pandas as pd
from pathlib import Path
import os

def convert_dir_csv_to_parquet(directory_path, delete_original=False):
    """
    Escanea un directorio y convierte todos los archivos .csv a formato .parquet.
    
    Parámetros:
    - directory_path (str o Path): Ruta al directorio que contiene los .csv.
    - delete_original (bool): Si es True, elimina el .csv después de crear el .parquet.
    """
    # Asegurarnos de que la ruta sea un objeto Path
    path = Path(directory_path)
    
    if not path.exists() or not path.is_dir():
        print(f"Error: El directorio '{directory_path}' no existe o no es válido.")
        return
    
    # Buscar todos los archivos .csv en el directorio
    csv_files = list(path.glob('*.csv'))
    
    if not csv_files:
        print(f"No se encontraron archivos .csv en {directory_path}")
        return
        
    print(f"Se encontraron {len(csv_files)} archivos .csv. Iniciando conversión...\n")
    
    for csv_file in csv_files:
        # Definir el nombre del nuevo archivo cambiando la extensión
        parquet_file = csv_file.with_suffix('.parquet')
        
        print(f"Procesando: {csv_file.name}...")
        
        try:
            # Leer el archivo CSV
            # Nota: Si el CSV es monstruosamente grande para tu RAM, aquí se podría 
            # usar pyarrow.csv.read_csv directamente, pero pandas suele ser suficiente.
            df = pd.read_csv(csv_file)
            
            # Guardar como Parquet usando compresión 'snappy' (por defecto en pyarrow)
            df.to_parquet(parquet_file, engine='pyarrow', index=False)
            
            # Calcular cuánto se comprimió
            size_csv_mb = csv_file.stat().st_size / (1024 * 1024)
            size_pqt_mb = parquet_file.stat().st_size / (1024 * 1024)
            
            print(f"  -> Guardado exitosamente como: {parquet_file.name}")
            print(f"  -> Compresión: de {size_csv_mb:.1f} MB a {size_pqt_mb:.1f} MB")
            
            # Opción para liberar espacio en disco
            if delete_original:
                os.remove(csv_file)
                print(f"  -> Archivo original eliminado.\n")
            else:
                print("") # Salto de línea por estética
                
        except Exception as e:
            print(f"Error al procesar {csv_file.name}: {e}\n")

# ==========================================
# CÓMO USARLO EN TU PROYECTO MERLIN
# ==========================================
if __name__ == "__main__":
    # Define la ruta absoluta o relativa a tu carpeta interim
    # Ajusta esta ruta según la ubicación de tu script
    DIRECTORIO_INTERIM = r"../data/interim" 
    
    # Ejecutar la función (pon delete_original=True SOLO si estás seguro 
    # de que ya no necesitas los .csv de respaldo)
    convert_dir_csv_to_parquet(DIRECTORIO_INTERIM, delete_original=False)