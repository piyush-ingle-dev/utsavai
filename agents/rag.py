"""Retrieval over the planning knowledge base (agents/kb/knowledge.md).

Sparse BM25 retrieval wrapped as a LangChain retriever. It needs no embedding
service, so retrieval works offline and can never fail on a network error.
"""
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import PrivateAttr
from rank_bm25 import BM25Okapi

KB_FILE = Path(__file__).parent / "kb" / "knowledge.md"
_TOKEN = re.compile(r"[a-z0-9]+")


_STOP = {"the", "a", "an", "and", "or", "of", "to", "for", "in", "on", "at", "is", "are", "how", "do", "i",
         "we", "our", "my", "what", "can", "should", "with", "it", "be", "this", "that", "about", "need"}


def _stem(word: str) -> str:
    for suffix in ("ing", "ed", "s"):
        if len(word) > len(suffix) + 2 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


_SYNONYMS = {"feed": "food", "meal": "food", "lunch": "food", "dinner": "food", "eat": "food",
             "dj": "sound", "speaker": "loudspeaker", "noise": "loudspeaker", "kid": "children",
             "cost": "budget", "price": "budget", "money": "budget"}


def tokenize(text: str) -> list[str]:
    words = [_SYNONYMS.get(w, w) for w in _TOKEN.findall(text.lower())]
    return [_stem(w) for w in words if w not in _STOP]


@lru_cache(maxsize=1)
def load_documents() -> tuple[Document, ...]:
    docs = []
    for block in re.split(r"^## ", KB_FILE.read_text(encoding="utf-8"), flags=re.M)[1:]:
        head, _, body = block.partition("\n")
        title, types, kind = [p.strip() for p in head.split("|")]
        docs.append(Document(page_content=body.strip(),
                             metadata={"title": title, "types": types.split(","), "kind": kind}))
    return tuple(docs)


class KnowledgeRetriever(BaseRetriever):
    """Top-k BM25 passages, optionally limited to one event type."""

    k: int = 6
    event_type: str | None = None
    _docs: tuple = PrivateAttr(default=())
    _bm25: Any = PrivateAttr(default=None)

    def model_post_init(self, __context: Any) -> None:
        self._docs = load_documents()
        self._bm25 = _bm25()

    def _get_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun | None = None) -> list[Document]:
        scores = self._bm25.get_scores(tokenize(query))
        order = sorted(range(len(self._docs)), key=lambda i: scores[i], reverse=True)
        found = []
        for i in order:
            doc = self._docs[i]
            types = doc.metadata["types"]
            if self.event_type and "all" not in types and self.event_type not in types:
                continue
            if scores[i] <= 0:
                break
            found.append(doc)
            if len(found) >= self.k:
                break
        return found


@lru_cache(maxsize=1)
def _bm25() -> BM25Okapi:
    return BM25Okapi([tokenize((d.metadata["title"] + " ") * 2 + d.page_content) for d in load_documents()])


def retrieve(query: str, event_type: str | None = None, k: int = 6) -> list[Document]:
    return KnowledgeRetriever(k=k, event_type=event_type).invoke(query)
