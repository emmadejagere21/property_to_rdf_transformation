# property_to_rdf_transformation

# property_to_rdf_transformation

This project provides tools for transforming property graph data (in JSON format) into RDF using Morph-KGC, along with utility scripts for data manipulation, visualization, and formatting.

## Features

- Modify and update property graph data (`data_alteration.py`)
- Backup graph data to JSON (`data_backup.json`)
- Convert CSV files to LaTeX tables (`csvtolatex.py`)
- Visualize property graphs (`plot.py`)
- Main orchestration script for processing and transformation (`main.py`)

## Requirements

- Python 3.8 or higher
- Morph-KGC

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/emmadejagere21/property_to_rdf_transformation.git
cd property_to_rdf_transformation
```
### 2. Install Morph-KGC
```bash
pip install morph-kgc
```
### 3. To run script
```bash
python main.py
```
Other scripts:

- data_alteration.py: Edit or update JSON graph data
- csvtolatex.py: Convert a CSV file to LaTeX format
- plot.py: Visualize the data graphically

## Data Format

Sample JSON files (data.json, data_backup.json) include nodes (e.g., Movies, People) and relationships (e.g., WATCHED) for demonstration.
