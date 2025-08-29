#!/bin/bash

# Check if a directory is provided
if [ -z "$1" ]; then
  echo "Error: Please provide a directory path."
  echo "Usage: $0 <directory_path>"
  exit 1
fi

# Assign the provided directory to a variable
TARGET_DIR="$1"

# Check if the directory exists
if [ ! -d "$TARGET_DIR" ]; then
  echo "Error: Directory '$TARGET_DIR' not found."
  exit 1
fi

echo "Searching for and removing non-_processed.maf files in: $TARGET_DIR"

# Use find to locate all .maf files that do not match the pattern
# The ! -name "*_processed.maf" part negates the pattern
find "$TARGET_DIR" -type f -name "*.maf" ! -name "*_processed.maf" -print0 | while IFS= read -r -d $'\0' file; do
    echo "Deleting: $file"
    rm "$file"
done

echo "Script finished."