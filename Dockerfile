FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 \
    --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir -r requirements.txt && \
    pip cache purge

COPY backend/app ./app

COPY models ./models

RUN mkdir -p /app/data/uploads /app/models/detectors /app/models/classifiers

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 5434

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5434"]