# ============================================================================
# FILE 1: backend/reset_chromadb.py
# Full system reset - Stop services before running
# ============================================================================

import os
import shutil
import glob
import sys
from pathlib import Path

print("=" * 80)
print(" " * 20 + "CHROMADB FULL RESET SCRIPT")
print("=" * 80)

print("\n⚠️  Make sure to STOP all services before running:")
print("    - Press Ctrl+C in Ollama terminal")
print("    - Press Ctrl+C in Backend terminal")
print("    - Press Ctrl+C in Frontend terminal")

confirm = input("\nHave you stopped all services? (yes/no): ").strip().lower()
if confirm != 'yes':
    print("Cancelled.")
    sys.exit(1)

removed_count = 0

# ============================================================================
# STEP 1: Clear ChromaDB Cache Directories
# ============================================================================

print("\n[STEP 1] Clearing ChromaDB cache...")

chroma_paths = [
    os.path.expanduser("~/.chroma"),
    os.path.expanduser("~/.local/share/chroma"),
    os.path.expanduser("~/AppData/Local/chroma"),
    os.path.expanduser("~/AppData/Roaming/chroma"),
    os.path.join(os.getcwd(), ".chroma"),
    "backend/.chroma"
]

for path in chroma_paths:
    if os.path.exists(path):
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            print(f"   ✓ Removed: {path}")
            removed_count += 1
        except PermissionError:
            print(f"   ⚠ Permission denied: {path}")
        except Exception as e:
            print(f"   ⚠ Error: {path} - {e}")
    else:
        print(f"   - Not found: {path}")

# ============================================================================
# STEP 2: Delete Uploaded Documents
# ============================================================================

print("\n[STEP 2] Clearing uploaded documents...")

upload_dir = "backend/uploaded_documents"
if os.path.exists(upload_dir):
    files = os.listdir(upload_dir)
    for file in files:
        file_path = os.path.join(upload_dir, file)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"   ✓ Deleted: {file}")
                removed_count += 1
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
                print(f"   ✓ Deleted directory: {file}")
                removed_count += 1
        except Exception as e:
            print(f"   ⚠ Error: {file} - {e}")
    
    if not files:
        print("   - Directory already empty")
else:
    print(f"   - Directory not found: {upload_dir}")
    print("   Creating directory...")
    os.makedirs(upload_dir, exist_ok=True)

# ============================================================================
# STEP 3: Clear Python Cache
# ============================================================================

print("\n[STEP 3] Clearing Python cache files...")

cache_patterns = [
    "backend/__pycache__",
    "frontend/__pycache__",
    "backend/utils/__pycache__",
    "frontend/components/__pycache__",
    "frontend/utils/__pycache__",
    "backend/.pytest_cache",
    "frontend/.pytest_cache"
]

for pattern in cache_patterns:
    if os.path.exists(pattern):
        try:
            if os.path.isdir(pattern):
                shutil.rmtree(pattern)
                print(f"   ✓ Removed: {pattern}")
                removed_count += 1
        except Exception as e:
            print(f"   ⚠ Error: {pattern} - {e}")

# ============================================================================
# STEP 4: Verify Cleanup
# ============================================================================

print("\n[STEP 4] Verifying cleanup...")

# Check ChromaDB
chroma_exists = False
for path in chroma_paths:
    if os.path.exists(path):
        chroma_exists = True
        print(f"   ⚠ Still exists: {path}")

if not chroma_exists:
    print("   ✓ ChromaDB cache fully cleared")

# Check uploaded documents
upload_files = []
if os.path.exists(upload_dir):
    upload_files = os.listdir(upload_dir)

if not upload_files:
    print(f"   ✓ Uploaded documents cleared")
else:
    print(f"   ⚠ Still has {len(upload_files)} files")

# ============================================================================
# COMPLETION
# ============================================================================

print("\n" + "=" * 80)
print(" " * 30 + "✅ RESET COMPLETE!")
print("=" * 80)

print(f"\nRemoved {removed_count} items")

print("\n📝 NEXT STEPS:")
print("   1. Start backend: cd backend && python app.py")
print("   2. Start frontend: cd frontend && streamlit run streamlit_app.py")
print("   3. Upload documents via UI")
print("   4. Chat should show ONLY new documents")

print("\n")


# ============================================================================
# FILE 2: backend/clear_database.py
# Clear database while system is running
# ============================================================================

import os
import sys
import glob
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print(" " * 15 + "CLEAR DATABASE (System Running)")
print("=" * 80)

deleted_count = 0

# ============================================================================
# STEP 1: Delete Uploaded Files
# ============================================================================

print("\n[STEP 1] Deleting uploaded documents...")

upload_dir = "uploaded_documents"

if os.path.exists(upload_dir):
    files = os.listdir(upload_dir)
    
    for file in files:
        file_path = os.path.join(upload_dir, file)
        try:
            os.remove(file_path)
            print(f"   ✓ Deleted: {file}")
            deleted_count += 1
        except Exception as e:
            print(f"   ✗ Error: {file} - {e}")
    
    if not files:
        print("   - Directory already empty")
else:
    print(f"   - Directory not found: {upload_dir}")

# ============================================================================
# STEP 2: Clear ChromaDB Collection
# ============================================================================

print("\n[STEP 2] Clearing ChromaDB collection...")

try:
    from chromadb_setup import initialize_chromadb
    import chromadb
    
    # Initialize ChromaDB
    collection = initialize_chromadb()
    
    # Get current count
    before_count = collection.count()
    print(f"   Current documents: {before_count}")
    
    # Get all document IDs
    all_data = collection.get()
    doc_ids = all_data.get('ids', [])
    
    # Delete all documents
    if doc_ids:
        print(f"   Deleting {len(doc_ids)} documents...")
        collection.delete(ids=doc_ids)
        deleted_count += len(doc_ids)
    
    # Verify deletion
    after_count = collection.count()
    print(f"   ✓ Documents after delete: {after_count}")
    
    if after_count == 0:
        print("   ✓ ChromaDB collection cleared successfully")
    else:
        print(f"   ⚠ Still has {after_count} documents")

except ImportError:
    print("   ⚠ chromadb_setup not found")
    print("   Make sure you're in backend directory")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# COMPLETION
# ============================================================================

print("\n" + "=" * 80)
print(" " * 30 + "✅ DATABASE CLEARED!")
print("=" * 80)

print(f"\nDeleted {deleted_count} items")

print("\n📝 NEXT STEPS:")
print("   1. Refresh browser (F5)")
print("   2. Go to Chat tab - should show 0 documents")
print("   3. Go to Upload tab")
print("   4. Upload new documents")
print("   5. Chat should work with new documents only")

print("\n")


# ============================================================================
# FILE 3: backend/verify_clean.py
# Verify system is clean
# ============================================================================

import os
from pathlib import Path

print("=" * 80)
print(" " * 20 + "VERIFY SYSTEM IS CLEAN")
print("=" * 80)

clean = True

# Check ChromaDB
print("\n[CHECK 1] ChromaDB Cache")
chroma_paths = [
    os.path.expanduser("~/.chroma"),
    os.path.expanduser("~/.local/share/chroma"),
    ".chroma",
    "backend/.chroma"
]

for path in chroma_paths:
    if os.path.exists(path):
        print(f"   ✗ Found: {path}")
        clean = False

if clean:
    print("   ✓ No ChromaDB cache found")

# Check uploaded documents
print("\n[CHECK 2] Uploaded Documents")
upload_dir = "backend/uploaded_documents"

if os.path.exists(upload_dir):
    files = os.listdir(upload_dir)
    if files:
        print(f"   ✗ Found {len(files)} files:")
        for f in files:
            print(f"     - {f}")
        clean = False
    else:
        print("   ✓ Upload directory is empty")
else:
    print(f"   ✗ Directory missing: {upload_dir}")
    clean = False

# Check ChromaDB contents
print("\n[CHECK 3] ChromaDB Database")
try:
    from chromadb_setup import initialize_chromadb
    
    collection = initialize_chromadb()
    count = collection.count()
    
    if count == 0:
        print(f"   ✓ ChromaDB is empty (0 documents)")
    else:
        print(f"   ✗ ChromaDB has {count} documents")
        clean = False

except Exception as e:
    print(f"   ⚠ Could not check: {e}")

# Summary
print("\n" + "=" * 80)

if clean:
    print(" " * 25 + "✅ SYSTEM IS CLEAN!")
    print("=" * 80)
    print("\nYou can now:")
    print("  1. Upload new documents")
    print("  2. Chat will only see new documents")
    print("  3. No old data will appear")
else:
    print(" " * 20 + "⚠️  SYSTEM STILL HAS DATA")
    print("=" * 80)
    print("\nTo fully clean:")
    print("  1. Stop all services (Ctrl+C)")
    print("  2. Run: python reset_chromadb.py")
    print("  3. Then restart services")

print("\n")