import os
import subprocess
import urllib3
import config 

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


trec_files = [f for f in os.listdir(config.RESULTS_DIR) if f.endswith("_trec.txt")]

if not trec_files:
    print(f"Δεν βρέθηκαν αρχεία *_trec.txt στον φάκελο: {config.RESULTS_DIR}")

for results_file in trec_files:
    input_results_path = os.path.join(config.RESULTS_DIR, results_file)

    k = results_file.split("_")[1][3:]

    output_file_path = os.path.join(config.RESULTS_DIR, f"eval_top{k}.txt")

    with open(output_file_path, "w", encoding="utf-8") as out_file:
        subprocess.run(
            [config.TREC_EVAL_PATH, config.QRELS_FILE, input_results_path],
            stdout=out_file,
            stderr=subprocess.DEVNULL
        )

    print(f"Evaluation for {results_file} saved to {output_file_path}")


