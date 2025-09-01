import os
import glob
import argparse
import numpy as np
import pandas as pd


def find_files(patient_dir, patterns):
    files = []
    for p in patterns:
        files.extend(glob.glob(os.path.join(patient_dir, '**', f'*{p}'), recursive=True))
    # keep unique and sorted for determinism
    return sorted(list(dict.fromkeys(files)))


def _series_from_files(files, feature_col, value_col, numeric=True):
    """Read multiple files that have (feature_col, value_col) and return a Series (feature -> mean value).
    If numeric=True, convert values to float and ignore non-numeric / NA.
    """
    series_list = []
    for f in files:
        try:
            df = pd.read_csv(f, sep='\t', header=0, dtype=str)
        except Exception:
            # fallback to no header two-column
            try:
                df = pd.read_csv(f, sep='\t', header=None)
            except Exception:
                continue

        # normalize column names
        cols = [c.strip() for c in df.columns.astype(str)]
        df.columns = cols

        if feature_col not in df.columns or value_col not in df.columns:
            # try lowercase alternatives
            lowcols = {c.lower(): c for c in df.columns}
            if feature_col.lower() in lowcols and value_col.lower() in lowcols:
                feature_col_act = lowcols[feature_col.lower()]
                value_col_act = lowcols[value_col.lower()]
            else:
                # can't use this file
                continue
        else:
            feature_col_act = feature_col
            value_col_act = value_col

        s = df[[feature_col_act, value_col_act]].dropna()
        if s.empty:
            continue
        s = s.set_index(feature_col_act)[value_col_act]
        if numeric:
            s = pd.to_numeric(s, errors='coerce').dropna()
        # group duplicates and average
        s = s.groupby(s.index).mean()
        series_list.append(s)

    if not series_list:
        return None

    if len(series_list) == 1:
        return series_list[0]

    concat = pd.concat(series_list, axis=1)
    return concat.mean(axis=1)


def load_gene_expression(patient_dir):
    patterns = ['rna_seq.augmented_star_gene_counts.tsv']
    files = find_files(patient_dir, patterns)
    # record what files this loader inspected/found for downstream reporting
    setattr(load_gene_expression, '_last_files', files)
    s = _series_from_files(files, 'gene_name', 'tpm_unstranded', numeric=True)
    if s is None:
        return None
    s.index = [f'GeneExpr_{g}' for g in s.index]
    return s


def load_miRNA(patient_dir):
    patterns = ['mirnaseq.mirnas.quantification.txt']
    files = find_files(patient_dir, patterns)
    setattr(load_miRNA, '_last_files', files)
    s = _series_from_files(files, 'miRNA_ID', 'reads_per_million_miRNA_mapped', numeric=True)
    if s is None:
        return None
    s.index = [f'miRNA_{g}' for g in s.index]
    return s


def load_cnv(patient_dir):
    patterns = ['gene_level_copy_number.v36.tsv']
    files = find_files(patient_dir, patterns)
    setattr(load_cnv, '_last_files', files)
    s = _series_from_files(files, 'gene_name', 'copy_number', numeric=True)
    if s is None:
        return None
    s.index = [f'CNV_{g}' for g in s.index]
    return s


def load_methylation(patient_dir):
    patterns = ['methylation_array.sesame.level3betas.txt']
    files = find_files(patient_dir, patterns)
    setattr(load_methylation, '_last_files', files)
    if not files:
        return None

    series_list = []
    for f in files:
        try:
            df = pd.read_csv(f, sep='\t', header=None, names=['feature', 'value'], dtype=str)
        except Exception:
            continue
        df = df.dropna()
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df = df.dropna(subset=['value'])
        if df.empty:
            continue
        s = df.set_index('feature')['value'].groupby(level=0).mean()
        series_list.append(s)

    if not series_list:
        return None

    if len(series_list) == 1:
        s = series_list[0]
    else:
        s = pd.concat(series_list, axis=1).mean(axis=1)

    s.index = [f'Meth_{g}' for g in s.index]
    return s


def load_proteome(patient_dir):
    patterns = ['_RPPA_data.tsv', 'RPPA_data.tsv']
    files = find_files(patient_dir, patterns)
    setattr(load_proteome, '_last_files', files)
    s = _series_from_files(files, 'peptide_target', 'protein_expression', numeric=True)
    if s is None:
        return None
    s.index = [f'Prot_{g}' for g in s.index]
    return s


def load_snv(patient_dir):
    # SNV handling is dataset-specific. Look for a processed SNV table and, if present,
    # return it as-is (prefixing columns). If not present, return None.
    patterns = ['_processed.tsv', '.processed.tsv', '.snv_processed.tsv']
    files = find_files(patient_dir, patterns)
    setattr(load_snv, '_last_files', files)
    if not files:
        return None
    # try to read first
    for f in files:
        try:
            df = pd.read_csv(f, sep='\t', index_col=0)
            df.columns = [f'SNV_{c}' for c in df.columns]
            # flatten to a single-row series if it has only one row
            if df.shape[0] == 1:
                s = df.iloc[0]
                return s
            else:
                # otherwise, collapse by summing / taking presence
                s = (df != 0).any(axis=0).astype(int)
                return s
        except Exception:
            continue
    return None


def create_multi_omics(root_dir, out_path, label='tumor'):
    """Iterate patient case directories under root_dir and build one-row-per-patient table.
    """
    if not os.path.isdir(root_dir):
        raise FileNotFoundError(f"Root dir not found: {root_dir}")

    patients = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]
    patients = sorted(patients)

    rows = []
    index = []

    # Prepare for missing-files reporting: we'll record which loaders found files per patient
    loader_names = [l.__name__ for l in (load_gene_expression, load_miRNA, load_cnv, load_methylation, load_proteome, load_snv)]
    missing_report_rows = []

    for pid in patients:
        pdir = os.path.join(root_dir, pid)
        print(f'Processing {pid}...')

        parts = []
        per_loader_files = {}
        for loader in (load_gene_expression, load_miRNA, load_cnv, load_methylation, load_proteome, load_snv):
            try:
                s = loader(pdir)
            except Exception as e:
                print(f'  - loader {loader.__name__} failed for {pid}: {e}')
                s = None
            # capture what files that loader inspected/found
            last_files = getattr(loader, '_last_files', None)
            per_loader_files[loader.__name__] = last_files if last_files else []

            if s is not None and not s.empty:
                parts.append(s)

        if not parts:
            print(f'  - no data found for {pid}, skipping')
            # still record missing files (all loaders had none)
            row = {'case_id': pid, 'has_data': False}
            for ln in loader_names:
                row[ln] = 0
            missing_report_rows.append(row)
            continue

        # concat series into one-row dataframe
        row = pd.concat(parts, axis=0)
        rows.append(row)
        index.append(pid)
    # for reporting, mark which loaders had files
    found_flags = {ln: (1 if per_loader_files.get(ln) else 0) for ln in loader_names}
    row = {'case_id': pid, 'has_data': True}
    row.update(found_flags)
    missing_report_rows.append(row)

    if not rows:
        print('No patients produced data. Exiting.')
        return

    df = pd.DataFrame(rows, index=index)
    # ensure case id is first column when saved
    df.index.name = 'case_id'
    df = df.sort_index()

    out_dir = os.path.dirname(out_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    # reset index to make case_id the first column, insert class label as second column
    df_reset = df.reset_index()
    # insert class column at position 1 so columns are: case_id, class, ...features
    df_reset.insert(1, 'class', label)
    df_reset.to_csv(out_path, sep='\t', index=False)
    print(f'Wrote multi-omics file to {out_path} ({len(df_reset)} rows)')

    # Also create a features-by-case file: rows = features, columns = case_ids
    # include the 'class' feature as one of the rows
    features_df = df.copy()
    # append class as a row in features_df: class per case is the same label scalar here
    # convert class into a Series indexed by case id and then append
    class_series = pd.Series(label, index=features_df.index, name='class')
    features_df_with_class = pd.concat([features_df, pd.DataFrame({'class': class_series})], axis=1)
    features_final = features_df_with_class.T
    # Reset index so first column is 'feature' and rest are case IDs
    features_reset = features_final.reset_index().rename(columns={'index': 'feature'})

    base, ext = os.path.splitext(out_path)
    if ext == '':
        ext = '.tsv'
    features_out = f"{base}_features_by_case{ext}"
    features_reset.to_csv(features_out, sep='\t', index=False)
    print(f'Wrote features-by-case file to {features_out} ({len(features_reset)} rows)')

    # write missing-files report next to out_path by default
    base, ext = os.path.splitext(out_path)
    missing_out = f"{base}_missing_files.tsv"
    try:
        mr_df = pd.DataFrame(missing_report_rows)
        mr_df.to_csv(missing_out, sep='\t', index=False)
        print(f'Wrote missing-files report to {missing_out} ({len(mr_df)} rows)')
    except Exception as e:
        print(f'Failed to write missing-files report: {e}')


def main():
    parser = argparse.ArgumentParser(description='Create one-row-per-case multi-omics TSV from organizedTop10')
    parser.add_argument('--root', '-r', required=True, help='Root organizedTop10 directory (contains one folder per case)')
    parser.add_argument('--out', '-o', required=True, help='Output TSV path')
    parser.add_argument('--label', '-l', default='tumor', help='Class label to write into final column')
    args = parser.parse_args()

    create_multi_omics(args.root, args.out, args.label)


if __name__ == '__main__':
    main()
