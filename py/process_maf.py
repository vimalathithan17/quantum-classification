import os
import pandas as pd

def process_maf_file(file_path):
    """
    Processes a .maf file to create a binary mutation matrix.
    """
    try:
        # Load the MAF file, skipping metadata rows that start with '#'
        maf_df = pd.read_csv(file_path, sep='\t', comment='#', low_memory=False)

        # Check if the required columns exist
        required_cols = ['Hugo_Symbol', 'Tumor_Sample_Barcode']
        if not all(col in maf_df.columns for col in required_cols):
            print(f"Skipping {file_path}: Missing required columns.")
            return None

        # Select the columns for gene and patient
        maf_df = maf_df[required_cols]

        # Remove duplicate entries for a single gene-patient combination
        maf_df = maf_df.drop_duplicates()

        # Create a new column of 1s to indicate a mutation
        maf_df['mutation_status'] = 1

        # Pivot the table to create the binary matrix
        mutation_matrix = maf_df.pivot_table(
            index='Tumor_Sample_Barcode',
            columns='Hugo_Symbol',
            values='mutation_status',
            fill_value=0
        )

        return mutation_matrix

    except Exception as e:
        print(f"An error occurred while processing {file_path}: {e}")
        return None

def find_and_process_all_maf_files(root_dir):
    """
    Walks through a directory, finds all .maf files, processes them,
    and saves the output to a new file.
    """
    print(f"Starting to process .maf files in {root_dir}...")
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.maf'):
                original_file_path = os.path.join(dirpath, filename)
                print(f"  Found file: {original_file_path}")

                # Process the file
                processed_matrix = process_maf_file(original_file_path)

                if processed_matrix is not None:
                    # Construct the new output file path
                    base_name = os.path.splitext(filename)[0]
                    output_filename = f"{base_name}_processed.tsv"
                    output_file_path = os.path.join(dirpath, output_filename)

                    # Save the processed matrix
                    processed_matrix.to_csv(output_file_path, sep='\t')
                    print(f"  Successfully processed and saved to {output_file_path}")
                print("-" * 50)
    print("All mutation files have been processed.")

# --- How to Use ---
# Set the path to your 'organizedTop10' directory here
organized_top10_dir = 'organizedTop10'

# Run the function
find_and_process_all_maf_files(organized_top10_dir)