from text_normalization import pipeline
from elasticsearch import Elasticsearch
import json
from dataclasses import asdict

client = Elasticsearch(
    "http://localhost:9200/"
)

#diagnoses = ["glaucoma", "anxiety", "COPD", "breast cancer", "COVID-19", "rheumatoid arthritis", "sickle cell anemia", "type 2 diabetes"]
diagnoses = ["glaucoma", "anxiety"]

entries = []
uids = set()

for diagnosis in diagnoses:
    
    search_query = {
        "size": 10,
        "query": {
            "bool": {
                "must": [
                    {
                        "query_string": {
                            "query": diagnosis
                        }
                    }
                ]
            }
        }
    }

    search_results = client.search(index="trials", body=search_query)

    for hit in search_results["hits"]["hits"]:
        stored_json_data = hit["_source"]

        uid = stored_json_data['nct_id']

        if uid in uids:
            print("Trial {stored_json_data['nct_id']} already found.")
        else:
            inclusion_criteria = stored_json_data['inclusion']
            
            inclusion_criteria_preprocessed = []
            for criterium in inclusion_criteria:
                preprocessed_criteria = pipeline(criterium)
                for preprocessed_criterium in preprocessed_criteria:
                    inclusion_criteria_preprocessed.append(preprocessed_criterium)

            exclusion_criteria = stored_json_data['exclusion']
            
            exclusion_criteria_preprocessed = []
            for criterium in exclusion_criteria:
                preprocessed_criteria = pipeline(criterium)
                for preprocessed_criterium in preprocessed_criteria:
                    exclusion_criteria_preprocessed.append(preprocessed_criterium)

            entries.append({"nct_id": stored_json_data['nct_id'],
                            "inclusion": inclusion_criteria_preprocessed,
                            "exclusion": exclusion_criteria_preprocessed})
print(entries)


