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
    zlib1g || { echo "Error instalando dependencias"; exit 1; } && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Instalar acestream-engine desde tar.gz
RUN echo "Paso 1: Descargando tar.gz" && \
    wget -q -O /tmp/acestream.tar.gz https://download.acestream.media/linux/acestream_3.2.3_ubuntu_18.04_x86_64_py3.8.tar.gz || { echo "Error descargando tar.gz"; exit 1; } && \
    echo "Paso 2: Descarga completada" && \
    mkdir -p /opt/acestream || { echo "Error creando /opt/acestream"; exit 1; } && \
    echo "Paso 3: Descomprimiendo tar.gz" && \
    tar --verbose -xzf /tmp/acestream.tar.gz -C /opt/acestream || { echo "Error descomprimiendo tar.gz"; exit 1; } && \
    echo "Paso 4: Descompresión completada" && \
    rm -f /tmp/acestream.tar.gz && \
    echo "Paso 5: Buscando acestreamengine" && \
    find /opt/acestream -type f -name acestreamengine || { echo "acestreamengine no encontrado"; exit 1; } && \
    echo "Paso 6: Binario encontrado" && \
    find /opt/acestream -type f -name acestreamengine -exec chmod +x {} \; -exec ln -sf {} /usr/bin/acestreamengine \; || { echo "Error creando enlace simbólico"; exit 1; } && \
    echo "Paso 7: Enlace simbólico creado" && \
    ls -lR /opt/acestream || { echo "Error listando /opt/acestream"; exit 1; } && \
    echo "Paso 8: Listado de /opt/acestream completado" && \
    which acestreamengine || { echo "acestreamengine no encontrado en /usr/bin"; exit 1; } && \
    echo "Paso 9: which completado" && \
    ldd /usr/bin/acestreamengine || { echo "Error ejecutando ldd"; exit 1; } && \
    echo "Paso 10: ldd completado" && \
    acestreamengine --version || { echo "acestreamengine no ejecutable"; ldd /usr/bin/acestreamengine; exit 1; }

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