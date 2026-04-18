"""
panel_docs.py — document library management panel.
Browse, upload, delete, and re-index PDFs.
"""
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

from config import THEME, DATA_PATH


class DocsPanel(tk.Frame):
    def __init__(self, parent, engine, status_cb, **kwargs):
        super().__init__(parent, bg=THEME["bg"], **kwargs)
        self._engine    = engine
        self._status_cb = status_cb
        self._build()
        self.refresh()

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=THEME["surface"], height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="Document Library",
                 font=("Consolas", 13, "bold"),
                 fg=THEME["text"], bg=THEME["surface"]).pack(
            side="left", padx=20, pady=14)

        for label, cmd in [
            ("+ Upload PDF",  self._upload),
            ("⟳ Re-index all", self._reindex),
        ]:
            btn = tk.Label(hdr, text=label,
                           font=("Consolas", 10, "bold"),
                           fg="#fff", bg=THEME["accent"],
                           cursor="hand2", padx=10, pady=5)
            btn.pack(side="right", padx=(0, 12), pady=10)
            btn.bind("<Button-1>", lambda e, c=cmd: c())
            btn.bind("<Enter>",
                     lambda e, b=btn: b.config(bg=THEME["accent_hover"]))
            btn.bind("<Leave>",
                     lambda e, b=btn: b.config(bg=THEME["accent"]))

        # ── Stats bar ─────────────────────────────────────────────────────────
        self._stats_lbl = tk.Label(
            self, text="",
            font=("Consolas", 9), fg=THEME["text_muted"], bg=THEME["bg"],
            anchor="w")
        self._stats_lbl.pack(fill="x", padx=20, pady=(10, 4))

        # ── Search box ────────────────────────────────────────────────────────
        search_row = tk.Frame(self, bg=THEME["bg"])
        search_row.pack(fill="x", padx=20, pady=(0, 8))

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self.refresh())
        tk.Entry(
            search_row,
            textvariable=self._search_var,
            font=("Consolas", 11),
            fg=THEME["text"], bg=THEME["surface2"],
            insertbackground=THEME["accent"],
            relief="flat", bd=0,
        ).pack(fill="x", ipady=6, padx=4)

        # ── File list ─────────────────────────────────────────────────────────
        list_frame = tk.Frame(self, bg=THEME["bg"])
        list_frame.pack(fill="both", expand=True, padx=20)

        self._canvas = tk.Canvas(list_frame, bg=THEME["bg"],
                                 bd=0, highlightthickness=0)
        sb = tk.Scrollbar(list_frame, orient="vertical",
                          command=self._canvas.yview,
                          bg=THEME["surface"], width=8, bd=0)
        self._canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._list_inner = tk.Frame(self._canvas, bg=THEME["bg"])
        self._win = self._canvas.create_window(
            (0, 0), window=self._list_inner, anchor="nw")

        self._list_inner.bind("<Configure>",
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
            lambda e: self._canvas.itemconfig(self._win, width=e.width))
        self._canvas.bind_all("<MouseWheel>",
            lambda e: self._canvas.yview_scroll(
                -1*(e.delta//120), "units"))

        # ── Log strip ─────────────────────────────────────────────────────────
        self._log = tk.Label(
            self, text="",
            font=("Consolas", 9), fg=THEME["warning"],
            bg=THEME["surface"], anchor="w", pady=6)
        self._log.pack(fill="x", side="bottom", padx=0)

    # ── Refresh list ──────────────────────────────────────────────────────────

    def refresh(self):
        for w in self._list_inner.winfo_children():
            w.destroy()

        query = self._search_var.get().lower() if hasattr(self, "_search_var") else ""
        pdfs  = [f for f in self._engine.list_pdfs()
                 if query in f.lower()]

        self._stats_lbl.config(
            text=f"{len(pdfs)} document(s)  ·  "
                 f"Folder: {DATA_PATH}")

        if not pdfs:
            tk.Label(self._list_inner,
                     text="No documents yet. Upload a PDF to get started.",
                     font=("Consolas", 11), fg=THEME["text_muted"],
                     bg=THEME["bg"], pady=20).pack()
            return

        for fname in pdfs:
            self._make_row(fname)

    def _make_row(self, fname: str):
        fpath = os.path.join(DATA_PATH, fname)
        size  = os.path.getsize(fpath) if os.path.exists(fpath) else 0
        size_str = f"{size/1024:.1f} KB" if size < 1_048_576 \
                   else f"{size/1_048_576:.2f} MB"

        row = tk.Frame(self._list_inner, bg=THEME["surface2"],
                       highlightthickness=1,
                       highlightbackground=THEME["border"])
        row.pack(fill="x", pady=3, ipady=2)

        # Icon
        tk.Label(row, text="📄", font=("", 16),
                 bg=THEME["surface2"]).pack(side="left", padx=(10, 0))

        # Name + size
        info = tk.Frame(row, bg=THEME["surface2"])
        info.pack(side="left", fill="x", expand=True, padx=10, pady=6)
        tk.Label(info, text=fname,
                 font=("Consolas", 11),
                 fg=THEME["text"], bg=THEME["surface2"],
                 anchor="w").pack(fill="x")
        tk.Label(info, text=size_str,
                 font=("Consolas", 9),
                 fg=THEME["text_muted"], bg=THEME["surface2"],
                 anchor="w").pack(fill="x")

        # Delete button
        del_btn = tk.Label(row, text=" 🗑 ",
                           font=("Consolas", 11),
                           fg=THEME["danger"], bg=THEME["surface2"],
                           cursor="hand2")
        del_btn.pack(side="right", padx=10)
        del_btn.bind("<Button-1>",
                     lambda e, f=fname: self._delete(f))
        del_btn.bind("<Enter>",
                     lambda e, b=del_btn: b.config(bg=THEME["surface3"]))
        del_btn.bind("<Leave>",
                     lambda e, b=del_btn: b.config(bg=THEME["surface2"]))

    # ── Actions ───────────────────────────────────────────────────────────────

    def _log_msg(self, msg: str):
        self._log.config(text=f"  {msg}")
        self._status_cb(msg)

    def _upload(self):
        paths = filedialog.askopenfilenames(
            filetypes=[("PDF files", "*.pdf")])
        if not paths:
            return

        def worker():
            for p in paths:
                self._engine.add_pdf(p, progress_cb=self._log_msg)
            self.after(0, self.refresh)
            self.after(0, lambda: self._status_cb(
                f"{len(paths)} file(s) added & indexed."))

        threading.Thread(target=worker, daemon=True).start()

    def _delete(self, fname: str):
        if not messagebox.askyesno(
                "Delete document",
                f"Remove '{fname}' from the library and re-index?"):
            return

        def worker():
            self._engine.delete_pdf(fname, progress_cb=self._log_msg)
            self.after(0, self.refresh)

        threading.Thread(target=worker, daemon=True).start()

    def _reindex(self):
        def worker():
            self._log_msg("Re-indexing all documents…")
            self._engine.index(force=True, progress_cb=self._log_msg)
            self.after(0, self.refresh)

        threading.Thread(target=worker, daemon=True).start()
