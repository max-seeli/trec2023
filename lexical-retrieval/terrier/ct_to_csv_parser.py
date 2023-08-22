from argparse import ArgumentParser
from dataclasses import asdict
import csv

from CTnlp.parsers import parse_clinical_trials_from_folder

TRIALS_FOLDER = "data/clinical_trials"

def get_clinical_trial_dict(first_n=None):
    cts = parse_clinical_trials_from_folder(folder_name=TRIALS_FOLDER, first_n=first_n)
    cts = [asdict(ct) for ct in cts]
    return cts

if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument("-n", "--first_n", type=int, default=None, help="Number of clinical trials to write to csv")
    args = parser.parse_args()

    cts = get_clinical_trial_dict(100)

    # Rename field nct_id to docno (required by pyterrier)
    for ct in cts:
        ct["docno"] = ct.pop("nct_id")

    # Write the clinical trials to a csv file
    with open("data/clinical_trials/clinical_trials.csv", "w") as f:
        writer = csv.DictWriter(f, fieldnames=cts[0].keys())
        writer.writeheader()
        writer.writerows(cts)

    
