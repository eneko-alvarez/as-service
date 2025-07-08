# Usar imagen base Ubuntu 20.04 para compatibilidad con libpython3.8 y libssl1.1
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
    libavahi-compat-libdnssd1 || { echo "Error instalando dependencias"; exit 1; } && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Instalar acestream-engine manualmente
RUN wget -q -O /tmp/acestream.deb https://download.acestream.media/linux/acestream_3.2.3_ubuntu_18.04_x86_64_py3.8.tar.gz || { echo "Error descargando paquete .deb"; exit 1; } && \
    dpkg -i /tmp/acestream.deb || apt-get install -f -y && \
    rm -f /tmp/acestream.deb

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