FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    gcc \
    pkg-config \
    libportaudio2 \
    portaudio19-dev \
    libasound2-dev \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1 \
    DB_HOST=db \
    DB_PORT=3306 \
    DB_USER=root \
    DB_PASSWORD=trinhquocviet2005 \
    GROQ_API_KEY=changeme \
    OPENAI_API_KEY=

EXPOSE 7860

CMD ["python", "gradio_starter.py"]