# ── Enterprise RAG Assistant — Dockerfile ────────────────────────────────────
# Builds a Python image that runs the Tkinter desktop app.
# Ollama runs as a SEPARATE container (see docker-compose.yml).
#
# Usage (via docker-compose):
#   docker compose up --build
#
# Display forwarding required on the host:
#   Linux  → DISPLAY env var + xhost +local:docker
#   macOS  → XQuartz + DISPLAY=host.docker.internal:0
#   Windows → VcXsrv or X410

FROM python:3.11-slim

# System deps for Tkinter + Tcl/Tk
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3-tk \
        tk-dev \
        tcl-dev \
        libx11-6 \
        libxext6 \
        libxrender1 \
        libxtst6 \
        libxi6 \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app/ ./

# Documents folder is mounted as a volume (see docker-compose.yml)
RUN mkdir -p /app/documents /app/vector_db

ENV PYTHONUNBUFFERED=1
ENV OLLAMA_BASE_URL=http://ollama:11434

CMD ["python", "main.py"]
