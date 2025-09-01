#!/usr/bin/env bash

set -euo pipefail

usage() {
	cat <<EOF
Usage: $(basename "$0") -m MANIFEST_PATH

Download files listed in a GDC manifest using the bundled gdc-client.

Options:
  -m, --manifest PATH   Path to the GDC manifest file (required).
  -d, --dest DIR        Destination directory for downloads (default: gdc_downloads).
  -h, --help            Show this help message and exit.

Example:
  $(basename "$0") -m manifest/gdc_manifest.2025-09-01.txt

This script makes the included gdc-client executable and runs:
  tools/gdc-client download -m <manifest> -d <dest>

EOF
}

MANIFEST=""
DEST_DIR="gdc_downloads"

if [ "$#" -eq 0 ]; then
	usage
	exit 1
fi

while [ "$#" -gt 0 ]; do
	case "$1" in
		-m|--manifest)
			if [ -n "${2-}" ]; then
				MANIFEST="$2"
				shift 2
				continue
			else
				echo "Error: --manifest requires a path argument" >&2
				exit 1
			fi
			;;
		-d|--dest)
			if [ -n "${2-}" ]; then
				DEST_DIR="$2"
				shift 2
				continue
			else
				echo "Error: --dest requires a path argument" >&2
				exit 1
			fi
			;;
		-h|--help)
			usage
			exit 0
			;;
		*)
			echo "Unknown argument: $1" >&2
			usage
			exit 1
			;;
	esac
done

if [ -z "$MANIFEST" ]; then
	echo "Error: manifest path is required." >&2
	usage
	exit 1
fi

if [ ! -f "$MANIFEST" ]; then
	echo "Error: manifest file not found: $MANIFEST" >&2
	exit 1
fi

if [ ! -x "tools/gdc-client" ]; then
	if [ -f "tools/gdc-client" ]; then
		chmod +x "tools/gdc-client"
	else
		echo "Error: tools/gdc-client not found in repository." >&2
		exit 1
	fi
fi

mkdir -p "$DEST_DIR"

echo "Downloading manifest: $MANIFEST -> $DEST_DIR"
tools/gdc-client download -m "$MANIFEST" -d "$DEST_DIR"

# Optionally call organize script (uncomment if desired)
# sh/organize.sh -c csv/files_by_case_flat.csv -s top10gbm -t organizedTop10