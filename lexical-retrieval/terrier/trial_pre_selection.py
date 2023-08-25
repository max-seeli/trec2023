from argparse import ArgumentParser

import pyterrier as pt 
import pandas as pd
import xml.etree.ElementTree as ET
import json
from tqdm import tqdm
import os
from CTnlp.parsers import parse_clinical_trial

TOPICS_FILE = "data/patients/topics2023.xml"
TOPIC_TEMPLATES = ["glaucoma", "anxiety", "COPD", "breast cancer", "covid 19", "rheumatoid arthritis", "sickle cell anemia", "type 2 diabetes"]

RAW_TRIALS_FOLDER = "data/clinical_trials/raw"
TRIAL_PRE_SELECTION_FILE = "data/clinical_trials/trial_pre_selection_16k.json"
TRIAL_PRE_SELECTION_FILE_SLIM = "data/clinical_trials/trial_pre_selection_16k_slim.json"



def create_topic_templates_query():

    queries = [{"query": query, "qid": qid} for qid, query in enumerate(TOPIC_TEMPLATES)]
    return pd.DataFrame(queries)

def create_patient_query():
    tree = ET.parse(TOPICS_FILE)
    root = tree.getroot()

    queries = []
    for topic in root:
        patient_tokens = [topic.attrib["template"]]
        for child in topic:
            patient_tokens.append(child.attrib["name"])
            if child.text is not None:
                patient_tokens.append(child.text)
        
        patient_tokens = [token.replace("+", "and").replace("/", "-") for token in patient_tokens]
        patient_query = " ".join(patient_tokens)
        
        queries.append({"query": patient_query, "qid": topic.attrib["number"]})

    return pd.DataFrame(queries)
    

def rank_documents(index, queries, num_results_per_query=100):

    pipeline = pt.BatchRetrieve(index, wmodel="BM25", verbose=True, num_results=num_results_per_query)
    pipeline.compile()
    
    results = pipeline.transform(queries)
    return results

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

    # Create a slim version of the pre selection file
    keys_to_remove = ["brief_title", "brief_summary", "detailed_description"]
    trial_selection_slim = [{k: v for k, v in trial.items() if k not in keys_to_remove} for trial in trial_selection]
   
    with open(TRIAL_PRE_SELECTION_FILE_SLIM, "w") as f:
        json.dump(trial_selection_slim, f, indent=4)

def check_overlap(n=100):
    
    if not pt.started(): 
        pt.init()
    index = pt.IndexFactory.of("./ct_index")

    query_patient = create_patient_query()
    query_topic = create_topic_templates_query()

    docs_per_patient_query = n // len(query_patient)
    docs_per_topic_query = n // len(query_topic)

    results_patient = rank_documents(index, query_patient, num_results_per_query=docs_per_patient_query)
    results_topic = rank_documents(index, query_topic, num_results_per_query=docs_per_topic_query)

    patient_documents = results_patient["docno"].unique()
    topic_documents = results_topic["docno"].unique()

    print(f"Number of unique documents for patient queries: {len(patient_documents)}")
    print(f"Number of unique documents for topic queries: {len(topic_documents)}")

    overlap = set(patient_documents).intersection(set(topic_documents))
    print(f"Number of overlapping documents: {len(overlap)}")

if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument("-p", "--patient_queries", action="store_true", help="Use patient queries instead of templates")
    parser.add_argument("-n", "--num_results", type=int, default=100, help="Number of results")
    parser.add_argument("--no_store", action="store_true", help="Do not store results")
    args = parser.parse_args()

    pt.init()
    index = pt.IndexFactory.of("./ct_index")

    if args.patient_queries:
        print("Creating Patient Queries...")
        queries = create_patient_query()
    else:
        print("Creating Topic Template Queries...")
        queries = create_topic_templates_query()

    print(queries.info())

    num_results_per_query = args.num_results // len(queries)

    results = rank_documents(index, queries, num_results_per_query=num_results_per_query)

    for _, query in queries.iterrows():
        print(f"Query: {query['query']}, Number: {query['qid']}")
        print(f"Number of results: {len(results[results['qid'] == query['qid']])}")
        print("Results:")
        # Print the top 10 results (highest score) for this query (qid = query["qid"])
        for j, result in results[results["qid"] == query["qid"]].head(10).iterrows():
            print(f"Trial: {result['docno']}, Score: {result['score']}")
            print(index.getMetaIndex().getItem("brief_title", result["docid"]))
            
        print()

    print(results.head())
    print(results.info())

    documents = results["docno"].unique()
    print(f"Number of unique documents: {len(documents)}")

    if not args.no_store:
        parse_results(index, results)
