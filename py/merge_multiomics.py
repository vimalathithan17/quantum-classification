#!/usr/bin/env python3
"""Merge multiple case-by-feature TSVs (outputs of create_multiomics.py).

Reads one or more input TSVs with the same columns (first column should be 'case_id'),
validates compatibility, concatenates rows, and writes a merged TSV.

Usage examples:
  python py/merge_multiomics.py tumor.tsv normal.tsv -o merged.tsv
  python py/merge_multiomics.py a.tsv b.tsv -o merged.tsv --on-duplicates keep-first

The default behavior on duplicate case_id is to error; use --on-duplicates to control.
"""
import argparse
import sys
from pathlib import Path
import pandas as pd


def read_tsv(path: Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, sep='\t', header=0, dtype=object)
    except Exception as e:
        raise RuntimeError(f"Failed to read {path}: {e}")
    return df


def validate_columns(dfs):
    # Collect sets of columns per df
    cols_list = [list(df.columns) for df in dfs]
    # Use the first set as reference
    ref = cols_list[0]
    for i, cols in enumerate(cols_list[1:], start=2):
        if cols != ref:
            # not identical — allow union but warn
            return False, ref
    return True, ref


def merge_files(paths, out_path: Path, on_duplicates: str = 'error'):
    dfs = []
    for p in paths:
        p = Path(p)
        if not p.exists():
            raise FileNotFoundError(f"Input file not found: {p}")
        dfs.append(read_tsv(p))

    if not dfs:
        raise ValueError("No input files provided")

    identical, ref_cols = validate_columns(dfs)
    if not identical:
        # align to union of columns, filling missing with NaN
        all_cols = []
        for df in dfs:
            for c in df.columns:
                if c not in all_cols:
                    all_cols.append(c)
        aligned = []
        for df in dfs:
            aligned.append(df.reindex(columns=all_cols))
        df_all = pd.concat(aligned, axis=0, ignore_index=True)
        print("Warning: input files had different column orders/sets — aligned to union of columns", file=sys.stderr)
    else:
        df_all = pd.concat(dfs, axis=0, ignore_index=True)

    # Expect a case_id column
    if 'case_id' not in df_all.columns:
        # try index name
        if df_all.index.name == 'case_id':
            df_all = df_all.reset_index()
        else:
            raise RuntimeError("No 'case_id' column found in inputs; expected first column to be case_id")

    # detect duplicates
    dupes = df_all['case_id'].duplicated(keep=False)
    if dupes.any():
        if on_duplicates == 'error':
            dup_ids = df_all.loc[dupes, 'case_id'].unique().tolist()
            raise RuntimeError(f"Duplicate case_id values found: {dup_ids}; use --on-duplicates to control behavior")
        elif on_duplicates == 'keep-first':
            df_all = df_all.drop_duplicates(subset=['case_id'], keep='first')
        elif on_duplicates == 'keep-last':
            df_all = df_all.drop_duplicates(subset=['case_id'], keep='last')
        else:
            raise ValueError(f"Unknown on_duplicates mode: {on_duplicates}")

    # sort by case_id for determinism
    df_all = df_all.set_index('case_id').sort_index().reset_index()

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df_all.to_csv(out_path, sep='\t', index=False)
    print(f"Wrote merged TSV to {out_path} ({len(df_all)} rows)")


def main():
    parser = argparse.ArgumentParser(description='Merge case-by-feature TSVs produced by create_multiomics.py')
    parser.add_argument('inputs', nargs='+', help='Input TSV files (two or more)')
    parser.add_argument('--out', '-o', required=True, help='Output merged TSV path')
    parser.add_argument('--on-duplicates', choices=['error', 'keep-first', 'keep-last'], default='error',
                        help="Behavior when duplicate case_id values are present across inputs (default: error)")
    args = parser.parse_args()

    try:
        merge_files(args.inputs, args.out, args.on_duplicates)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
