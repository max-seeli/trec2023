import pyterrier as pt
import pandas as pd
import xml.etree.ElementTree as ET

pt.init()

index = pt.IndexFactory.of("./ct_index")

# Parse the topics file to get the queries
file_path = "data/patients/topics2023.xml"
tree = ET.parse(file_path)
root = tree.getroot()

# Create a query dataframe for every topic
queries = []
for topic in root:
    # Print number with all the attributes
    patient_tokens = []
    for child in topic:
        patient_tokens.append(child.attrib["name"])
        if child.text is not None:
            patient_tokens.append(child.text.replace("/", "-"))
    patient_query = " ".join(patient_tokens)
    queries.append({"query": patient_query, "qid": topic.attrib["number"]})

# Create a dataframe from the queries
queries = pd.DataFrame(queries)

print(queries.info())


# Create a retrieval pipeline
pipeline = pt.BatchRetrieve(index, wmodel="BM25")

results = pipeline.transform(queries)

# Print the first 10 results
print(results)

# Retrieve the first result
print(results.iloc[0])

# Retrieve the first result's document
print(index.getMetaIndex().getAllItems(results.iloc[0]["docid"]))
