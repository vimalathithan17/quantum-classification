import os
import glob
import pandas as pd

def load_data_for_patient(patient_dir, data_type, patient_id):
    """
    Loads and processes a single data file for a specific patient.
    """
    # Define a priority list of file patterns for each data type
    file_patterns = {
        'Gene Expression': ['rna_seq.augmented_star_gene_counts.tsv'],
        'miRNA Expression': ['mirnaseq.mirnas.quantification.txt'],
        'Copy Number Variation': ['gene_level_copy_number.v36.tsv'],
        'DNA Methylation': ['methylation_array.sesame.level3betas.txt'],
        'Proteome Profiling': ['_RPPA_data.tsv'],
        'Simple Nucleotide Variation': ['_processed.tsv'] # Use the processed SNV file
    }

    # Define the columns to use for each data type
    column_mappings = {
        'Gene Expression': ('gene_name', 'tpm_unstranded'),
        'miRNA Expression': ('miRNA_ID', 'reads_per_million_miRNA_mapped'),
        'Copy Number Variation': ('gene_name', 'copy_number'),
        'DNA Methylation': (None, None), # Special handling for this file type
        'Proteome Profiling': ('peptide_target', 'protein_expression'),
        'Simple Nucleotide Variation': (None, None) # Special handling for processed SNV file
    }

    df = None
    for pattern in file_patterns[data_type]:
        search_path = os.path.join(patient_dir, f"**/*{pattern}")
        file_paths = glob.glob(search_path, recursive=True)

        if file_paths:
            # We'll just take the first file found based on priority
            file_path = file_paths[0]
            
            try:
                if data_type == 'DNA Methylation':
                    # DNA Methylation files have a different structure
                    df = pd.read_csv(file_path, sep='\t', header=None, index_col=0, names=['feature', 'value'])
                    df = df.T
                    df.index = [patient_id]
                    df.columns = [f"Methylation_{col}" for col in df.columns]
                elif data_type == 'Simple Nucleotide Variation':
                    # SNV file is already processed
                    df = pd.read_csv(file_path, sep='\t', index_col=0)
                    df.index = [patient_id]
                    df.columns = [f"SNV_{col}" for col in df.columns]
                else:
                    # Generic handling for other file types
                    df = pd.read_csv(file_path, sep='\t')
                    feature_col, value_col = column_mappings[data_type]
                    
                    if feature_col in df.columns and value_col in df.columns:
                        df = df[[feature_col, value_col]]
                        df = df.pivot_table(index=df.index, columns=feature_col, values=value_col, fill_value=0)
                        df.index = [patient_id]
                        df.columns = [f"{data_type}_{col}" for col in df.columns]
                    else:
                        print(f"  - Skipped {file_path}: Missing required columns ({feature_col}, {value_col}).")
                        df = None
            except Exception as e:
                print(f"  - Failed to process {file_path}: {e}")
                df = None
            
            if df is not None:
                print(f"  - Loaded {data_type} data from {file_path}")
                break
    
    if df is None:
        print(f"  - No suitable file found for {data_type} in {patient_dir}.")
    
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
    
    # Get all patient directories
    patient_dirs = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]
    
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
            print(f"  - Finished combining data for {patient_id}. Total rows now: {len(all_patients_df)}")
        else:
            print(f"  - No complete data found for {patient_id}. Skipping.")

    if not all_patients_df.empty:
        # Save the final combined data frame
        output_path = os.path.join(root_dir, output_file_name)
        all_patients_df.to_csv(output_path, sep='\t')
        print(f"\nSuccessfully created multi-omics data file and saved to: {output_path}")
    else:
        print("\nNo data could be processed to create a combined multi-omics file.")

# --- How to Use ---
# Set the root directory of your organized data
organized_top10_dir = '/workspace/quantum-classification/organizedTop10'

# Run the function to create the file
create_multi_omics_data_file(organized_top10_dir)
