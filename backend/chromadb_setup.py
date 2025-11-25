import chromadb
from chromadb.config import Settings
import uuid
from langchain_core.documents import Document

CHROMA_PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "finance_docs"


def initialize_chromadb():
    """Initialize ChromaDB with persistent storage"""
    try:
        client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=Settings(
                allow_reset=True,
                anonymized_telemetry=False
            )
        )
        
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Finance documents collection"}
        )
        
        print(f"[ChromaDB] Initialized collection: {COLLECTION_NAME}")
        print(f"[ChromaDB] Current document count: {collection.count()}")
        
        return collection
        
    except Exception as e:
        print(f"[ChromaDB ERROR] {e}")
        raise


def query_documents(collection, query_text: str, n_results: int = 5):
    """Query documents from ChromaDB"""
    try:
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        # Format results
        passages = []
        if results['documents'] and len(results['documents'][0]) > 0:
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                distance = results['distances'][0][i] if results['distances'] else None
                
                passages.append({
                    "text": doc,
                    "source": metadata.get("source", "Unknown"),
                    "type": metadata.get("type", "document"),
                    "distance": distance,
                    "metadata": metadata
                })
        
        return {
            "passages": passages,
            "total": len(passages)
        }
        
    except Exception as e:
        print(f"[ChromaDB Query ERROR] {e}")
        return {"passages": [], "total": 0}


def add_documents_to_chromadb(collection, documents):
    """
    Add documents to ChromaDB
    
    Args:
        collection: ChromaDB collection
        documents: List of Document objects or dicts
    
    Returns:
        int: Number of documents added
    """
    try:
        if not documents:
            print("[ChromaDB] No documents to add")
            return 0
        
        ids = []
        texts = []
        metadatas = []
        
        for doc in documents:
            # Handle both Document objects and dicts
            if isinstance(doc, Document):
                # LangChain Document object
                doc_id = str(uuid.uuid4())
                text = doc.page_content
                metadata = doc.metadata or {}
            elif isinstance(doc, dict):
                # Dictionary format
                doc_id = doc.get("id", str(uuid.uuid4()))
                text = doc.get("text") or doc.get("page_content") or doc.get("content", "")
                metadata = doc.get("metadata", {})
            elif hasattr(doc, 'text') and hasattr(doc, 'metadata'):
                # Object with text and metadata attributes (like CompositeElement)
                doc_id = str(uuid.uuid4())
                text = str(doc.text) if hasattr(doc, 'text') else str(doc)
                # Get metadata - handle ElementMetadata objects
                if hasattr(doc, 'metadata'):
                    if hasattr(doc.metadata, '__dict__'):
                        metadata = vars(doc.metadata)
                    else:
                        metadata = {}
                else:
                    metadata = {}
            else:
                # Fallback: treat as string
                print(f"[ChromaDB] Warning: Unknown document type: {type(doc)}")
                doc_id = str(uuid.uuid4())
                text = str(doc)
                metadata = {"type": "text"}
            
            # Validate text
            if not text or not text.strip():
                print(f"[ChromaDB] Skipping empty document")
                continue
            
            # Ensure metadata is serializable and has source
            clean_metadata = {}
            
            # Handle ElementMetadata objects from unstructured
            if hasattr(metadata, '__dict__'):
                metadata_dict = vars(metadata)
            elif isinstance(metadata, dict):
                metadata_dict = metadata
            else:
                metadata_dict = {}
            
            # Extract metadata values
            for key, value in metadata_dict.items():
                # Skip private attributes
                if key.startswith('_'):
                    continue
                    
                if isinstance(value, (str, int, float, bool)):
                    clean_metadata[key] = value
                elif value is None:
                    clean_metadata[key] = ""
                else:
                    clean_metadata[key] = str(value)
            
            # Ensure we have a source - CRITICAL FIX
            if 'source' not in clean_metadata or not clean_metadata['source']:
                if 'filename' in clean_metadata:
                    clean_metadata['source'] = clean_metadata['filename']
                elif 'file_path' in clean_metadata:
                    clean_metadata['source'] = os.path.basename(clean_metadata['file_path'])
                else:
                    clean_metadata['source'] = "uploaded_document"
            
            # Ensure we have a type
            if 'type' not in clean_metadata:
                clean_metadata['type'] = "document"
            
            ids.append(doc_id)
            texts.append(text)
            metadatas.append(clean_metadata)
        
        if not texts:
            print("[ChromaDB] No valid documents to add")
            return 0
        
        # Add to collection
        collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )
        
        print(f"[ChromaDB] ✓ Added {len(texts)} documents")
        
        # Debug: Show sample metadata
        if metadatas:
            print(f"[ChromaDB] Sample source: {metadatas[0].get('source', 'Unknown')}")
        
        return len(texts)
        
    except Exception as e:
        print(f"[ChromaDB Add ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 0


def clear_collection(collection):
    """Clear all documents from collection"""
    try:
        # Get all IDs
        all_docs = collection.get()
        if all_docs and all_docs['ids']:
            collection.delete(ids=all_docs['ids'])
            print(f"[ChromaDB] Cleared {len(all_docs['ids'])} documents")
            return len(all_docs['ids'])
        return 0
    except Exception as e:
        print(f"[ChromaDB Clear ERROR] {e}")
        return 0