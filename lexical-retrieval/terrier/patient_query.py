import xml.etree.ElementTree as ET
import pandas as pd


def generate_patient_queries_from_topics(file):
    tree = ET.parse(file)
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
