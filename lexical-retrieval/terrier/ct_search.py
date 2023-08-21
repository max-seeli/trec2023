import pyterrier as pt
import pandas as pd
import xml.etree.ElementTree as ET

TOPICS_FILE = "data/patients/topics2023.xml"

def create_query_dataframe():
    tree = ET.parse(TOPICS_FILE)
    root = tree.getroot()

    # Create a query dataframe for every topic
    queries = []
    for topic in root:
        # Print number with all the attributes
        patient_tokens = [topic.attrib["template"]]
        for child in topic:
            patient_tokens.append(child.attrib["name"])
            if child.text is not None:
                patient_tokens.append(child.text.replace("/", "-"))
        patient_query = " ".join(patient_tokens)
        queries.append({"query": patient_query, "qid": topic.attrib["number"]})

    # Create a dataframe from the queries
    queries = pd.DataFrame(queries)

    print(queries.info())
    return queries


def rank_documents(index, queries, num_results_per_query=None):

    # Create a retrieval pipeline
    pipeline = pt.BatchRetrieve(index, wmodel="BM25", verbose=True) 
    
    if num_results_per_query is not None:
        pipeline = pipeline % num_results_per_query

    pipeline.compile()
    results = pipeline.transform(queries) 

    print(results.info())
    return results



def print_results(index, queries, results):

    for _, query in queries.iterrows():
        print(f"Query: {query['query']}, Number: {query['qid']}")
        print("Results:")
        # Print the top 10 results (highest score) for this query (qid = query["qid"])
        for j, result in results[results["qid"] == query["qid"]].head(10).iterrows():
            print(f"Trial: {result['docno']}, Score: {result['score']}")
            # print(index.getMetaIndex().getAllItems(result["docid"]))
            print(index.getMetaIndex().getItem("brief_title", result["docid"]))
            print()
            
        print()


if __name__ == "__main__":

    queries = create_query_dataframe()


    pt.init()
    index = pt.IndexFactory.of("./ct_index")
    results = rank_documents(index, queries, 100)

    print_results(index, queries, results)

