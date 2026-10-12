import asyncio
from pathlib import Path
from threading import Lock
import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.utils import embedding_functions
from app.config import BASE_DIR


KB_DIR = BASE_DIR / "data" / "kb" #知识库的路径
CHROMA_DIR = BASE_DIR / "data" / "chroma" #chromadb 本地化路径

COLLECTION_NAME = "lab_kb" #名称
CHUNK_SIZE = 500 #以500字符分割
CHUNK_OVERLAP = 80 #重复内容
TOP_K = 5 #取5条


_collection:Collection | None = None #当前对象没有集合对象
_init_lock = Lock() #让同一进程的初始化依次执行减少竞争


#默认是英文检索  切换成中文的
_embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-small-zh-v1.5"
)


def split_text(text:str,chunk_size:int=CHUNK_SIZE,overlap:int=CHUNK_OVERLAP):
    #按照锻炼切分文本，并保留一定的段落
    text = text.strip()
    if not text:
        return []

    #先按空行切分，尽量抱愧原有段落
    paragraphs = [
        paragraph.strip()
        for paragraph in text.split("\n\n")
        if paragraph.strip()
    ]

    chunks:list[str] = []
    current = ""

    for paragraph in paragraphs:
        #超长段落再按字符长度七日分
        if len(paragraph) > chunk_size:
            if current:
                chunks.append(current)
                current=""

            start = 0
            while start < len(paragraph):
                end = start+chunk_size
                chunks.append(paragraph[start:end])

                if end >= len(paragraph):
                    break

                start = end - overlap
            continue
        candidate = (
            f"{current}\n\n{paragraph}"
            if current
            else paragraph
        )

        if len(candidate) <= chunk_size:
            current = candidate
        else:
            chunks.append(current)
            current = current[-overlap:]+"\n\n"+paragraph
    if current:
        chunks.append(current)

    return chunks


def get_collection():
    """获取持久化的"""
    global _collection

    if _collection is not None:
        return _collection

    with _init_lock:
        if _collection is not None:
            return _collection

        KB_DIR.mkdir(parents=True,exist_ok=True)
        CHROMA_DIR.mkdir(parents=True,exist_ok=True)

        client = chromadb.PersistentClient(
            path = str(CHROMA_DIR)
        )

        collection = client.get_or_create_collection(
            name = COLLECTION_NAME,
            embedding_function=_embedding_fn,
            metadata={"hnsw:space":"cosine"}
        )
        sync_konwledge_base(collection)

        _collection = collection

        return _collection


def sync_konwledge_base(collection:Collection):
    """同步markdown文档，新增或更新对应的chunk"""
    for path in sorted(KB_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8").strip()
        chunks = split_text(text)

        if not text:
            continue

        ids = [
            f"{path.stem}_{index}"
            for index in range(len(chunks))
        ]

        metadatas = [
            {
                "source":path.name,
                "chunk_index":index,
            }
            for index in range(len(chunks))
        ]

        collection.upsert(
            ids=ids,
            documents=chunks,
            metadatas=metadatas
        )

def search(query:str):
    """检索用户问题"""
    query = query.strip()
    if not query:
        return ""
    collection =  get_collection()
    if collection.count() == 0:
        return ""
    result = collection.query(
        query_texts = [query],
        n_results = min(TOP_K,collection.count()),
        include=["documents","metadatas","distances"]
    )

    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]

    results= []

    for document,metadata,distance in zip(documents,metadatas,distances):

        if document is None or distance is None:
            continue

        results.append(
            {
                "distance":distance,
                "content":(
                    f"[{metadata.get('source','')}]\n"
                    f"{document}"
                )
            }
        )
    results.sort(key=lambda item: item["distance"])

    #返回top2
    final_parts = [
        item["content"]
        for item in results[:2]
    ]

    return "\n\n".join(final_parts)


async def async_search(query: str) -> str:
    """在线程池中执行同步检索，避免阻塞事件循环。"""

    return await asyncio.to_thread(search, query)



async def async_init_knowledge_base() -> None:
    """供 FastAPI 启动阶段调用，提前初始化知识库。"""

    await asyncio.to_thread(get_collection)