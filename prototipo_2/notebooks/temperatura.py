import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

def graficar_temperatura(ruta_csv, comuna_objetivo, fecha_inicio, fecha_fin):
    """
    Lee el CSV generado, filtra por comuna y rango de fechas, y grafica la serie de tiempo.
    Formatos esperados de fecha: 'YYYY-MM-DD' o 'YYYY-MM-DD HH:MM:SS'
    """
    print(f"\nGenerando gráfico para {comuna_objetivo} desde {fecha_inicio} hasta {fecha_fin}...")
    
    # 1. Cargar el dataset
    df = pd.read_csv(ruta_csv)
    
    # 2. Convertir la columna de fecha a tipo datetime de Pandas
    df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])
    
    # 3. Filtrar por la comuna deseada
    df_comuna = df[df['comuna'] == comuna_objetivo]
    
    if df_comuna.empty:
        print(f"[!] No se encontraron datos para la comuna: {comuna_objetivo}")
        return
        
    # 4. Crear máscara booleana para el rango de fechas
    mascara_fechas = (df_comuna['fecha_hora'] >= fecha_inicio) & (df_comuna['fecha_hora'] <= fecha_fin)
    df_final = df_comuna.loc[mascara_fechas]
    
    if df_final.empty:
        print(f"[!] No hay datos en el rango de fechas {fecha_inicio} a {fecha_fin} para {comuna_objetivo}.")
        return

    # 5. Configurar y dibujar el gráfico
    plt.figure(figsize=(14, 6))
    
    # Graficar la línea
    plt.plot(df_final['fecha_hora'], df_final['temperatura'], 
             color='#d62728', linewidth=1.5, label='Temperatura (°C)')
    
    # Formateo visual
    plt.title(f'Temperatura Horaria Urbana - Comuna: {comuna_objetivo}\n(Modelo MERLIN)', fontsize=14, fontweight='bold')
    plt.xlabel('Fecha y Hora', fontsize=12)
    plt.ylabel('Temperatura (°C)', fontsize=12)
    
    # Mejorar la visualización del eje X (Fechas)
    ax = plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.xticks(rotation=45)
    
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout() # Ajusta los márgenes para que no se corten las etiquetas
    
    # Mostrar el gráfico en pantalla
    plt.show()

if __name__ == "__main__":
    
    # 2. Definir la ruta del archivo que main() acaba de crear
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.dirname(SCRIPT_DIR)
    ruta_salida = os.path.join(BASE_DIR, "data", "interim", "demanda_comunal_horaria_temperatura.csv")
    
    # 3. Llamar a la función de graficado
    # Puedes ajustar la comuna y las fechas según lo que haya en tu mes de prueba
    graficar_temperatura(
        ruta_csv=ruta_salida,
        comuna_objetivo="SANTIAGO", # Cambia esto por una comuna de tu interés
        fecha_inicio="2018-01-01 00:00:00",
        fecha_fin="2023-01-01 23:59:59" 
    )