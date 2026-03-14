import os
import uuid
import numpy as np
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import DirectoryLoader, PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb

# Constants for consistency
PERSIST_DIR = "./data/vector_store"
COLLECTION_NAME = "pdf_documents"

class EmbeddingManager:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        return self.model.encode(texts, show_progress_bar=True)

class VectorStoreManager:
    def __init__(self, collection_name: str = COLLECTION_NAME, persist_directory: str = PERSIST_DIR):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_documents(self, documents: List[Document], embeddings: np.ndarray):
        ids = [f"doc_{uuid.uuid4().hex[:8]}_{i}" for i in range(len(documents))]
        self.collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            metadatas=[doc.metadata for doc in documents],
            documents=[doc.page_content for doc in documents]
        )

# --- NEW: This is what llmrag.py needs to work ---
def get_collection():
    """Returns the ChromaDB collection for querying."""
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    return client.get_collection(name=COLLECTION_NAME)

def build_index():
    """Function called by app.py on startup to ensure data is ready."""
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    if collection.count() > 0:
        return collection.count()

    if not os.path.exists("./data"):
        os.makedirs("./data")
        return 0
    
    loader = DirectoryLoader("./data", glob="**/*.pdf", loader_cls=PyMuPDFLoader)
    raw_docs = loader.load()
    if not raw_docs: return 0

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = splitter.split_documents(raw_docs)
    
    embedder = EmbeddingManager()
    vectors = embedder.generate_embeddings([c.page_content for c in chunks])
    
    store = VectorStoreManager()
    store.add_documents(chunks, vectors)
    return len(chunks)

if __name__ == "__main__":
    count = build_index()
    print(f"Ingestion complete: {count} chunks processed.")