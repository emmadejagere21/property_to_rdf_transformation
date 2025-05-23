from os import WCONTINUED

import numpy as np
import pandas as pd
import os

input_dir = "new_results"
output_dir = "new_latex"
os.makedirs(output_dir, exist_ok=True)

csv_files = [
    "average_rf_mapping.csv",
    "median_rf_mapping.csv",
    "average_ng_mapping.csv",
    "median_ng_mapping.csv",
    "average_sp_mapping.csv",
    "median_sp_mapping.csv",
    "average_pgo_mapping.csv",
    "median_pgo_mapping.csv",
    "average_spg_mapping.csv",
    "median_spg_mapping.csv",
    "average_rdfs_mapping.csv",
    "median_rdfs_mapping.csv",
    "average_results.csv",
    "median_results.csv"
]

time_columns = ["mapper_time"]
six_decimal_columns = ["mapper_cpu"]
three_decimal_columns = ["yatter_cpu"]
int_columns = ["triples", "nodes", "edges", "total_nodes", "quads", "total triples and quads"]

for csv_file in csv_files:
    input_path = os.path.join(input_dir, csv_file)
    output_filename = os.path.splitext(csv_file)[0] + ".tex"
    output_path = os.path.join(output_dir, output_filename)

    df = pd.read_csv(input_path)

    for col in df.columns:
        if col in six_decimal_columns and col in df:
            continue
        elif col in three_decimal_columns and col in df:
            df[col] = df[col].ceil(3)
        elif col in time_columns and col in df:
            df[col] = df[col].round(3)
        elif col in int_columns and col in df:
            df[col] = np.ceil(df[col])
            df[col] = df[col].astype(int)

    with open(output_path, "w") as f:
        f.write(df.to_latex(index=False, float_format="%.4f"))
