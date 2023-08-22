from argparse import ArgumentParser

import pyterrier as pt
from tqdm import tqdm
from dataclasses import asdict

from CTnlp.parsers import parse_clinical_trials_from_folder

TRIALS_FOLDER = "data/clinical_trials"

def get_clinical_trial_dict(first_n=None):
    cts = parse_clinical_trials_from_folder(folder_name=TRIALS_FOLDER, first_n=first_n)
    cts = [asdict(ct) for ct in cts]
    return cts


def index_clinical_trials(cts, ct_meta_fields, ct_text_fields):
    pt.init()
    iter_indexer = pt.IterDictIndexer("./ct_index", verbose=True, num_docs=len(cts),
                                      meta=ct_meta_fields,
                                      stemmer="porter",
                                      stopwords="terrier",
                                      tokeniser="english")

    print("Indexing...")
    indexref = iter_indexer.index(cts, fields=ct_text_fields)

    index = pt.IndexFactory.of(indexref)
    print(index.getCollectionStatistics().toString())

if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument("-n", "--first_n", type=int, default=None, help="Number of clinical trials to index")
    args = parser.parse_args()

    cts = get_clinical_trial_dict(args.first_n)

    # Rename field nct_id to docno (required by pyterrier)
    for ct in tqdm(cts):
        ct["docno"] = ct.pop("nct_id")

    # Relevant fields:
    ct_fields = ["docno", "brief_title", "brief_summary",
                 "detailed_description", "inclusion", "exclusion",
                 "gender", "minimum_age", "maximum_age",
                 "conditions", "interventions"] 
    print("Fields:", ct_fields, ct_fields[1:])

    index_clinical_trials(cts, ct_fields, ct_fields[1:])


