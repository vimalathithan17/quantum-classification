#!/usr/bin/env bash
set -euo pipefail

usage() {
	cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Run the organize pipeline: unpack, move files, call Python organizer and cleanups.

Options:
  -c, --csv PATH       Path to flattened CSV to pass to py/organize.py (default: csv/files_by_case_flat.csv)
  -s, --source PATH    Source directory where files currently are (default: top10gbm)
  -t, --target PATH    Target directory for organized output (default: organizedTop10)
	-D, --downloads DIR  Downloads directory containing GDC downloads (default: gdc_downloads)
  --dry-run            Print commands without executing them
  -h, --help           Show this help message and exit

This script runs a sequence of helpers and then invokes:
  python py/organize.py --csv <CSV> --source <SOURCE> --target <TARGET>

EOF
}

CSV="csv/files_by_case_flat.csv"
SOURCE="top10gbm"
TARGET="organizedTop10"
DOWNLOADS="gdc_downloads"
DRY_RUN=0

while [ "$#" -gt 0 ]; do
	case "$1" in
		-c|--csv)
			CSV="$2"; shift 2;;
		-s|--source)
			SOURCE="$2"; shift 2;;
		-t|--target)
			TARGET="$2"; shift 2;;
		--dry-run)
			DRY_RUN=1; shift;;
		-D|--downloads)
			DOWNLOADS="$2"; shift 2;;
		-h|--help)
			usage; exit 0;;
		*)
			echo "Unknown argument: $1" >&2; usage; exit 1;;
	esac
done

echo "CSV: $CSV"
echo "Source: $SOURCE"
echo "Target: $TARGET"
echo "Downloads: $DOWNLOADS"

run_or_echo() {
	if [ "$DRY_RUN" -eq 1 ]; then
		echo "+ $*"
	else
		eval "$@"
	fi
}

run_or_echo bash sh/gzunzip.sh "$DOWNLOADS"
run_or_echo mkdir -p "$SOURCE"
run_or_echo bash sh/mvfiles.sh "$DOWNLOADS" "$SOURCE"
run_or_echo mkdir -p "$TARGET"
run_or_echo python py/organize.py --csv "$CSV" --source "$SOURCE" --target "$TARGET"
run_or_echo python py/process_maf.py
run_or_echo bash sh/rmun.sh "$TARGET"
run_or_echo bash sh/rm#.sh "$TARGET"
run_or_echo bash sh/rmmaf.sh "$TARGET"
