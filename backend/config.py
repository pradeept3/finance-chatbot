import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DEBUG = False
    TESTING = False
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    JSON_SORT_KEYS = False

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    FLASK_ENV = 'development'
    CHROMADB_PATH = os.getenv('CHROMADB_PATH', './chroma_db')
    DATA_DIR = os.getenv('DATA_DIR', './data/finance_docs')
    CHUNK_SIZE = 1000
    MAX_RESULTS = 5

class ProductionConfig(Config):
    DEBUG = False
    CHROMADB_PATH = os.getenv('CHROMADB_PATH', '/data/chroma_db')
    DATA_DIR = os.getenv('DATA_DIR', '/data/finance_docs')

config = DevelopmentConfig if os.getenv('FLASK_ENV') == 'development' else ProductionConfig