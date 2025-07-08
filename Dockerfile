# Usar imagen base Ubuntu 20.04
FROM ubuntu:20.04

# Establecer variables de entorno para evitar interacciones interactivas
ENV DEBIAN_FRONTEND=noninteractive

# Actualizar e instalar dependencias básicas
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    curl \
    python3 \
    python3-pip \
    libpython3.8 \
    libssl1.1 \
    libavahi-compat-libdnssd1 \
    libcrypto++6 \
    libglib2.0-0 \
    libstdc++6 \
    libgcc1 \
    libc6 \
    libffi7 \
    zlib1g && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Solo descargar y ver qué pasa
RUN wget -v -O /tmp/acestream.tar.gz https://download.acestream.media/linux/acestream_3.2.3_ubuntu_18.04_x86_64_py3.8.tar.gz

# Ver el archivo descargado
RUN ls -la /tmp/acestream.tar.gz && file /tmp/acestream.tar.gz

# Descomprimir y ver estructura
RUN mkdir -p /opt/acestream && \
    tar -xzf /tmp/acestream.tar.gz -C /opt/acestream && \
    ls -la /opt/acestream/

# Ver toda la estructura
RUN find /opt/acestream -type f | head -20

# Buscar el binario específico
RUN find /opt/acestream -name "*stream*" -type f
RUN find /opt/acestream -name "acestreamengine*" -type f

# Instalar dependencias Python
RUN pip3 install --no-cache-dir flask psutil requests

# Crear directorio de trabajo
WORKDIR /app

# Copiar la API
COPY control_api.py /app/

# Exponer puertos
EXPOSE 8080 6878

# Ejecutar la API
CMD ["python3", "control_api.py"]