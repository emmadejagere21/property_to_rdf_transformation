import csv
import subprocess
import time
import os
import re
import shutil
import datetime
import pandas as pd
from rdflib import URIRef, BNode, Dataset
import matplotlib.pyplot as plt

from data_alteration import generate_graph_data, backup_data, restore_backup, remove_backup

#gewone tijd meten
#nodes, edges, triples, quads tellen
#probeer ook cpu usage time te meten
#RAM

mapping_files = [
    "rf_mapping.yml",
    "ng_mapping.yml",
    "sp_mapping.yml",
    "pgo_mapping.yml",
    "spg_mapping.yml",
    "rdfs_mapping.ttl"
]

node_sizes = [5000, 10000, 25000, 50000, 100000, 150000]
multipliers = [1, 5, 10, 15]

yatter_output_dir = "yatter_output"
mapper_output_dir = "mapper_output"
morph_output_dir = "morph_output"
mapper_jar = "rmlmapper-7.1.2-r374-all.jar"

os.makedirs(yatter_output_dir, exist_ok=True)
os.makedirs(mapper_output_dir, exist_ok=True)
os.makedirs(morph_output_dir, exist_ok=True)


def run_command(cmd):
    start_reg_time = time.time()
    start_cpu_time = time.process_time()

    try:
        subprocess.run(cmd, shell=True, check=True)

        end_reg_time = time.time()
        end_cpu_time = time.process_time()

        total_reg_time = end_reg_time - start_reg_time
        total_cpu_time = end_cpu_time - start_cpu_time
        return total_reg_time, total_cpu_time
    except subprocess.CalledProcessError as e:
        print(f"\n️Command failed:\n{cmd}")
        print(f"Error: {e}")
        return None

def analyze(file_path):
    f = open(file_path, "r")

    nodes = set()
    edges = set()
    named_node_patterns = set()
    total_nodes = 0
    total_triples = 0
    triple_count = 0
    quad_count = 0
    nested_triples = 0

    for line in f:
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        if "<<" in line:
            nested_triples += 1

        if line.endswith("."):
            total_triples += 1
            parts = line[:-1].strip().split()
            if len(parts) == 4:
                quad_count += 1
            elif len(parts) == 3:
                triple_count += 1

            if len(parts) >= 3:
                s = parts[0]
                p = parts[1]
                o = parts[2]

                nodes.add(s)
                nodes.add(o)
                total_nodes += 2

                edges.add((s, p, o))

                for term in [s, o]:
                    if re.search(r'/node/\d+', term):
                        named_node_patterns.add(term)
                    if re.search(r'/node_\d+', term):
                        named_node_patterns.add(term)
                    if re.search(r'/n\d+', term):
                        named_node_patterns.add(term)

    f.close()

    return {
        "nodes": len(nodes),
        "total_nodes": total_nodes,
        "edges": len(edges),
        "triples": triple_count,
        "quads": quad_count,
        "nested_triples": nested_triples,
        "total triples and quads": total_triples

    }
"""
def rdf_star_analysis(file_path):
    nested_triples = 0
    triple_count = 0
    total_nodes = 0
    nodes = set()
    edges = set()

    f = open(file_path, "r")
    for line in f:
        line = line.strip()

        if "<<" in line:
            nested_triples += 1

        if line.endswith("."):
            triple_count += 1

        parts = line.split()
        if len(parts) >= 3:
            s = parts[0]
            p = parts[1]
            o = parts[2]

            nodes.add(s)
            nodes.add(o)
            total_nodes += 2

            if not s.startswith("<<") and not o.startswith(">>"):
                edges.add((s, p, o))
    f.close()
    return {
        "nodes": len(nodes),
        "total_nodes": total_nodes,
        "edges": len(edges),
        "triples": triple_count,
        "nested_triples": nested_triples,
        "quads": 0

    }
"""
runs = []
backup_data()

for i in range(10):
    print(f"{'-'*10} RUN {i+1}/10 {'-'*10}")
    results = []

    for size in node_sizes:
        for multiplier in multipliers:
            total_edges = size * multiplier
            output_path = f"input/data_{size}_nodes_{multiplier}x_edges.json"
            print(f"\n Genereren van nieuwe data voor {size} nodes met {multiplier}x edges...")

            generate_graph_data(
                num_people=size // 2,
                num_movies=size // 2,
                num_relationships=total_edges,
                output_path=output_path
            )

            temp_data_json = "data.json"
            shutil.copyfile(output_path, temp_data_json)

            for mapping_file in mapping_files:
                base_name = os.path.splitext(mapping_file)[0]
                print(f"\n🔍 Verwerken van: {base_name} bij {size} nodes × {multiplier} edges")

                ext = "nq" if mapping_file == "ng_mapping.yml" else "nt"
                output_format = "N-QUADS" if ext == "nq" else "N-TRIPLES"

                morph_temp_output = os.path.join(morph_output_dir, f"{base_name}_output.{ext}")
                morph_output = os.path.join(morph_output_dir, f"{base_name}_{size}_{multiplier}x_output.{ext}")
                config_file = "config.ini"

                if mapping_file == "ng_mapping.yml":
                    morph_output = morph_output.replace(".nt", ".nq")
                    output_format = "N-QUADS"
                else:
                    output_format = "N-TRIPLES"

                config_content = f"""
                [CONFIGURATION]
                output_file = {morph_temp_output}
                output_format = {output_format}

                [map]
                mappings = {mapping_file}
                """.strip()

                with open(config_file, "w") as config:
                        config.write(config_content)

                if os.path.exists(morph_temp_output):
                    os.remove(morph_temp_output)

                morph_time, morph_cpu = run_command(f"python3 -m morph_kgc {config_file}")


                if morph_time is None or not os.path.exists(morph_temp_output):
                    print(f" Morph-KGC failed of geen output gevonden voor {base_name}, size={size}, multiplier={multiplier}")
                    continue

                shutil.move(morph_temp_output, morph_output)

                try:
                    #stats = rdf_star_analysis(morph_output) if base_name == "rdfs_mapping.ttl" else analyze(morph_output)
                    stats = analyze(morph_output)
                except Exception:
                    print(f" Analyse mislukt voor {base_name} bij {size} nodes × {multiplier} edges.")
                    continue

                results.append({
                    "algorithm": base_name,
                    "size": size,
                    "multiplier": multiplier,
                    "mapper_time": round(morph_time, 5),
                    "mapper_cpu": round(morph_cpu, 5),
                    **stats
                })
    runs.extend(results)
    restore_backup()
""""
                else:
                    yatter_output = os.path.join(yatter_output_dir, f"{base_name}_{size}_{multiplier}x_yatter.ttl")
                    yatter_cmd = f"python3 -m yatter -i {mapping_file} -o {yatter_output}"
                    yatter_time, yatter_cpu = run_command(yatter_cmd)
                    if yatter_time is None:
                        print(f"Yatter failed, {base_name}, size={size}, multiplier={multiplier}")
                        continue

                    mapper_output = os.path.join(mapper_output_dir, f"{base_name}_{size}_{multiplier}x_mapped.ttl")
                    mapper_cmd = f"java -Xmx14G -jar {mapper_jar} -m {yatter_output} -o {mapper_output}"
                    mapper_time, mapper_cpu = run_command(mapper_cmd)
                    if mapper_time is None:
                        print(f"RMLMapper failed, {base_name}, size={size}, multiplier={multiplier}")
                        continue

                    try:
                        stats = analyze(mapper_output)
                    except Exception:
                        print(f"Analyse mislukt voor {base_name} bij {size} nodes × {multiplier} edges.")
                        continue

                    results.append({
                        "algorithm": base_name,
                        "size": size,
                        "multiplier": multiplier,
                        "yatter_time": round(yatter_time * 1000, 3),
                        "yatter_cpu": round(yatter_cpu * 1000, 3),
                        "mapper_time": round(mapper_time * 1000, 3),
                        "mapper_cpu": round(mapper_cpu *1000, 3),
                        **stats
                    })
    runs.extend(results)
    restore_backup()
  """


#
#    print("\n Resultaten:")
#    print(f"{'Algorithm':<15} {'Size':<8} {'Mult':<6} {'Yatter (ms)':<12} {'Y_CPU (ms)':<12} {'Mapper (ms)':<12} {'M_CPU (ms)':<12} {'Unique nodes':<12} {'Edges':<8} "
#          f"{'Triples':<8} {'Quads':<8} {'Nested':<8} {'Total nodes':<8} ")

#   print("=" * 140)
#    for r in results:
#        print(
#            f"{r['algorithm']:<15} {r['size']:<8} {r['multiplier']:<6} {r['yatter_time']:<12} {r.get('yatter_cpu', '-'):<12} "
            #            f"{r['mapper_time']:<14} {r.get('mapper_cpu', '-'):<14} "
            #f"{r['nodes']:<10} {r['edges']:<8} {r['triples']:<8} {r['quads']:<8} {r.get('nested_triples', 0):<8} {r['total_nodes']:<8}")


def make_plots(file_path, prefix):
    df = pd.read_csv(file_path)

    df["config"] = df.apply(lambda r: f"node_{int(r['size'])}_edges_x{int(r['multiplier'])}", axis=1)

    df_t = df.drop(columns=["algorithm", "size", "multiplier"]).set_index("config").T
    df_t.index.name = "metric"

    for metric in df_t.index:
        plt.figure()
        df_t.loc[metric].plot(marker="o")
        plt.title(f"{prefix} - {metric}")
        plt.xlabel("config")
        plt.ylabel(metric)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f"new_plots/{prefix}_{metric}.png")
        plt.close()

def combined_metric_plot(file_template, label):
    for alg in df["algorithm"].unique():
        path = file_template.format(algorithm=alg)
        data = pd.read_csv(path)

        metrics = [col for col in data.columns if col not in ["algorithm", "size", "multiplier", "config"]]

        for metric in metrics:
            plt.figure(figsize=(14, 8))
            for size in sorted(data["size"].unique()):
                sub = data[data["size"] == size]
                plt.plot(sub["multiplier"], sub[metric], marker='o', label=f"{size} nodes")

            plt.title(f"{alg} - {label} - {metric}")
            plt.xlabel("Edge multiplier")
            plt.ylabel(metric)
            plt.legend(title="Node size")
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(f"plots/all_nodes_one_graph/{alg}_{label}_{metric}.png")
            plt.close()


def big_combined_plot(file_template, label):
    dfs = []
    for alg in df["algorithm"].unique():
        path = file_template.format(algorithm=alg)
        d = pd.read_csv(path)
        d["algorithm"] = alg
        d["config"] = d.apply(lambda r: f"node_{int(r['size'])}_edges_x{int(r['multiplier'])}", axis=1)
        dfs.append(d)

    full_df = pd.concat(dfs)
    metrics = [col for col in full_df.columns if col not in ["algorithm", "size", "multiplier", "config"]]

    for metric in metrics:
        plt.figure(figsize=(16, 8))
        for alg in full_df["algorithm"].unique():
            sub = full_df[full_df["algorithm"] == alg]
            plt.plot(sub["config"], sub[metric], marker='o', label=alg)

        plt.title(f"{label.capitalize()} - {metric}")
        plt.xlabel("Config (nodes × edges)")
        plt.ylabel(metric)
        plt.xticks(rotation=45, ha='right')
        plt.legend(title="Algorithm")
        plt.tight_layout()
        plt.savefig(f"new_plots/combined/{label}_{metric}.png")
        plt.close()

def per_algorithm_detailed_plot(file_template, label):
    for alg in df["algorithm"].unique():
        path = file_template.format(algorithm=alg)
        data = pd.read_csv(path)
        node_sizes = sorted(data["size"].unique())
        metrics = [col for col in data.columns if col not in ["algorithm", "size", "multiplier", "config"]]

        for metric in metrics:
            fig, axes = plt.subplots(len(node_sizes), 1, figsize=(10, 4 * len(node_sizes)), sharey=False)
            if len(node_sizes) == 1:
                axes = [axes]

            for ax, size in zip(axes, node_sizes):
                subset = data[data["size"] == size]
                ax.plot(subset["multiplier"], subset[metric], marker='o')
                ax.set_title(f"{alg} - {metric} - {size} nodes")
                ax.set_xlabel("Edge multiplier")
                ax.set_ylabel(metric)
                ax.grid(True)

            plt.tight_layout()
            plt.savefig(f"plots/per_algorithm/{alg}_{label}_{metric}.png")
            plt.close()

""""
if runs:
    df = pd.DataFrame(runs)
    group_cols = ["algorithm", "size", "multiplier"]
    average_df = df.groupby(group_cols).mean(numeric_only=True).reset_index()
    median_df = df.groupby(group_cols).median(numeric_only=True).reset_index()

    average_df.to_csv("results/average_results.csv", index=False)
    median_df.to_csv("results/median_results.csv", index=False)

    for algorithm in df["algorithm"].unique():
        avg_subset = average_df[average_df["algorithm"] == algorithm]
        med_subset = median_df[median_df["algorithm"] == algorithm]

        avg_subset.to_csv(f"results/average_{algorithm}.csv", index=False)
        med_subset.to_csv(f"results/median_{algorithm}.csv", index=False)

        big_combined_plot(f"results/average_{algorithm}.csv", f"{algorithm} - Average")
        big_combined_plot(f"results/median_{algorithm}.csv", f"{algorithm} - Median")

"""
df = pd.DataFrame(runs)

 #
 # -----------------------------------------------------opslaan naar csv bestand en plotten--------------------------------------------------------------
 #

group_cols = ["algorithm", "size", "multiplier"]
average_df = df.groupby(group_cols).mean(numeric_only=True).reset_index()
median_df = df.groupby(group_cols).median(numeric_only=True).reset_index()

average_df.round(6).to_csv("new_results/average_results.csv", index=False)
median_df.round(6).to_csv("new_results/median_results.csv", index=False)

for algorithm in df["algorithm"].unique():
    avg_subset = average_df[average_df["algorithm"] == algorithm]
    med_subset = median_df[median_df["algorithm"] == algorithm]

    avg_subset.to_csv(f"new_results/average_{algorithm}.csv", index=False)
    med_subset.to_csv(f"new_results/median_{algorithm}.csv", index=False)

    make_plots(f"new_results/average_{algorithm}.csv", f"{algorithm} - Average")
    make_plots(f"new_results/median_{algorithm}.csv", f"{algorithm} - Median")

    big_combined_plot(f"new_results/average_{algorithm}.csv", "average")
    big_combined_plot(f"new_results/median_{algorithm}.csv", "median")

    per_algorithm_detailed_plot(f"new_results/average_{algorithm}.csv", "average")
    per_algorithm_detailed_plot(f"new_results/median_{algorithm}.csv", "median")

print("-"*15 + "done" + "-"*15)
