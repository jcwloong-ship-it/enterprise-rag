"""
app.py — root window, sidebar navigation, panel switching.
"""
import threading
import tkinter as tk
import customtkinter as ctk
import requests

from config import (
    THEME, WINDOW_TITLE, WINDOW_SIZE, SIDEBAR_WIDTH,
    OLLAMA_BASE_URL, DEFAULT_CHAT_MODEL, CHAT_MODELS,
)
from widgets import StatusDot, SidebarButton
from rag_engine import RAGEngine
from panel_chat import ChatPanel
from panel_docs import DocsPanel
from panel_settings import SettingsPanel

ctk.set_appearance_mode("dark")


def _get_chat_models():
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        if r.status_code == 200:
            all_m = [m["name"] for m in r.json().get("models", [])]
            chat  = [m for m in all_m
                     if not any(x in m.lower()
                                for x in ("nomic", "embed"))]
            return chat or all_m
    except Exception:
        pass
    return [DEFAULT_CHAT_MODEL]


class EnterpriseApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(WINDOW_TITLE)
        self.geometry(WINDOW_SIZE)
        self.configure(fg_color=THEME["bg"])
        self.minsize(900, 600)

        self._engine    = RAGEngine()
        self._model_var = tk.StringVar(value=DEFAULT_CHAT_MODEL)
        self._panels    = {}
        self._nav_btns  = {}
        self._active    = None

        self._build_titlebar()
        self._build_body()
        self._show_panel("chat")

        # Boot indexing in background
        threading.Thread(
            target=self._engine.index,
            kwargs={"progress_cb": self._status_cb},
            daemon=True,
        ).start()

    # ── Title bar ─────────────────────────────────────────────────────────────

    def _build_titlebar(self):
        bar = tk.Frame(self, bg=THEME["surface"], height=52)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        # Logo
        tk.Label(bar, text="◈  ENTERPRISE AI",
                 font=("Consolas", 13, "bold"),
                 fg=THEME["accent"],
                 bg=THEME["surface"]).pack(side="left", padx=20)

        # Status dot
        self._status_dot = StatusDot(bar, THEME)
        self._status_dot.pack(side="left", padx=16)

        # Model picker
        right = tk.Frame(bar, bg=THEME["surface"])
        right.pack(side="right", padx=16)

        all_chat = _get_chat_models()
        if self._model_var.get() not in all_chat and all_chat:
            self._model_var.set(all_chat[0])

        tk.Label(right, text="MODEL",
                 font=("Consolas", 8),
                 fg=THEME["text_muted"],
                 bg=THEME["surface"]).pack(side="left", padx=(0, 6))

        om = tk.OptionMenu(right, self._model_var, *all_chat)
        om.config(font=("Consolas", 10),
                  fg=THEME["text"], bg=THEME["surface2"],
                  activeforeground=THEME["text"],
                  activebackground=THEME["accent_dim"],
                  relief="flat", bd=0,
                  highlightthickness=0, cursor="hand2",
                  indicatoron=False, width=22)
        om["menu"].config(font=("Consolas", 10),
                          fg=THEME["text"], bg=THEME["surface2"],
                          activeforeground=THEME["text"],
                          activebackground=THEME["accent_dim"],
                          relief="flat")
        om.pack(side="left")

    # ── Body: sidebar + content ───────────────────────────────────────────────

    def _build_body(self):
        body = tk.Frame(self, bg=THEME["bg"])
        body.pack(fill="both", expand=True)

        # Sidebar
        sidebar = tk.Frame(body, bg=THEME["sidebar_bg"],
                           width=SIDEBAR_WIDTH)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Frame(sidebar, bg=THEME["border"],
                 height=1).pack(fill="x")

        nav_items = [
            ("💬  Chat",       "chat"),
            ("📁  Documents",  "docs"),
            ("⚙️   Settings",  "settings"),
        ]
        for label, key in nav_items:
            btn = SidebarButton(
                sidebar, text=label, theme=THEME,
                command=lambda k=key: self._show_panel(k))
            btn.pack(fill="x")
            self._nav_btns[key] = btn

        # Version footer
        tk.Label(sidebar, text="v2.0  ·  LangGraph RAG",
                 font=("Consolas", 8),
                 fg=THEME["text_dim"],
                 bg=THEME["sidebar_bg"]).pack(
            side="bottom", pady=12)

        # Content area
        self._content = tk.Frame(body, bg=THEME["bg"])
        self._content.pack(side="left", fill="both", expand=True)

        # Instantiate all panels (hidden until shown)
        self._panels["chat"]     = ChatPanel(
            self._content, self._engine,
            self._model_var, self._status_cb)
        self._panels["docs"]     = DocsPanel(
            self._content, self._engine, self._status_cb)
        self._panels["settings"] = SettingsPanel(
            self._content, self._engine,
            self._model_var, self._status_cb)

    # ── Navigation ────────────────────────────────────────────────────────────

    def _show_panel(self, key: str):
        if self._active == key:
            return
        if self._active and self._active in self._panels:
            self._panels[self._active].pack_forget()
            self._nav_btns[self._active].set_active(False)

        self._panels[key].pack(fill="both", expand=True)
        self._nav_btns[key].set_active(True)
        self._active = key

        # Refresh docs list when switching to that panel
        if key == "docs":
            self._panels["docs"].refresh()

    # ── Status callback ───────────────────────────────────────────────────────

    def _status_cb(self, msg: str):
        color = THEME["success"] if "active" in msg or "Ready" in msg \
                else THEME["warning"]
        self.after(0, lambda: self._status_dot.set(msg, color))
