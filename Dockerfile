# Dockerfile completamente nuevo
FROM vstavrinov/acestream-engine

# Instalar dependencias adicionales
RUN apt-get update && apt-get install -y python3-pip
RUN pip install flask psutil requests

# Copiar nuestra API
COPY control_api.py /app/
WORKDIR /app

# Exponer puertos
EXPOSE 8080 6878

# Ejecutar solo nuestra API (que controlará acestream internamente)
CMD ["python", "control_api.py"]