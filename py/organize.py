import os
import shutil
import pandas as pd

# --- Config ---
df_csv_path = "csv/files_by_case_flat.csv"  # CSV exported from your df
source_dir = "top10gbm"    # Folder where the files currently are
target_dir = "organizedTop10"          # Base folder for reorganized files

# --- Load the flattened CSV ---
df = pd.read_csv(df_csv_path)

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
