# Enterprise RAG Assistant

A fully local, private AI assistant for small enterprises.
Indexes your internal PDF documents and answers questions using
**Ollama · LangChain · LangGraph · ChromaDB · Docker**.

---

## Architecture

```
┌─────────────────────────────────────────────┐
│              Tkinter Desktop UI              │
│  ┌──────────┐ ┌───────────┐ ┌────────────┐  │
│  │   Chat   │ │ Documents │ │  Settings  │  │
│  └──────────┘ └───────────┘ └────────────┘  │
└────────────────────┬────────────────────────┘
                     │
          ┌──────────▼──────────┐
          │   LangGraph Pipeline │
          │  classify → chat     │
          │         ↘ retrieve   │
          │           → grade    │
          │           → generate │
          └──────────┬──────────┘
          ┌──────────▼──────────┐
          │  ChromaDB (local)   │  ← PDF chunks + embeddings
          └──────────┬──────────┘
          ┌──────────▼──────────┐
          │  Ollama (local LLM) │  ← mistral / llama / phi / etc.
          └─────────────────────┘
```

---

## Quick Start (Docker — recommended)

### 1. Prerequisites
- Docker Desktop (or Docker Engine + Compose)
- Linux: X11 running. macOS: XQuartz. Windows: VcXsrv or X410.

### 2. Pull models
```bash
docker compose run --rm ollama ollama pull mistral
docker compose run --rm ollama ollama pull nomic-embed-text
```

### 3. Add your PDFs
Drop PDF files into the `documents/` folder.

### 4. Start
```bash
# Linux
export DISPLAY=:0 && xhost +local:docker
docker compose up --build

# macOS (after opening XQuartz)
export DISPLAY=host.docker.internal:0
docker compose up --build

# Windows (after starting VcXsrv with "Disable access control")
set DISPLAY=host.docker.internal:0
docker compose up --build
```

---

## Quick Start (Local Python — no Docker)

### 1. Install Ollama
Download from https://ollama.com and run:
```bash
ollama pull mistral
ollama pull nomic-embed-text
ollama serve
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run
```bash
python app/main.py
```

---

## Project Structure

```
enterprise_rag/
├── app/
│   ├── main.py            # Entry point
│   ├── app.py             # Root window + navigation
│   ├── config.py          # All settings (paths, thresholds, theme)
│   ├── rag_engine.py      # LangGraph RAG pipeline
│   ├── history.py         # Chat history persistence
│   ├── widgets.py         # Reusable UI widgets
│   ├── panel_chat.py      # Chat interface
│   ├── panel_docs.py      # Document library manager
│   └── panel_settings.py  # Model + RAG settings
├── documents/             # ← Drop your PDFs here
├── vector_db/             # ChromaDB auto-created here
├── chat_history.json      # Persisted conversation log
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Features

| Feature | Details |
|---|---|
| Local & private | Everything runs on your machine — no data leaves |
| Multi-PDF indexing | Drop PDFs in `/documents`, they auto-index |
| Incremental upload | Upload individual files from the Documents panel |
| Smart intent routing | Casual chat goes direct to LLM; doc questions go through RAG |
| LangGraph pipeline | classify → retrieve → grade → generate |
| MMR retrieval | Diverse, non-duplicate context chunks |
| Relevance filtering | Configurable score threshold in Settings |
| Chat history | Persisted across sessions as JSON |
| Text highlighting | Select & highlight any part of any response |
| Delete documents | Remove a PDF and auto re-index |
| Settings panel | Live model switcher, temperature & threshold sliders |
| Docker ready | Full docker-compose setup with Ollama sidecar |

---

## Configuration

Edit `app/config.py` to change defaults, or set environment variables:

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API endpoint |
| `EMBED_MODEL` | `nomic-embed-text` | Embedding model |
| `CHAT_MODEL` | `mistral:latest` | Default chat model |

---

## GPU Support (Docker)

Uncomment the `deploy` section in `docker-compose.yml` for NVIDIA GPU support.
Requires the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/).
