# quantum-classification

Tools to download, organize and convert TCGA case folders into per-case multi-omics tables.

This repo contains small helpers and Python scripts to:
- download files listed in GDC manifests (bundled gdc-client helper),
- organize files into per-case folders (organizedTop10_*),
- create one-row-per-case multi-omics TSVs, and
- merge multiple per-run TSVs into a single dataset for downstream modelling.

## Quick checklist
- Download using a GDC manifest: `sh/install.sh`
- Organize downloaded files and build `organizedTop10_*`: `sh/organize.sh` (calls `py/organize.py`)
- Create a per-run multi-omics TSV: `py/create_multiomics.py`
- Optionally check which data categories are present per case: `py/check_datacategories.py`
- Merge per-run TSVs (tumor + normal): `py/merge_multiomics.py`

All examples assume you run commands from the repository root.

## Scripts reference and examples

### 1) Download files from a GDC manifest — `sh/install.sh`

Purpose: use the bundled download helper to fetch files listed in a GDC manifest.

Example:

```bash
bash sh/install.sh -m manifest/tumor_gdc_manifest.txt -d gdc_downloads_tumor
```

Options:
- `-m, --manifest PATH` : Path to a GDC manifest file (required).
- `-d, --dest DIR` : Destination directory for downloads (default: `gdc_downloads`).
- `-h, --help` : Show help and exit.

Notes:
- The script calls `tools/gdc-client` included in this repo. Ensure the binary is executable.

### 2) Organize files into per-case folders — `sh/organize.sh` (wraps `py/organize.py`)

Purpose: uncompress/move/rename downloaded files and run `py/organize.py` to build an `organizedTop10_*` tree with one folder per case.

Example:

```bash
bash sh/organize.sh -c csv/files_by_case_flat_all_gbm_tumor.csv -s top10gbm_tumor -t organizedTop10_tumor
```

Options:
- `-c, --csv PATH` : Flattened CSV mapping files to cases (default: `csv/files_by_case_flat.csv`).
- `-s, --source PATH` : Source folder containing downloaded/unpacked files (default: `top10gbm`).
- `-t, --target PATH` : Target organized directory (default: `organizedTop10`).
- `--downloads PATH` : If different from default downloads dir, pass it here (alias for `-d`).
- `--dry-run` : Print actions without performing them.
- `-h, --help` : Show usage.

If you already have an `organizedTop10_*` tree, you can skip this step.

### 3) Inspect which data categories exist per case — `py/check_datacategories.py`

Purpose: quick check of presence/absence of major TCGA data categories by inspecting the first-level subdirectories under each case folder.

Supported categories (defaults):
- `Copy Number Variation`
- `Simple Nucleotide Variation`
- `DNA Methylation`
- `Transcriptome Profiling`

Example:

```bash
python3 py/check_datacategories.py --root organizedTop10_tumor --out outputs/tumor_datacats.tsv
```

Options:
- `--root, -r` : organizedTop10 root directory (one folder per case) — required.
- `--out, -o` : Output TSV path — required.
- `--categories-json` : Optional JSON file to override category -> keyword lists.

Output: TSV with columns `case_id`, `has_Copy_Number_Variation`, `has_Simple_Nucleotide_Variation`, `has_DNA_Methylation`, `has_Transcriptome_Profiling`, and `missing` (semicolon-separated missing categories).

### 4) Create per-run multi-omics TSV — `py/create_multiomics.py`

Purpose: scan each case directory under a given `organizedTop10` root, load modalities where present, and produce:
- `<out>.tsv` : case-by-feature table (columns: `case_id`, `class`, then feature columns)
- `<out>_features_by_case.tsv` : transposed features-by-case (rows = features)
- `<out>_missing_files.tsv` : Per-case report showing whether specific loaders found files.

Example:

```bash
python3 py/create_multiomics.py --root organizedTop10_tumor --out outputs/tumor_all_gbm.tsv --label tumor
```

Options:
- `--root, -r` : Path to organizedTop10 root (required).
- `--out, -o` : Output TSV path (required).
- `--label, -l` : Class label to insert into the `class` column (default: `tumor`).

Notes and behavior:
- The script runs a set of per-modality loader functions: gene expression, miRNA, CNV, methylation, proteome (RPPA), and SNV. Features are prefixed by modality (e.g. `GeneExpr_`, `miRNA_`, `CNV_`, `Meth_`, `Prot_`, `SNV_`).
- If multiple aliquot files exist for the same modality, values are averaged across files.
- The `_missing_files.tsv` file gives a per-case flag for which loaders found files; use it to understand modality coverage.
- For large runs, redirect stdout/stderr to a log file to avoid filling your terminal. Example:

```bash
mkdir -p outputs/logs
python3 py/create_multiomics.py -r organizedTop10_tumor -o outputs/tumor_all_gbm.tsv -l tumor > outputs/logs/tumor_create.log 2>&1
```

### 5) Merge per-run TSVs — `py/merge_multiomics.py`

Purpose: combine multiple case-by-feature TSVs produced by `py/create_multiomics.py` into a single table. Columns are aligned by union; missing cells left as NaN.

Example:

```bash
python3 py/merge_multiomics.py outputs/tumor_all_gbm.tsv outputs/normal_all_gbm.tsv -o outputs/merged_all_gbm.tsv --on-duplicates keep-first
```

Options:
- `--out, -o` : Output merged TSV path (required).
- `--on-duplicates` : How to handle duplicate `case_id` across inputs: `error` (default), `keep-first`, or `keep-last`.

Notes:
- Use `--on-duplicates keep-first` if you expect the same `case_id` to appear in multiple inputs and want the first occurrence kept.

## Recommended workflow example (tumor + normal)

1) Download tumor files

```bash
bash sh/install.sh -m manifest/tumor_manifest.txt -d gdc_downloads_tumor
```

2) Organize tumor files and run create

```bash
bash sh/organize.sh -c csv/files_by_case_flat_all_gbm_tumor.csv -s top10gbm_tumor -t organizedTop10_tumor
python3 py/create_multiomics.py -r organizedTop10_tumor -o outputs/tumor_all_gbm.tsv -l tumor > outputs/logs/tumor_create.log 2>&1
```

3) Repeat for normal

```bash
bash sh/install.sh -m manifest/normal_manifest.txt -d gdc_downloads_normal
bash sh/organize.sh -c csv/files_by_case_flat_all_gbm_normal.csv -s top10gbm_normal -t organizedTop10_normal
python3 py/create_multiomics.py -r organizedTop10_normal -o outputs/normal_all_gbm.tsv -l normal > outputs/logs/normal_create.log 2>&1
```

4) Merge

```bash
python3 py/merge_multiomics.py outputs/tumor_all_gbm.tsv outputs/normal_all_gbm.tsv -o outputs/merged_all_gbm.tsv --on-duplicates keep-first
```

## Troubleshooting
- If a run is terminated unexpectedly with exit code 143, it received SIGTERM — this usually means the process was manually stopped or the environment killed it for time/maintenance reasons. For long runs, redirect logs and run in background (`nohup`) or run per-chunk tests first.
- For memory pressure issues, prefer working with the case-by-feature TSV (wide) rather than transposing it; the transposed features-by-case can be extremely wide.

## Development notes
- The per-modality loader functions are in `py/create_multiomics.py`. They attempt to be forgiving about header names and will try lowercase variants.
- If you want quieter runs, I can add a `--quiet` flag or replace prints with Python logging and a verbosity flag.

If you'd like, I can now:
- run `py/check_datacategories.py` on your `organizedTop10_tumor` and show the first 20 lines, or
- run a smoke test of `py/create_multiomics.py` on the first N cases and verify the outputs.

---

If you want any changes to wording or more examples (e.g., expected CSV layout), tell me which and I'll add them.

Overview
========
This repository contains scripts to download TCGA files from GDC manifests, organize them by case, build per-case multi-omics TSVs, and merge multiple per-run outputs into a single dataset.

High-level workflow
-------------------
1. Upload one or more GDC manifest files to the repo (or provide their path).
2. For each manifest: run `sh/install.sh` to download files.
3. Run `sh/organize.sh` to unpack/move files and call the Python organizer (`py/organize.py`).
4. Run `py/create_multiomics.py` to build a case-by-feature TSV for the run (label each run with `--label tumor|normal`).
5. (Optional) Run cleanup scripts (the repo includes helpers called by `sh/organize.sh`) to remove temporary files.
6. After you have two or more per-run multi-omics TSVs (for example `tumor.tsv` and `normal.tsv`), run `py/merge_multiomics.py` to merge them into a single table for downstream analysis.

Files and purpose
-----------------
- `sh/install.sh` - Download files from a GDC manifest using the bundled `tools/gdc-client`.
- `sh/organize.sh` - Pipeline wrapper: uncompress, move files, call `py/organize.py` and other processing scripts. Supports `--dry-run`.
- `py/organize.py` - Python script that reorganizes files into `organizedTop10/<case>/<category>/<data_type>/` using a flattened CSV.
- `py/create_multiomics.py` - Build a case-by-feature TSV. Outputs:
  - `<out>.tsv` : case-by-features (first column `case_id`, second column `class`)
  - `<out>_features_by_case.tsv` : features-by-case (first column `feature`)
  - `<out>_missing_files.tsv` : per-case per-loader presence report
- `py/merge_multiomics.py` - Merge multiple case-by-feature TSVs into one table.

Command reference
-----------------
All commands assume you run them from the repository root.

1) Download a manifest

- Basic usage (manifest required):

```bash
bash sh/install.sh -m path/to/gdc_manifest.txt
```

- Options:
  - `-m / --manifest PATH` : path to GDC manifest file (required)
  - `-d / --dest DIR` : destination folder for downloads (default: `gdc_downloads`)
  - `-h / --help` : show usage

2) Organize files (unpack/move and call organizer)

```bash
bash sh/organize.sh --csv csv/files_by_case_flat.csv --source top10gbm --target organizedTop10
```

- Options:
  - `-c / --csv PATH` : flattened CSV path (default: `csv/files_by_case_flat.csv`)
  - `-s / --source PATH` : source folder where files currently are (default: `top10gbm`)
  - `-t / --target PATH` : organized output dir (default: `organizedTop10`)
  - `--dry-run` : print commands without executing them
  - `-h / --help` : show usage

3) Create multi-omics per-run TSV

```bash
python3 py/create_multiomics.py --root organizedTop10 --out /path/to/tumor_run1.tsv --label tumor
```

- Options:
  - `--root, -r` : root directory containing one folder per case (e.g. `organizedTop10`)
  - `--out, -o` : output TSV path (required)
  - `--label, -l` : class label to write into the `class` column, e.g. `tumor` or `normal` (default `tumor`)

Outputs created:
- `<out>.tsv` — case-by-features, with columns `case_id`, `class`, then features
- `<out>_features_by_case.tsv` — transposed features-by-case
- `<out>_missing_files.tsv` — report showing which loaders found files per case

4) Repeat steps 1–3 for other manifests / labels

Do the same for a normal set, e.g.:

```bash
bash sh/install.sh -m manifest_normal.txt -d gdc_downloads_normal
bash sh/organize.sh -c csv/files_by_case_flat_normal.csv -s top10gbm_normal -t organizedTop10_normal
python3 py/create_multiomics.py -r organizedTop10_normal -o /path/to/normal_run1.tsv -l normal
```

5) Merge per-run TSVs (tumor + normal)

```bash
python3 py/merge_multiomics.py /path/to/tumor_run1.tsv /path/to/normal_run1.tsv --out /path/to/merged.tsv --on-duplicates keep-first
```

- Options:
  - `--out, -o` : output merged TSV path (required)
  - `--on-duplicates` : behavior for duplicate `case_id` values across inputs. One of:
    - `error` (default) — abort if duplicates are present
    - `keep-first` — keep the first occurrence and drop later duplicates
    - `keep-last` — keep the last occurrence and drop earlier duplicates

Example full workflow (tumor + normal)
--------------------------------------
1) Place manifests in `manifests/`:

```
manifests/tumor_manifest.txt
manifests/normal_manifest.txt
```

2) Download tumor:

```bash
bash sh/install.sh -m manifests/tumor_manifest.txt -d gdc_downloads_tumor
```

3) Organize tumor files and create CSV (assumes you have produced `csv/files_by_case_flat.csv` via your prior tooling):

```bash
bash sh/organize.sh -c csv/files_by_case_flat.csv -s top10gbm_tumor -t organizedTop10_tumor
python3 py/create_multiomics.py -r organizedTop10_tumor -o outputs/tumor_run1.tsv -l tumor
```

4) Repeat for normal:

```bash
bash sh/install.sh -m manifests/normal_manifest.txt -d gdc_downloads_normal
bash sh/organize.sh -c csv/files_by_case_flat_normal.csv -s top10gbm_normal -t organizedTop10_normal
python3 py/create_multiomics.py -r organizedTop10_normal -o outputs/normal_run1.tsv -l normal
```

5) Merge the two runs:

```bash
python3 py/merge_multiomics.py outputs/tumor_run1.tsv outputs/normal_run1.tsv -o outputs/merged.tsv --on-duplicates keep-first
```

Notes and tips
--------------
- The `py/create_multiomics.py` script will write a `_missing_files.tsv` next to your output; inspect that to see whether some loaders were absent for certain cases.
- If input TSVs have different columns, `py/merge_multiomics.py` will align them by the union of columns and fill missing values with empty (NaN) cells.
- If you expect many variants in file formats, consider running smaller test runs and inspecting the `_features_by_case.tsv` output to verify feature naming/prefixes.

Help / Troubleshooting
----------------------
- If a script complains about missing helper tools (e.g. `tools/gdc-client`), verify the file exists and is executable. `sh/install.sh` will try to make `tools/gdc-client` executable for you.
- For large datasets, operations may use a lot of memory when transposing very wide tables — prefer the case-by-feature table for model training.

If you'd like, I can:
- Add a `--dry-run` mode to `sh/install.sh` (currently `sh/organize.sh` supports `--dry-run`).
- Add examples of expected CSV layout or a small example dataset.
- Add a short wrapper script that chains the entire flow for a manifest and label.
