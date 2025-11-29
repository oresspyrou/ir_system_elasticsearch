import os
import time
import pandas as pd
import subprocess
import urllib3
from elasticsearch import Elasticsearch, helpers
from elastic_client import Search
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()
ES_USER = os.getenv("ES_USERNAME")
ES_PASSWORD = os.getenv("ES_PASSWORD")
ES_HOST = os.getenv("ES_HOST")

INDEX_NAME = "ir2025_documents"
DOCS_CSV = r"C:\Users\user\Desktop\SAP_1\data\IR2025\documents.csv"
QUERIES_CSV = r"C:\Users\user\Desktop\SAP_1\data\IR2025\queries.csv"
RESULTS_DIR = r"C:\Users\user\Desktop\SAP_1\results"
os.makedirs(RESULTS_DIR, exist_ok=True)

TREC_EVAL_PATH = r"C:\Users\user\Desktop\trec_eval\trec_eval.exe"
QRELS_PATH = r"C:\Users\user\Desktop\SAP_1\data\IR2025\qrels.txt"

print("🔹 Connecting to Elasticsearch...")
es = Elasticsearch(
    ES_HOST,
    basic_auth=(ES_USER, ES_PASSWORD),
    verify_certs=False
)

if not es.indices.exists(index=INDEX_NAME):
    es.indices.create(
        index=INDEX_NAME,
        body={
            "mappings": {
                "properties": {
                    "ID": {"type": "keyword"},
                    "Text": {"type": "text", "analyzer": "english"}
                }
            }
        }
    )
    print(f"Index '{INDEX_NAME}' created!")
else:
    print(f"ℹIndex '{INDEX_NAME}' already exists.")

df_docs = pd.read_csv(DOCS_CSV)
actions = [
    {
        "_index": INDEX_NAME,
        "_id": row["ID"],
        "_source": {"ID": row["ID"], "Text": row["Text"]}
    }
    for _, row in df_docs.iterrows()
]
helpers.bulk(es, actions)

es.indices.refresh(index=INDEX_NAME)
print(f"Inserted {len(actions)} documents and refreshed index.")

def search_query(es_client, query_text, k=20):
    response = es_client.search(
        index=INDEX_NAME,
        body={
            "query": {"match": {"Text": query_text}},
            "size": k,
            "sort": ["_score"]
        }
    )
    return response['hits']['hits']

df_queries = pd.read_csv(QUERIES_CSV)
df_queries = df_queries.drop_duplicates(subset=["ID", "Text"])
print(f"Loaded {len(df_queries)} unique queries")

TOP_K_LIST = [20, 30, 50]
RUN_NAME = "elasticsearch_bm25"

for k in TOP_K_LIST:
    trec_lines = []
    for _, row in df_queries.iterrows():
        query_id = row["ID"]
        query_text = row["Text"]
        hits = search_query(es, query_text, k=k)

        seen_ids = set()
        unique_count = 0
        for rank, hit in enumerate(hits, start=1):
            doc_id = hit['_source'].get('ID') if '_source' in hit else hit.get('_id')
            if doc_id in seen_ids:
                continue
            seen_ids.add(doc_id)
            unique_count += 1
            line = f"{query_id} Q0 {doc_id} {unique_count} {hit['_score']} {RUN_NAME}"
            trec_lines.append(line)
            if unique_count >= k:
                break

    output_file = os.path.join(RESULTS_DIR, f"results_top{k}_trec.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(trec_lines))
    print(f"TREC-ready results for top {k} saved to {output_file}")

trec_files = sorted([f for f in os.listdir(RESULTS_DIR) if f.endswith("_trec.txt")],
                    key=lambda x: int(x.split("_")[1][3:]))
for results_file in trec_files:
    input_results_path = os.path.join(RESULTS_DIR, results_file)
    k_val = results_file.split("_")[1][3:]
    output_file_path = os.path.join(RESULTS_DIR, f"eval_top{k_val}.txt")
    with open(output_file_path, "w", encoding="utf-8") as out_file:
        subprocess.run([TREC_EVAL_PATH, QRELS_PATH, input_results_path],
                       stdout=out_file, stderr=subprocess.DEVNULL)
    print(f"Evaluation for {results_file} saved to {output_file_path}")

print("Pipeline completed successfully!")



