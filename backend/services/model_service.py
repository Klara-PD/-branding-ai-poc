import os
from threading import Lock
from typing import Optional

from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

_model: Optional[SentenceTransformer] = None
_model_lock = Lock()

_pinecone_client: Optional[Pinecone] = None
_pinecone_lock = Lock()

_index_cache = {}
_index_lock = Lock()


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                _model = SentenceTransformer("clip-ViT-B-32")
    return _model


def get_pinecone_client() -> Pinecone:
    global _pinecone_client
    if _pinecone_client is None:
        with _pinecone_lock:
            if _pinecone_client is None:
                api_key = os.getenv("PINECONE_API_KEY")
                if not api_key:
                    raise ValueError("PINECONE_API_KEY is not set")
                _pinecone_client = Pinecone(api_key=api_key)
    return _pinecone_client


def get_index(index_name: Optional[str] = None):
    if not index_name:
        index_name = os.getenv("PINECONE_INDEX_NAME", "branding-playground")
    with _index_lock:
        if index_name not in _index_cache:
            pc = get_pinecone_client()
            _index_cache[index_name] = pc.Index(index_name)
        return _index_cache[index_name]


def init_services() -> None:
    # Force initialization at startup
    get_model()
    get_index()
