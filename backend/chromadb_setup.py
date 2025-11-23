import os
import uuid
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

CHROMADB_PATH = os.getenv('CHROMADB_PATH', './chroma_db')
DATA_DIR = os.getenv('DATA_DIR', './data/finance_docs')
COLLECTION_NAME = 'finance_chatbot'
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'

def initialize_chromadb():
    """Initialize ChromaDB with persistent storage"""
    os.makedirs(CHROMADB_PATH, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMADB_PATH)
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function,
        metadata={'hnsw:space': 'cosine'}
    )
    return collection

def add_documents_to_chromadb(collection, chunks):
    """Add chunked documents to ChromaDB"""
    doc_texts = [str(chunk.text) for chunk in chunks if hasattr(chunk, 'text')]
    doc_ids = [str(uuid.uuid4()) for _ in doc_texts]
    doc_metadatas = []
    
    for chunk in chunks:
        if hasattr(chunk, 'metadata') and chunk.metadata:
            metadata = {k: str(v) for k, v in chunk.metadata.to_dict().items() if v}
            doc_metadatas.append(metadata)
        else:
            doc_metadatas.append({'source': 'unknown'})
    
    if doc_texts:
        collection.add(
            documents=doc_texts,
            metadatas=doc_metadatas,
            ids=doc_ids
        )
        return len(doc_texts)
    return 0

def query_documents(collection, query, n_results=5):
    """Query documents from ChromaDB"""
    try:
        model = SentenceTransformer(EMBEDDING_MODEL)
        query_embedding = model.encode([query])
        results = collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )
        return {
            'documents': results['documents'][0] if results['documents'] else [],
            'metadatas': results['metadatas'][0] if results['metadatas'] else [],
            'distances': results['distances'][0] if results['distances'] else []
        }
    except Exception as e:
        print(f"Error querying documents: {e}")
        return {'documents': [], 'metadatas': [], 'distances': []}

if __name__ == '__main__':
    print("🔄 Initializing ChromaDB...")
    collection = initialize_chromadb()
    print("✓ ChromaDB initialized")