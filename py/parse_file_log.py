import pandas as pd

log_file = "file_log.txt"
records = []

with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
    block = []
    for line in f:
        line = line.strip()
        if line == "---":
            if block:
                file_path = None
                header = ""
                first_row = ""
                for b in block:
                    if b.startswith("File: "):
                        file_path = b.replace("File: ", "")
                    elif header == "":
                        header = b
                    elif first_row == "":
                        first_row = b

                # --- Exclusion rules ---
                if file_path:
                    lower_path = file_path.lower()
                    if (
                        lower_path.endswith(".cel")
                        or lower_path.endswith(".xml")
                        or "biospecimen" in lower_path
                        or "clinical" in lower_path
                        or "nationwidechildrens" in lower_path
                    ):
                        block = []
                        continue

                dtype = "Unknown"
                if "gene_id" in header:
                    dtype = "Gene Expression Quantification"
                elif "Composite Element REF" in header:
                    dtype = "Methylation Beta Value"
                elif "copy_number" in header:
                    dtype = "Gene Level Copy Number"
                elif "Hugo_Symbol" in header:
                    dtype = "Masked Somatic Mutation"

                if file_path:
                    records.append([file_path, header, first_row, dtype])

            block = []
        else:
            block.append(line)

# Create DataFrame
df = pd.DataFrame(records, columns=["file_path", "header", "first_row", "data_type"])

# Save metadata
df.to_csv("parsed_file_metadata.csv", index=False)

print("✅ Metadata saved to parsed_file_metadata.csv")
print(df.head(10))
