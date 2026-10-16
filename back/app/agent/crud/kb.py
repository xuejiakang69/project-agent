import asyncio
import hashlib
import json
import sys
from pathlib import Path
from threading import RLock

try:
    import pysqlite3
    sys.modules["sqlite3"] = pysqlite3
except ImportError:
    # Windows 上没有 pysqlite3-binary，直接用系统自带的 sqlite3
    pass

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.utils import embedding_functions

from app.config import BASE_DIR

# 本地 BGE 模型目录
MODEL_PATH = Path("/www/wwwroot/fastapi/fastapi-test/model-cache/bge-small-zh-v1.5")
KB_DIR = BASE_DIR / "data" / "kb"
CHROMA_DIR = BASE_DIR / "data" / "chroma"
MANIFEST_PATH = CHROMA_DIR / "kb_manifest.json"

_collection: Collection | None = None
_embedding_fn = None
_lock = RLock()


def get_collection() -> Collection:
    global _collection, _embedding_fn

    if _collection is None:
        _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=str(MODEL_PATH),
            device="cpu",
            normalize_embeddings=True,
            local_files_only=True,
        )
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = client.get_or_create_collection(
            name="lab_kb",
            embedding_function=_embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    return _collection


def _load_documents() -> dict[str, dict]:
    KB_DIR.mkdir(parents=True, exist_ok=True)
    documents = {}

    for path in sorted(KB_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8").strip()
        documents[path.name] = {
            "hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "chunks": [part.strip() for part in text.split("\n\n") if part.strip()],
        }

    return documents


def _load_hashes() -> dict:
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_hashes(documents: dict[str, dict]) -> None:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    hashes = {name: item["hash"] for name, item in documents.items()}
    MANIFEST_PATH.write_text(
        json.dumps(hashes, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def sync_if_changed() -> bool:
    """资料未变化时跳过 Embedding 和向量更新。"""
    with _lock:
        documents = _load_documents()
        old_hashes = _load_hashes()

        changed = []
        for name, item in documents.items():
            old_hash = old_hashes.get(name)
            if isinstance(old_hash, dict):
                old_hash = old_hash.get("hash")
            if old_hash != item["hash"]:
                changed.append(name)

        removed = set(old_hashes) - set(documents)
        if not changed and not removed:
            return False

        collection = get_collection()
        for source in set(changed) | removed:
            collection.delete(where={"source": source})

        for source in changed:
            chunks = documents[source]["chunks"]
            if not chunks:
                continue

            collection.upsert(
                ids=[f"{Path(source).stem}_{i}" for i in range(len(chunks))],
                documents=chunks,
                metadatas=[
                    {"source": source, "chunk_index": i} for i in range(len(chunks))
                ],
            )

        _save_hashes(documents)
        return True


def search(query: str) -> str:
    query = query.strip()
    if not query:
        return ""

    sync_if_changed()
    collection = get_collection()
    if collection.count() == 0:
        return ""

    result = collection.query(
        query_texts=[query],
        n_results=min(5, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    rows = [
        (distance, f"[{(metadata or {}).get('source', '')}]\n{document}")
        for document, metadata, distance in zip(
            result["documents"][0],
            result["metadatas"][0],
            result["distances"][0],
        )
        if document is not None
    ]
    rows.sort(key=lambda item: item[0])
    return "\n\n".join(content for _, content in rows[:2])


async def async_search(query: str) -> str:
    return await asyncio.to_thread(search, query)


async def async_init_knowledge_base() -> None:
    await asyncio.to_thread(sync_if_changed)
