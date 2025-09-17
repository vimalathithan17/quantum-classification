#!/usr/bin/env python3
"""Check which TCGA data categories are present per case by inspecting the
first-level directories under each case folder in an organizedTop10 root.

Outputs a TSV with one row per case and boolean flags for each category plus
a `missing` column listing which categories are absent.

Usage:
  python3 py/check_datacategories.py --root organizedTop10_tumor -o outputs/tumor_datacats.tsv

"""
import os
import argparse
import csv
import json
from typing import Dict, List


DEFAULT_CATEGORIES = {
    'Copy Number Variation': [
        'copy number', 'copy_number', 'copy-number', 'copy_number_variation', 'copy number variation'
    ],
    'Simple Nucleotide Variation': [
        'simple nucleotide variation', 'simple nucleotide', 'masked somatic mutation', 'masked somatic', 'somatic mutation', 'mutations', 'snv'
    ],
    'DNA Methylation': [
        'dna methylation', 'methylation', 'methylation_array', 'methylation array'
    ],
    'Transcriptome Profiling': [
        'transcriptome profiling', 'transcriptome', 'transcriptome_profile', 'rna', 'rna_seq', 'mirna', 'mirnaseq', 'gene_expression'
    ],
}


def normalize_name(s: str) -> str:
    return s.strip().lower().replace('-', ' ').replace('_', ' ')


def match_category(subdirs: List[str], keywords: List[str]) -> bool:
    """Return True if any keyword appears in any immediate subdirectory name."""
    for d in subdirs:
        dn = normalize_name(d)
        for kw in keywords:
            if kw in dn:
                return True
    return False


def inspect_root(root: str, categories: Dict[str, List[str]]) -> List[Dict[str, object]]:
    if not os.path.isdir(root):
        raise FileNotFoundError(f"Root not found: {root}")

    cases = [d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))]
    cases = sorted(cases)

    out = []
    for case in cases:
        case_dir = os.path.join(root, case)
        try:
            entries = [e for e in os.listdir(case_dir) if os.path.isdir(os.path.join(case_dir, e))]
        except Exception:
            entries = []

        row = {'case_id': case}
        missing = []
        for cat, kws in categories.items():
            present = match_category(entries, kws)
            key = f'has_{cat.replace(" ", "_")}'
            row[key] = 1 if present else 0
            if not present:
                missing.append(cat)

        row['missing'] = ';'.join(missing) if missing else ''
        out.append(row)

    return out


def write_tsv(rows: List[Dict[str, object]], out_path: str):
    if not rows:
        # write header only
        with open(out_path, 'w', newline='') as fh:
            fh.write('case_id\n')
        return

    # determine header ordering: case_id, category flags..., missing
    keys = list(rows[0].keys())
    # ensure predictable ordering: case_id first, missing last
    if 'case_id' in keys:
        keys.remove('case_id')
        keys = ['case_id'] + keys
    if 'missing' in keys:
        keys.remove('missing')
        keys = keys + ['missing']

    with open(out_path, 'w', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=keys, delimiter='\t')
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def main():
    parser = argparse.ArgumentParser(description='Report which data categories are present per case')
    parser.add_argument('--root', '-r', required=True, help='organizedTop10 root directory (one folder per case)')
    parser.add_argument('--out', '-o', required=True, help='Output TSV path')
    parser.add_argument('--categories-json', help='Optional path to a JSON file defining categories->keywords (overrides defaults)')
    args = parser.parse_args()

    categories = DEFAULT_CATEGORIES
    if args.categories_json:
        with open(args.categories_json, 'r') as fh:
            categories = json.load(fh)

    rows = inspect_root(args.root, categories)
    out_dir = os.path.dirname(args.out)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    write_tsv(rows, args.out)
    print(f'Wrote data category report to {args.out} ({len(rows)} cases)')


if __name__ == '__main__':
    main()