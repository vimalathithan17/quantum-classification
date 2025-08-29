#!/bin/bash

# The parent directory to search within, taken from the first script argument.
PARENT_DIR="$1"

# --- Validations ---
if [ -z "$PARENT_DIR" ]; then
  echo "Error: No directory specified."
  echo "Usage: ./unzip_gz.sh /path/to/your/directory"
  exit 1
fi

if [ ! -d "$PARENT_DIR" ]; then
  echo "Error: '$PARENT_DIR' is not a valid directory."
  exit 1
fi

# --- Main Logic ---
echo "Searching for .gz files under $PARENT_DIR (depth=2)..."

# Find .gz files and unzip them in place
find "$PARENT_DIR" -mindepth 2 -maxdepth 2 -type f -name "*.gz" | while read -r gzfile; do
  echo "Unzipping: $gzfile"
  gunzip "$gzfile"   # -k keeps original .gz file, remove -k if you want it deleted
done

echo "Done. All .gz files processed."
