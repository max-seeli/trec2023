#!/bin/sh

 for i in {0..5}
 do
    FILE="ClinicalTrials.2023-05-08.trials${i}.zip"
    FOLDER="data/clinical_trials/raw"
    wget -P ${FOLDER} http://trec-cds.org/2023_data/${FILE}
    unzip -d ${FOLDER} ${FOLDER}/${FILE}
    rm ${FOLDER}/${FILE}
 done
