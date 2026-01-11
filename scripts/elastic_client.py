from elasticsearch import Elasticsearch
from pprint import pprint
import sys
import config


class Search:
    def __init__(self):
        host = config.ES_HOST
        username = config.ES_USERNAME
        password = config.ES_PASSWORD

        missing = [var for var, val in [("ES_HOST", host), ("ES_USERNAME", username), ("ES_PASSWORD", password)] if not val]
        if missing:
            print(f"Missing configuration variables: {', '.join(missing)}")
            sys.exit(1)

        self.es = Elasticsearch(
            host,
            basic_auth=(username, password),
            verify_certs=False
        )

        try:
            if self.es.ping():
                print("Connected successfully to Elasticsearch!")
            else:
                print("Connection failed! Check server status.")
                sys.exit(1)
            info = self.es.info()
            pprint(info)
        except Exception as e:
            print(f"Error connecting to Elasticsearch: {e}")
            sys.exit(1)

if __name__ == "__main__":
    s = Search()

