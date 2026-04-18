"""
config.py — all tunable settings in one place.
Edit this file to change paths, thresholds, and model defaults.
"""
import os

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH   = os.path.join(BASE_DIR, "documents")        # PDF source folder
DB_PATH     = os.path.join(BASE_DIR, "vector_db")        # Chroma persist dir
HISTORY_PATH = os.path.join(BASE_DIR, "chat_history.json")

# ── Ollama ───────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL   = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBED_MODEL       = os.getenv("EMBED_MODEL",     "nomic-embed-text")
DEFAULT_CHAT_MODEL = os.getenv("CHAT_MODEL",     "mistral:latest")

# ── RAG tuning ───────────────────────────────────────────────────────────────
CHUNK_SIZE       = 600
CHUNK_OVERLAP    = 120
SCORE_THRESHOLD  = 0.35
RETRIEVER_K      = 8
RETRIEVER_FETCH_K = 20
RETRIEVER_LAMBDA = 0.6          # MMR diversity (0 = max diversity, 1 = max relevance)

# ── UI ───────────────────────────────────────────────────────────────────────
WINDOW_TITLE  = "Enterprise AI  ·  RAG Assistant"
WINDOW_SIZE   = "1280x820"
SIDEBAR_WIDTH = 260

CHAT_MODELS = {"llama", "mistral", "phi", "gemma", "qwen", "deepseek", "openhermes"}

# ── Theme ────────────────────────────────────────────────────────────────────
THEME = {
    "bg":           "#0d0f18",
    "surface":      "#13162b",
    "surface2":     "#1c2040",
    "surface3":     "#242850",
    "border":       "#2a2f5a",
    "accent":       "#5b6af0",
    "accent_hover": "#7c89ff",
    "accent_dim":   "#1e2260",
    "success":      "#22c55e",
    "warning":      "#f59e0b",
    "danger":       "#ef4444",
    "text":         "#e8eaf6",
    "text_muted":   "#6b7280",
    "text_dim":     "#3d4267",
    "user_bubble":  "#1a2244",
    "ai_bubble":    "#13162b",
    "sys_bubble":   "#1f1500",
    "highlight":    "#fef08a",
    "highlight_fg": "#1a1400",
    "selection":    "#3b4fd6",
    "sidebar_bg":   "#0a0c18",
    "tag_bg":       "#1e2260",
    "tag_fg":       "#a5b4fc",
}
