#!/usr/bin/env python3
"""
Debug script to check what's actually stored in ChromaDB
Run: python debug_chromadb.py
"""

import chromadb
from chromadb.config import Settings

CHROMA_PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "finance_docs"

print("="*70)
print("🔍 CHROMADB CONTENT DEBUG")
print("="*70)

try:
    # Connect to ChromaDB
    print("\n[1] Connecting to ChromaDB...")
    client = chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR,
        settings=Settings(
            allow_reset=True,
            anonymized_telemetry=False
        )
    )
    print(f"    ✓ Connected to: {CHROMA_PERSIST_DIR}")
    
    # Get collection
    print(f"\n[2] Getting collection: {COLLECTION_NAME}")
    collection = client.get_collection(name=COLLECTION_NAME)
    print(f"    ✓ Collection found")
    
    # Get document count
    count = collection.count()
    print(f"\n[3] Document count: {count}")
    
    if count == 0:
        print("\n    ❌ NO DOCUMENTS IN DATABASE!")
        print("    💡 You need to upload files first")
        print("="*70)
        exit(1)
    
    # Get all documents (limit to 10 for display)
    print(f"\n[4] Fetching documents (showing first 10)...")
    results = collection.get(limit=10)
    
    print(f"\n[5] Document Details:")
    print("="*70)
    
    for i, (doc_id, text, metadata) in enumerate(zip(
        results['ids'],
        results['documents'],
        results['metadatas']
    ), 1):
        print(f"\n📄 Document #{i}")
        print(f"   ID: {doc_id}")
        print(f"   Source: {metadata.get('source', 'Unknown')}")
        print(f"   Type: {metadata.get('type', 'Unknown')}")
        print(f"   Text Length: {len(text)} characters")
        print(f"   Preview: {text[:200]}...")
        print("-"*70)
    
    # Test query
    print(f"\n[6] Testing query: 'finance prerequisite'")
    query_results = collection.query(
        query_texts=["finance prerequisite"],
        n_results=5
    )
    
    print(f"\n[7] Query Results:")
    if query_results['documents'] and len(query_results['documents'][0]) > 0:
        print(f"    ✓ Found {len(query_results['documents'][0])} relevant documents")
        for i, (doc, metadata, distance) in enumerate(zip(
            query_results['documents'][0],
            query_results['metadatas'][0],
            query_results['distances'][0]
        ), 1):
            print(f"\n    Result #{i}")
            print(f"       Source: {metadata.get('source', 'Unknown')}")
            print(f"       Relevance: {distance:.4f} (lower is better)")
            print(f"       Preview: {doc[:150]}...")
    else:
        print("    ❌ NO RESULTS FOUND!")
        print("    💡 This means your query doesn't match stored documents")
    
    # Show all sources
    print(f"\n[8] All document sources in database:")
    all_docs = collection.get()
    sources = set()
    for metadata in all_docs['metadatas']:
        sources.add(metadata.get('source', 'Unknown'))
    
    for source in sorted(sources):
        count = sum(1 for m in all_docs['metadatas'] if m.get('source') == source)
        print(f"    📁 {source}: {count} chunks")
    
    print("\n" + "="*70)
    print("✅ DIAGNOSIS COMPLETE")
    print("="*70)
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    if count < 10:
        print("   ⚠️  Very few documents - upload more files")
    
    if query_results['documents'] and len(query_results['documents'][0]) == 0:
        print("   ⚠️  Query returns no results - check document content")
    
    if all(len(doc) < 100 for doc in results['documents'][:5]):
        print("   ⚠️  Documents are very short - may need better chunking")
    
    print("\n" + "="*70)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    print("\n💡 Make sure:")
    print("   1. Backend has been run at least once")
    print("   2. Files have been uploaded")
    print("   3. ChromaDB directory exists: ./chroma_db")
    print("="*70)