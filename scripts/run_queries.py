import os
import pandas as pd
from elastic_client import Search
import urllib3
import config  

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
#ggs

def search_query(es, query_text, k=20):
    response = es.search(
        index=config.INDEX_NAME,
        body={
            "query": {"match": {"Text": query_text}},
            "size": k
        }
    )
    return response['hits']['hits']


def main():
    os.makedirs(config.RESULTS_DIR, exist_ok=True)

    s = Search()
    es = s.es

    queries_df = pd.read_csv(config.QUERIES_FILE)

    before = len(queries_df)
    queries_df = queries_df.drop_duplicates(subset=["ID", "Text"])
    after = len(queries_df)
    print(f"🔎 Loaded {after} unique queries (removed {before - after} duplicates)")

    top_k_list = [20, 30, 50]
    
    run_name = config.RUN_NAME

    for k in top_k_list:
        trec_lines = []

        for _, row in queries_df.iterrows():
            query_id = row["ID"]
            query_text = row["Text"]

            hits = search_query(es, query_text, k=k)

            seen_ids = set()
            unique_count = 0

            for rank, hit in enumerate(hits, start=1):
                doc_id = (
                    hit['_source'].get('ID')
                    if '_source' in hit
                    else hit.get('_id')
                )

                if doc_id in seen_ids:
                    continue

                seen_ids.add(doc_id)
                unique_count += 1

                line = f"{query_id} Q0 {doc_id} {unique_count} {hit['_score']} {run_name}"
                trec_lines.append(line)

                if unique_count >= k:
                    break 

        output_file = os.path.join(config.RESULTS_DIR, f"results_top{k}_trec.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(trec_lines))

        print(f"TREC-ready results for top {k} saved to {output_file}")


if __name__ == "__main__":
    main()






