FROM vstavrinov/acestream-engine

# Instalar Python y dependencias
RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install flask psutil requests

# Copiar API
COPY control_api.py /app/
WORKDIR /app

# Exponer puertos
EXPOSE 8080 6878

# Ejecutar API
CMD ["python3", "control_api.py"]