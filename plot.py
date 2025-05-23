import pandas as pd
import matplotlib.pyplot as plt
import os

df = pd.read_csv("new_results/average_results.csv")

df['algorithm'] = df['algorithm'].str.strip()

df['custom_label'] = df['size'].astype(str) + "nodesx" + df['multiplier'].astype(str) + "multiplier"

columns_to_plot = df.select_dtypes(include='number').columns.tolist()

algorithms = df['algorithm'].unique()

colors = {
    'ng_mapping': 'black',
    'pgo_mapping': 'red',
    'rdfs_mapping': 'orange',
    'rf_mapping': 'purple',
    'sp_mapping': 'blue',
    'spg_mapping': 'green'
}

output_dir = "final_plots"
os.makedirs(output_dir, exist_ok=True)

for col in columns_to_plot:
    plt.figure(figsize=(12, 6))
    for algo in algorithms:
        subset = df[df['algorithm'] == algo].sort_values(by=['size', 'multiplier'])
        plt.plot(
            subset['custom_label'],
            subset[col],
            marker='o',
            label=algo,
            color=colors.get(algo, None)
        )
    plt.title(f"{col} vs Nodes x Multiplier by Algorithm")
    plt.xlabel("Nodes x Multiplier")
    plt.ylabel(col)
    plt.xticks(rotation=45, ha='right')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    safe_col_name = col.replace(" ", "_").replace("/", "_")
    filepath = os.path.join(output_dir, f"{safe_col_name}_vs_multiplier.png")
    plt.savefig(filepath)
    plt.close()
