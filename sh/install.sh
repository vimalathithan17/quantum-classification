#!/bin/bash
chmod +x tools/gdc-client
mkdir gdc_downloads
tools/gdc-client download -m $1 -d gdc_downloads
#sh/organize.sh