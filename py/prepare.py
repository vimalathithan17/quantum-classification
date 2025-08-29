import pandas as pd
import os

# ---- Load metadata ----
df = pd.read_csv("final_multiomics_metadata.csv")

def parse_dynamic(filepath, patient, dtype):
    """
    Generic parser: keeps ALL numeric columns, prefixes features by patient.
    Special case: mutations → binary 0/1 features.
    """
    try:
        d = pd.read_csv(filepath, sep="\t", comment="#", low_memory=False)
    except Exception as e:
        print(f"❌ Could not parse {filepath}: {e}")
        return None

    if d.empty:
        return None

    # ---- Handle mutations separately (binary features) ----
    if dtype == "Masked Somatic Mutation" and "Hugo_Symbol" in d.columns:
        muts = d.groupby("Hugo_Symbol").size().to_frame("mutated")
        muts["mutated"] = (muts["mutated"] > 0).astype(int)  # binary flag
        muts.index = ["MUT_" + str(g) for g in muts.index]
        muts.columns = [f"{patient}_mutated"]
        return muts

    # ---- General case ----
    index_col = None
    for col in ["gene_id", "Composite Element REF", "Hugo_Symbol", "Gene Symbol", "gene_symbol"]:
        if col in d.columns:
            index_col = col
            break

    if index_col is not None:
        d = d.set_index(index_col)
    else:
        # fallback: row-based index
        d.index = [f"{os.path.basename(filepath)}_row{i}" for i in range(len(d))]

    # Keep only numeric columns
    d = d.apply(pd.to_numeric, errors="ignore")
    num_cols = d.select_dtypes(include=["number"]).columns
    d = d[num_cols]

    if d.empty:
        return None

    # Rename columns with patient prefix
    d.columns = [f"{patient}_{col}" for col in d.columns]

    return d

def make_unique(df, how="mean"):
    """Ensure unique indices by aggregating duplicates."""
    if not df.index.is_unique:
        if how == "mean":
            df = df.groupby(df.index).mean()
        elif how == "sum":
            df = df.groupby(df.index).sum()
    return df


# ---- Build patient tables ----
patient_tables = {}

for _, row in df.iterrows():
    patient = row["patient_barcode"]
    fpath   = row["file_path"]
    dtype   = row["final_data_type"]

    parsed = parse_dynamic(fpath, patient, dtype)

    if parsed is not None:
        patient_tables.setdefault(patient, []).append(parsed)
        print(f"✅ Parsed {fpath} ({dtype}) for patient {patient}, shape={parsed.shape}")
    else:
        print(f"⚠️ Skipped {fpath} ({dtype}) for patient {patient}")

# ---- Merge features across patients ----
all_patient_features = []

for patient, tables in patient_tables.items():
    merged_patient = pd.concat(tables, axis=0)   # stack features
    merged_patient = make_unique(merged_patient) # handle duplicates
    all_patient_features.append(merged_patient)

# ---- Final matrices ----
if all_patient_features:
    feature_matrix = pd.concat(all_patient_features, axis=1).fillna(0)
    feature_matrix.to_csv("multiomics_feature_matrix_col.csv")
    print("💾 Saved multiomics_feature_matrix_col.csv")
    print("Shape:", feature_matrix.shape)

    # Patients = rows, features = columns
    feature_matrix_T = feature_matrix.T
    feature_matrix_T.to_csv("multiomics_feature_matrix_row.csv")
    print("💾 Saved multiomics_feature_matrix_row.csv")
    print("Shape:", feature_matrix_T.shape)

else:
    print("❌ No features parsed. Check metadata or file paths.")
