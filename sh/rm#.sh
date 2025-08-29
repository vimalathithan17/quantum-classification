#!/bin/bash

# Check if a directory is provided as an argument
if [ -z "$1" ]; then
  echo "Usage: $0 <directory>"
  exit 1
fi

# Store the provided directory
target_dir="$1"

# Check if the provided directory exists
if [ ! -d "$target_dir" ]; then
  echo "Error: Directory '$target_dir' not found."
  exit 1
fi

# Find all files and use a loop to process each one
find "$target_dir" -type f -print0 | while IFS= read -r -d $'\0' file; do
    echo "Processing: $file"
    # Use sed to delete lines starting with # in place
    sed -i '/^#/d' "$file"
    sed -i '/^N_/d' "$file"
done

echo "Done."