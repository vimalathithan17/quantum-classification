#!/bin/bash

bash sh/gzunzip.sh gdc_downloads
mkdir top10gbm
bash sh/mvfiles.sh gdc_downloads top10gbm
mkdir organizedTop10
python py/organize.py
python py/process_maf.py
bash sh/rmun.sh organizedTop10
bash sh/rm#.sh organizedTop10
bash sh/rmmaf.sh organizedTop10
