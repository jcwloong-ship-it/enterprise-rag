# Enterprise RAG Assistant

> A fully local, private AI assistant for enterprise document Q&A

---

## What Is Enterprise RAG Assistant?

Enterprise RAG Assistant is a fully local, privacy-first AI document assistant built for small and medium enterprises. It allows teams to upload internal PDF documents and ask natural-language questions — receiving accurate, cited answers grounded in their own content, with no data ever sent to the cloud.

Unlike SaaS AI tools, everything runs on your own hardware: the language model, the embedding model, and the vector database all operate inside Docker containers on your machine. There are no API keys, no subscriptions, and no risk of confidential documents leaving your network.

---

## Key Highlights

- Fully offline — no internet required after initial model download
- Supports any Ollama-compatible model: Mistral, LLaMA, Phi, Gemma, Qwen, and more
- Smart intent routing automatically decides when to search documents vs. chat freely
- Real-time embedding progress percentage so you know exactly how far indexing has gone
- Persistent chat history saved across sessions
- One-command startup via Docker Compose

---

## Architecture & Technology Stack

The system is composed of two Docker containers that communicate over an internal network:

| Layer | Technology | Role |
|---|---|---|
| LLM Server | Ollama | Runs local models (Mistral, LLaMA, Phi…) |
| Embeddings | nomic-embed-text | Converts text chunks to vectors |
| Vector Store | ChromaDB | Stores & retrieves embedded chunks |
| RAG Pipeline | LangChain + LangGraph | Orchestrates classify → retrieve → generate |
| UI | Tkinter / customtkinter | Desktop GUI panels (Chat, Docs, Settings) |
| Container | Docker Compose | Runs Ollama + app as isolated services |

The RAG pipeline follows a LangGraph state machine with four nodes:

- **classify** — determines if the query needs document retrieval or direct LLM chat
- **retrieve** — performs similarity search against the ChromaDB vector store
- **grade** — deduplicates and re-ranks retrieved chunks by relevance
- **generate** — constructs a cited, conversational answer using the top chunks

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

## Features

| Feature | Details |
|---|---|
| 100% Local & Private | No data ever leaves your machine |
| Multi-PDF Indexing | Drop PDFs in `/documents` — auto-indexed on startup |
| Incremental Upload | Upload files directly from the Documents panel |
| Smart Intent Routing | General chat goes direct to LLM; doc questions use RAG |
| LangGraph Pipeline | classify → retrieve → grade → generate |
| Embedding Progress | Real-time % progress bar while indexing chunks |
| Relevance Filtering | Configurable similarity score threshold |
| Chat History | Persisted across sessions as JSON |
| Delete Documents | Remove a PDF and auto re-index |
| Settings Panel | Live model switcher, temperature & threshold sliders |
| Docker Ready | Full docker-compose setup with Ollama sidecar |

---

## Quick Start (Docker — Recommended)

### Prerequisites

- Docker Desktop (Windows / macOS) or Docker Engine + Compose (Linux)
- **Windows:** VcXsrv installed and running with "Disable access control" checked
- **macOS:** XQuartz installed
- At least 8 GB RAM recommended (6 GB minimum — CPU-only will be slow)

### 1. Pull the required models

```bash
docker compose run --rm ollama ollama pull mistral
docker compose run --rm ollama ollama pull nomic-embed-text
```

> Wait for both downloads to complete before proceeding.

### 2. Start the display server (Windows only)

Launch **XLaunch** → Multiple windows → Display `0` → check **"Disable access control"** → Finish.

### 3. Start everything

```bash
docker compose up
```

The GUI window will appear on your desktop. On first run, allow 1–2 minutes for Ollama to pass its health check.

### Uploading Documents

Open the **Documents** panel, click **"+ Upload PDF"**, and select one or more files. The app will split, embed, and index each file automatically. A progress percentage is shown in the status bar during embedding.

### Re-indexing

Click **"⟳ Re-index all"** in the Documents panel to force a full rebuild of the vector database. This is useful after manually adding files to the `documents/` folder.

---

## Quick Start (Local Python — No Docker)

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

## Configuration

All settings live in `app/config.py` or can be overridden via environment variables in `docker-compose.yml`:

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API endpoint |
| `EMBED_MODEL` | `nomic-embed-text` | Embedding model name |
| `CHAT_MODEL` | `mistral:latest` | Default chat/inference model |

Additional tuning parameters in `config.py`:

| Parameter | Default | Description |
|---|---|---|
| `CHUNK_SIZE` | `600` | Characters per text chunk |
| `CHUNK_OVERLAP` | `120` | Overlap between chunks |
| `SCORE_THRESHOLD` | `0.35` | Minimum similarity score to include a chunk |
| `RETRIEVER_K` | `8` | Number of chunks to pass to the LLM |

---

## Project Structure

```
enterprise_rag/
├── app/
│   ├── main.py            # Entry point
│   ├── app.py             # Root window + navigation
│   ├── config.py          # All settings (paths, thresholds, theme)
│   ├── rag_engine.py      # LangGraph RAG pipeline + embedding
│   ├── history.py         # Chat history persistence
│   ├── widgets.py         # Reusable UI widgets
│   ├── panel_chat.py      # Chat interface
│   ├── panel_docs.py      # Document library manager
│   └── panel_settings.py  # Model + RAG settings
├── documents/             # ← Drop your PDFs here
├── vector_db/             # ChromaDB index (auto-created)
├── chat_history.json      # Persisted conversation log
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## GPU Support

CPU-only mode is supported but slow — embedding 1800+ chunks can take 20–30 minutes. For significantly faster performance, enable NVIDIA GPU support by uncommenting the `deploy` section in `docker-compose.yml`:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

Requires the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/) to be installed on the host machine.

---

## Common Issues & Fixes

### Container enterprise-ollama is unhealthy

Ollama takes time to start. The healthcheck uses `ollama list` with a 60-second `start_period`. If it still fails, ensure models have been pulled first.

### TclError: couldn't connect to display

VcXsrv (Windows) or XQuartz (macOS) is not running, or was launched without "Disable access control". Restart the display server then run:

```bash
docker restart enterprise-rag
```

### readonly database / ChromaDB error

The `vector_db` folder has incorrect permissions. Delete the folder, recreate it, and restart. The `docker-compose.yml` includes `user: root` on the `rag-app` service to prevent this.

### nomic-embed-text not found

The embedding model was not pulled before starting. Run:

```bash
docker exec enterprise-ollama ollama pull nomic-embed-text
```

### Embedding stuck at 0%

CPU embedding is slow — each batch of 10 chunks takes time. Check `docker logs enterprise-rag -f` to confirm it is progressing. With 1800+ chunks expect 20–30 minutes on CPU.

---

> Enterprise RAG Assistant is open-source and runs entirely on-premise. No telemetry. No cloud. Your documents stay yours.
