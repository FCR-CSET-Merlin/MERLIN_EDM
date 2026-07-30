# Usamos una imagen base oficial de Python ligera
FROM python:3.10-slim

# Instalar dependencias del sistema operativo requeridas por GeoPandas (GDAL, GEOS, PROJ)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    proj-data \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Configurar variables de entorno para compilar librerías espaciales correctamente
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Definir el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo de dependencias e instalarlas
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el contenido de prototipo_3 y el resto del código del repositorio
COPY . .

# Comando por defecto para ejecutar tu script principal dentro de prototipo_3
# (Modifica la ruta si tu orquestador principal tiene otra ubicación)
CMD ["python", "prototipo_3/src/train_mlp.py"]