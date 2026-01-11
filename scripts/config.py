import os
from dotenv import load_dotenv

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPTS_DIR)

dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path)

# --- DIRECTORIES ---
DATA_DIR = os.path.join(BASE_DIR, "data", "IR2025")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
TOOLS_DIR = r"C:\Users\user\Desktop\trec_eval" 

# --- FILES ---
DOCUMENTS_FILE = os.path.join(DATA_DIR, "documents.csv")
QUERIES_FILE = os.path.join(DATA_DIR, "queries.csv")
QRELS_FILE = os.path.join(DATA_DIR, "qrels.txt")

# --- EXECUTABLES ---
TREC_EVAL_PATH = os.path.join(TOOLS_DIR, "trec_eval.exe")

# --- ELASTICSEARCH SETTINGS ---
INDEX_NAME = "ir2025_documents"
RUN_NAME = "elasticsearch_bm25"

# --- CREDENTIALS ---
ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
ES_USERNAME = os.getenv("ES_USERNAME", "elastic")
ES_PASSWORD = os.getenv("ES_PASSWORD")