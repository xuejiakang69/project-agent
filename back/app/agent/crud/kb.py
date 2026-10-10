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
