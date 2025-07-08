# Usar imagen base Ubuntu 22.04
FROM ubuntu:22.04

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
    libavahi-compat-libdnssd1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Instalar acestream-engine desde tar.gz
RUN wget -q -O /tmp/acestream.tar.gz http://dl.acestream.org/linux/acestream_3.1.75_ubuntu_18.04_x86_64.tar.gz && \
    mkdir -p /opt/acestream && \
    tar -xzf /tmp/acestream.tar.gz -C /opt/acestream && \
    rm -f /tmp/acestream.tar.gz && \
    ln -s /opt/acestream/acestreamengine /usr/bin/acestreamengine

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