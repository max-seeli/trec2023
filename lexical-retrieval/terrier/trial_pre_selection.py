import pyterrier as pt 
import pandas as pd
import xml.etree.ElementTree as ET
import json
from tqdm import tqdm
import os
from CTnlp.parsers import parse_clinical_trial

TOPICS_FILE = "data/patients/topics2023.xml"
RAW_TRIALS_FOLDER = "data/clinical_trials/raw"
TRIAL_PRE_SELECTION_FILE = "data/clinical_trials/trial_pre_selection_16k.json"

def get_topic_categories():
    
    root = ET.parse(TOPICS_FILE).getroot()
    return set([topic.attrib["template"] for topic in root])


def create_topic_categories_dataframe(topic_categories):

    queries = [{"query": query, "qid": qid} for qid, query in enumerate(topic_categories)]
    return pd.DataFrame(queries)



def parse_results(index, results):
    trial_selection = []

    trial_files = [os.path.join(root, file) for root, _, files in os.walk(RAW_TRIALS_FOLDER) for file in files]

    for _, result in tqdm(results.iterrows(), total=len(results)):
        nct_id = index.getMetaIndex().getItem("docno", result["docid"])
        trial_file = [file for file in trial_files if nct_id in file][0]

        trial = parse_clinical_trial(ET.parse(trial_file).getroot())
        trial_selection.append({
            "nct_id": nct_id,
            "minimum_age": trial.minimum_age,
            "maximium_age": trial.maximum_age,
            "gender": trial.gender,
            "inclusion": trial.inclusion,
            "exclusion": trial.exclusion,
            "brief_title": trial.brief_title,
            "brief_summary": trial.brief_summary,
            "detailed_description": trial.detailed_description,
            })
    
    with open(TRIAL_PRE_SELECTION_FILE, "w") as f:
        json.dump(trial_selection, f, indent=4)

    

if __name__ == "__main__":
    pt.init()
    index = pt.IndexFactory.of("./ct_index/data.properties")

    diagnoses = ["glaucoma", "anxiety", "COPD", "breast cancer", "covid 19", "rheumatoid arthritis", "sickle cell anemia", "type 2 diabetes"]

    queries = create_topic_categories_dataframe(diagnoses)

    pipeline = pt.BatchRetrieve(index, wmodel="BM25", verbose=True, num_results=2000)

    pipeline.compile()
    results = pipeline.transform(queries)
    print("Tests")
    print(results.head())
    print(results.info())

    documents = results["docno"].unique()
    print(f"Number of unique documents: {len(documents)}")
    print()
    
    for _, query in queries.iterrows():
        print(f"Query: {query['query']}, Number: {query['qid']}")
        print(f"Number of results: {len(results[results['qid'] == query['qid']])}")
        print("Results:")
        # Print the top 10 results (highest score) for this query (qid = query["qid"])
        for j, result in results[results["qid"] == query["qid"]].head(10).iterrows():
            print(f"Trial: {result['docno']}, Score: {result['score']}")
            # print(index.getMetaIndex().getAllItems(result["docid"]))
            print(index.getMetaIndex().getItem("brief_title", result["docid"]))
            
        print()
    
    # parse_results(index, results)
