import json
import random
from datetime import datetime, timedelta
import sys
import os
import shutil

def load_data():
    path = os.path.join(os.path.dirname(__file__), "data.json")
    f = open(path)
    try:
        data = json.load(f)
    finally:
        f.close()
    return data

def save_data(data, path):
    f = open(path, 'w')
    try:
        json.dump(data, f, indent=2)
    finally:
        f.close()

def backup_data():
    dir_path = os.path.dirname(__file__)
    original = os.path.join(dir_path, "data.json")
    backup = os.path.join(dir_path, "data_backup.json")
    shutil.copyfile(original, backup)

def restore_backup():
    dir_path = os.path.dirname(__file__)
    backup = os.path.join(dir_path, "data_backup.json")
    original = os.path.join(dir_path, "data.json")
    shutil.copyfile(backup, original)

import os

def remove_backup():
    path = os.path.join(os.path.dirname(__file__), "data_backup.json")
    if os.path.exists(path):
        os.remove(path)

def separate_data(data):
    nodes = [entry for entry in data if entry['type'] == 'node']
    relationships = [entry for entry in data if entry['type'] == 'relationship']
    return nodes, relationships

def get_next_ids(nodes, relationships):
    next_node_id = max((int(n['id']) for n in nodes if n['id'].isdigit()), default=0) + 1
    next_rel_id = max((int(r['id']) for r in relationships if r['id'].isdigit()), default=0) + 1
    return next_node_id, next_rel_id

def add_nodes(num_people, num_movies, next_node_id):
    new_nodes = []
    for _ in range(num_people):
        new_nodes.append({
            "type": "node",
            "id": str(next_node_id),
            "labels": ["Person"],
            "properties": {
                "name": f"Person_{next_node_id}"
            }
        })
        next_node_id += 1
    for _ in range(num_movies):
        new_nodes.append({
            "type": "node",
            "id": str(next_node_id),
            "labels": ["Movie"],
            "properties": {
                "title": f"Movie_{next_node_id}"
            }
        })
        next_node_id += 1
    return new_nodes, next_node_id

def create_random_relationships(num_relationships, person_nodes, movie_nodes, next_rel_id):
    new_relationships = []
    used_pairs = set()
    attempts = 0
    while len(new_relationships) < num_relationships and attempts < num_relationships * 10:
        person = random.choice(person_nodes)
        movie = random.choice(movie_nodes)
        pair_key = (person['id'], movie['id'])
        if pair_key in used_pairs:
            attempts += 1
            continue
        used_pairs.add(pair_key)
        date = datetime.now() - timedelta(days=random.randint(0, 365))
        new_relationships.append({
            "type": "relationship",
            "id": str(next_rel_id),
            "label": "WATCHED",
            "properties": {
                "date": date.strftime("%Y-%m-%d")
            },
            "start": person,
            "end": movie
        })
        next_rel_id += 1
    return new_relationships

def generate_graph_data(num_people, num_movies, num_relationships, output_path):
    data = load_data()
    nodes, relationships = separate_data(data)

    existing_people = [n for n in nodes if n['labels'] == ['Person']]
    existing_movies = [n for n in nodes if n['labels'] == ['Movie']]

    total_people = max(num_people, len(existing_people))
    total_movies = max(num_movies, len(existing_movies))

    next_node_id, _ = get_next_ids(nodes, relationships)
    if len(existing_people) < total_people or len(existing_movies) < total_movies:
        extra_nodes, next_node_id = add_nodes(total_people - len(existing_people), total_movies - len(existing_movies), next_node_id)
        nodes.extend(extra_nodes)
        existing_people.extend([n for n in extra_nodes if n['labels'] == ['Person']])
        existing_movies.extend([n for n in extra_nodes if n['labels'] == ['Movie']])

    sampled_people = random.sample(existing_people, num_people)
    sampled_movies = random.sample(existing_movies, num_movies)

    next_node_id, next_rel_id = get_next_ids(nodes, relationships)
    new_relationships = create_random_relationships(num_relationships, sampled_people, sampled_movies, next_rel_id)
    updated_data = sampled_people + sampled_movies + new_relationships
    save_data(updated_data, output_path)
    restore_backup()


def launch_gui():
    import tkinter as tk
    from tkinter import messagebox, filedialog

    def generate_from_gui():
        try:
            node_size = int(node_entry.get())
            multiplier = int(multiplier_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers.")
            return

        num_people = node_size // 2
        num_movies = node_size - num_people
        num_relationships = node_size * multiplier

        save_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Save updated data as..."
        )
        if not save_path:
            messagebox.showinfo("Cancelled", "Save operation cancelled.")
            return

        generate_graph_data(num_people, num_movies, num_relationships, save_path)
        messagebox.showinfo("Success", f"Data written to:\n{save_path}")
        root.quit()

    root = tk.Tk()
    root.title("Graph Data Generator")

    tk.Label(root, text="Total Node Size:").grid(row=0, column=0, padx=10, pady=5, sticky='e')
    tk.Label(root, text="Relationship Multiplier:").grid(row=1, column=0, padx=10, pady=5, sticky='e')

    node_entry = tk.Entry(root)
    multiplier_entry = tk.Entry(root)

    node_entry.grid(row=0, column=1, pady=5)
    multiplier_entry.grid(row=1, column=1, pady=5)

    generate_button = tk.Button(root, text="Generate", command=generate_from_gui)
    generate_button.grid(row=2, column=0, columnspan=2, pady=15)

    root.mainloop()

if __name__ == "__main__":
    launch_gui()
