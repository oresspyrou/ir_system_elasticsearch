import os
from dotenv import load_dotenv

load_dotenv()

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

BASE_DIR = os.path.dirname(SCRIPTS_DIR)

DATA_DIR = os.path.join(BASE_DIR, "data", "IR2025")
RESULTS_DIR = os.path.join(BASE_DIR, "results")

TOOLS_DIR = r"C:\Users\user\Desktop\trec_eval" 

DOCUMENTS_FILE = os.path.join(DATA_DIR, "documents.csv")
QUERIES_FILE = os.path.join(DATA_DIR, "queries.csv")
QRELS_FILE = os.path.join(DATA_DIR, "qrels.txt")

TREC_EVAL_PATH = os.path.join(TOOLS_DIR, "trec_eval.exe")

INDEX_NAME = "ir2025_documents"
RUN_NAME = "elasticsearch_bm25"
ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")