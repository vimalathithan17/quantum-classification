import os
import glob
import pandas as pd

def find_best_file(patient_dir, patterns):
    """
    Finds the best-matching file in a patient's directory based on a list of patterns.
    Returns the first matching file found.
    """
    for pattern in patterns:
        search_path = os.path.join(patient_dir, '**', pattern)
        file_paths = glob.glob(search_path, recursive=True)
        if file_paths:
            return file_paths[0]
    return None

def find_header_line(file_path):
    """Finds the correct header line for a file by skipping comments."""
    with open(file_path, 'r') as f:
        for i, line in enumerate(f):
            if not line.startswith('#'):
                return i
    return 0

def load_data_for_patient(patient_dir, data_type, patient_id):
    """
    Loads and processes a single data file for a specific patient.
    """
    file_patterns = {
        'Gene Expression': ['rna_seq.augmented_star_gene_counts.tsv'],
        'miRNA Expression': ['mirnaseq.mirnas.quantification.txt'],
        'Copy Number Variation': ['gene_level_copy_number.v36.tsv'],
        'DNA Methylation': ['methylation_array.sesame.level3betas.txt'],
        'Proteome Profiling': ['_RPPA_data.tsv'],
        'Simple Nucleotide Variation': ['_processed.tsv'] # Using the previously generated file
    }

    column_mappings = {
        'Gene Expression': ('gene_name', 'tpm_unstranded'),
        'miRNA Expression': ('miRNA_ID', 'reads_per_million_miRNA_mapped'),
        'Copy Number Variation': ('gene_name', 'copy_number'),
        'DNA Methylation': (None, None), # Special handling
        'Proteome Profiling': ('peptide_target', 'protein_expression'),
        'Simple Nucleotide Variation': (None, None) # Special handling
    }

    df = None
    file_path = find_best_file(patient_dir, file_patterns[data_type])

    if not file_path:
        print(f"  - No suitable file found for {data_type} in {patient_dir}.")
        return None

    print(f"  - Found {data_type} file: {file_path}")

    try:
        header_row = find_header_line(file_path)

        if data_type in ['DNA Methylation', 'Simple Nucleotide Variation']:
            # These files have a simpler structure and don't require pivoting
            df = pd.read_csv(file_path, sep='\t', index_col=0, header=header_row)
            df = df.T
            df.index = [patient_id]
            df.columns = [f"{data_type}_{col}" for col in df.columns]

        else:
            # For other files that require pivoting
            df = pd.read_csv(file_path, sep='\t', header=header_row)
            feature_col, value_col = column_mappings[data_type]

            if feature_col in df.columns and value_col in df.columns:
                df = df[[feature_col, value_col]].copy()
                df = df.pivot_table(index=df.index, columns=feature_col, values=value_col, fill_value=0)
                df.index = [patient_id]
                df.columns = [f"{data_type}_{col}" for col in df.columns]
            else:
                print(f"  - Skipped {file_path}: Missing required columns ({feature_col}, {value_col}).")
                df = None

    except Exception as e:
        print(f"  - Failed to process {file_path}: {e}")
        df = None

    return df

def create_multi_omics_data_file(root_dir, output_file_name='multi_omics_dataset.tsv'):
    """
    Creates a combined multi-omics data file by iterating through patient folders.
    """
    data_types = [
        'Gene Expression',
        'miRNA Expression',
        'Copy Number Variation',
        'DNA Methylation',
        'Proteome Profiling',
        'Simple Nucleotide Variation'
    ]

    all_patients_df = pd.DataFrame()

    patient_dirs = sorted([d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))])
    
    for patient_id in patient_dirs:
        patient_dir = os.path.join(root_dir, patient_id)
        
        print(f"\nProcessing data for patient: {patient_id}")
        patient_combined_df = None
        
        for data_type in data_types:
            df = load_data_for_patient(patient_dir, data_type, patient_id)
            if df is not None:
                if patient_combined_df is None:
                    patient_combined_df = df
                else:
                    patient_combined_df = pd.merge(patient_combined_df, df, left_index=True, right_index=True, how='outer')

        if patient_combined_df is not None:
            all_patients_df = pd.concat([all_patients_df, patient_combined_df])
            print(f"  - Finished combining data for {patient_id}. Total patients processed so far: {len(all_patients_df)}")
        else:
            print(f"  - No complete data found for {patient_id}. Skipping.")

    if not all_patients_df.empty:
        output_path = os.path.join(root_dir, output_file_name)
        all_patients_df.to_csv(output_path, sep='\t')
        print(f"\nSuccessfully created multi-omics data file and saved to: {output_path}")
    else:
        print("\nNo data could be processed to create a combined multi-omics file.")

# --- How to Use ---
organized_top10_dir = '/workspace/QuantumClassification/organizedTop10'
create_multi_omics_data_file(organized_top10_dir)