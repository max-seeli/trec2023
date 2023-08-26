from argparse import ArgumentParser
import os
import pyterrier as pt
pt.init()

import pandas as pd
from dataclasses import asdict

from CTnlp.parsers import parse_clinical_trials_from_folder

INDICES_FOLDER = "./indices/"

def setup(df, index_name, meta_fields=["docno"], force=False):

    if exists(index_name) and not force:
        return ValueError(f"Index {index_name} already exists")

    indexer = pt.DFIndexer(index_path(index_name),
                           stemmer="porter",
                           stopwords="terrier",
                           tokeniser="english",
                           verbose=True,
                           overwrite=force)

    index_ref = indexer.index(df["text"], df[meta_fields])
    index = pt.IndexFactory.of(index_ref)

    print(index.getCollectionStatistics().toString())

    return index



def exists(index_name):

    try:
        pt.IndexFactory.of(index_path(index_name))
        return True
    except:
        return False
    
def get(index_name):

    if not exists(index_name):
        raise ValueError(f"Index {index_name} does not exist")
    
    return pt.IndexFactory.of(index_path(index_name))

def index_path(index_name):

    path = INDICES_FOLDER + index_name
    # check for path traversal
    if not os.path.abspath(path).startswith(os.path.abspath(INDICES_FOLDER)):
        raise ValueError(f"Invalid index name: {index_name}")
    
    return path

if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument("-n", "--first_n", type=int, default=None, help="Number of clinical trials to index")
    args = parser.parse_args()

    cts = parse_clinical_trials_from_folder(folder_name="data/clinical_trials", first_n=args.first_n)
    cts = [asdict(ct) for ct in cts]

    

    # Relevant fields:
    ct_fields = ["brief_title", "brief_summary",
                 "detailed_description", "inclusion", "exclusion"]

    df = pd.DataFrame(cts)
    print(df.info())

    # convert inclusion and exclusion lists to strings (space separated)
    df["inclusion"] = df["inclusion"].apply(lambda x: " ".join(x))
    df["exclusion"] = df["exclusion"].apply(lambda x: " ".join(x))

    df["docno"] = df.pop("nct_id")
    df["text"] = df[ct_fields].apply(lambda x: " ".join(x), axis=1)
    df = df[["docno", "text", "brief_title"]]

    setup(df, "ct_base", ["docno", "brief_title"], force=True)

    


