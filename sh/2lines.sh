#!/bin/bash

# The parent directory to search within, taken from the first script argument.
PARENT_DIR="$1"
# The name of the file where the output will be saved.
LOG_FILE="file_log.txt"

# --- Validations ---
if [ -z "$PARENT_DIR" ]; then
  echo "Error: No directory specified."
  echo "Usage: ./log_files.sh /path/to/your/directory"
  exit 1
fi

if [ ! -d "$PARENT_DIR" ]; then
  echo "Error: '$PARENT_DIR' is not a valid directory."
  exit 1
fi

# --- Main Logic ---
> "$LOG_FILE"
echo "Log file created at: $(pwd)/$LOG_FILE"

# Find all files (depth=2), excluding *.idat and *annotations.txt
find "$PARENT_DIR" -mindepth 4 -maxdepth 4 -type f \
  ! -name "*.idat" \
  ! -name "*annotations.txt" | while read -r file; do
  
  echo "---" >> "$LOG_FILE"
  echo "File: $file" >> "$LOG_FILE"

  head -n 2 "$file" >> "$LOG_FILE"
done

echo "Done. All matching files have been processed (excluding .idat and annotations.txt files)."
