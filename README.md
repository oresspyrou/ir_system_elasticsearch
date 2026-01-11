# Αναλυτικό Τεχνικό Report - Elasticsearch Information Retrieval Pipeline

## 1. Επισκόπηση του Έργου

Αυτό το έργο υλοποιεί ένα **πλήρες σύστημα Information Retrieval (IR)** που χρησιμοποιεί **Elasticsearch** για την αναζήτηση και κατάταξη εγγράφων βάσει συνάφειας με queries. Το σύστημα περιλαμβάνει:

- **Indexing**: Καταχώρηση εγγράφων σε Elasticsearch
- **Searching**: Εκτέλεση queries και ανάκτηση top-k αποτελεσμάτων
- **Evaluation**: Αξιολόγηση της απόδοσης του συστήματος χρησιμοποιώντας TREC eval

---

## 2. Δομή δεδομένων και ρόλος αρχείων

### 2.1 Δεδομένα Εισόδου

```
data/IR2025/
├── documents.csv      → Τα έγγραφα που θα ευρετηριοποιηθούν (ID, Text)
├── queries.csv        → Οι queries που θα αναζητηθούν (ID, Text)
├── qrels.txt          → Relevant judgments (ground truth για αξιολόγηση)
└── qrels.csv          → Ίδια σε CSV format
```

**Τι περιέχουν:**
- **documents.csv**: Χιλιάδες τεκμήρια με ID και κείμενο που θα αναζητηθούν
- **queries.csv**: Queries που χρήστες θέλουν να βρουν
- **qrels.txt**: Η "σωστή απάντηση" - ποια έγγραφα είναι σχετικά με κάθε query (χρησιμοποιείται για αξιολόγηση)

### 2.2 Δεδομένα Εξόδου

```
results/
├── results_top20_trec.txt    → Αποτελέσματα για top-20 έγγραφα
├── results_top30_trec.txt    → Αποτελέσματα για top-30 έγγραφα
├── results_top50_trec.txt    → Αποτελέσματα για top-50 έγγραφα
├── eval_top20.txt            → Αξιολόγηση top-20 (precision, recall κλπ)
├── eval_top30.txt            → Αξιολόγηση top-30
└── eval_top50.txt            → Αξιολόγηση top-50
```

---

## 3. Κύρια Κομμάτια του Project

### 3.1 ΒΗΜΑ 1: Indexing Εγγράφων (`index_documents.py` & `elastic_client.py`)

**Τι κάνει:** Αποθηκεύει όλα τα έγγραφα σε Elasticsearch, δημιουργώντας έναν **ευρετήριο (index)**.

**Κλειδιακός κώδικας:**
```python

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

actions = [
    {
        "_index": INDEX_NAME,
        "_id": row["ID"],
        "_source": {"ID": row["ID"], "Text": row["Text"]}
    }
    for _, row in df_docs.iterrows()
]
helpers.bulk(es, actions)
```

**Γιατί είναι σημαντικό:**
- Το field `ID` είναι `keyword` → δεν tokenizεται, ώστε να μπορεί να αναφορά στο document uniquely
- Το field `Text` είναι `text` με English analyzer → σπάει το κείμενο σε λέξεις και εφαρμόζει stemming (π.χ. "running" → "run")
- Η `refresh` εντολή κάνει τα έγγραφα αμέσως αναζητήσιμα

---

### 3.2 ΒΗΜΑ 2: Searching & TREC Formatting (`run_queries.py` & `run_pipeline.py`)

**Τι κάνει:** Για κάθε query, εκτελεί αναζήτηση στο Elasticsearch και αποθηκεύει τα αποτελέσματα σε **TREC format** (το standard format για IR αξιολόγηση).

#### 3.2.1 Η Αναζήτηση (BM25 Algorithm)

```python
def search_query(es, query_text, k=20):
    response = es.search(
        index="ir2025_documents",
        body={
            "query": {"match": {"Text": query_text}},  # BM25 είναι το default
            "size": k                                   
        }
    )
    return response['hits']['hits']
```

**Τι σημαίνει:**
- **BM25**: Το default scoring algorithm του Elasticsearch. Κοιτάει τη συχνότητα λέξεων και την εμφάνισή τους σε documents
- **size=k**: Ζητάμε τα top-20, top-30 ή top-50 documents

#### 3.2.2 Deduplication & TREC Output

```python
seen_ids = set()
unique_count = 0

for rank, hit in enumerate(hits, start=1):
    doc_id = hit['_source'].get('ID')
    
    if doc_id in seen_ids:
        continue
    
    seen_ids.add(doc_id)
    unique_count += 1
    
    line = f"{query_id} Q0 {doc_id} {unique_count} {hit['_score']} {run_name}"
    trec_lines.append(line)
    
    if unique_count >= k:
        break
```

**Γιατί deduplication:**
- Μερικές φορές ο Elasticsearch επιστρέφει το ίδιο document δύο φορές με διαφορετικό score
- Θέλουμε **μόνο k μοναδικά documents**

#### 3.2.3 TREC Format Εξήγηση

Παράδειγμα αποτελέσματος:
```
Q01 Q0 193378 1 764.02673 elasticsearch_bm25
Q01 Q0 193373 2 273.72284 elasticsearch_bm25
Q01 Q0 205685 3 244.1519 elasticsearch_bm25
```

**Κάθε πεδίο:**
- `Q01` = Query ID
- `Q0` = Placeholder (standard TREC format, δεν έχει σημασία)
- `193378` = Document ID που ανακτήθηκε
- `1` = Rank (position) - 1st, 2nd, 3rd κλπ
- `764.02673` = Relevance score (όσο μεγαλύτερο, τόσο πιο σχετικό)
- `elasticsearch_bm25` = Όνομα του run (για tracking)

---

### 3.3 ΒΗΜΑ 3: Αξιολόγηση (`run_trec_eval.py`)

**Τι κάνει:** Συγκρίνει τα αποτελέσματά μας με την ground truth (`qrels.txt`) και υπολογίζει μετρικές απόδοσης.

```python
subprocess.run(
    [TREC_EVAL_PATH, QRELS_PATH, INPUT_RESULTS_PATH],
    stdout=output_file
)
```

**Παράδειγμα αξιολόγησης output:**
```
runid                     all    elasticsearch_bm25
num_q                     all           10
num_ret                   all           50
num_rel                   all           20
num_rel_ret               all           15

map                       all         0.5234
p_10                      all         0.7000
recall_100                all         0.8500
```

**Κύρια metrics:**
- **MAP (Mean Average Precision)**: Μέσος όρος precision στα relevant documents
- **P_10**: Accuracy στα πρώτα 10 αποτελέσματα
- **Recall**: Πόσα από τα σχετικά documents βρήκαμε

---

## 4. Ροή Εκτέλεσης

```
┌─────────────────────────────────────────────────┐
│ 1. INDEX DOCUMENTS                              │
│    - Διαβάζει documents.csv                     │
│    - Δημιουργεί Elasticsearch index             │
│    - Εισάγει όλα τα documents με BM25 mapping   │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│ 2. RUN QUERIES                                  │
│    - Διαβάζει queries.csv                       │
│    - Για κάθε query: αναζήτηση top-20/30/50     │
│    - Deduplication των αποτελεσμάτων            │
│    - Αποθήκευση σε TREC format                  │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│ 3. EVALUATE RESULTS                             │
│    - Σύγκριση με qrels.txt                      │
│    - Υπολογισμός precision, recall, MAP κλπ     │
│    - Αποθήκευση metrics σε eval_top*.txt        │
└─────────────────────────────────────────────────┘
```

---

## 5. Τεχνικές Λεπτομέρειες

### 5.1 Elasticsearch Connectivity

**Αρχείο:** `elastic_client.py`

Χρησιμοποιεί:
- **SSL Certificate Verification Disabled**: `verify_certs=False` (για development)
- **Basic Authentication**: username/password από `.env` file
- **Connection Check**: `es.ping()` επαληθεύει τη σύνδεση

### 5.2 Data Processing

**Deduplication των queries:**
```python
queries_df = queries_df.drop_duplicates(subset=["ID", "Text"])
```
Αφαιρεί duplicate queries πριν την αναζήτηση

**Deduplication των αποτελεσμάτων:**
Αφαιρεί duplicate documents από τα αποτελέσματα

### 5.3 Multiple Top-K Evaluations

Ο κώδικας τρέχει **3 διαφορετικά scenarios**:
- **top-20**: Τα 20 καλύτερα αποτελέσματα ανά query
- **top-30**: Τα 30 καλύτερα αποτελέσματα ανά query
- **top-50**: Τα 50 καλύτερα αποτελέσματα ανά query

Αυτό επιτρέπει σύγκριση της απόδοσης σε διαφορετικές "cut-offs"

---

## 6. Κύρια Challenges και Λύσεις

| Challenge | Λύση |
|-----------|------|
| Τα documents δεν είναι αμέσως searchable | Χρήση `es.indices.refresh()` μετά το bulk insert |
| Duplicate results από Elasticsearch | Tracking με `seen_ids` set |
| Duplicate queries στο input | `drop_duplicates()` στο DataFrame |
| Δεν ξέρουμε την ποιότητα αποτελεσμάτων | TREC eval σύγκριση με qrels ground truth |
| Πολλά queries × πολλά documents = σχετικά αργά | Χρήση Elasticsearch (full-text engine) για efficiency |

---

## 7. Αρχιτεκτονική του Συστήματος

```
┌─────────────────────────────────────────────┐
│         Python Scripts                      │
├─────────────────────────────────────────────┤
│ • elastic_client.py    (Elasticsearch API)  │
│ • index_documents.py   (Indexing)           │
│ • run_queries.py       (Search)             │
│ • run_trec_eval.py     (Evaluation)         │
│ • run_pipeline.py      (End-to-end)         │
└────────────┬────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────┐
│    Elasticsearch Server (BM25 Engine)       │
│    - Index: ir2025_documents                │
│    - Documents: με ID + Text fields         │
└────────────┬────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────┐
│         Data Files                          │
├─────────────────────────────────────────────┤
│ Input:                                      │
│ • documents.csv → Ευρετηριοποίηση           │
│ • queries.csv → Αναζήτηση                   │
│ • qrels.txt → Αξιολόγηση                    │
│                                             │
│ Output:                                     │
│ • results_top*.txt → TREC format            │
│ • eval_top*.txt → Metrics                   │
└─────────────────────────────────────────────┘
```

---

## 8. Συμπεράσματα

Αυτό είναι ένα **πλήρες Information Retrieval pipeline** που:
 Δεξιά ευρετηριοποιεί εγγράφα σε Elasticsearch  
 Εκτελεί αναζητήσεις με BM25 scoring  
 Παράγει TREC-compliant αποτελέσματα  
 Αξιολογεί την απόδοση έναντι ground truth  


