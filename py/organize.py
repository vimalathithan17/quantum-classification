import os
import shutil
import pandas as pd
import argparse


# --- Defaults ---
DEFAULT_CSV = "csv/files_by_case_flat.csv"  # CSV exported from your df
DEFAULT_SOURCE = "top10gbm"    # Folder where the files currently are
DEFAULT_TARGET = "organizedTop10"          # Base folder for reorganized files


def main(csv_path: str, source_dir: str, target_dir: str):
    """Reorganize files according to the flattened CSV.

    csv_path: path to flattened CSV (columns: Case ID, Data Category, Data Type, file_names)
    source_dir: directory where files currently live
    target_dir: directory to create organized structure under
    """

    # --- Load the flattened CSV ---
    df = pd.read_csv(csv_path)

    # Convert list columns back to lists
    df['file_ids'] = df['file_ids'].apply(lambda x: [str(i) for i in x.split(',')] if pd.notna(x) else [])
    df['file_names'] = df['file_names'].apply(lambda x: x.split(',') if pd.notna(x) else [])

    # --- Iterate and move files ---
    for idx, row in df.iterrows():
        case = row['Case ID']
        category = row['Data Category']
        data_type = row['Data Type']
        files = row['file_names']

        # Construct target folder path
        dest_folder = os.path.join(target_dir, case, category, data_type)
        os.makedirs(dest_folder, exist_ok=True)

        # Move files
        for f in files:
            src_path = os.path.join(source_dir, f)
            dest_path = os.path.join(dest_folder, f)
            if os.path.exists(src_path):
                shutil.move(src_path, dest_path)
            else:
                print(f"Warning: {src_path} not found.")

    print("All files moved successfully.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Organize files by case using flattened CSV')
    parser.add_argument('--csv', '-c', default=DEFAULT_CSV, help='Path to flattened CSV (default: csv/files_by_case_flat.csv)')
    parser.add_argument('--source', '-s', default=DEFAULT_SOURCE, help='Source directory where files currently are (default: top10gbm)')
    parser.add_argument('--target', '-t', default=DEFAULT_TARGET, help='Target root directory to organize files into (default: organizedTop10)')
    args = parser.parse_args()

    main(args.csv, args.source, args.target)
