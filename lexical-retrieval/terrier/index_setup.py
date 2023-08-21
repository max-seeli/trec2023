import pyterrier as pt
from dataclasses import asdict

from CTnlp.parsers import parse_clinical_trials_from_folder

TRIALS_FOLDER = "data/clinical_trials"

cts = parse_clinical_trials_from_folder(folder_name=TRIALS_FOLDER)
cts = [asdict(ct) for ct in cts]

# Rename field nct_id to docno (required by pyterrier)
for ct in cts:
    ct["docno"] = ct.pop("nct_id")

# Relevant fields:
ct_fields = ["docno", "brief_title", "brief_summary",
             "detailed_description", "inclusion", "exclusion",
             "gender", "minimum_age", "maximum_age",
             "conditions", "interventions"] 
print("Fields:", ct_fields)

# Create a new index
pt.init()
iter_indexer = pt.IterDictIndexer("./ct_index", overwrite=True, verbose=True,
                                  meta=ct_fields,
                                  stemmer="porter",
                                  stopwords="terrier",
                                  tokeniser="english")

print("Indexing...")
# Index the documents
indexref = iter_indexer.index(cts, fields=ct_fields[1:])

index = pt.IndexFactory.of(indexref)

print(index.getCollectionStatistics().toString())
