import pandas as pd
from elasticsearch import Elasticsearch, helpers
import urllib3
import config 

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


es = Elasticsearch(
    config.ES_HOST,
    basic_auth=(config.ES_USERNAME, config.ES_PASSWORD),
    verify_certs=False
)

if not es.indices.exists(index=config.INDEX_NAME):
    es.indices.create(
        index=config.INDEX_NAME,
        body={
            "mappings": {
                "properties": {
                    "ID": {"type": "keyword"},
                    "Text": {"type": "text", "analyzer": "english"}
                }
            }
        }
    )
    print(f"Index '{config.INDEX_NAME}' δημιουργήθηκε!")
else:
    print(f"ℹIndex '{config.INDEX_NAME}' υπάρχει ήδη.")

print(f"Reading documents from: {config.DOCUMENTS_FILE}")
df = pd.read_csv(config.DOCUMENTS_FILE)

actions = [
    {
        "_index": config.INDEX_NAME, 
        "_id": row["ID"],
        "_source": {
            "ID": row["ID"],
            "Text": row["Text"]
        }
    }
    for _, row in df.iterrows()
]

helpers.bulk(es, actions)

es.indices.refresh(index=config.INDEX_NAME)

print(f"Εισαγωγή {len(actions)} documents ολοκληρώθηκε!")
