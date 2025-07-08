# Usar una imagen base más confiable y reciente
FROM ubuntu:22.04

# Instalar dependencias del sistema y configurar repositorio de AceStream
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    curl \
    gnupg \
    ca-certificates \
    python3 \
    python3-pip && \
    # Configurar repositorio de AceStream
    wget -q -O - http://acestream.org/keys/acestream.asc | gpg --dearmor > /etc/apt/trusted.gpg.d/acestream.gpg && \
    echo "deb http://repo.acestream.org/ubuntu/ jammy main" > /etc/apt/sources.list.d/acestream.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends acestream-engine && \
    # Limpiar caché para reducir tamaño de la imagen
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Instalar dependencias Python
RUN pip3 install --no-cache-dir flask psutil requests

# Crear directorio de trabajo
WORKDIR /app

# Copiar nuestra API
COPY control_api.py /app/

# Exponer puertos
EXPOSE 8080 6878

# Ejecutar nuestra API
CMD ["python3", "control_api.py"]