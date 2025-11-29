import pandas as pd
from elasticsearch import Elasticsearch, helpers
from dotenv import load_dotenv
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()
ES_USER = os.getenv("ES_USERNAME")
ES_PASSWORD = os.getenv("ES_PASSWORD")
ES_HOST = os.getenv("ES_HOST")

es = Elasticsearch(
    ES_HOST,
    basic_auth=(ES_USER, ES_PASSWORD),
    verify_certs=False
)

index_name = "ir2025_documents"

if not es.indices.exists(index=index_name):
    es.indices.create(
        index=index_name,
        body={
            "mappings": {
                "properties": {
                    "ID": {"type": "keyword"},
                    "Text": {"type": "text", "analyzer": "english"}
                }
            }
        }
    )
    print(f"Index '{index_name}' δημιουργήθηκε!")
else:
    print(f"ℹIndex '{index_name}' υπάρχει ήδη.")

df = pd.read_csv(r"C:\Users\user\Desktop\SAP_1\data\IR2025\documents.csv")

actions = [
    {
        "_index": index_name,
        "_id": row["ID"],
        "_source": {
            "ID": row["ID"],
            "Text": row["Text"]
        }
    }
    for _, row in df.iterrows()
]

helpers.bulk(es, actions)

print(f"Εισαγωγή {len(actions)} documents ολοκληρώθηκε!")

