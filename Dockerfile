# 1. Imagen base de Python
FROM python:3.10-slim

# 2. Instalar dependencias del sistema (LaTeX y utilidades)
RUN apt-get update && apt-get install -y \
    texlive-full \
    && rm -rf /var/lib/apt/lists/*

# 3. Directorio de trabajo
WORKDIR /app

# 4. Copiar e instalar librerías de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar el código del proyecto
COPY . .

# 6. Exponer el puerto de FastAPI
EXPOSE 8000

# 7. Comando para iniciar la API
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["python", "-m", "uvicorn", "main:api", "--host", "0.0.0.0", "--port", "8000"]
