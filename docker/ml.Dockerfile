# docker/ml.Dockerfile
FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    python-multipart \
    python-dotenv \
    pydantic \
    pydantic-settings \
    minio \
    boto3 \
    cryptography \
    numpy \
    scikit-learn \
    matplotlib \
    seaborn \
    tqdm \
    Pillow \
    pandas \
    torchvision \
    opencv-python

# Копирование кода приложения
COPY app/ ./app/
COPY scripts/ ./scripts/

# Создание директорий
RUN mkdir -p /models /data /uploads

ENV PYTHONPATH=/app

ENTRYPOINT ["python"]