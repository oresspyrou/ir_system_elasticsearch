import os
import subprocess
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

trec_eval_path = r"C:\Users\user\Desktop\trec_eval\trec_eval.exe"  
qrels_path = r"C:\Users\user\Desktop\SAP_1\data\IR2025\qrels.txt"  
results_folder = r"C:\Users\user\Desktop\SAP_1\results"            
output_folder = results_folder                                     


trec_files = [f for f in os.listdir(results_folder) if f.endswith("_trec.txt")]

for results_file in trec_files:
    input_results_path = os.path.join(results_folder, results_file)

    k = results_file.split("_")[1][3:]

    output_file_path = os.path.join(output_folder, f"eval_top{k}.txt")

    with open(output_file_path, "w", encoding="utf-8") as out_file:
        subprocess.run(
            [trec_eval_path, qrels_path, input_results_path],
            stdout=out_file,
            stderr=subprocess.DEVNULL
        )

    print(f"Evaluation for {results_file} saved to {output_file_path}")


