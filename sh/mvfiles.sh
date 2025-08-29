#!/bin/bash

# Parent directory and target directory
PARENT_DIR="$1"
TARGET_DIR="$2"

# --- Validations ---
if [ -z "$PARENT_DIR" ] || [ -z "$TARGET_DIR" ]; then
  echo "Usage: $0 /path/to/parent_dir /path/to/target_dir"
  exit 1
fi

if [ ! -d "$PARENT_DIR" ]; then
  echo "Error: '$PARENT_DIR' is not a valid directory."
  exit 1
fi

# Create target directory if it doesn't exist
mkdir -p "$TARGET_DIR"

# --- Main Logic ---
echo "Moving files from subdirectories of $PARENT_DIR to $TARGET_DIR (excluding annotations.txt)..."

# Loop over immediate subdirectories (1-level depth)
for subdir in "$PARENT_DIR"/*/; do
  [ -d "$subdir" ] || continue  # Skip if not a directory
  echo "Processing subdir: $subdir"

  # Move all files except annotations.txt
  find "$subdir" -maxdepth 1 -type f ! -name "annotations.txt" -exec mv {} "$TARGET_DIR"/ \;
done

echo "Done. Files moved."
