"""
panel_settings.py — model selector, RAG tuning, and system info.
"""
import requests
import tkinter as tk

from config import THEME, OLLAMA_BASE_URL, CHAT_MODELS, SCORE_THRESHOLD


def _get_models():
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        if r.status_code == 200:
            return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass
    return ["mistral:latest", "llama3.2"]


def _is_chat(name: str) -> bool:
    n = name.lower()
    if "nomic" in n or "embed" in n:
        return False
    return any(k in n for k in CHAT_MODELS)


class SettingsPanel(tk.Frame):
    def __init__(self, parent, engine, model_var, status_cb, **kwargs):
        super().__init__(parent, bg=THEME["bg"], **kwargs)
        self._engine    = engine
        self._model_var = model_var
        self._status_cb = status_cb
        self._build()

    def _build(self):
        pad = dict(padx=30, pady=10)

        tk.Label(self, text="Settings",
                 font=("Consolas", 15, "bold"),
                 fg=THEME["text"], bg=THEME["bg"]).pack(
            anchor="w", padx=30, pady=(24, 4))

        tk.Frame(self, bg=THEME["border"], height=1).pack(
            fill="x", padx=30, pady=(0, 16))

        # ── Model ─────────────────────────────────────────────────────────────
        self._section("Chat Model")
        all_models   = _get_models()
        chat_models  = [m for m in all_models if _is_chat(m)] or all_models
        embed_models = [m for m in all_models if not _is_chat(m)]

        if self._model_var.get() not in chat_models and chat_models:
            self._model_var.set(chat_models[0])

        model_row = tk.Frame(self, bg=THEME["bg"])
        model_row.pack(fill="x", **pad)

        om = tk.OptionMenu(model_row, self._model_var, *chat_models)
        om.config(font=("Consolas", 11),
                  fg=THEME["text"], bg=THEME["surface2"],
                  activeforeground=THEME["text"],
                  activebackground=THEME["accent_dim"],
                  relief="flat", bd=0,
                  highlightthickness=0, cursor="hand2",
                  indicatoron=False, width=30)
        om["menu"].config(font=("Consolas", 11),
                          fg=THEME["text"], bg=THEME["surface2"],
                          activeforeground=THEME["text"],
                          activebackground=THEME["accent_dim"],
                          relief="flat")
        om.pack(side="left")

        refresh_btn = tk.Label(model_row, text="⟳ Refresh",
                               font=("Consolas", 10),
                               fg=THEME["accent"], bg=THEME["bg"],
                               cursor="hand2")
        refresh_btn.pack(side="left", padx=16)
        refresh_btn.bind("<Button-1>", lambda e: self._refresh_models())

        # ── RAG threshold ─────────────────────────────────────────────────────
        self._section("Relevance Threshold  (lower = more results)")
        self._threshold_var = tk.DoubleVar(value=SCORE_THRESHOLD)
        thr_row = tk.Frame(self, bg=THEME["bg"])
        thr_row.pack(fill="x", **pad)
        self._thr_lbl = tk.Label(thr_row,
                                  text=f"{SCORE_THRESHOLD:.2f}",
                                  font=("Consolas", 11),
                                  fg=THEME["accent"], bg=THEME["bg"],
                                  width=5)
        self._thr_lbl.pack(side="right")
        tk.Scale(
            thr_row,
            variable=self._threshold_var,
            from_=0.0, to=1.0, resolution=0.01,
            orient="horizontal",
            bg=THEME["bg"], fg=THEME["text"],
            troughcolor=THEME["surface2"],
            highlightthickness=0,
            showvalue=False,
            command=lambda v: (
                self._thr_lbl.config(text=f"{float(v):.2f}"),
                self._apply_threshold(float(v))
            ),
        ).pack(side="left", fill="x", expand=True)

        # ── Temperature ───────────────────────────────────────────────────────
        self._section("Response Temperature  (higher = more creative)")
        self._temp_var = tk.DoubleVar(value=0.7)
        temp_row = tk.Frame(self, bg=THEME["bg"])
        temp_row.pack(fill="x", **pad)
        self._temp_lbl = tk.Label(temp_row, text="0.70",
                                   font=("Consolas", 11),
                                   fg=THEME["accent"], bg=THEME["bg"],
                                   width=5)
        self._temp_lbl.pack(side="right")
        tk.Scale(
            temp_row,
            variable=self._temp_var,
            from_=0.0, to=1.0, resolution=0.05,
            orient="horizontal",
            bg=THEME["bg"], fg=THEME["text"],
            troughcolor=THEME["surface2"],
            highlightthickness=0,
            showvalue=False,
            command=lambda v: self._temp_lbl.config(text=f"{float(v):.2f}"),
        ).pack(side="left", fill="x", expand=True)

        # ── Ollama status ─────────────────────────────────────────────────────
        self._section("Ollama Connection")
        info_row = tk.Frame(self, bg=THEME["bg"])
        info_row.pack(fill="x", **pad)
        self._ollama_lbl = tk.Label(info_row, text="Checking…",
                                     font=("Consolas", 11),
                                     fg=THEME["warning"], bg=THEME["bg"])
        self._ollama_lbl.pack(side="left")
        tk.Label(info_row, text=OLLAMA_BASE_URL,
                 font=("Consolas", 10),
                 fg=THEME["text_muted"], bg=THEME["bg"]).pack(
            side="left", padx=16)
        self.after(200, self._check_ollama)

        # ── Embed models list ─────────────────────────────────────────────────
        if embed_models:
            self._section("Embedding Models Detected")
            tk.Label(self, text="  " + "  ·  ".join(embed_models),
                     font=("Consolas", 10),
                     fg=THEME["text_muted"], bg=THEME["bg"]).pack(
                anchor="w", padx=30)

    def _section(self, title: str):
        tk.Label(self, text=title,
                 font=("Consolas", 10, "bold"),
                 fg=THEME["text_muted"], bg=THEME["bg"]).pack(
            anchor="w", padx=30, pady=(18, 2))

    def _apply_threshold(self, val: float):
        import config
        config.SCORE_THRESHOLD = val

    def _refresh_models(self):
        # Rebuild widget — simplest approach
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _check_ollama(self):
        try:
            r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
            if r.status_code == 200:
                n = len(r.json().get("models", []))
                self._ollama_lbl.config(
                    text=f"● Connected  ({n} model(s) available)",
                    fg=THEME["success"])
                return
        except Exception:
            pass
        self._ollama_lbl.config(
            text="✕ Ollama not reachable — is it running?",
            fg=THEME["danger"])

    @property
    def temperature(self) -> float:
        return self._temp_var.get()
