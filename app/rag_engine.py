"""
rag_engine.py — LangChain + LangGraph RAG pipeline.

Graph nodes:
  classify → [chat_node | retrieve_node → grade_node → generate_node]

All heavy work runs in a background thread; the UI calls
engine.run(query, callback) which invokes callback(text) on the main thread.
"""
import os
import json
import shutil
from typing import TypedDict, List, Literal, Callable, Optional

from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.documents import Document
from langgraph.graph import StateGraph, END

from config import (
    DATA_PATH, DB_PATH, OLLAMA_BASE_URL, EMBED_MODEL,
    CHUNK_SIZE, CHUNK_OVERLAP, SCORE_THRESHOLD,
    RETRIEVER_K, RETRIEVER_FETCH_K, RETRIEVER_LAMBDA,
)


# ── LangGraph state ──────────────────────────────────────────────────────────
class RAGState(TypedDict):
    query:        str
    intent:       Literal["chat", "rag"]
    documents:    List[Document]
    context_text: str
    answer:       str
    model_name:   str
    temperature:  float


# ── RAG Engine ───────────────────────────────────────────────────────────────
class RAGEngine:
    def __init__(self):
        self.vectorstore: Optional[Chroma] = None
        self.embeddings = OllamaEmbeddings(
            model=EMBED_MODEL, base_url=OLLAMA_BASE_URL)
        self._graph = self._build_graph()
        self.indexed_files: List[str] = []

    # ── Graph builder ─────────────────────────────────────────────────────────
    def _build_graph(self) -> object:
        g = StateGraph(RAGState)

        g.add_node("classify",  self._node_classify)
        g.add_node("chat",      self._node_chat)
        g.add_node("retrieve",  self._node_retrieve)
        g.add_node("grade",     self._node_grade)
        g.add_node("generate",  self._node_generate)
        g.add_node("no_docs",   self._node_no_docs)

        g.set_entry_point("classify")

        g.add_conditional_edges(
            "classify",
            lambda s: s["intent"],
            {"chat": "chat", "rag": "retrieve"},
        )
        g.add_edge("chat",     END)
        g.add_edge("retrieve", "grade")
        g.add_conditional_edges(
            "grade",
            lambda s: "generate" if s["documents"] else "no_docs",
            {"generate": "generate", "no_docs": "no_docs"},
        )
        g.add_edge("generate", END)
        g.add_edge("no_docs",  END)

        return g.compile()

    # ── Graph nodes ───────────────────────────────────────────────────────────
    def _llm(self, state: RAGState) -> ChatOllama:
        return ChatOllama(
            model=state["model_name"],
            base_url=OLLAMA_BASE_URL,
            temperature=state["temperature"],
        )

    def _node_classify(self, state: RAGState) -> RAGState:
        llm = self._llm(state)
        result = llm.invoke([
            SystemMessage(content=(
                "You are a query classifier. Decide if the message is:\n"
                "A) General conversation, greeting, or general knowledge question "
                "that does NOT need internal company documents.\n"
                "B) A question that needs information from uploaded internal documents.\n"
                "Reply ONLY with a single letter: A or B."
            )),
            HumanMessage(content=state["query"]),
        ])
        letter = result.content.strip().upper()
        return {**state, "intent": "chat" if letter == "A" else "rag"}

    def _node_chat(self, state: RAGState) -> RAGState:
        llm = self._llm(state)
        result = llm.invoke([
            SystemMessage(content=(
                "You are a friendly, knowledgeable assistant embedded inside an "
                "enterprise document Q&A tool. Chat naturally and warmly. You can "
                "answer general questions, make small talk, and help with anything "
                "you know. If the user seems to be looking for something from their "
                "uploaded documents, let them know they can ask about those too. "
                "Keep responses concise and human — no bullet dumps, no stiff phrasing."
            )),
            HumanMessage(content=state["query"]),
        ])
        return {**state, "answer": result.content}

    def _node_retrieve(self, state: RAGState) -> RAGState:
        if self.vectorstore is None:
            return {**state, "documents": []}
        raw = self.vectorstore.similarity_search_with_relevance_scores(
            state["query"], k=RETRIEVER_K * 2)
        docs = [d for d, score in raw if score >= SCORE_THRESHOLD]
        return {**state, "documents": docs}

    def _node_grade(self, state: RAGState) -> RAGState:
        """Re-rank and deduplicate retrieved chunks."""
        seen, unique = set(), []
        for doc in state["documents"]:
            key = doc.page_content[:120]
            if key not in seen:
                seen.add(key)
                unique.append(doc)
        return {**state, "documents": unique[:RETRIEVER_K]}

    def _node_generate(self, state: RAGState) -> RAGState:
        ctx = ""
        for doc in state["documents"]:
            src  = os.path.basename(doc.metadata.get("source", "Unknown"))
            page = doc.metadata.get("page", "N/A")
            ctx += f"\n[SOURCE: {src} | PAGE: {page}]\n{doc.page_content}\n"

        llm = self._llm(state)
        result = llm.invoke([
            SystemMessage(content=(
                "You are a knowledgeable and conversational assistant who has just "
                "read through internal company documents on behalf of the user. "
                "Answer warmly and naturally like a helpful colleague — not a search engine.\n\n"
                "Guidelines:\n"
                "- Base your answer on the document excerpts provided.\n"
                "- Cite sources conversationally, e.g. 'According to Policy.pdf (page 2)…'\n"
                "- If the docs only partially answer the question, say so honestly.\n"
                "- Never invent facts. If sources disagree, mention both.\n"
                "- Write in flowing prose; use lists only when the question calls for them."
            )),
            HumanMessage(content=f"DOCUMENT EXCERPTS:\n{ctx}\n\nQUESTION: {state['query']}"),
        ])
        return {**state, "context_text": ctx, "answer": result.content}

    def _node_no_docs(self, state: RAGState) -> RAGState:
        llm = self._llm(state)
        result = llm.invoke([
            SystemMessage(content=(
                "You are a friendly assistant. The user asked something that sounds "
                "document-related, but nothing relevant was found in the uploaded files. "
                "Respond naturally in 1-2 sentences — mention the docs didn't seem to "
                "cover it and either offer to help from your own knowledge or suggest "
                "uploading a relevant file. Sound warm and human, not robotic."
            )),
            HumanMessage(content=state["query"]),
        ])
        return {**state, "answer": result.content}

    # ── Public API ────────────────────────────────────────────────────────────
    def run(self, query: str, model_name: str,
            temperature: float = 0.7) -> str:
        init: RAGState = {
            "query":        query,
            "intent":       "rag",
            "documents":    [],
            "context_text": "",
            "answer":       "",
            "model_name":   model_name,
            "temperature":  temperature,
        }
        final = self._graph.invoke(init)
        return final.get("answer", "Something went wrong — please try again.")

    # ── Indexing ──────────────────────────────────────────────────────────────
    def index(self, force: bool = False,
              progress_cb: Optional[Callable[[str], None]] = None) -> int:
        """Load all PDFs in DATA_PATH into the vector store.
        Returns number of indexed documents."""
        os.makedirs(DATA_PATH, exist_ok=True)

        if force and os.path.exists(DB_PATH):
            shutil.rmtree(DB_PATH)
            if progress_cb:
                progress_cb("Cleared old index.")

        pdfs = [f for f in os.listdir(DATA_PATH) if f.lower().endswith(".pdf")]
        self.indexed_files = pdfs

        if not force and os.path.exists(DB_PATH) and os.listdir(DB_PATH):
            if progress_cb:
                progress_cb(f"Loading existing index ({len(pdfs)} sources)…")
            self.vectorstore = Chroma(
                persist_directory=DB_PATH,
                embedding_function=self.embeddings)
            return len(pdfs)

        if not pdfs:
            if progress_cb:
                progress_cb("No PDFs found. Upload documents to get started.")
            self.vectorstore = None
            return 0

        if progress_cb:
            progress_cb(f"Indexing {len(pdfs)} PDF(s)…")

        loader = DirectoryLoader(DATA_PATH, glob="./*.pdf",
                                 loader_cls=PyPDFLoader)
        docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        splits = splitter.split_documents(docs)

        total = len(splits)
        if progress_cb:
            progress_cb(f"Embedding {total} chunks…  0%")

        BATCH = 50  # embed in batches so we can report progress
        self.vectorstore = None
        for i in range(0, total, BATCH):
            batch = splits[i:i + BATCH]
            if self.vectorstore is None:
                self.vectorstore = Chroma.from_documents(
                    documents=batch,
                    embedding=self.embeddings,
                    persist_directory=DB_PATH,
                )
            else:
                self.vectorstore.add_documents(batch)
            done = min(i + BATCH, total)
            pct  = int(done / total * 100)
            if progress_cb:
                progress_cb(f"Embedding {total} chunks…  {pct}%")

        if progress_cb:
            progress_cb(f"Ready — {len(pdfs)} source(s) indexed.")
        return len(pdfs)

    def add_pdf(self, src_path: str,
                progress_cb: Optional[Callable[[str], None]] = None) -> None:
        """Copy a PDF into DATA_PATH then incrementally add it to the store."""
        os.makedirs(DATA_PATH, exist_ok=True)
        dest = os.path.join(DATA_PATH, os.path.basename(src_path))
        shutil.copy(src_path, dest)

        if progress_cb:
            progress_cb(f"Loading '{os.path.basename(src_path)}'…")

        loader = PyPDFLoader(dest)
        docs   = loader.load()
        splits = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
        ).split_documents(docs)

        if self.vectorstore is None:
            total = len(splits)
            if progress_cb:
                progress_cb(f"Embedding {total} chunks…  0%")
            for i in range(0, total, 50):
                batch = splits[i:i + 50]
                if self.vectorstore is None:
                    self.vectorstore = Chroma.from_documents(
                        documents=batch,
                        embedding=self.embeddings,
                        persist_directory=DB_PATH,
                    )
                else:
                    self.vectorstore.add_documents(batch)
                done = min(i + 50, total)
                pct  = int(done / total * 100)
                if progress_cb:
                    progress_cb(f"Embedding {total} chunks…  {pct}%")
        else:
            total = len(splits)
            if progress_cb:
                progress_cb(f"Embedding {total} chunks…  0%")
            for i in range(0, total, 50):
                batch = splits[i:i + 50]
                self.vectorstore.add_documents(batch)
                done = min(i + 50, total)
                pct  = int(done / total * 100)
                if progress_cb:
                    progress_cb(f"Embedding {total} chunks…  {pct}%")

        self.indexed_files.append(os.path.basename(dest))
        if progress_cb:
            progress_cb(f"'{os.path.basename(src_path)}' added & indexed.")

    def delete_pdf(self, filename: str,
                   progress_cb: Optional[Callable[[str], None]] = None) -> None:
        """Remove a PDF from disk then rebuild the index without it."""
        target = os.path.join(DATA_PATH, filename)
        if os.path.exists(target):
            os.remove(target)
        if filename in self.indexed_files:
            self.indexed_files.remove(filename)
        if progress_cb:
            progress_cb(f"Removed '{filename}'. Re-indexing…")
        self.index(force=True, progress_cb=progress_cb)

    def list_pdfs(self) -> List[str]:
        os.makedirs(DATA_PATH, exist_ok=True)
        return sorted(f for f in os.listdir(DATA_PATH)
                      if f.lower().endswith(".pdf"))
