"""
widgets.py — reusable tkinter widgets used across panels.
"""
import tkinter as tk


class MessageBubble(tk.Frame):
    """Selectable, highlightable chat bubble backed by tk.Text."""

    def __init__(self, parent, role: str, text: str, theme: dict, **kwargs):
        bg = theme["bg"]
        super().__init__(parent, bg=bg, **kwargs)

        self.theme      = theme
        self.role       = role
        self._full_text = text

        if role == "User":
            bubble_bg   = theme["user_bubble"]
            label_color = theme["accent"]
        elif role == "System":
            bubble_bg   = theme["sys_bubble"]
            label_color = theme["warning"]
        else:
            bubble_bg   = theme["ai_bubble"]
            label_color = theme["text_muted"]

        self.bubble_bg = bubble_bg

        row = tk.Frame(self, bg=bg)
        row.pack(fill="x", padx=10, pady=2)

        role_lbl = tk.Label(
            row, text=role.upper(),
            font=("Consolas", 8, "bold"),
            fg=label_color, bg=bg,
        )
        role_lbl.pack(side="left", padx=(4, 0), pady=(0, 2))

        card = tk.Frame(row, bg=bubble_bg, bd=0,
                        highlightthickness=1,
                        highlightbackground=theme["border"])
        card.pack(fill="x", expand=True)

        # ── Toolbar ──────────────────────────────────────────────────────────
        toolbar = tk.Frame(card, bg=bubble_bg)
        toolbar.pack(fill="x", padx=10, pady=(6, 0))

        for label, enter_color, handler in [
            ("⎘ Copy",              theme["text"],    self._copy_all),
            ("▐ Highlight",         theme["warning"], self._highlight_selection),
            ("✕ Clear highlights",  theme["danger"],  self._clear_highlights),
        ]:
            lbl = tk.Label(toolbar, text=label, font=("Consolas", 8),
                           fg=theme["text_muted"], bg=bubble_bg, cursor="hand2")
            lbl.pack(side="left", padx=(0, 12))
            lbl.bind("<Button-1>", lambda e, h=handler: h())
            lbl.bind("<Enter>", lambda e, l=lbl, c=enter_color: l.config(fg=c))
            lbl.bind("<Leave>", lambda e, l=lbl: l.config(fg=theme["text_muted"]))
            if label == "⎘ Copy":
                self._copy_lbl = lbl

        # ── Text widget ───────────────────────────────────────────────────────
        self.textbox = tk.Text(
            card,
            wrap="word",
            font=("Georgia", 13),
            fg=theme["text"],
            bg=bubble_bg,
            bd=0, padx=16, pady=10,
            relief="flat",
            cursor="xterm",
            selectbackground=theme["selection"],
            selectforeground="#ffffff",
            insertwidth=0,
            highlightthickness=0,
            spacing3=4,
        )
        self.textbox.pack(fill="x", expand=True)
        self.textbox.tag_configure(
            "highlight",
            background=theme["highlight"],
            foreground=theme["highlight_fg"],
        )
        self.textbox.insert("1.0", text)
        self.textbox.configure(state="disabled")
        self.textbox.bind("<Configure>", lambda e: self._resize())
        self.after(50, self._resize)

    def _resize(self):
        self.textbox.update_idletasks()
        count = self.textbox.count("1.0", "end", "displaylines")
        lines = count[0] if count else 1
        self.textbox.configure(height=max(lines, 1))

    def update_text(self, new_text: str):
        self._full_text = new_text
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", new_text)
        self.textbox.configure(state="disabled")
        self.after(50, self._resize)

    def _copy_all(self):
        self.clipboard_clear()
        self.clipboard_append(self._full_text)
        self._copy_lbl.config(text="✓ Copied!", fg=self.theme["success"])
        self.after(1500, lambda: self._copy_lbl.config(
            text="⎘ Copy", fg=self.theme["text_muted"]))

    def _highlight_selection(self):
        try:
            s = self.textbox.index("sel.first")
            e = self.textbox.index("sel.last")
            self.textbox.tag_add("highlight", s, e)
        except tk.TclError:
            pass

    def _clear_highlights(self):
        self.textbox.tag_remove("highlight", "1.0", "end")


class StatusDot(tk.Frame):
    def __init__(self, parent, theme, **kwargs):
        super().__init__(parent, bg=theme["surface"], **kwargs)
        self.theme = theme
        self._c = tk.Canvas(self, width=10, height=10,
                            bg=theme["surface"], bd=0, highlightthickness=0)
        self._c.pack(side="left", padx=(0, 6))
        self._dot = self._c.create_oval(1, 1, 9, 9,
                                        fill=theme["warning"], outline="")
        self._lbl = tk.Label(self, text="Starting…",
                             font=("Consolas", 10),
                             fg=theme["warning"],
                             bg=theme["surface"])
        self._lbl.pack(side="left")

    def set(self, text: str, color: str):
        self._c.itemconfig(self._dot, fill=color)
        self._lbl.config(text=text, fg=color)


class SidebarButton(tk.Label):
    """Flat sidebar nav button."""
    def __init__(self, parent, text, theme, command=None, **kwargs):
        super().__init__(
            parent, text=text,
            font=("Consolas", 11),
            fg=theme["text_muted"],
            bg=theme["sidebar_bg"],
            cursor="hand2",
            anchor="w",
            padx=18, pady=10,
            **kwargs,
        )
        self._theme   = theme
        self._command = command
        self._active  = False
        self.bind("<Button-1>", lambda e: command() if command else None)
        self.bind("<Enter>",   self._on_enter)
        self.bind("<Leave>",   self._on_leave)

    def set_active(self, active: bool):
        self._active = active
        if active:
            self.config(fg=theme_fg(self._theme),
                        bg=self._theme["surface2"])
        else:
            self.config(fg=self._theme["text_muted"],
                        bg=self._theme["sidebar_bg"])

    def _on_enter(self, _e):
        if not self._active:
            self.config(fg=self._theme["text"], bg=self._theme["surface"])

    def _on_leave(self, _e):
        if not self._active:
            self.config(fg=self._theme["text_muted"],
                        bg=self._theme["sidebar_bg"])


def theme_fg(theme):
    return theme["text"]
