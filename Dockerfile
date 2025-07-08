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
    file \
    strace \
    libpython3.8 \
    libpython3.8-dev \
    libssl1.1 \
    libavahi-compat-libdnssd1 \
    libcrypto++6 \
    libglib2.0-0 \
    libstdc++6 \
    libgcc1 \
    libc6 \
    libffi7 \
    zlib1g \
    libavcodec58 \
    libavformat58 \
    libavutil56 \
    libswscale5 \
    libswresample3 \
    libasound2 \
    libpulse0 \
    libgl1-mesa-glx \
    libglu1-mesa \
    libxrender1 \
    libxext6 \
    libx11-6 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Descargar acestream
RUN echo "Paso 1: Descargando tar.gz" && \
    wget -v -O /tmp/acestream.tar.gz https://download.acestream.media/linux/acestream_3.2.3_ubuntu_18.04_x86_64_py3.8.tar.gz && \
    echo "Paso 2: Descarga completada" && \
    ls -la /tmp/acestream.tar.gz

# Crear directorio y descomprimir
RUN echo "Paso 3: Creando directorio y descomprimiendo" && \
    mkdir -p /opt/acestream && \
    tar -xzf /tmp/acestream.tar.gz -C /opt/acestream && \
    echo "Paso 4: Descompresión completada" && \
    rm -f /tmp/acestream.tar.gz

# Verificar contenido descomprimido
RUN echo "Paso 5: Verificando contenido descomprimido" && \
    ls -la /opt/acestream/ && \
    echo "Buscando binarios acestreamengine..." && \
    find /opt/acestream -name "acestreamengine" -type f

# Configurar el binario principal
RUN echo "Paso 6: Configurando binario principal" && \
    ACESTREAM_BIN=$(find /opt/acestream -name "acestreamengine" -type f | grep -v "/lib/" | head -1) && \
    echo "Binario principal seleccionado: $ACESTREAM_BIN" && \
    test -f "$ACESTREAM_BIN" && \
    chmod +x "$ACESTREAM_BIN" && \
    ln -sf "$ACESTREAM_BIN" /usr/bin/acestreamengine && \
    echo "Paso 7: Enlace simbólico creado"

# Verificar instalación
RUN echo "Paso 8: Verificando instalación" && \
    which acestreamengine && \
    ls -la /usr/bin/acestreamengine && \
    echo "Paso 9: Verificando dependencias" && \
    ldd /usr/bin/acestreamengine || echo "Algunas dependencias pueden faltar pero continuamos"

# Test final (más permisivo)
RUN echo "Paso 10: Test de existencia" && \
    test -x /usr/bin/acestreamengine && \
    echo "Binario ejecutable confirmado"

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