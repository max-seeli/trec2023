import index
import patient_query
import pandas as pd
import pyterrier as pt

"""
Unprocessed trials indexed
"""
def run_arthur():

    if not index.exists("arthur"):
        trials = pd.read_csv("data/clinical_trials/clinical_trials.csv")

        print(trials.info())
        print(trials.head())
        arthur = index.setup(trials, "arthur", ["docno"], force=True)
    else:
        arthur = index.get("arthur")

    patients = patient_query.generate_patient_queries_from_topics("data/patients/topics2023.xml")

    print(patients.info())
    print(patients.head())

    pipeline = pt.BatchRetrieve(arthur, wmodel="BM25", verbose=True, num_results=1000)

    results = pipeline.transform(patients)

    print(results.info())
    print(results.head())

    pt.io.write_results(results, "data/results/arthur.txt", format="trec", run_name="arthur")


"""
Create two indices:
    - bertha_1: inclusion criteria
    - bertha_2: exclusion criteria
"""
def run_bertha():
    
    trials = pd.read_json("data/clinical_trials/trials_preprocessed.json")

    trials["docno"] = trials.pop("nct_id")
    
    df_b1 = trials[["docno", "inclusion"]]
    df_b1["text"] = df_b1.pop("inclusion").apply(lambda x: " ".join(x))
    b1 = index.setup(df_b1, "bertha_1", ["docno"], force=True)

    df_b2 = trials[["docno", "exclusion"]]
    df_b2["text"] = df_b2.pop("exclusion").apply(lambda x: " ".join(x))
    b2 = index.setup(df_b2, "bertha_2", ["docno"], force=True)

    print("Bertha 1")
    print(b1.getCollectionStatistics().toString())
    print()
    print("Bertha 2")
    print(b2.getCollectionStatistics().toString())
    print()

    patients = pd.read_json("data/patients/patients_preprocessed.json")

    queries = patients[["id", "diagnoses"]]
    queries["qid"] = queries.pop("id")
    queries["query"] = queries.pop("diagnoses").apply(lambda x: " ".join(x))

    # Remove special characters
    queries["query"] = queries["query"].apply(lambda x: x.replace("+", "and").replace("/", "-").replace("'",""))

    # find trials that score high on bertha 1 and low or not at all on bertha 2
    pos = pt.BatchRetrieve(b1, wmodel="BM25")
    neg = pt.BatchRetrieve(b2, wmodel="BM25")
    pipeline = pos + (-1 * neg)

    results = pipeline.transform(queries)

    print(results.info())
    print(results.head())

    pt.io.write_results(results, "data/results/bertha.txt", format="trec", run_name="bertha")



if __name__ == "__main__":
    run_arthur()