"""
Enterprise RAG Assistant — entry point.
Run:  python app/main.py
"""
from ui.app import EnterpriseApp

if __name__ == "__main__":
    app = EnterpriseApp()
    app.mainloop()
