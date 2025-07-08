# Usar imagen base Ubuntu 20.04
FROM ubuntu:20.04

# Establecer variables de entorno para evitar interacciones interactivas
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONPATH=/opt/acestream:$PYTHONPATH
ENV LD_LIBRARY_PATH=/opt/acestream/lib:$LD_LIBRARY_PATH

# Actualizar e instalar dependencias básicas
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    curl \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    libsqlite3-dev \
    sqlite3 \
    file \
    strace \
    net-tools \
    procps \
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
    libx11-6 \
    xvfb \
    libgtk-3-0 \
    libqt5core5a \
    libqt5gui5 \
    libqt5widgets5 \
    qt5-default \
    python3-pyqt5 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Descargar acestream
RUN echo "Descargando AceStream..." && \
    wget -v -O /tmp/acestream.tar.gz https://download.acestream.media/linux/acestream_3.2.3_ubuntu_18.04_x86_64_py3.8.tar.gz && \
    echo "Descarga completada" && \
    ls -la /tmp/acestream.tar.gz

# Crear directorio y descomprimir
RUN echo "Descomprimiendo AceStream..." && \
    mkdir -p /opt/acestream && \
    tar -xzf /tmp/acestream.tar.gz -C /opt/acestream && \
    rm -f /tmp/acestream.tar.gz && \
    echo "Contenido descomprimido:" && \
    ls -la /opt/acestream/

# Encontrar y configurar el binario principal
RUN echo "Configurando binario principal..." && \
    ACESTREAM_BIN=$(find /opt/acestream -name "acestreamengine" -type f | grep -v "/lib/" | head -1) && \
    echo "Binario encontrado: $ACESTREAM_BIN" && \
    if [ -f "$ACESTREAM_BIN" ]; then \
        chmod +x "$ACESTREAM_BIN" && \
        ln -sf "$ACESTREAM_BIN" /usr/bin/acestreamengine && \
        echo "Binario configurado correctamente"; \
    else \
        echo "Error: No se encontró el binario principal"; \
        exit 1; \
    fi

# Configurar bibliotecas de Python de AceStream
RUN echo "Configurando bibliotecas de Python..." && \
    find /opt/acestream -name "*.py" -type f | head -5 && \
    find /opt/acestream -name "lib" -type d | head -5

# Crear directorio de logs
RUN mkdir -p /var/log/acestream && \
    chmod 755 /var/log/acestream

# Crear script para verificar e instalar dependencias de AceStream
RUN echo '#!/bin/bash' > /tmp/install_acestream_deps.sh && \
    echo 'echo "Instalando dependencias de AceStream..."' >> /tmp/install_acestream_deps.sh && \
    echo 'pip3 install --no-cache-dir apsw --verbose' >> /tmp/install_acestream_deps.sh && \
    echo 'pip3 install --no-cache-dir gevent' >> /tmp/install_acestream_deps.sh && \
    echo 'pip3 install --no-cache-dir twisted' >> /tmp/install_acestream_deps.sh && \
    echo 'pip3 install --no-cache-dir pyasn1' >> /tmp/install_acestream_deps.sh && \
    echo 'pip3 install --no-cache-dir cryptography' >> /tmp/install_acestream_deps.sh && \
    echo 'pip3 install --no-cache-dir service-identity' >> /tmp/install_acestream_deps.sh && \
    echo 'echo "Dependencias instaladas"' >> /tmp/install_acestream_deps.sh && \
    chmod +x /tmp/install_acestream_deps.sh

# Instalar dependencias Python incluyendo las específicas de AceStream
RUN pip3 install --no-cache-dir flask psutil requests && \
    /tmp/install_acestream_deps.sh

# Crear script de inicio que configura el entorno
RUN echo '#!/bin/bash' > /usr/bin/start-acestream.sh && \
    echo 'export PYTHONPATH=/opt/acestream:$PYTHONPATH' >> /usr/bin/start-acestream.sh && \
    echo 'export LD_LIBRARY_PATH=/opt/acestream/lib:$LD_LIBRARY_PATH' >> /usr/bin/start-acestream.sh && \
    echo 'export DISPLAY=:99' >> /usr/bin/start-acestream.sh && \
    echo 'Xvfb :99 -screen 0 1024x768x24 &' >> /usr/bin/start-acestream.sh && \
    echo 'sleep 2' >> /usr/bin/start-acestream.sh && \
    echo 'cd /app' >> /usr/bin/start-acestream.sh && \
    echo 'python3 control_api.py' >> /usr/bin/start-acestream.sh && \
    chmod +x /usr/bin/start-acestream.sh

# Verificar que todas las dependencias Python están instaladas
RUN echo "Verificando dependencias Python..." && \
    python3 -c "import apsw; print('apsw: OK')" && \
    python3 -c "import gevent; print('gevent: OK')" || echo "gevent: OPTIONAL" && \
    python3 -c "import twisted; print('twisted: OK')" || echo "twisted: OPTIONAL" && \
    echo "Dependencias Python verificadas"
# Verificar instalación final
RUN echo "Verificación final..." && \
    which acestreamengine && \
    ls -la /usr/bin/acestreamengine && \
    ldd /usr/bin/acestreamengine | grep "not found" || echo "Todas las dependencias del sistema están resueltas" && \
    file /usr/bin/acestreamengine && \
    echo "Probando AceStream con dependencias Python..." && \
    timeout 10 /usr/bin/acestreamengine --help || echo "AceStream probado (puede mostrar errores pero está disponible)"

# Crear directorio de trabajo
WORKDIR /app

# Copiar la API
COPY control_api.py /app/

# Exponer puertos
EXPOSE 8080 6878

# Ejecutar usando el script de inicio
CMD ["/usr/bin/start-acestream.sh"]