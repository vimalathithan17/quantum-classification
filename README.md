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
