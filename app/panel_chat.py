"""
panel_chat.py — the main chat interface panel.
"""
import threading
import tkinter as tk
from tkinter import filedialog

import history as hist
from widgets import MessageBubble
from config import THEME


class ChatPanel(tk.Frame):
    def __init__(self, parent, engine, model_var, status_cb, **kwargs):
        super().__init__(parent, bg=THEME["bg"], **kwargs)
        self._engine    = engine
        self._model_var = model_var
        self._status_cb = status_cb
        self._bubbles   = []

        self._build()
        self._restore_history()

    def _build(self):
        # ── Chat scroll area ──────────────────────────────────────────────────
        canvas_frame = tk.Frame(self, bg=THEME["bg"])
        canvas_frame.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(canvas_frame, bg=THEME["bg"],
                                 bd=0, highlightthickness=0)
        sb = tk.Scrollbar(canvas_frame, orient="vertical",
                          command=self._canvas.yview,
                          bg=THEME["surface"], troughcolor=THEME["bg"],
                          width=8, bd=0)
        self._canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._msg_frame = tk.Frame(self._canvas, bg=THEME["bg"])
        self._win = self._canvas.create_window(
            (0, 0), window=self._msg_frame, anchor="nw")

        self._msg_frame.bind("<Configure>",
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
            lambda e: self._canvas.itemconfig(self._win, width=e.width))
        self._canvas.bind_all("<MouseWheel>",
            lambda e: self._canvas.yview_scroll(-1*(e.delta//120), "units"))

        # Welcome notice
        self._notice("Welcome! Ask me anything — or switch to the Documents tab to manage your PDFs.")

        # ── Input bar ─────────────────────────────────────────────────────────
        bar = tk.Frame(self, bg=THEME["surface"], height=76)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        inner = tk.Frame(bar, bg=THEME["surface2"],
                         highlightthickness=1,
                         highlightbackground=THEME["border"])
        inner.pack(fill="x", padx=20, pady=14)

        self._entry_var = tk.StringVar()
        self._entry = tk.Entry(
            inner,
            textvariable=self._entry_var,
            font=("Georgia", 14),
            fg=THEME["text_muted"],
            bg=THEME["surface2"],
            insertbackground=THEME["accent"],
            relief="flat", bd=0,
        )
        self._entry.insert(0, "Ask anything about your documents…")
        self._entry.pack(side="left", fill="x", expand=True, padx=16, pady=10)
        self._entry.bind("<Return>",   lambda e: self._submit())
        self._entry.bind("<FocusIn>",  self._clear_placeholder)
        self._entry.bind("<FocusOut>", self._restore_placeholder)

        # char counter
        char_lbl = tk.Label(inner, text="0", font=("Consolas", 9),
                            fg=THEME["text_muted"], bg=THEME["surface2"])
        char_lbl.pack(side="right", padx=(0, 6))
        self._entry_var.trace_add(
            "write",
            lambda *_: char_lbl.config(text=str(len(self._entry_var.get()))))

        send = tk.Label(inner, text="  Send  ",
                        font=("Consolas", 11, "bold"),
                        fg="#fff", bg=THEME["accent"],
                        cursor="hand2", padx=6, pady=5)
        send.pack(side="right", padx=(0, 6))
        send.bind("<Button-1>", lambda e: self._submit())
        send.bind("<Enter>", lambda e: send.config(bg=THEME["accent_hover"]))
        send.bind("<Leave>", lambda e: send.config(bg=THEME["accent"]))

        # Clear chat button
        clr = tk.Label(inner, text="⟳ Clear",
                       font=("Consolas", 9),
                       fg=THEME["text_muted"], bg=THEME["surface2"],
                       cursor="hand2")
        clr.pack(side="right", padx=(0, 10))
        clr.bind("<Button-1>", lambda e: self._clear_chat())
        clr.bind("<Enter>", lambda e: clr.config(fg=THEME["danger"]))
        clr.bind("<Leave>", lambda e: clr.config(fg=THEME["text_muted"]))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _notice(self, text: str):
        tk.Label(self._msg_frame, text=text,
                 font=("Consolas", 9), fg=THEME["text_muted"],
                 bg=THEME["bg"], pady=8).pack(fill="x", padx=24)
        self.after(100, self._scroll_bottom)

    def add_message(self, role: str, text: str) -> MessageBubble:
        bubble = MessageBubble(self._msg_frame, role, text, THEME)
        bubble.pack(fill="x", pady=4)
        self._bubbles.append(bubble)
        self.after(120, self._scroll_bottom)
        return bubble

    def _scroll_bottom(self):
        self._canvas.update_idletasks()
        self._canvas.yview_moveto(1.0)

    def _clear_placeholder(self, _e=None):
        if self._entry.get() == "Ask anything about your documents…":
            self._entry.delete(0, "end")
            self._entry.config(fg=THEME["text"])

    def _restore_placeholder(self, _e=None):
        if not self._entry.get():
            self._entry.insert(0, "Ask anything about your documents…")
            self._entry.config(fg=THEME["text_muted"])

    def _clear_chat(self):
        for w in self._msg_frame.winfo_children():
            w.destroy()
        self._bubbles.clear()
        hist.clear()
        self._notice("Chat cleared.")

    def _restore_history(self):
        for rec in hist.load_all():
            self.add_message(rec["role"], rec["text"])

    # ── Submit ────────────────────────────────────────────────────────────────

    def _submit(self):
        raw = self._entry.get().strip()
        if not raw or raw == "Ask anything about your documents…":
            return
        self._entry.delete(0, "end")
        self._restore_placeholder()

        self.add_message("User", raw)
        hist.append("User", raw)

        thinking = self.add_message("AI", "Thinking…")
        model = self._model_var.get()

        def worker():
            try:
                answer = self._engine.run(raw, model)
            except Exception as exc:
                answer = f"Something went wrong: {exc}"
            self.after(0, lambda: thinking.update_text(answer))
            self.after(0, lambda: hist.append("AI", answer))

        threading.Thread(target=worker, daemon=True).start()
